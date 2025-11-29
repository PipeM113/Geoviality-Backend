# Usar la imagen slim para evitar problemas de compilación
FROM python:3.10-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para OpenCV y otras librerías
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación (incluye ia_service/, .env, modelos, etc.)
COPY . .

# (Opcional pero útil) no bufferizar stdout/stderr
ENV PYTHONUNBUFFERED=1

# Comando para ejecutar la aplicación (nuevo entrypoint)
# Opción 1: como módulo
CMD ["python", "-m", "ia_service.app"]

# Si prefieres ruta directa de archivo, sería:
# CMD ["python", "ia_service/app.py"]
