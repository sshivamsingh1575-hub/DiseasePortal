import os
import random
import requests
import folium
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    r = requests.get(url, timeout=10)
    data = r.json()
    current = data.get('current_weather', {})
    return {
        "temperature": current.get("temperature"),
        "windspeed": current.get("windspeed"),
        "weathercode": current.get("weathercode")
    }

def get_health_data(lat, lon):
    dengue = random.randint(0, 1500)
    malaria = random.randint(0, 1500)
    chik = random.randint(0, 1500)
    total = dengue + malaria + chik
    if total > 2000:
        risk = "red"
    elif total > 1000:
        risk = "yellow"
    elif total < 200:
        risk = "green"
    else:
        risk = "purple"
    return {
        "dengue": dengue,
        "malaria": malaria,
        "chikungunya": chik,
        "risk": risk
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def data():
    lat = float(request.json.get('lat'))
    lon = float(request.json.get('lon'))

    w = get_weather(lat, lon)
    h = get_health_data(lat, lon)

    # Build folium map centered on location with satellite tiles
    m = folium.Map(location=[lat, lon], zoom_start=11, tiles=None)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Satellite",
        overlay=False,
        control=True
    ).add_to(m)

    # Add risk marker
    folium.CircleMarker(
        location=[lat, lon],
        radius=25,
        color=h['risk'],
        fill=True,
        fill_color=h['risk'],
        popup=f"<b>Risk Level: {h['risk']}</b><br>Dengue:{h['dengue']}<br>Malaria:{h['malaria']}<br>Chik:{h['chikungunya']}"
    ).add_to(m)

    m.save('templates/map_temp.html')

    return jsonify({"weather": w, "health": h})

@app.route('/map')
def map_view():
    return render_template('map_temp.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    prompt = f"You are a health & weather advisor. User asked: {user_input}. Give clear advice."

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        answer = f"Error: {e}"

    return jsonify({"reply": answer})

if __name__ == '__main__':
    app.run(debug=True)

