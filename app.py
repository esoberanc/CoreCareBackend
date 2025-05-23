from flask import Flask, jsonify
import requests
import os
from flask import request

app = Flask(__name__)

MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORGANIZATION_ID = os.getenv("MERAKI_ORG_ID")
SENSOR_MT20_SERIAL = os.getenv("SENSOR_MT20_SERIAL")
SENSOR_MT15_SERIAL = os.getenv("SENSOR_MT15_SERIAL")

HEADERS = {
    "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
    "Content-Type": "application/json"
}

@app.route("/")
def index():
    return "Meraki sensor backend is running with organization-level API."

@app.route("/api/puerta")
def puerta():
    url = f"https://api.meraki.com/api/v1/organizations/{ORGANIZATION_ID}/sensor/readings/latest"
    res = requests.get(url, headers=HEADERS)
    readings = res.json()

    for r in readings:
        if r["serial"] == SENSOR_MT20_SERIAL and r["metric"] == "door":
            return jsonify({"open": r["value"], "timestamp": r["ts"]})
    
    return jsonify({"error": "No data found for MT20"}), 404

@app.route("/api/calidad-aire")
def calidad_aire():
    serial = request.args.get("serial")
    if not serial:
        return jsonify({"error": "Falta el parámetro serial"}), 400

    url = f"https://api.meraki.com/api/v1/organizations/{ORGANIZATION_ID}/sensor/readings/latest"
    res = requests.get(url, headers=HEADERS)
    readings = res.json()

    resultados = {}
    for r in readings:
        if r["serial"] == serial:
            resultados[r["metric"]] = {
                "value": r["value"],
                "ts": r["ts"]
            }

    if resultados:
        return jsonify(resultados)
    else:
        return jsonify({"error": f"No data found for serial {serial}"}), 404


if __name__ == "__main__":
    app.run()
