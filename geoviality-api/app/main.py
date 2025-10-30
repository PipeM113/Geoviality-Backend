from fastapi import FastAPI
from dotenv import load_dotenv
from pyngrok import ngrok, conf
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from controllers.v1 import create_directories
from routes.v1 import auth_router, users_router, files_router, sidewalks_router, historical_router, events_router, notify_router

# Si USE_NGROK es "True" o no se especifica en .env, se usará NGROK (default)
useNgrok = os.getenv("USE_NGROK", "True").lower()
if useNgrok.lower() == "true":
    useNgrok = True
# La unica forma de usar IP local es si USE_NGROK es "False" en el .env

create_directories()

app = FastAPI()

# Incluir routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(files_router)
app.include_router(sidewalks_router)
app.include_router(historical_router)
app.include_router(events_router)
app.include_router(notify_router)

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [
    origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()
] if allowed_origins_env else ["*"]
allow_credentials = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
#...existing code...
app_host = os.getenv("HOST", "127.0.0.1")
app_port = int(os.getenv("PORT_NUMBER", "8080"))
ngrok_domain = os.getenv("NGROK_DOMAIN")

ngrok_auth_token = os.getenv("NGROK_AUTH_TOKEN")
if ngrok_auth_token:
    conf.get_default().auth_token = ngrok_auth_token

if __name__ == "__main__":
    if useNgrok:
        ngrok_tunnel = ngrok.connect(f"{app_port}", hostname=ngrok_domain)
        print(">>> Usando NGROK. Public URL:", ngrok_tunnel.public_url)
        print(">>> Bindeando NGROK en puerto:", app_port)

    uvicorn.run(app, host=app_host, port=app_port)
