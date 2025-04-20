#crea un script que mueva las imágenes de la carpeta 'services/pre' 'services/post' a services/imgs
#y además que mueva las imágenes de la carpeta /app/services/imgs a /services/imgs

import os
import shutil

def move_images():
    """
    Mueve las imágenes de la carpeta 'services/pre' 'services/post' a services/imgs
    y además mueve las imágenes de la carpeta /app/services/imgs a /services/imgs
    """
    pre_pro_dir = os.path.join(os.getcwd(),"services", "pre_pro")
    post_pro_dir = os.path.join(os.getcwd(),"services", "post_pro")
    imgs_dir = os.path.join(os.getcwd(),"app" ,"services", "imgs")
    directorio_final = os.path.join(os.getcwd(), "services", "imgs")

    print("Directorios: \n   - pre_pro_dir: ", pre_pro_dir, "\n    - post_pro_dir: ", post_pro_dir, "\n    - imgs_dir: ", imgs_dir, "\n    - directorio_final: ", directorio_final)
    #mueve las imágenes de la carpeta pre_pro a directorio_final
    for filename in os.listdir(pre_pro_dir):
        image_path = os.path.join(pre_pro_dir, filename)
        if not os.path.exists(os.path.join(directorio_final, filename)):
            shutil.move(image_path, directorio_final)
        print(f"    - [IA] Imagen '{filename}' movida de 'pre_pro' a 'imgs'.")
    #mueve las imágenes de la carpeta post_pro a directorio_final
    for filename in os.listdir(post_pro_dir):
        image_path = os.path.join(post_pro_dir, filename)
        if not os.path.exists(os.path.join(directorio_final, filename)):
            shutil.move(image_path, directorio_final)
        print(f"    - [IA] Imagen '{filename}' movida de 'post_pro' a 'imgs'.")
    #mueve las imágenes de la carpeta imgs a directorio_final
    for filename in os.listdir(imgs_dir):
        image_path = os.path.join(imgs_dir, filename)
        if not os.path.exists(os.path.join(directorio_final, filename)):
            shutil.move(image_path, directorio_final)
        print(f"    - [IA] Imagen '{filename}' movida de 'imgs' a 'imgs'.")