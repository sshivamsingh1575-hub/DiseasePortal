import os
from openai import OpenAI
from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
import folium

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')

    # Pull state and disease info from DB for context
    conn = get_db_connection()
    states = conn.execute('SELECT * FROM states').fetchall()
    conn.close()

    states_text = ""
    for s in states:
        states_text += (f"{s['name']} - MaxTemp:{s['max_temp']} MinTemp:{s['min_temp']} "
                        f"Precipitation:{s['precipitation']} Dengue:{s['dengue_cases']} "
                        f"Malaria:{s['malaria_cases']} Chikungunya:{s['chikungunya_cases']} Deaths:{s['deaths']}\n")

    prompt = f"""
You are HealthBot for India's Disease Portal.
You have this data:
{states_text}

Answer the user’s question below, giving helpful and preventive advice. 
If asked about a state, use the data above. 
If asked for general health advice, respond appropriately:

Question: {user_input}
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # or another available model
            messages=[
                {"role": "system", "content": "You are a helpful public health advisor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        answer = f"Error: {e}"

    return jsonify({"reply": answer})
from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
import folium
import os
from openai import OpenAI

app = Flask(__name__)

# ---- OpenAI client ----
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---- DB Connection ----
def get_db_connection():
    conn = sqlite3.connect('data/database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ---- Index route ----
@app.route('/')
def index():
    conn = get_db_connection()
    states = conn.execute('SELECT * FROM states').fetchall()
    conn.close()
    return render_template('index.html', states=states)

# ---- Map route ----
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

# ---- API route (optional) ----
@app.route('/api/states')
def api_states():
    conn = get_db_connection()
    states = conn.execute('SELECT * FROM states').fetchall()
    conn.close()
    return jsonify([dict(s) for s in states])

# ---- PASTE NEW CHAT ROUTE BELOW ----
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')

    conn = get_db_connection()
    states = conn.execute('SELECT * FROM states').fetchall()
    conn.close()

    states_text = ""
    for s in states:
        states_text += (f"{s['name']} - MaxTemp:{s['max_temp']} MinTemp:{s['min_temp']} "
                        f"Precipitation:{s['precipitation']} Dengue:{s['dengue_cases']} "
                        f"Malaria:{s['malaria_cases']} Chikungunya:{s['chikungunya_cases']} Deaths:{s['deaths']}\n")

    prompt = f"""
You are HealthBot for India's Disease Portal.
You have this data:
{states_text}

Answer the user’s question below, giving helpful and preventive advice.
If asked about a state, use the data above.
If asked for general health advice, respond appropriately:

Question: {user_input}
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful public health advisor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        answer = f"Error: {e}"

    return jsonify({"reply": answer})

# ---- Run app ----
if __name__ == '__main__':
    app.run(debug=True)
if __name__ == '__main__':
    app.run(debug=True)
