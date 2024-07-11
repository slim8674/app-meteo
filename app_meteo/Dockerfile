# Usa un'immagine di Python ufficiale come immagine di base
FROM python:3.9-slim

# Imposta la directory di lavoro nel container
WORKDIR /app

# Copia il file dei requisiti nella directory di lavoro
COPY requirements.txt .

# Aggiorna pip e installa le dipendenze
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice dell'applicazione nella directory di lavoro
COPY . .

# Esponi la porta su cui l'app Flask sarà in ascolto
EXPOSE 5372

# Definisci la variabile d'ambiente per Flask
ENV FLASK_APP=app.py

# Comando per eseguire l'applicazione
CMD ["flask", "run", "--host=0.0.0.0", "--port=5372"]