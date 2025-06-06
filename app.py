from flask import Flask, jsonify
import requests
import os
from flask import request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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
    url = f"https://api.meraki.com/api/v1/organizations/{ORGANIZATION_ID}/sensor/readings/latest"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        return jsonify({"error": "Meraki API error", "status": res.status_code}), res.status_code

    try:
        readings = res.json()
    except:
        return jsonify({"error": "No se pudo parsear la respuesta de Meraki"}), 500

    resultados = {}
    for sensor in readings:
        if sensor.get("serial") != SENSOR_MT15_SERIAL:
             continue

        for r in sensor.get("readings", []):
            metrica = r.get("metric")
            if not metrica:
                continue

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

            if valor is not None:
                resultados[metrica] = {
                    "value": valor,
                    "ts": r.get("ts", "")
              }

    if resultados:
        return jsonify(resultados)
    else:
        return jsonify({"error": f"No se encontraron métricas para el sensor {SENSOR_MT15_SERIAL}"}), 404

@app.route("/api/vitales")
def vitales():
    base_url = os.getenv("HA_BASE_URL")
    token = os.getenv("HA_TOKEN")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    sensores = {
        "heartRate": "sensor.seeedstudio_mr60bha2_kit_b46e04_real_time_heart_rate",
        "breathRate": "sensor.seeedstudio_mr60bha2_kit_b46e04_real_time_respiratory_rate"
           }

    resultados = {}
    for nombre, entidad in sensores.items():
        url = f"{base_url}/api/states/{entidad}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            print(f"[{nombre}] {url} -> {res.status_code}")
            if res.status_code == 200:
                datos = res.json()
                resultados[nombre] = {
                    "value": datos.get("state"),
                    "unit": datos.get("attributes", {}).get("unit_of_measurement", "")
                }
            else:
                resultados[nombre] = {"error": f"Error {res.status_code}"}
        except Exception as e:
            resultados[nombre] = {"error": str(e)}

    return jsonify(resultados)

@app.route("/api/caidas")
def caidas():
    base_url = os.getenv("HA_BASE_URL")
    token = os.getenv("HA_TOKEN")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    sensores = {
        "falling": "sensor.seeedstudio_mr60fda2_kit_b471ec_falling_information",
        "presence": "binary_sensor.seeedstudio_mr60fda2_kit_b471ec_person_information"
    }

    resultados = {}
    for nombre, entidad in sensores.items():
        url = f"{base_url}/api/states/{entidad}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                datos = res.json()
                resultados[nombre] = datos.get("state", "unknown")
            else:
                resultados[nombre] = f"error {res.status_code}"
        except Exception as e:
            resultados[nombre] = str(e)

    return jsonify(resultados)


@app.route("/api/test-home-assistant")
def test_home_assistant():
    base_url = os.getenv("HA_BASE_URL")
    token = os.getenv("HA_TOKEN")

    url = f"{base_url}/api/"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        return jsonify({
            "status_code": res.status_code,
            "body": res.text,
            "ok": res.ok
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "ok": False
        })

def obtener_datos_sensor_mt15():
    url = f"https://api.meraki.com/api/v1/organizations/{ORGANIZATION_ID}/sensor/readings/latest"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        raise Exception("Meraki API error")

    readings = res.json()
    resultados = {}

    for sensor in readings:
        if sensor.get("serial") != SENSOR_MT15_SERIAL:
            continue

        for r in sensor.get("readings", []):
            metrica = r.get("metric")
            if not metrica:
                continue

            valor = None
            if metrica == "temperature":
                valor = r.get("temperature", {}).get("celsius")
            elif metrica == "humidity":
                valor = r.get("humidity", {}).get("relativePercentage")

            if valor is not None:
                resultados[metrica] = valor

    return {
        "temperature": resultados.get("temperature"),
        "humidity": resultados.get("humidity")
    }

def obtener_datos_sensor_mt20():
    url = f"https://api.meraki.com/api/v1/organizations/{ORGANIZATION_ID}/sensor/readings/latest"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        raise Exception("Meraki API error")

    readings = res.json()

    for r in readings:
        if r["serial"] == SENSOR_MT20_SERIAL and r["metric"] == "door":
            return {
                "door": r["value"]  # True = abierta, False = cerrada
            }

    raise Exception("No se encontró lectura de apertura para el sensor MT20")


@app.route("/api/sensores/<serial>")
def obtener_sensor(serial):
    try:
        print(f"🔍 Recibida petición para serial: {serial}")
        print(f"👉 MT15: {SENSOR_MT15_SERIAL}")
        print(f"👉 MT20: {SENSOR_MT20_SERIAL}")

        if serial == SENSOR_MT15_SERIAL:
            data = obtener_datos_sensor_mt15()
            print(f"📦 Datos MT15: {data}")
            return jsonify({
                "temperature": {
                    "value": data.get("temperature"),
                    "unit": "°C"
                },
                "humidity": {
                    "value": data.get("humidity"),
                    "unit": "%"
                }
            })

        elif serial == SENSOR_MT20_SERIAL:
            data = obtener_datos_sensor_mt20()
    print(f"📦 Datos MT20: {data}")
    return jsonify({
        "door": {
            "value": data.get("door"),
            "unit": "abierta" if data.get("door") else "cerrada"
        }
    })


        print("❌ Serial no reconocido")
        return jsonify({"error": "Serial no reconocido"}), 404

    except Exception as e:
        print(f"💥 Error interno: {e}")
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run()
