from flask import Flask, render_template, request, jsonify
import requests
import random
from openai import OpenAI
import os

app = Flask(__name__)

# --- OpenAI API client ---
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data", methods=["POST"])
def data():
    user_data = request.get_json()
    lat = user_data.get("lat")
    lon = user_data.get("lon")

    # WEATHER: Open-Meteo API
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    weather = requests.get(weather_url).json().get("current_weather", {})

    temp = weather.get("temperature", 30)
    wind = weather.get("windspeed", 5)

    # MOCK NASA/DISEASE Data:
    dengue = random.randint(0, 200)
    malaria = random.randint(0, 200)
    chikungunya = random.randint(0, 200)

    risk_level = "green"
    if dengue + malaria + chikungunya > 400:
        risk_level = "red"
    elif dengue + malaria + chikungunya > 200:
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
