# Procfile - Render dùng `startCommand` trong render.yaml, hoặc file này nếu dùng Web Service thủ công.
# Chạy FastAPI bằng Gunicorn + UvicornWorker (production, hỗ trợ multi-worker).
web: gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
