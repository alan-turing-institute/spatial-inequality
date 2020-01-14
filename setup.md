## install redis
```bash
brew install redis
```

## start redis server
```bash
redis-server
```

## start reids worker on a queue called spineq
```bash
rq worker spineq
```

## start flask with gunicorn
```bash
cd app
gunicorn --bind 0.0.0.0:8000 app:app
```