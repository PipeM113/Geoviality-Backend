# Makefile

# Nombre del archivo de configuración de Docker Compose
COMPOSE_FILE=docker-compose.yml

# Levantar los servicios definidos en docker-compose.yml
up:
	docker-compose -f $(COMPOSE_FILE) up -d

# Detener los servicios definidos en docker-compose.yml
down:
	docker-compose -f $(COMPOSE_FILE) down

# Reiniciar los servicios definidos en docker-compose.yml
restart:
	docker-compose -f $(COMPOSE_FILE) down
	docker-compose -f $(COMPOSE_FILE) up -d

# Ver los logs de los servicios definidos en docker-compose.yml
logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

# Limpiar los contenedores, volúmenes y redes creados por Docker Compose
clean:
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f

# Construir las imágenes de Docker definidas en docker-compose.yml
build:
	docker-compose -f $(COMPOSE_FILE) build

# Ver el estado de los servicios definidos en docker-compose.yml
status:
	docker-compose -f $(COMPOSE_FILE) ps

# Ejecutar todo en secuencia para levantar los servicios
run: build up
	@echo "Servicios levantados correctamente"

venv:
	python3 -m venv .venv && . ./.venv/bin/activate && pip install -r ./geoviality-api/requirements.txt && pip install -r ./geoviality-ia/requirements.txt