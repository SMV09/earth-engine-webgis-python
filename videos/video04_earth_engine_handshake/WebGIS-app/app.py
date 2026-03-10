from flask import Flask
import ee
from config import initialize_ee

# Initialize Earth Engine
initialize_ee()

app = Flask(__name__)

@app.route("/")
def home():
   return "🌍Earth Engine is initialized!🌍"

if __name__ == "__main__":
   app.run(debug=True)