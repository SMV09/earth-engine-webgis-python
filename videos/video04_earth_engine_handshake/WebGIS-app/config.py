import ee
import time

def initialize_ee():
    # Use the Project ID (the one with numbers)
    PROJECT_ID = "climate-tech-487705"
   
    print("BOOT: Starting WebGIS Engine...")
    t0 = time.time()
   
    try:
        # Try to initialize with the explicit Project ID
        ee.Initialize(project=PROJECT_ID)
        print(f"EE: Connected to {PROJECT_ID} in {round(time.time() - t0, 2)}s")
       
    except Exception as e:
            print(f"EE: Login required. Opening browser...")
            ee.Authenticate()
            ee.Initialize(project=PROJECT_ID)
















# ===============================
# App Constants (Wrapped in a clasS or function)
# ===============================


def get_roi():
    """Returns the ROI only after initialization is done"""
    return ee.Geometry.Rectangle([75.8, 10.4, 76.5, 11.0])


# Alternatively, if app.py expects variables,
# you MUST call initialize_ee() inside config.py itself:


initialize_ee() # <--- ADD THIS LINE HERE


ROI = ee.Geometry.Rectangle([75.8, 10.4, 76.5, 11.0])
SCALE = 30
MAX_PIXELS = 1e13