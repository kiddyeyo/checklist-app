# Aplicación de Checklist

Esta es una pequeña aplicación en FastAPI para registrar listas de verificación preoperativas, revisiones de supervisor y tareas de mantenimiento de una flota de vehículos. La información enviada se agrega a una hoja de cálculo de Google y las imágenes subidas se almacenan en el directorio `uploads/`.

## Prerrequisitos

- **Python**: versión 3.12 o más reciente si se ejecuta localmente.
- **Variables de entorno**
  - `GOOGLE_SHEETS_CREDENTIALS_JSON` – ruta al archivo JSON de la cuenta de servicio de Google con acceso a la hoja.
  - `SHEETS_SPREADSHEET_ID` – ID de la hoja de cálculo donde se guardarán los registros.
- **Archivos de datos**: crea un directorio `data/` junto a `app.py` con archivos de texto que llenen los desplegables del formulario:

```
data/
  operators.txt
  units.txt
  routes.txt
  supervisors.txt
  mechanics.txt
```

Cada archivo debe contener una entrada por línea codificada en UTF-8.

Puedes definir las variables de entorno en tu sistema o en un archivo `.env`. Uvicorn las cargará automáticamente si `python-dotenv` está instalado.

El directorio `uploads/` se creará automáticamente al iniciar la aplicación.

## Ejecución local con Uvicorn

Instala las dependencias y ejecuta el servidor de desarrollo:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_SHEETS_CREDENTIALS_JSON=/ruta/credenciales.json
export SHEETS_SPREADSHEET_ID=tu_spreadsheet_id
uvicorn app:app --reload
```

Visita <http://localhost:8000> para usar la aplicación.

## Ejecución con Docker

Compila la imagen y ejecuta el contenedor:

```bash
docker build -t checklist-app .
docker run --rm -p 8000:8000 \
  -e GOOGLE_SHEETS_CREDENTIALS_JSON=/app/credentials.json \
  -e SHEETS_SPREADSHEET_ID=tu_spreadsheet_id \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  -v $(pwd)/data:/app/data:ro \
  -v $(pwd)/uploads:/app/uploads \
  checklist-app
```

También puedes utilizar `docker-compose`:

```bash
docker-compose up
```

La aplicación estará disponible en <http://localhost:8000>.
