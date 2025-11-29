"""Utilidades comunes de la API (directorios y red local)."""

# stdlib
import os
import socket

def create_directories() -> None:
    """Crea la estructura básica de directorios 'services' y 'services/imgs'."""
    base_dir = os.path.join(os.getcwd(), "services")
    imgs_dir = os.path.join(base_dir, "imgs")
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(imgs_dir, exist_ok=True)
    print(f"     -[API] Directorio base: {base_dir}")
    print(f"     -[API] Directorio imgs: {imgs_dir}")

def get_local_ip() -> str:
    """Obtiene la IP local preferida para la máquina (fallback a 127.0.0.1)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.254.254.254", 1))
        ip = sock.getsockname()[0]
    except Exception:  # pylint: disable=broad-exception-caught
        ip = "127.0.0.1"
    finally:
        sock.close()
    return ip
