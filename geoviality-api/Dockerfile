# Usar la imagen base de Python 3.13 con Alpine 3.22
FROM python:3.13-alpine3.22

# Instalar curl como dependencia del sistema
RUN apk add --no-cache curl

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /code

# Copiar el archivo de requerimientos al directorio de trabajo en el contenedor
COPY requirements.txt /code/requirements.txt

# Instalar las dependencias listadas en requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copiar todo el contenido del directorio actual en el host al directorio de trabajo en el contenedor
COPY . /code

# Exponer el puerto 8080 para que la aplicación sea accesible desde el host
EXPOSE 8080

# Comando por defecto para ejecutar la aplicación cuando el contenedor se inicie
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

# Instrucciones para construir la imagen Docker:
# docker build -t geoviality-api-image .

# Instrucciones para correr el contenedor Docker:
# docker run -d --name geoviality-api-container -p 8080:8080 -v "$(pwd):/code" geoviality-api-image