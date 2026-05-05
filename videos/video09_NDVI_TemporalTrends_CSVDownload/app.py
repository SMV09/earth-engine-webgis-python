import ee
import json
import config
from flask import Flask, render_template, jsonify, request, Response

from config import initialize_ee, ROI, SCALE, MAX_PIXELS

# --------------------------------
# Initialize EE
# --------------------------------
initialize_ee()

app = Flask(__name__)

# --------------------------------
# Constants
# --------------------------------
TIMESERIES_SCALE = 500

# =====================================================
# Helpers
# =====================================================

def get_roi():
    return config.ROI

# =====================================================
# Home
# =====================================================
@app.route("/")
def index():
    return render_template("index.html")

# =====================================================
# Satellite Utils
# =====================================================

def get_landsat(start, end, roi):
    return (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(roi)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUD_COVER", 20)))

def scale(img):
    optical = img.select("SR_B.*").multiply(0.0000275).add(-0.2)
    return img.addBands(optical, None, True)

# =====================================================
# NDVI API
# =====================================================

@app.route("/get_stats")
def get_stats():
    try:
        start = request.args.get("start")
        end = request.args.get("end")

        if not start or not end:
            return jsonify({"error": "Provide start and end date"}), 400

        roi = config.ROI
        image = scale(get_landsat(start, end, roi).median()).clip(roi)

        # NDVI Calculation
        ndvi = image.normalizedDifference(["SR_B5", "SR_B4"]).rename("ndvi")

        # ReduceRegion for Mean
        stats = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=SCALE,
            maxPixels=MAX_PIXELS
        )

        ndvi_value = stats.get("ndvi").getInfo()

        # Map IDs for Leaflet
        rgb_map = image.getMapId({"bands": ["SR_B4", "SR_B3", "SR_B2"], "min": 0, "max": 0.3})
        ndvi_map = ndvi.getMapId({"min": -1, "max": 1, "palette": ["brown", "yellow", "green"]})

        return jsonify({
            "start": start,
            "end": end,
            "mean_ndvi": ndvi_value,
            "rgb": rgb_map["tile_fetcher"].url_format,
            "ndvi": ndvi_map["tile_fetcher"].url_format
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# Upload ROI 
# =====================================================

@app.route("/upload_roi", methods=["POST"])
def upload_roi():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file"}), 400

        geojson = json.load(file)
        geom = geojson["features"][0]["geometry"]

        config.ROI = ee.Geometry(geom).simplify(100)
        bounds = config.ROI.bounds().coordinates().getInfo()[0]

        lats = [p[1] for p in bounds]
        lngs = [p[0] for p in bounds]

        return jsonify({
            "status": "ROI updated",
            "bounds": [[min(lats), min(lngs)], [max(lats), max(lngs)]],
            "geojson": geojson
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====================================================
# Time Series (5 Years) Logic
# =====================================================

def run_timeseries(end_str, roi):
    end = ee.Date(end_str)
    start = end.advance(-5, "year")

    def monthly_feature(n):
        month_start = start.advance(n, "month")
        month_end = month_start.advance(1, "month")

        collection = get_landsat(month_start, month_end, roi).map(scale)
        image = collection.median()
        ndvi = image.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")

        # Check if imagery exists to prevent "Band Not Found" errors
        stats = ee.Dictionary(ee.Algorithms.If(
            collection.size().gt(0),
            ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=TIMESERIES_SCALE,
                maxPixels=1e13,
                bestEffort=True
            ),
            ee.Dictionary({"NDVI": None})
        ))

        return ee.Feature(None, {
            "date": month_start.format("YYYY-MM"),
            "NDVI": stats.get("NDVI")
        })

    months = ee.List.sequence(0, 59)
    return ee.FeatureCollection(months.map(monthly_feature))

@app.route("/timeseries")
def timeseries():
    try:
        end_str = request.args.get("end")
        if not end_str:
            return jsonify({"error": "Missing end date"}), 400

        features = run_timeseries(end_str, get_roi())
        return jsonify(features.getInfo())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# Download CSV
# =====================================================

@app.route("/download_csv")
def download_csv():
    try:
        end_str = request.args.get("end")
        if not end_str:
            return jsonify({"error": "Missing end date"}), 400

        data = run_timeseries(end_str, get_roi()).getInfo()
        rows = [["Date", "NDVI"]]
        
        for feature in data["features"]:
            props = feature["properties"]
            rows.append([props["date"], props.get("NDVI")])

        def generate():
            for row in rows:
                yield ",".join(map(str, row)) + "\n"

        return Response(
            generate(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=ndvi_timeseries_{end_str}.csv"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)