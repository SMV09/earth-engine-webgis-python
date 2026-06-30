import os
import ee
from flask import Flask, render_template, jsonify, request

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import initialize_ee, get_roi, SCALE, MAX_PIXELS

# --------------------------------
# Initialize EE
# --------------------------------
initialize_ee()

# --------------------------------
# Flask App
# --------------------------------
app = Flask(__name__)

# --------------------------------
# Rate Limiter (IMPORTANT)
# --------------------------------
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["50 per hour"]  # global safety
)


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
@limiter.limit("10 per minute")   # endpoint protection
def get_stats():

    try:
        start = request.args.get("start")
        end = request.args.get("end")

        if not start or not end:
            return jsonify({"error": "Provide start and end date"}), 400

        roi = get_roi()

        image = scale(get_landsat(start, end, roi).median()).clip(roi)

        # NDVI
        ndvi = image.normalizedDifference(["SR_B5", "SR_B4"]).rename("ndvi")

        # Mean NDVI
        stats = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=SCALE,
            maxPixels=MAX_PIXELS
        )

        # Safe extraction
        ndvi_value = stats.get("ndvi")
        ndvi_value = ndvi_value.getInfo() if ndvi_value else None

        # Visualization
        rgb_vis = {
            "bands": ["SR_B4", "SR_B3", "SR_B2"],
            "min": 0,
            "max": 0.3
        }

        ndvi_vis = {
            "min": -1,
            "max": 1,
            "palette": ["brown", "yellow", "green"]
        }

        rgb_map = image.getMapId(rgb_vis)
        ndvi_map = ndvi.getMapId(ndvi_vis)

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
# Run Server (Cloud Run Compatible)
# =====================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)