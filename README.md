# Checklist App

Aplicación web desarrollada con **FastAPI** para el registro de distintos formularios de revisión de unidades de transporte. Los datos se guardan automáticamente en hojas de cálculo de Google Sheets y las fotografías se almacenan localmente.

## Requisitos

- Python 3.12 o superior
- Credenciales de servicio de Google para acceder a la API de Sheets
- Acceso a una hoja de cálculo de Google (ID del Spreadsheet)

Opcionalmente se puede ejecutar mediante Docker y `docker-compose`.

## Instalación

1. Clona este repositorio.
2. Crea los directorios `data/` y `uploads/` en la raíz del proyecto. Estos se utilizan para archivos de configuración (listas de operadores, unidades, etc.) y para almacenar las imágenes subidas.
3. Copia tus archivos de texto en `data/` (`operators.txt`, `units.txt`, `routes.txt`, `supervisors.txt`, `mechanics.txt`). Cada archivo debe contener un elemento por línea.
4. Instala las dependencias con:
   ```bash
   pip install -r requirements.txt
   ```
5. Define las siguientes variables de entorno:
   - `GOOGLE_SHEETS_CREDENTIALS_JSON`: ruta al archivo JSON con las credenciales del servicio de Google.
   - `SHEETS_SPREADSHEET_ID`: identificador de la hoja de cálculo donde se registrarán los datos.

## Uso

Para un entorno de desarrollo rápido puedes iniciar la aplicación con:

```bash
uvicorn app:app --reload
```

La interfaz principal se encuentra en `http://localhost:8000/` y permite acceder a tres formularios:

- **Precheck del operador** (`/precheck`)
- **Revisión del supervisor** (`/supervisor`)
- **Registro de mantenimiento** (`/mantenimiento`)

Cada formulario genera una fila en la hoja de cálculo correspondiente y, si se adjuntan fotografías, se guardan en el directorio `uploads/`.

## Docker

También es posible ejecutar el proyecto dentro de un contenedor. Asegúrate de colocar el archivo `credentials.json` y la carpeta `data/` junto al `docker-compose.yml`.

```bash
docker-compose up --build
```

El servicio quedará disponible en el puerto `8000` (o en el dominio configurado mediante Traefik si así se define en el `docker-compose.yml`).

## Estructura

- `app.py` – Lógica principal de la aplicación y definición de rutas.
- `templates/` – Plantillas HTML con TailwindCSS para los formularios y la página de éxito.
- `Dockerfile` y `docker-compose.yml` – Archivos para contenedores.
- `requirements.txt` – Dependencias de Python.

## Licencia

Este proyecto se publica sin una licencia explícita. Úsalo bajo tu propio riesgo.

