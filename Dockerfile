FROM python:3.12-slim

WORKDIR /app

# Copia y instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de tu aplicación
COPY . .

# Comando para producción con Gunicorn + Uvicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "app:app"]