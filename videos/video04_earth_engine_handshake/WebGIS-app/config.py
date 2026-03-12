import ee
import time

def initialize_ee():
    # Use the Project ID (the one with numbers)
    PROJECT_ID = "YOUR_PROJECT_ID"
   
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


