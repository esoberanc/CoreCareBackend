from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")  # Asegúrate de configurarlo en Render
NETWORK_ID = os.getenv("MERAKI_NETWORK_ID")
SENSOR_MT20_SERIAL = os.getenv("SENSOR_MT20_SERIAL")
SENSOR_MT15_SERIAL = os.getenv("SENSOR_MT15_SERIAL")

HEADERS = {
    "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
    "Content-Type": "application/json"
}

@app.route("/")
def index():
    return "Meraki sensor backend is running!"

@app.route("/api/puerta")
def puerta():
    url = f"https://api.meraki.com/api/v1/networks/{NETWORK_ID}/sensor/stats/latest?serials[]={SENSOR_MT20_SERIAL}"
    response = requests.get(url, headers=HEADERS)
    return jsonify(response.json())

@app.route("/api/calidad-aire")
def calidad_aire():
    url = f"https://api.meraki.com/api/v1/networks/{NETWORK_ID}/sensor/stats/latest?serials[]={SENSOR_MT15_SERIAL}"
    response = requests.get(url, headers=HEADERS)
    return jsonify(response.json())

if __name__ == "__main__":
    app.run()
