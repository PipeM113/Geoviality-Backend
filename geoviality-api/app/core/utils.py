import os
import socket

def create_directories() -> None:
    base_dir = os.path.join(os.getcwd(), "services")
    imgs_dir = os.path.join(base_dir, "imgs")
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(imgs_dir, exist_ok=True)
    print(f"     -[API] Directorio base: {base_dir}")
    print(f"     -[API] Directorio imgs: {imgs_dir}")

def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip
