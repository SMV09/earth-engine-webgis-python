import ee
import time

# -----------------------------
# Earth Engine Initialization
# -----------------------------

def initialize_ee():

    PROJECT_ID = "YOUR_PROJECT_ID"

    print("BOOT: Starting WebGIS Engine...")
    t0 = time.time()

    try:
        ee.Initialize(project=PROJECT_ID)
        print(f"EE: Connected to {PROJECT_ID} in {round(time.time()-t0,2)}s")

    except Exception:
        print("EE: Login required. Opening browser...")
        ee.Authenticate()
        ee.Initialize(project=PROJECT_ID)


# ==========================================
# 2. Global Project Constants
# ==========================================

# Run the initialization on startup
initialize_ee()

# Define the study area (Region of Interest)
# Format: [Min Longitude, Min Latitude, Max Longitude, Max Latitude]
ROI = ee.Geometry.Rectangle([75.8, 10.4, 76.5, 11.0])

# Processing settings: Scale is in meters (30m for Landsat)
SCALE = 30
MAX_PIXELS = 1e13