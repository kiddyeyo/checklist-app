import os
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Inicialización de la app y templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Configuración de Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
CREDS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")

credentials = service_account.Credentials.from_service_account_file(
    CREDS_FILE, scopes=SCOPES
)
service = build("sheets", "v4", credentials=credentials)
sheet = service.spreadsheets()

# Definición de ítems de checklist (clave, etiqueta)
CHECK_ITEMS = [
    ("lubricante_anticongelante", "Revisar niveles de lubricante y anticongelante"),
    ("fugas", "Verificar que no existan fugas"),
    ("tapas", "Checar que las tapas estén cerradas"),
    ("bayoneta", "Revisar que la bayoneta del aceite esté colocada"),
    ("ventilador", "Asegurarse que el ventilador no esté roto"),
    ("cables", "Verificar estado y conexión de cables"),
    ("llantas", "Revisar presión y estado de llantas"),
    ("lineas_aire", "Inspección visual de líneas de aire y cable compresor"),
    ("suspension", "Verificar suspensión: resortes y bolsas"),
    ("indicadores", "Revisar que indicadores y sistema eléctrico funcionen"),
    ("clutch", "Probar presión del clutch"),
    ("frenos", "Probar freno y freno de emergencia"),
    ("fugas2", "Revisar fugas tras apagar motor"),
    ("bandas", "Verificar tensión y giro libre de bandas"),
    ("luces", "Verificar luces, intermitentes y faros")
]

@app.get("/")
async def form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "items": CHECK_ITEMS})

@app.post("/submit")
async def submit(request: Request):
    form_data = await request.form()
    timestamp = datetime.utcnow().isoformat()
    # Construye la fila: timestamp + datos básicos
    row = [timestamp,
           form_data.get("operator"),
           form_data.get("unit")]
    # Añade cada ítem: Sí/No
    for key, _ in CHECK_ITEMS:
        row.append("Sí" if form_data.get(key) == "on" else "No")
    body = {"values": [row]}
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A1",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    return RedirectResponse(url="/", status_code=303)