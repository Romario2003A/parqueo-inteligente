import serial
import time
import csv
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify

# ── Configuracion
PUERTO = "/dev/ttyACM0"
BAUD   = 9600

# ── Estado global
estado = {
    "distancia": 0.0,
    "sonido": 0,
    "llama": 1023,
    "plaza": "LIBRE",
    "incendio": False,
    "total_entradas": 0,
    "ultimo_update": "Sin datos",
}

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="2">
  <title>Parqueo Inteligente</title>
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #0d0d0d;
      color: #eee;
      min-height: 100vh;
      padding: 30px;
    }
    .header {
      text-align: center;
      margin-bottom: 40px;
    }
    .header h1 {
      font-size: 2.5em;
      background: linear-gradient(90deg, #00d4aa, #0088ff);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: 2px;
    }
    .header p {
      color: #555;
      font-size: 0.9em;
      margin-top: 5px;
      letter-spacing: 1px;
    }

    /* ALERTA INCENDIO */
    .alerta-incendio {
      background: #2a0000;
      border: 3px solid #ff0000;
      border-radius: 16px;
      padding: 20px;
      text-align: center;
      margin-bottom: 25px;
      animation: parpadeo 0.5s infinite;
    }
    .alerta-incendio h2 {
      color: #ff0000;
      font-size: 2em;
      letter-spacing: 3px;
    }
    @keyframes parpadeo {
      0%,100% { opacity:1; }
      50%      { opacity:0.6; }
    }

    .grid {
      display: grid;
      grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
      gap: 20px;
      max-width: 1200px;
      margin: 0 auto;
    }
    .card {
      background: #161616;
      border-radius: 16px;
      padding: 25px;
      border: 1px solid #222;
      text-align: center;
      transition: 0.3s;
    }
    .card:hover { border-color: #333; transform: translateY(-2px); }
    .card .label {
      font-size: 0.75em;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: #555;
      margin-bottom: 15px;
    }
    .card .value { font-size: 2.8em; font-weight: bold; }
    .libre   { border-color: #00ff88 !important; box-shadow: 0 0 20px #00ff8820; }
    .ocupado { border-color: #ff3355 !important; box-shadow: 0 0 20px #ff335520; }
    .fuego   { border-color: #ff0000 !important; box-shadow: 0 0 30px #ff000050; background: #1a0000 !important; }
    .verde   { color: #00ff88; }
    .rojo    { color: #ff3355; }
    .azul    { color: #0088ff; }
    .amarillo{ color: #ffcc00; }
    .naranja { color: #ff6600; }
    .blanco  { color: #fff; }
    .dot {
      display: inline-block;
      width: 14px; height: 14px;
      border-radius: 50%;
      margin-right: 8px;
      animation: pulse 1.5s infinite;
      vertical-align: middle;
    }
    .dot-verde  { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
    .dot-rojo   { background: #ff3355; box-shadow: 0 0 10px #ff3355; }
    .dot-fuego  { background: #ff0000; box-shadow: 0 0 10px #ff0000; animation: parpadeo 0.3s infinite !important; }
    @keyframes pulse {
      0%,100% { opacity:1; transform:scale(1); }
      50%      { opacity:0.5; transform:scale(0.8); }
    }
    .barra-container {
      background: #222;
      border-radius: 10px;
      height: 10px;
      margin-top: 15px;
      overflow: hidden;
    }
    .barra-fill {
      height: 100%;
      border-radius: 10px;
      background: linear-gradient(90deg, #00ff88, #ffcc00, #ff3355);
      transition: width 0.5s;
    }
    .footer {
      text-align: center;
      margin-top: 30px;
      color: #333;
      font-size: 0.8em;
      letter-spacing: 1px;
    }
    .badge {
      display: inline-block;
      background: #1a1a1a;
      border: 1px solid #333;
      border-radius: 20px;
      padding: 4px 14px;
      font-size: 0.75em;
      color: #555;
      margin-top: 10px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🅿 PARQUEO INTELIGENTE</h1>
    <p>Raspberry Pi Zero 2W + Arduino UNO R3 · Sistema Embebido Bicefalo</p>
  </div>

  {% if data.incendio %}
  <div class="alerta-incendio">
    <h2>🔥 ALERTA DE INCENDIO DETECTADA 🔥</h2>
    <p style="color:#ff6600; margin-top:8px;">Barrera abierta para evacuacion — Contactar emergencias</p>
  </div>
  {% endif %}

  <div class="grid">
    <div class="card {{ 'fuego' if data.incendio else ('ocupado' if data.plaza == 'OCUPADO' else 'libre') }}">
      <div class="label">Estado de la Plaza</div>
      <div class="value {{ 'naranja' if data.incendio else ('rojo' if data.plaza == 'OCUPADO' else 'verde') }}">
        <span class="dot {{ 'dot-fuego' if data.incendio else ('dot-rojo' if data.plaza == 'OCUPADO' else 'dot-verde') }}"></span>
        {{ '🔥 INCENDIO' if data.incendio else data.plaza }}
      </div>
      <div class="badge">
        {% if data.incendio %}
          ⚠ Emergencia activa
        {% elif data.plaza == 'OCUPADO' %}
          🚗 Vehiculo detectado
        {% else %}
          ✅ Plaza disponible
        {% endif %}
      </div>
    </div>

    <div class="card">
      <div class="label">Distancia</div>
      <div class="value azul">
        {{ data.distancia }}<span style="font-size:0.5em"> cm</span>
      </div>
      <div class="badge">HC-SR04</div>
    </div>

    <div class="card">
      <div class="label">Nivel de Ruido</div>
      <div class="value amarillo">{{ data.sonido }}</div>
      <div class="barra-container">
        <div class="barra-fill" style="width: {{ [data.sonido / 10, 100] | min }}%"></div>
      </div>
      <div class="badge">Sound Sensor</div>
    </div>

    <div class="card {{ 'fuego' if data.incendio else '' }}">
      <div class="label">Sensor de Llama</div>
      <div class="value {{ 'naranja' if data.incendio else 'verde' }}">
        {{ '🔥' if data.incendio else '✅' }}
      </div>
      <div class="badge">{{ 'FUEGO!' if data.incendio else 'Normal - ' + data.llama|string }}</div>
    </div>

    <div class="card">
      <div class="label">Entradas Hoy</div>
      <div class="value blanco">{{ data.total_entradas }}</div>
      <div class="badge">Total registradas</div>
    </div>
  </div>

  <div class="footer">
    Ultima actualizacion: {{ data.ultimo_update }} &nbsp;·&nbsp;
    <a href="/api" style="color:#333;">API JSON</a>
  </div>
</body>
</html>
"""

def guardar_csv(distancia, sonido, llama, plaza, incendio):
    with open("registro.csv", "a", newline="") as f:
        csv.writer(f).writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            distancia, sonido, llama, plaza,
            "INCENDIO" if incendio else "OK"
        ])

def hilo_serial():
    try:
        with open("registro.csv", "x", newline="") as f:
            csv.writer(f).writerow([
                "timestamp", "distancia", "sonido", "llama", "estado", "emergencia"
            ])
    except FileExistsError:
        pass

    try:
        ser = serial.Serial(PUERTO, BAUD, timeout=2)
        time.sleep(2)
        print(f"[OK] Arduino conectado en {PUERTO}")
        ser.write(b"PING\n")
        resp = ser.readline().decode("utf-8").strip()
        print(f"[PING] {resp}")
    except serial.SerialException as e:
        print(f"[ERROR] No se encontro Arduino: {e}")
        return

    while True:
        try:
            linea = ser.readline().decode("utf-8").strip()
            if not linea:
                continue

            print(f"[SERIAL] {linea}")

            # Alerta de incendio
            if linea == "INCENDIO":
                estado["incendio"] = True
                estado["ultimo_update"] = datetime.now().strftime("%H:%M:%S")
                print("[ALERTA] INCENDIO DETECTADO")

            elif linea == "INCENDIO_OFF":
                estado["incendio"] = False
                estado["ultimo_update"] = datetime.now().strftime("%H:%M:%S")
                print("[OK] Incendio apagado")

            # Datos normales
            elif linea.startswith("DATOS,"):
                partes = linea.split(",")
                if len(partes) == 5:
                    distancia = float(partes[1])
                    sonido    = int(partes[2])
                    llama     = int(partes[3])
                    plaza     = partes[4]

                    if plaza == "OCUPADO" and estado["plaza"] == "LIBRE":
                        estado["total_entradas"] += 1

                    estado.update({
                        "distancia":     round(distancia, 1),
                        "sonido":        sonido,
                        "llama":         llama,
                        "plaza":         plaza,
                        "ultimo_update": datetime.now().strftime("%H:%M:%S")
                    })

                    guardar_csv(distancia, sonido, llama, plaza, estado["incendio"])

        except ValueError:
            print("[WARN] Dato invalido")
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(1)

@app.route("/")
def dashboard():
    return render_template_string(HTML, data=estado)

@app.route("/api")
def api():
    return jsonify(estado)

if __name__ == "__main__":
    t = threading.Thread(target=hilo_serial, daemon=True)
    t.start()
    print("[FLASK] http://10.166.58.83:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
