import os
import requests
from flask import Flask, render_template, request, jsonify
import folium

app = Flask(__name__)

# Simulated disease + crop advice (replace with real DB later)
def get_health_data(lat, lon):
    # For demo: decide by latitude
    if lat > 20:
        return dict(dengue=150, malaria=200, chikungunya=50, heatwave=10, crop_season="Rabi (wheat, mustard)")
    else:
        return dict(dengue=300, malaria=600, chikungunya=100, heatwave=50, crop_season="Kharif (rice, maize)")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather')
def weather():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    # --- Open-Meteo API for real weather ---
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,wind_speed_10m&forecast_days=1"
    r = requests.get(weather_url)
    w = r.json()

    temp_values = w['hourly']['temperature_2m']
    precip_values = w['hourly']['precipitation']
    wind_values = w['hourly']['wind_speed_10m']

    temp_max = max(temp_values)
    temp_min = min(temp_values)
    precipitation = sum(precip_values)
    wind_speed = max(wind_values)

    # Simple forecast
    forecast = "Rainy" if precipitation > 5 else "Clear"

    # Health + crop info
    health = get_health_data(float(lat), float(lon))

    return jsonify({
        "location": f"{lat},{lon}",
        "temp_max": round(temp_max, 1),
        "temp_min": round(temp_min, 1),
        "precipitation": round(precipitation, 1),
        "wind_speed": round(wind_speed, 1),
        "forecast": forecast,
        "crop_season": health['crop_season'],
        "dengue": health['dengue'],
        "malaria": health['malaria'],
        "chikungunya": health['chikungunya'],
        "heatwave": health['heatwave']
    })

@app.route('/map')
def map_view():
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))

    health = get_health_data(lat, lon)

    # Determine color risk
    total_cases = health['dengue'] + health['malaria'] + health['chikungunya']
    color = 'green'
    if total_cases > 500:
        color = 'red'
    elif total_cases > 200:
        color = 'orange'

    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.CircleMarker(location=[lat, lon],
                        radius=15,
                        color=color,
                        fill=True,
                        fill_color=color,
                        popup=(f"Dengue:{health['dengue']} Malaria:{health['malaria']} "
                               f"Chikungunya:{health['chikungunya']}")).add_to(m)

    map_path = 'templates/map_temp.html'
    m.save(map_path)
    return render_template('map_temp.html')

if __name__ == '__main__':
    app.run(debug=True)
