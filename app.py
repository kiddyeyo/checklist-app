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
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

# Inicialización
app = FastAPI()
templates = Jinja2Templates(directory="templates")

BASE_DIR  = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
VIDEOS_DIR  = os.path.join(BASE_DIR, "videos")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/videos_static", StaticFiles(directory=VIDEOS_DIR), name="videos_static")

# Carga de listas
def load_list(filename):
    path = os.path.join(BASE_DIR, "data", filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

OPERATORS = load_list("operators.txt")
UNITS     = load_list("units.txt")
ROUTES    = load_list("routes.txt")
SUPERVISORS = load_list("supervisors.txt")
MECHANICS   = load_list("mechanics.txt")

# Google Sheets API
SCOPES         = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
CREDS_FILE     = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
sheet_service = build("sheets", "v4", credentials=creds).spreadsheets()

# Ítems compartidos (puedes adaptarlos por formulario)
CHECK_ITEMS = [
    ("lubricante_anticongelante", "Revisa si los niveles de lubricante y anticongelante están dentro del rango:", ["Correcto", "Bajo", "Alto"]),
    ("fugas",                     "Abre el cofre y checa fugas de combustible/anticongelante/líquido de dirección:", ["Sin fugas", "Con fugas"]),
    ("bayoneta",                  "Verifica la bayoneta de aceite (colocación y estado):", ["Correcta", "Mal colocada", "Dañada"]),
    ("llantas",                   "Verifica presión y estado de todas las llantas:", ["Presión correcta y sin daños", "Baja presión", "Daño en llanta"]),
    ("lineas_aire",               "Inspecciona líneas de aire y cables de compresor de frenos:", ["Buen estado", "Fugas/Pérdida", "Daño"]),
    ("suspension",                "Revisa la suspensión (resortes y bolsas):", ["Ok", "Resortes rotos", "Bolsas dañadas"]),
    ("indicadores",               "Enciende y checa indicadores y sistema eléctrico:", ["Funcionan", "Falla alguno"]),
    ("clutch",                    "Presiona y suelta el clutch y frenos; revisa presión y respuesta:", ["Buena respuesta", "Falla en presión"]),
    ("luces",                     "Chequea luces, direccionales e intermitentes:", ["Todas operan", "Alguna falla"])
]

# Preguntas para Supervisor
SUPERVISOR_ITEMS = [
    ("presencia",   "¿El operador se presentó a tiempo?", ["Sí", "No"]),
    ("uniforme",    "¿Porta el uniforme o indumentaria requerida?", ["Sí", "No"]),
    ("sobriedad",   "¿Muestra actitud sobria y apta para conducir?", ["Sí", "No"]),
    ("proteccion",  "¿Porta equipo de protección personal?", ["Sí", "No"]),
    ("licencia",    "¿Licencia de conducir vigente?", ["Sí", "No"]),
    ("credencial",  "¿Porta credencial de la empresa?", ["Sí", "No"]),
    ("condiciones", "¿El operador está en condiciones físicas óptimas?", ["Sí", "No"]),
]

# Ítems para Mantenimiento
MAINTENANCE_ITEMS = [
    ("cambio_aceite",      "Cambio de aceite",                            ["Sí", "No"]),
    ("filtro_aire",        "Reemplazo de filtro de aire",                 ["Sí", "No"]),
    ("revision_frenos",     "Revisión de frenos",                          ["Ok", "Fallas detectadas"]),
    ("rotacion_llantas",   "Rotación de llantas",                         ["Sí", "No"]),
    ("inspeccion_correas",  "Inspección de correas",                       ["Ok", "Reemplazar"]),
    ("revision_niveles",    "Revisión de nivel de fluidos",                ["Ok", "Bajo", "Alto"]),
    ("ajuste_tornilleria",  "Ajuste de tornillería crítica",               ["Completo", "Pendiente"]),
    ("limpieza_radiador",   "Limpieza de radiador/intercooler",            ["Completo", "Pendiente"])
]

def save_row_to_sheet(values: list[str], sheet_name: str):
    sheet_service.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A1",
        valueInputOption="USER_ENTERED",
        body={"values": [values]}
    ).execute()


async def save_uploaded_images(request: Request, photos: list[UploadFile] | None) -> list[str]:
    """Save uploaded images and return their accessible URLs."""
    urls: list[str] = []
    if photos:
        for up in photos:
            if up.content_type.startswith("image/"):
                ext = os.path.splitext(up.filename)[1]
                fname = f"{uuid.uuid4()}{ext}"
                dest = os.path.join(UPLOAD_DIR, fname)
                with open(dest, "wb") as out:
                    out.write(await up.read())
                base = str(request.base_url).rstrip("/")
                urls.append(f"{base}/uploads/{fname}")
    return urls

# 1) Menú principal
@app.get("/")
async def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

# 2) PRECHECK (operador)
@app.get("/precheck")
async def precheck_form(request: Request):
    return templates.TemplateResponse("precheck.html", {
        "request": request,
        "operators": OPERATORS,
        "units": UNITS,
        "routes": ROUTES,
        "items": CHECK_ITEMS
    })

@app.post("/submit/precheck")
async def submit_precheck(request: Request, photos: list[UploadFile] = File(None)):
    form = await request.form()
    now = datetime.now(ZoneInfo("America/Hermosillo"))
    date_str = now.strftime("%Y-%m-%d")
    time_str = form.get("check_time") or now.strftime("%H:%M:%S")

    row = [
        date_str, time_str,
        form.get("operator"), form.get("unit"), form.get("route")
    ]
    for key, _, _ in CHECK_ITEMS:
        row.append(form.get(key))
    row.append(form.get("comments", ""))

    # Fotos de evidencia
    urls = await save_uploaded_images(request, photos)
    row.append(" | ".join(urls))

    save_row_to_sheet(row, "Precheck")
    return templates.TemplateResponse("success.html", {"request": request})


# Supervisor: formulario GET
@app.get("/supervisor")
async def supervisor_form(request: Request):
    return templates.TemplateResponse("supervisor.html", {
        "request": request,
        "supervisors": SUPERVISORS,
        "operators": OPERATORS,
        "units": UNITS,
        "items": SUPERVISOR_ITEMS
    })

# Supervisor: procesamiento POST
@app.post("/submit/supervisor")
async def submit_supervisor(request: Request, photos: list[UploadFile] = File(None)):
    form = await request.form()
    now = datetime.now(ZoneInfo("America/Hermosillo"))
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    row = [
        date_str,
        time_str,
        form.get("supervisor"),
        form.get("operator"),
        form.get("unit")
    ]

    # Añade respuestas dinámicas
    for key, _, _ in SUPERVISOR_ITEMS:
        row.append(form.get(key))

    # Comentarios
    row.append(form.get("comments", ""))

    # Fotos de evidencia
    urls = await save_uploaded_images(request, photos)
    row.append(" | ".join(urls))

    save_row_to_sheet(row, "Supervisor")
    return templates.TemplateResponse("success.html", {"request": request})

# 4) MANTENIMIENTO
@app.get("/mantenimiento")
async def mantenimiento_form(request: Request):
    return templates.TemplateResponse("mantenimiento.html", {
        "request": request,
        "operators": OPERATORS,
        "units": UNITS,
        "mechanics": MECHANICS,
        "items": MAINTENANCE_ITEMS
    })

# 4b) MANTENIMIENTO - procesamiento POST
@app.post("/submit/mantenimiento")
async def submit_mantenimiento(request: Request, photos: list[UploadFile] = File(None)):
    form = await request.form()
    now = datetime.now(ZoneInfo("America/Hermosillo"))
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # Fila inicial
    row = [
        date_str,
        time_str,
        form.get("type"),           # Tipo de mantenimiento
        form.get("mechanic"),       # Mecánico
        form.get("unit"),           # Unidad
        form.get("hr_actual"),      # Horas motor actuales
        form.get("next_km"),        # Km próximo
        form.get("next_date", "")   # Fecha próxima (si se ingresó)
    ]

    # Respuestas dinámicas
    for key, _, _ in MAINTENANCE_ITEMS:
        row.append(form.get(key))
    
    # Piezas reemplazadas y observaciones
    row.append(form.get("parts", ""))
    row.append(form.get("comments", ""))

    # Fotos de evidencia
    urls = await save_uploaded_images(request, photos)
    row.append(" | ".join(urls))

    save_row_to_sheet(row, "Mantenimiento")
    return templates.TemplateResponse("success.html", {"request": request})

    # --- NUEVO: Página de Videos ---
@app.get("/videos")
async def videos_page(request: Request):
    # Listar todos los archivos de vídeo en VIDEOS_DIR
    video_files = [
        f for f in os.listdir(VIDEOS_DIR)
        if f.lower().endswith((".mp4", ".webm", ".ogg"))
    ]
    return templates.TemplateResponse("videos.html", {
        "request": request,
        "videos": video_files
    })
