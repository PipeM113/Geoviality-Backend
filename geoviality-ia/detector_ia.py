import ia_predictor as ia
import os
from funcs import delete_image, mark_image_for_deletion_db, get_images_to_delete_db

def arranque_ia():
    """
    Procesa las imágenes en la carpeta 'imgs/pre' con la IA.
    """
    # print("Iniciando IA...")
    directorio_pre_proceso = os.getcwd() + '\\imgs\\pre\\'
    directorio_post_proceso = os.getcwd() + '\\imgs\\post\\'
    directorio_info = os.getcwd() + '\\imgs\\'
    modelo_IA_auto = os.getcwd() + '\\Modelo 2 (Fuerte en Seco)\\Vista_Vehiculo_V2.pt'
    modelo_IA_peaton = os.getcwd() + '\\Modelo 2 (Fuerte en Seco)\\Vista_Peaton_General_V3_Refactorizado_Cris.pt'
    confianza = 0.65
    imgs = os.listdir(directorio_pre_proceso) # 'imgs' es una lista con los nombres de las imágenes en la carpeta 'pre'
    # to_del = [] # En vez de usar una lista, guardarlo en BD 'images_to_delete'
    for i in imgs: # 'i' es el nombre de la imagen
        print(f"- Viendo '{i}'...")
        res = ia.ia_imagenes(modelo_IA_auto,
                    modelo_IA_peaton,
                    directorio_pre_proceso + i, # \imgs\pre\<nombre de la imagen>
                    directorio_post_proceso + i, # \imgs\post\<nombre de la imagen>
                    directorio_info,
                    confianza
                    )
        # La funcion anterior si o si va a generar una imagen en la carpeta 'post' con el mismo nombre que la imagen de entrada
        
        # Solo si no hay detecciones, se agrega el nombre de la imagen a la lista 'to_del'
        if res:
            print(f"    - Imagen '{i}' marcado para BORRAR.")
            # to_del.append(i) # En vez de usar una lista, guardarlo en BD 'images_to_delete'
            mark_image_for_deletion_db(i)

        os.remove(directorio_pre_proceso + i) # Eliminar la imagen de la carpeta 'pre'
        print(f"    - Imagen '{i}' eliminada de 'pre', ahora queda en 'post'.\n")
        # !!!PROBLEMA!!!
        # Ver archivo 'ia_predictor.py', al final.
    
    lista_imgs_borrar = get_images_to_delete_db()
    
    for i in lista_imgs_borrar:
        delete_image(i)