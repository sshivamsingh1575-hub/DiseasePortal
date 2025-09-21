from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import random
from openai import OpenAI
import os

app = Flask(__name__)

# --- OpenAI API client ---
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# --- Load the CSV with all states ---
states_df = pd.read_csv("data/india_diseases_combined.csv")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data", methods=["POST"])
def data():
    user_data = request.get_json()
    lat = float(user_data.get("lat"))
    lon = float(user_data.get("lon"))

    # Find nearest state by distance
    coords = (lat, lon)
    states_df['distance'] = states_df.apply(
        lambda r: ((r['Latitude'] - lat)**2 + (r['Longitude'] - lon)**2)**0.5, axis=1
    )
    nearest = states_df.loc[states_df['distance'].idxmin()]

    # WEATHER: Open-Meteo API
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    weather = requests.get(weather_url).json().get("current_weather", {})

    temp = weather.get("temperature", 30)
    wind = weather.get("windspeed", 5)

    dengue = int(nearest['Cases']) if not pd.isna(nearest['Cases']) else random.randint(0, 200)
    malaria = int(nearest['Positive']) if not pd.isna(nearest['Positive']) else random.randint(0, 200)
    chikungunya = int(nearest['Deaths_x']) if not pd.isna(nearest['Deaths_x']) else random.randint(0, 200)

    total_cases = dengue + malaria + chikungunya
    if total_cases > 400:
        risk_level = "red"
    elif total_cases > 200:
        risk_level = "yellow"
    else:
        risk_level = "green"

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
        "state": nearest['State'],
        "weather": {
            "temperature": temp,
            "windspeed": wind
        },
        "health": {
            "dengue": dengue,
            "malaria": malaria,
            "chikungunya": chikungunya,
            "risk": risk_level,
            "precautions": precautions[risk_level]
        }
    })

@app.route("/all_states", methods=["GET"])
def all_states():
    state_list = []
    for _, row in states_df.iterrows():
        dengue = int(row['Cases']) if not pd.isna(row['Cases']) else 0
        malaria = int(row['Positive']) if not pd.isna(row['Positive']) else 0
        chikungunya = int(row['Deaths_x']) if not pd.isna(row['Deaths_x']) else 0
        total_cases = dengue + malaria + chikungunya
        if total_cases > 400:
            risk_level = "red"
        elif total_cases > 200:
            risk_level = "yellow"
        else:
            risk_level = "green"
        state_list.append({
            "state": row['State'],
            "lat": row['Latitude'],
            "lon": row['Longitude'],
            "dengue": dengue,
            "malaria": malaria,
            "chikungunya": chikungunya,
            "risk": risk_level
        })
    return jsonify(state_list)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.get_json().get("message", "")
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":"You are a helpful health & weather assistant."},
                  {"role":"user","content":user_message}]
    )
    reply = completion.choices[0].message.content
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
