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
cd api
gunicorn --bind 0.0.0.0:8000 app:app
```

## api doc

https://apidocjs.com/
```bash
npm install apidoc -g
apidoc
```
