from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pyngrok import ngrok, conf
import os
import uvicorn

from app.core.config import USE_NGROK, APP_HOST, APP_PORT, NGROK_AUTH_TOKEN, NGROK_DOMAIN
from app.core.utils import create_directories

# Routers por dominio (cada uno ya tiene prefix="/v1/<módulo>" adentro)
from app.auth.v1.auth_routes import router as auth_router
from app.users.v1.users_routes import router as users_router
from app.streets.v1.streets_routes import router as streets_router
from app.sidewalks.v1.sidewalks_routes import router as sidewalks_router
from app.historical.v1.historical_routes import router as historical_router
from app.notifications.v1.notifications_routes import router as notifications_router
from app.files.v1.files_routes import router as files_router

load_dotenv()
create_directories()

app = FastAPI(title="Geoviality API (modular v1)")

# Configura CORS (si en tu código actual usas env para orígenes, ponlas aquí)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # respeta tus settings actuales
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluye routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(streets_router)
app.include_router(sidewalks_router)
app.include_router(historical_router)
app.include_router(notifications_router)
app.include_router(files_router)

#añadir ruta de check health
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Geoviality API"}

# NGROK
if NGROK_AUTH_TOKEN:
    conf.get_default().auth_token = NGROK_AUTH_TOKEN

if __name__ == "__main__":
    if USE_NGROK:
        t = ngrok.connect(f"{APP_PORT}", hostname=NGROK_DOMAIN)
        print(">>> NGROK Public URL:", t.public_url)
        print(">>> Port:", APP_PORT)


    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
