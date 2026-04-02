import os
import json

from flask import Flask, render_template, jsonify, request

import ee
from config import initialize_ee, ROI, SCALE, MAX_PIXELS


# --------------------------------
# Flask App
# --------------------------------

app = Flask(__name__)


# =====================================================
# Home
# =====================================================

@app.route("/")
def index():
    return render_template("index.html")


# --------SATELLITE DATA UTILS ---------

def get_landsat(start, end):

    return (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(ROI)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUD_COVER", 20)))


def scale(img):

    optical = img.select("SR_B.*").multiply(0.0000275).add(-0.2)
    return img.addBands(optical, None, True)


# =====================================================
# NDVI API + MAP TILES
# =====================================================

@app.route("/get_stats")
def get_stats():

    start = request.args.get("start")
    end = request.args.get("end")

    if not start or not end:
        return jsonify({"error": "Please provide start and end date"}), 400

    image = scale(get_landsat(start, end).median()).clip(ROI)

    # NDVI
    ndvi = image.normalizedDifference(["SR_B5", "SR_B4"]).rename("ndvi")

    # Mean NDVI
    stats = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=ROI,
        scale=SCALE,
        maxPixels=MAX_PIXELS
    )

    ndvi_value = stats.get("ndvi").getInfo()

    # ===============================
    # Visualization (NEW)
    # ===============================

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

        # NEW (for map)
        "rgb": rgb_map["tile_fetcher"].url_format,
        "ndvi": ndvi_map["tile_fetcher"].url_format
    })


# =====================================================
# Run Server
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)