redis-server &
python worker.py & 
gunicorn --bind 0.0.0.0:$PORT app:app
