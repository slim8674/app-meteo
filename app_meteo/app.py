from flask import Flask, render_template
import sqlite3
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import logging

app = Flask(__name__)

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#creazione e importazione database
def get_db():
    db = sqlite3.connect('meteo.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('CREATE TABLE IF NOT EXISTS previsioni (id INTEGER PRIMARY KEY AUTOINCREMENT, data DATE, temperatura_max FLOAT, temperatura_min FLOAT, percentuale_precipitazioni INTEGER)')
    db.commit()
    db.close()

#funzione per chiamata API
def get_weather_data():
    url = "https://api.open-meteo.com/v1/forecast?latitude=41.8919&longitude=12.5113&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Europe%2FBerlin&forecast_days=1"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Solleva un'eccezione per risposte non 2xx
        
        data = response.json()

        date = data['daily']['time'][0]
        temp_max = data['daily']['temperature_2m_max'][0]
        temp_min = data['daily']['temperature_2m_min'][0]
        precip_prob = data['daily']['precipitation_probability_max'][0]

        return {
            'data': date,
            'temperatura_max': temp_max,
            'temperatura_min': temp_min,
            'percentuale_precipitazioni': precip_prob
        }
    except requests.RequestException as e:
        logger.error(f"Errore nella richiesta API: {e}")
        return None

def update_weather_db():
    logger.info("Iniziando l'aggiornamento dei dati meteo")
    db = get_db()
    cursor = db.cursor()
    
    weather_data = get_weather_data()
    
    if weather_data:
        cursor.execute("SELECT id FROM previsioni WHERE data = ?", (weather_data['data'],))
        existing_record = cursor.fetchone()
        
        if existing_record:
            # Aggiorna il record esistente
            cursor.execute('''
                UPDATE previsioni 
                SET temperatura_max = ?, temperatura_min = ?, percentuale_precipitazioni = ?
                WHERE data = ?
            ''', (
                weather_data['temperatura_max'],
                weather_data['temperatura_min'],
                weather_data['percentuale_precipitazioni'],
                weather_data['data']
            ))
        else:
            # Inserisci un nuovo record
            cursor.execute('''
                INSERT INTO previsioni 
                (data, temperatura_max, temperatura_min, percentuale_precipitazioni)
                VALUES (?, ?, ?, ?)
            ''', (
                weather_data['data'],
                weather_data['temperatura_max'],
                weather_data['temperatura_min'],
                weather_data['percentuale_precipitazioni']
            ))
        
        db.commit()
        logger.info(f"Dati meteo aggiornati per la data {weather_data['data']}")
    else:
        logger.error("Impossibile ottenere i dati meteo")
    
    db.close()

@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    
    # Recupera l'ultimo dato meteo
    c.execute("SELECT * FROM previsioni ORDER BY data DESC LIMIT 1")
    ultimo_meteo = c.fetchone()
    
    # Recupera lo storico (ad esempio, gli ultimi 7 giorni)
    c.execute("SELECT * FROM previsioni ORDER BY data DESC LIMIT 7")
    storico_meteo = c.fetchall()
    
    conn.close()
    
    return render_template('index.html', meteo=ultimo_meteo, storico=storico_meteo)

@app.route('/force_update')
def force_update():
    update_weather_db()
    return "Aggiornamento forzato completato"

# Inizializza lo scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_weather_db, trigger="interval", days=1)
scheduler.start()

if __name__ == '__main__':
    init_db()
    update_weather_db()  # Aggiornamento iniziale
    app.run(host='0.0.0.0', port=5372)