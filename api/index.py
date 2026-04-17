from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db import init_db
from backend.routes import router
from backend.mqtt_consumer import start_mqtt_in_background

app = FastAPI(title="Indoor Localization API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
start_mqtt_in_background()
app.include_router(router)


@app.get("/")
def root():
    return {"status": "running"}