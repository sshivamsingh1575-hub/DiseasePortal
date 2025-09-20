import sqlite3

conn = sqlite3.connect('data/database.db')
c = conn.cursor()

# Create tables
c.execute('''
CREATE TABLE IF NOT EXISTS states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    latitude REAL,
    longitude REAL,
    max_temp REAL,
    min_temp REAL,
    precipitation REAL,
    dengue_cases INTEGER,
    malaria_cases INTEGER,
    chikungunya_cases INTEGER,
    deaths INTEGER
)
''')

# Example entry
c.execute('''
INSERT INTO states (name, latitude, longitude, max_temp, min_temp, precipitation,
dengue_cases, malaria_cases, chikungunya_cases, deaths)
VALUES 
('Maharashtra', 19.7515, 75.7139, 42, 15, 1200, 1000, 800, 200, 50)
''')

conn.commit()
conn.close()

print("Database initialized!")
