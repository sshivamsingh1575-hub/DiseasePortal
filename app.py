import os
from flask import Flask, render_template, request, jsonify
import pandas as pd
import folium
from openai import OpenAI

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Load combined disease+coords data
states_df = pd.read_csv('data/india_diseases_combined.csv')

# Assign risk color
def assign_risk(row):
    try:
        dengue = float(row.get('Dengue', 0))
        malaria = float(row.get('Malaria', 0))
        chik = float(row.get('Chikungunya', 0))
    except:
        dengue = malaria = chik = 0
    total = dengue + malaria + chik
    if total > 2000:
        return 'red'
    elif total > 1000:
        return 'orange'
    elif total > 500:
        return 'yellow'
    else:
        return 'green'

states_df['Risk'] = states_df.apply(assign_risk, axis=1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/map')
def map_view():
    m = folium.Map(location=[22.9734, 78.6569], zoom_start=5)
    for _, row in states_df.iterrows():
        popup = f"""
        <b>{row['State']}</b><br>
        Dengue: {row.get('Dengue',0)}<br>
        Malaria: {row.get('Malaria',0)}<br>
        Chikungunya: {row.get('Chikungunya',0)}<br>
        Risk: {row['Risk']}
        """
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=10,
            color=row['Risk'],
            fill=True,
            fill_color=row['Risk'],
            popup=popup
        ).add_to(m)
    m.save('templates/map_temp.html')
    return render_template('map_temp.html')

@app.route('/state-data', methods=['GET'])
def state_data():
    state = request.args.get('state')
    row = states_df[states_df['State'].str.lower() == state.lower()]
    if row.empty:
        return jsonify({"error":"State not found"}),404
    return jsonify(row.to_dict(orient='records')[0])

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message','')
    # Combine all state data for AI context
    states_text = "\n".join(
        f"{r['State']} Dengue:{r.get('Dengue',0)} Malaria:{r.get('Malaria',0)} Chikungunya:{r.get('Chikungunya',0)} Risk:{r['Risk']}"
        for _, r in states_df.iterrows()
    )
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
    return jsonify({"reply":answer})

if __name__ == '__main__':
    app.run(debug=True)
