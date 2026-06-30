import ee
import time
import json
from google.cloud import secretmanager


def initialize_ee():

    PROJECT_ID = "YOUR CLOUD PROJECT ID"
    SECRET_ID = "gee-secret" // Secret Manager Name

    print("BOOT: Starting WebGIS Engine...")
    t0 = time.time()

    try:
        client = secretmanager.SecretManagerServiceClient()

        name = f"projects/{PROJECT_ID}/secrets/{SECRET_ID}/versions/latest"
        response = client.access_secret_version(name=name)

        key_data = json.loads(response.payload.data.decode("UTF-8"))

        credentials = ee.ServiceAccountCredentials(
            key_data["client_email"],
            key_data=json.dumps(key_data)
        )

        ee.Initialize(credentials)

        print(f"✅ EE initialized in {round(time.time()-t0, 2)}s")

    except Exception as e:
        print("❌ EE Initialization failed:", str(e))
        raise


ROI_COORDS = [75.8, 10.4, 76.5, 11.0]

SCALE = 30
MAX_PIXELS = 1e13


def get_roi():
    return ee.Geometry.Rectangle(ROI_COORDS)