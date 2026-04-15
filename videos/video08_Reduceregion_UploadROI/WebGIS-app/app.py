import ee
import json
import config
from flask import Flask, render_template, jsonify, request

from config import initialize_ee, ROI, SCALE, MAX_PIXELS

# --------------------------------
# Initialize EE
# --------------------------------
initialize_ee()

app = Flask(__name__)


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

        # ✅ UPDATED ROI
        roi = config.ROI

        image = scale(get_landsat(start, end, roi).median()).clip(roi)

        # NDVI
        ndvi = image.normalizedDifference(["SR_B5", "SR_B4"]).rename("ndvi")

        # ReduceRegion
        stats = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=SCALE,
            maxPixels=MAX_PIXELS
        )

        ndvi_value = stats.get("ndvi").getInfo()

        # Visualization
        rgb_map = image.getMapId({
            "bands": ["SR_B4", "SR_B3", "SR_B2"],
            "min": 0,
            "max": 0.3
        })

        ndvi_map = ndvi.getMapId({
            "min": -1,
            "max": 1,
            "palette": ["brown", "yellow", "green"]
        })

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

        # ✅ UPDATE GLOBAL ROI
        config.ROI = ee.Geometry(geom).simplify(100)

        # ✅ Get bounds for zoom
        bounds = config.ROI.bounds().coordinates().getInfo()[0]

        lats = [p[1] for p in bounds]
        lngs = [p[0] for p in bounds]

        return jsonify({
            "status": "ROI updated",
            "bounds": [
                [min(lats), min(lngs)],
                [max(lats), max(lngs)]
            ],
            "geojson": geojson
        })

    except Exception as e:
        print("ROI ERROR:", e)
        return jsonify({"error": str(e)}), 500


# =====================================================
# Run
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)