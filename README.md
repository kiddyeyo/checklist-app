# Checklist App

A small FastAPI application for recording pre-operation, supervisor and maintenance checklists for a fleet of vehicles. Submitted data is appended to a Google Sheet and uploaded images are stored in the `uploads/` directory.

## Prerequisites

- **Python**: version 3.12 or newer when running locally.
- **Environment variables**
  - `GOOGLE_SHEETS_CREDENTIALS_JSON` – path to the Google service account JSON file used to access the spreadsheet.
  - `SHEETS_SPREADSHEET_ID` – ID of the spreadsheet where submissions will be stored.
- **Data files**: create a `data/` directory next to `app.py` containing text files that populate the form dropdowns:

  ```
  data/
    operators.txt
    units.txt
    routes.txt
    supervisors.txt
    mechanics.txt
  ```

  Each file should list one entry per line.

## Running locally with Uvicorn

Install dependencies and start the development server:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_SHEETS_CREDENTIALS_JSON=/path/to/credentials.json
export SHEETS_SPREADSHEET_ID=your_spreadsheet_id
uvicorn app:app --reload
```

Visit <http://localhost:8000> to use the app.

## Running with Docker

Build the image and run the container:

```bash
docker build -t checklist-app .
docker run --rm -p 8000:8000 \
  -e GOOGLE_SHEETS_CREDENTIALS_JSON=/app/credentials.json \
  -e SHEETS_SPREADSHEET_ID=your_spreadsheet_id \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  -v $(pwd)/data:/app/data:ro \
  -v $(pwd)/uploads:/app/uploads \
  checklist-app
```

Alternatively, use `docker-compose`:

```bash
docker-compose up
```

The application will be available at <http://localhost:8000>.
