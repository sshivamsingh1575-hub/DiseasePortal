import os
import requests
import folium
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# --- Weather + Health data from APIs ---
def get_weather(lat, lon):
    # Open-Meteo API (free)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,wind_speed_10m&current_weather=true"
    r = requests.get(url)
    data = r.json()
    current = data.get('current_weather', {})
    return {
        "temperature": current.get("temperature"),
        "windspeed": current.get("windspeed"),
        "precipitation": current.get("precipitation", 0)
    }

def get_health_data(lat, lon):
    # Simulated risk zones for now
    import random
    dengue = random.randint(0, 1500)
    malaria = random.randint(0, 1500)
    chikungunya = random.randint(0, 1500)
    total = dengue + malaria + chikungunya
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
        "chikungunya": chikungunya,
        "risk": risk
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def data():
    user_lat = request.json.get('lat')
    user_lon = request.json.get('lon')

    w = get_weather(user_lat, user_lon)
    h = get_health_data(user_lat, user_lon)

    # Generate a map
    m = folium.Map(location=[user_lat, user_lon], zoom_start=8)
    folium.CircleMarker(
        location=[user_lat, user_lon],
        radius=15,
        color=h['risk'],
        fill=True,
        fill_color=h['risk'],
        popup=f"Dengue:{h['dengue']} Malaria:{h['malaria']} Chikungunya:{h['chikungunya']}"
    ).add_to(m)
    m.save('templates/map_temp.html')

    return jsonify({
        "weather": w,
        "health": h
    })

@app.route('/map')
def map_view():
    return render_template('map_temp.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    prompt = f"""
You are Health & Weather Advisor Bot.
The user asked: {user_input}.
Provide helpful, accurate information.
If you know location or conditions, include relevant health and safety advice.
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant for health, weather, and safety."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        answer = f"Error: {e}"
    return jsonify({"reply": answer})

if __name__ == '__main__':
    app.run(debug=True)
