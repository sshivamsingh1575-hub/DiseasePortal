from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
import folium

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('data/database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    states = conn.execute('SELECT * FROM states').fetchall()
    conn.close()
    return render_template('index.html', states=states)

@app.route('/map')
def map_view():
    conn = get_db_connection()
    states = conn.execute('SELECT * FROM states').fetchall()
    conn.close()

    m = folium.Map(location=[22.9734, 78.6569], zoom_start=5)

    for s in states:
        risk = 'green'
        if s['dengue_cases'] + s['malaria_cases'] + s['chikungunya_cases'] > 1500:
            risk = 'red'
        elif s['dengue_cases'] > 500:
            risk = 'orange'

        popup = f"{s['name']}<br>Dengue: {s['dengue_cases']}<br>Malaria: {s['malaria_cases']}"
        folium.CircleMarker(location=[s['latitude'], s['longitude']],
                            radius=10,
                            color=risk,
                            fill=True,
                            fill_color=risk,
                            popup=popup).add_to(m)

    m.save('templates/map.html')
    return render_template('map.html')

@app.route('/api/states')
def api_states():
    conn = get_db_connection()
    states = conn.execute('SELECT * FROM states').fetchall()
    conn.close()
    return jsonify([dict(s) for s in states])

if __name__ == '__main__':
    app.run(debug=True)
