web: gunicorn -b 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 worker:app
worker: python bot.py
