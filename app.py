from flask import Flask, render_template, request, jsonify
import requests, sqlite3, os
from openai import OpenAI
from datetime import date

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---- DB Connection (India health data) ----
def get_db_connection():
    conn = sqlite3.connect('data/database.db')  # same DB you used for India states
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data", methods=["POST"])
def data():
    user_data = request.get_json()
    lat = user_data.get("lat")
    lon = user_data.get("lon")

    # ---- NASA POWER WEATHER ----
    today = date.today().strftime("%Y%m%d")
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MAX,T2M_MIN,PRECTOTCORR&start={today}&end={today}&latitude={lat}&longitude={lon}&community=ag"
    nasa = requests.get(url).json()
    try:
        # latest day data
        data_day = list(nasa['properties']['parameter']['T2M_MAX'].keys())[0]
        max_temp = nasa['properties']['parameter']['T2M_MAX'][data_day]
        min_temp = nasa['properties']['parameter']['T2M_MIN'][data_day]
        precip = nasa['properties']['parameter']['PRECTOTCORR'][data_day]
    except:
        max_temp, min_temp, precip = 30, 20, 2

    # ---- Get India disease data from DB ----
    # If you know the nearest state, map lat/lon to state here.
    # For demo we just pick Maharashtra row:
    conn = get_db_connection()
    state = conn.execute("SELECT * FROM states WHERE name='Maharashtra'").fetchone()
    conn.close()

    dengue = state['dengue_cases']
    malaria = state['malaria_cases']
    chikungunya = state['chikungunya_cases']

    total_cases = dengue + malaria + chikungunya
    if total_cases > 1500:
        risk_level = "red"
    elif total_cases > 500:
        risk_level = "yellow"
    else:
        risk_level = "green"

    return jsonify({
        "weather": {
            "max_temp": max_temp,
            "min_temp": min_temp,
            "precipitation": precip
        },
        "health": {
            "state": state['name'],
            "dengue": dengue,
            "malaria": malaria,
            "chikungunya": chikungunya,
            "risk": risk_level
        }
    })

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.get_json().get("message", "")
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful health & weather advisor using NASA climate data and India disease DB."},
            {"role": "user", "content": user_message}
        ],
        max_tokens=350
    )
    reply = completion.choices[0].message.content
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
