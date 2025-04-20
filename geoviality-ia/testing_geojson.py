from pymongo import MongoClient
from bson import json_util
import json

# Variables directas
direccion_mongo = 'mongodb+srv://testingUser:testingPassword@testcluster.fnuyjq3.mongodb.net/'
nombre_bd = 'geojson'
nombre_coleccion = 'location'
nombre_archivo_salida = 'archivo_salida.geojson'
lista_datos = [
    {
        "_id": 0,
        "comuna": "Quinta Normal",
        "longitude": -70.69288145516872,
        "latitude": -33.43727024973133,
        "tipo": ["grieta", "hoyo"]
    },
    {
        "_id": 1,
        "comuna": "Fantasilandia",
        "longitude": -70.65424435766955,
        "latitude": -33.4600571198148,
        "tipo": ["grieta"]
    },
    {
        "_id": 2,
        "comuna": "Providencia",
        "longitude": -70.61742552085475,
        "latitude": -33.42179672778323,
        "tipo": ["hoyo"]
    },
    {
        "_id": 3,
        "comuna": "Quilicura",
        "longitude": -70.7308898934415,
        "latitude": -33.36459109625416,
        "tipo": ["grieta", "hoyo", "lomo de toro"]
    },
    {
        "_id": 4,
        "comuna": "Independencia creo",
        "longitude": -70.69020687543431,
        "latitude": -33.386902483266205,
        "tipo": ["grieta", "lomo de toro"]
    }
]
# Fin variables




# Variables indirectas
mongo_client = MongoClient(direccion_mongo)
mongo_db = mongo_client[nombre_bd]
mongo_collection = mongo_db[nombre_coleccion]
# Fin variables indirectas




# Esta funcion "normaliza" los datos de un punto al formato de un Feature GeoJSON
def transformar_a_feature_geojson(item):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [item["longitude"], item["latitude"]]
        },
        "properties": {
            "_id": item["_id"],
            "comuna": item["comuna"],
            "tipo": item["tipo"]
        }
    }
#? Esta funcion hay que modificarla para que se ajuste a los datos que se tienen en 'lista_datos'



# Esto simplemente guarda un objeto cualquiera en un archivo JSON en disco XD
def guardar_json_en_archivo(objeto, nombre_archivo):
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        json.dump(objeto, f, default=json_util.default, ensure_ascii=False, indent=4)

# ===============

# INICIO DE LOGICA


# Insertar los datos en la colección de MongoDB en formato Feature GeoJSON
for elemento in lista_datos:
    geojson_feature = transformar_a_feature_geojson(elemento)
    
    # Verificar si el _id del Feature ya existe en la colección
    existe = mongo_collection.find_one({"properties._id": geojson_feature["properties"]["_id"]})
    
    if not existe:
        mongo_collection.insert_one(geojson_feature)
        print(f"Nuevo GeoJSON insertado con _id: {geojson_feature['properties']['_id']}")
    else:
        print(f"El documento con _id: {geojson_feature['properties']['_id']} ya existe. No se inserta.")
# Fin inserción de datos en la colección de MongoDB






# FeatureCollection contiene una lista de Features GeoJSON
# Las Features individuales se guardan en la propiedad "features" de FeatureCollection
geojson_featureCollection = {
    "type": "FeatureCollection",
    "features": []
}

# Obtener todos los documentos de la colección de MongoDB (Features individuales)
lista_features = mongo_collection.find()
#? Notar que podemos cambiar la query de .find() para obtener solo los datos que necesitamos.
#? Por ejemplo, solo los que tienen tipo grieta: mongo_collection.find({"properties.tipo": "grieta"})

# Agregar cada Feature a la lista de Features del FeatureCollection
for elemento in lista_features:
    geojson_featureCollection["features"].append(elemento)

# El archivo de salida contiene el FeatureCollection completo. Esto puede usarse en un mapa web
guardar_json_en_archivo(geojson_featureCollection, nombre_archivo_salida)
#? Si abres este archivo en https://geojson.io/ puedes ver los puntos en un mapa interactivo