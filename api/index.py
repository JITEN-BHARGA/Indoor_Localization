from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import router
from backend.mqtt_consumer import start_mqtt_in_background, stop_mqtt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def startup():
    start_mqtt_in_background()

@app.on_event("shutdown")
def shutdown_event():
    stop_mqtt()