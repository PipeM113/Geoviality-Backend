"""Carga de variables de entorno y constantes de configuración de la API."""

# stdlib
import os

# third-party
from dotenv import load_dotenv

load_dotenv()

# App
USE_NGROK = os.getenv("USE_NGROK", "True").lower() == "true"
APP_HOST = os.getenv("HOST_ADDRESS", "0.0.0.0")
APP_PORT = int(os.getenv("PORT_NUMBER", "8080"))

# Ngrok
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN")
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")

# Auth / JWT
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_QUEUE_IMAGES = os.getenv("RABBITMQ_QUEUE_IMAGES", "images")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
