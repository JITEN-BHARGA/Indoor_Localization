# IoT Indoor Localization System

GitHub-ready, Vercel-friendly codebase for an indoor localization system using Wi-Fi RSSI fingerprinting, FastAPI, Next.js, PostgreSQL, and an ESP32 publisher.

## Final architecture

- **ESP32** scans nearby Wi-Fi access points and captures BSSID/MAC + RSSI
- **MQTT broker** receives device messages
- **Broker webhook or bridge** forwards scan payloads to the FastAPI ingest API
- **FastAPI** loads the trained model, predicts location, and stores scans/predictions
- **PostgreSQL** stores objects, raw scans, and predictions
- **Next.js dashboard** displays latest predictions and history

## Why this architecture

This project keeps the same flow described in your course project: ESP32 scan, MQTT transport, ML-based classification, and a live dashboard.

Because Vercel Functions are request-driven and do not act as a WebSocket server, this repo uses a **polling dashboard** and an **HTTP ingest API** instead of a long-running MQTT consumer on Vercel.

## Folder structure

```text
.
├── api/                      # Vercel Python entrypoint for FastAPI
├── app/                      # Next.js frontend (App Router)
├── backend/                  # Python backend modules
├── database/                 # SQL schema
├── esp32/                    # ESP32 sketch
├── model_training/           # Training pipeline
├── scripts/                  # Test/simulate payloads
├── .github/workflows/        # CI
├── requirements.txt          # Python deps for Vercel + local backend
├── package.json              # Next.js frontend deps
└── vercel.json               # Vercel routing/config
```

## Environment variables

Create a `.env.local` for local frontend testing and configure the same variables in Vercel Project Settings.

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/indoor_localization
MODEL_PATH=backend/artifacts/location_model.joblib
FINGERPRINT_PATH=backend/artifacts/fingerprint_reference.csv
LOW_CONFIDENCE_THRESHOLD=0.60
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
API_TOKEN=replace-with-a-long-random-string
```

For deployed Vercel frontend, set:

```env
NEXT_PUBLIC_API_BASE=
```

and the app will use relative `/api/...` requests.

## Database setup

Use Supabase Postgres or Neon Postgres for deployment.

Run `database/schema.sql` in your Postgres database.

## Train the model

Put your cleaned dataset in the project root, then run:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python model_training/train_model.py --input dataset_clean.csv --output_dir backend/artifacts
```

This creates:
- `backend/artifacts/location_model.joblib`
- `backend/artifacts/fingerprint_reference.csv`
- `backend/artifacts/model_metadata.json`
- plots and report in the same folder

## Run locally

### Backend

```bash
uvicorn api.index:app --reload
```

### Frontend

```bash
npm install
npm run dev
```

Then open:
- Frontend: `http://localhost:3000`
- API docs: `http://127.0.0.1:8000/docs`

## Test ingest locally

```bash
python scripts/send_sample_scan.py
```

## Deploy to Vercel

1. Push this repo to GitHub
2. Import the repo into Vercel
3. Add environment variables in Vercel
4. Make sure your Postgres database is reachable from Vercel
5. Deploy

## MQTT integration options

Vercel should not run a persistent MQTT subscriber. Use one of these patterns:

1. **Recommended:** Configure your MQTT broker to forward messages to `/api/ingest`
2. ESP32 publishes MQTT and also sends the same JSON to `/api/ingest`
3. Run a tiny bridge process elsewhere that subscribes to MQTT and POSTs to `/api/ingest`

## ESP32 payload format

```json
{
  "object_id": "bag_01",
  "device_id": "esp32_01",
  "scan_data": [
    {"mac_address": "AA:BB:CC:DD:EE:01", "rssi": -67},
    {"mac_address": "AA:BB:CC:DD:EE:02", "rssi": -74}
  ],
  "timestamp": "2026-04-15T12:30:00Z"
}
```

## Notes

- This repo is designed to be simple and easy to understand for a course project.
- For best accuracy, collect more fingerprints per location and keep AP coverage consistent.
