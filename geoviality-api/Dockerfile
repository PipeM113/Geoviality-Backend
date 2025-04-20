# Usar la imagen base de Python 3.12 con Alpine Linux
FROM python:3.12-alpine

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos al directorio de trabajo en el contenedor
COPY requirements.txt .

# Instalar las dependencias listadas en requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el contenido del directorio actual en el host al directorio de trabajo en el contenedor
COPY . .

# Exponer el puerto 8080 para que la aplicación sea accesible desde el host
EXPOSE 8080

# Comando por defecto para ejecutar la aplicación cuando el contenedor se inicie
CMD ["python", "app/main.py"]

# Instrucciones para construir la imagen Docker:
# docker build -t geoviality-api-image .

# Instrucciones para correr el contenedor Docker:
# docker run -d --name geoviality-api-container -p 8080:8080 -v "$(pwd):/app" geoviality-api-image