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

BASE_DIR    = os.path.dirname(__file__)
UPLOAD_DIR  = os.path.join(BASE_DIR, "uploads")
VIDEOS_DIR  = os.path.join(BASE_DIR, "videos")

# Asegurarse de que existan los directorios
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# Montar estáticos
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/videos_static", StaticFiles(directory=VIDEOS_DIR), name="videos_static")

# Carga de listas (igual que antes)
def load_list(filename):
    path = os.path.join(BASE_DIR, "data", filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

OPERATORS   = load_list("operators.txt")
UNITS       = load_list("units.txt")
ROUTES      = load_list("routes.txt")
SUPERVISORS = load_list("supervisors.txt")
MECHANICS   = load_list("mechanics.txt")

# Google Sheets API (igual que antes)
SCOPES         = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
CREDS_FILE     = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
creds          = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
sheet_service  = build("sheets", "v4", credentials=creds).spreadsheets()

# Funciones auxiliares (igual que antes)
def save_row_to_sheet(values: list[str], sheet_name: str):
    sheet_service.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A1",
        valueInputOption="USER_ENTERED",
        body={"values": [values]}
    ).execute()

async def save_uploaded_images(request: Request, photos: list[UploadFile] | None) -> list[str]:
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

# Rutas existentes...
@app.get("/")
async def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

# ... (todas tus rutas /precheck, /submit/precheck, /supervisor, etc.)

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
