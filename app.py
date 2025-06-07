# app.py
import os
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Inicialización de FastAPI y Jinja2
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Carpeta para subir y servir imágenes
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Carga de listas desde /data
def load_list(filename):
    path = os.path.join(BASE_DIR, "data", filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

OPERATORS = load_list("operators.txt")
UNITS     = load_list("units.txt")
ROUTES    = load_list("routes.txt")

# Configuración de Google Sheets API
SCOPES         = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
CREDS_FILE     = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")

creds = service_account.Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=SCOPES
)
sheet_service = build("sheets", "v4", credentials=creds).spreadsheets()

# Ítems del checklist: (clave, pregunta, opciones)
CHECK_ITEMS = [
    ("lubricante_anticongelante", "Revisa si los niveles de lubricante y anticongelante están dentro del rango:", ["Correcto", "Bajo", "Alto"]),
    ("fugas",                     "Abre la compuerta y checa filtraciones de combustible/anticongelante/líquido de dirección:", ["Sin fugas", "Con fugas"]),
    ("tapas",                     "Checa que las tapas de radiador, lubricante y dirección hidráulica estén:", ["Bien cerradas", "Abiertas", "Dañadas"]),
    ("bayoneta",                  "Verifica la bayoneta de aceite (colocación y estado):", ["Correcta", "Mal colocada", "Dañada"]),
    ("ventilador",                "Inspecciona el ventilador (aspas y montaje):", ["Ok", "Aspas rotas", "Holgura"]),
    ("cables",                    "Revisa cables y conexiones (especialmente batería):", ["Conectados y en buen estado", "Desconectados", "Dañados"]),
    ("llantas",                   "Verifica presión y estado de todas las llantas:", ["Presión correcta y sin daños", "Baja presión", "Daño en llanta"]),
    ("lineas_aire",               "Inspecciona líneas de aire y cables de compresor de frenos:", ["Buen estado", "Fugas/Pérdida", "Daño"]),
    ("suspension",                "Revisa la suspensión (resortes y bolsas):", ["Ok", "Resortes rotos", "Bolsas dañadas"]),
    ("indicadores",               "Enciende motor en neutral y checa indicadores y sistema eléctrico:", ["Funcionan", "Falla alguno"]),
    ("clutch",                    "Presiona y suelta el clutch; revisa presión y respuesta:", ["Buena respuesta", "Falla en presión"]),
    ("frenos",                    "Avanza y prueba freno normal y de emergencia:", ["Operan correctamente", "Falla normal", "Falla emergencia"]),
    ("fugas2",                    "Tras apagar motor, revisa nuevamente filtraciones:", ["Sin fugas", "Con fugas"]),
    ("bandas",                    "Verifica tensión y giro libre de bandas:", ["Tensión correcta", "Flojas/Tensas", "Obstrucción"]),
    ("luces",                     "Chequea luces, direccionales e intermitentes:", ["Todas operan", "Alguna falla"])
]

@app.get("/")
async def form(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "operators": OPERATORS,
        "units": UNITS,
        "routes": ROUTES,
        "items": CHECK_ITEMS
    })

@app.post("/submit")
async def submit(request: Request, photos: list[UploadFile] = File(None)):
    form = await request.form()
    # Fecha y hora en zona America/Hermosillo
    now = datetime.now(ZoneInfo("America/Hermosillo"))
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    operator = form.get("operator")
    unit     = form.get("unit")
    route    = form.get("route")
    comments = form.get("comments", "")

    # Construcción de la fila: fecha, hora, operador, unidad, ruta
    row = [date_str, time_str, operator, unit, route]

    # Respuestas a ítems
    for key, _, _ in CHECK_ITEMS:
        row.append(form.get(key))

    # Comentarios adicionales
    row.append(comments)

    # Guarda las fotos y genera URLs
    file_urls = []
    if photos:
        for upload in photos:
            if upload.content_type.startswith("image/"):
                ext = os.path.splitext(upload.filename)[1]
                filename = f"{uuid.uuid4()}{ext}"
                dest = os.path.join(UPLOAD_DIR, filename)
                with open(dest, "wb") as out:
                    out.write(await upload.read())
                base = str(request.base_url).rstrip("/")
                file_urls.append(f"{base}/uploads/{filename}")

    # Añade URLs de fotos al final
    row.append(" | ".join(file_urls))

    # Envía fila a Google Sheets en pestaña ‘Checklist’
    body = {"values": [row]}
    sheet_service.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Checklist!A1",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()

    return RedirectResponse("/", status_code=303)


