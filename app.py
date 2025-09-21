from flask import Flask, render_template, request, jsonify
import requests, random, os
import pandas as pd
from geopy.distance import geodesic  # find nearest state
from openai import OpenAI

app = Flask(__name__)

# --- OpenAI API client ---
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# --- Load CSV with statewise disease data ---
states_df = pd.read_csv('data/india_diseases_combined.csv')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data", methods=["POST"])
def data():
    user_data = request.get_json()
    lat = float(user_data.get("lat"))
    lon = float(user_data.get("lon"))

    # find nearest state by lat/lon from CSV
    def nearest_state(lat, lon):
        coords = (lat, lon)
        states_df['distance'] = states_df.apply(lambda r: geodesic(coords, (r['latitude'], r['longitude'])).km, axis=1)
        nearest = states_df.loc[states_df['distance'].idxmin()]
        return nearest

    nearest = nearest_state(lat, lon)

    # WEATHER: Open-Meteo API
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    weather = requests.get(weather_url).json().get("current_weather", {})

    temp = weather.get("temperature", 30)
    wind = weather.get("windspeed", 5)

    # Real disease data from CSV
    dengue = nearest.get('dengue_cases', random.randint(0,200))
    malaria = nearest.get('malaria_cases', random.randint(0,200))
    chikungunya = nearest.get('chikungunya_cases', random.randint(0,200))
    state_name = nearest.get('state', 'Unknown')

    total_cases = dengue + malaria + chikungunya
    risk_level = "green"
    if total_cases > 400:
        risk_level = "red"
    elif total_cases > 200:
        risk_level = "yellow"

    precautions = {
        "red": [
            "Avoid stagnant water areas",
            "Wear full-sleeve clothing",
            "Use mosquito repellents",
            "Stay indoors during peak heat"
        ],
        "yellow": [
            "Clean water storage regularly",
            "Use bed nets at night",
            "Stay hydrated"
        ],
        "green": [
            "Conditions safe but stay alert",
            "Maintain hygiene",
            "Regular health check-ups"
        ]
    }

    return jsonify({
        "state": state_name,
        "weather": {
            "temperature": temp,
            "windspeed": wind
        },
        "health": {
            "dengue": int(dengue),
            "malaria": int(malaria),
            "chikungunya": int(chikungunya),
            "risk": risk_level,
            "precautions": precautions[risk_level]
        },
        "coords": [lat, lon]
    })

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.get_json().get("message", "")
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":"You are a helpful health & weather assistant for India."},
                  {"role":"user","content":user_message}]
    )
    reply = completion.choices[0].message.content
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
