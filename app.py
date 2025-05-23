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

    if res.status_code != 200:
        return jsonify({
            "error": "Meraki API call failed",
            "status_code": res.status_code,
            "message": res.text
        }), res.status_code

    try:
        readings = res.json()
    except Exception as e:
        return jsonify({"error": "No se pudo decodificar JSON", "detalle": str(e), "raw": res.text}), 500

    resultados = {}
    for r in readings:
        if r.get("serial") == serial:
        metrica = r.get("metric")
        if not metrica:
            continue  # si no hay metrica, salta a la siguiente
        valor = None

        if metrica == "co2":
            valor = r.get("co2", {}).get("concentration")
        elif metrica == "temperature":
            valor = r.get("temperature", {}).get("celsius")
        elif metrica == "humidity":
            valor = r.get("humidity", {}).get("relativePercentage")
        elif metrica == "pm25":
            valor = r.get("pm25", {}).get("concentration")
        elif metrica == "noise":
            valor = r.get("noise", {}).get("ambient", {}).get("level")
        elif metrica == "tvoc":
            valor = r.get("tvoc", {}).get("concentration")
        elif metrica == "indoorAirQuality":
            valor = r.get("indoorAirQuality", {}).get("score")

        resultados[metrica] = {
            "value": valor,
            "ts": r.get("ts", "")
        
            }

    if resultados:
        return jsonify(resultados)
    else:
        return jsonify({"error": f"No se encontraron métricas para el sensor {serial}"}), 404




if __name__ == "__main__":
    app.run()
