import ee
import time

# ==========================================
# 1. Earth Engine Connection Setup
# ==========================================

def initialize_ee():
    """ Handles authentication and connection to Google Earth Engine """
    
    # Replace this with your own Google Cloud Project ID
    PROJECT_ID = "YOUR_CLOUD_PROJECT_ID"

    print("BOOT: Starting WebGIS Engine...")
    t0 = time.time()

    try:
        # Attempt to connect using the Project ID
        ee.Initialize(project=PROJECT_ID)
        print(f"EE: Connected to {PROJECT_ID} in {round(time.time()-t0,2)}s")

    except Exception:
        # If connection fails, trigger the browser-based login
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