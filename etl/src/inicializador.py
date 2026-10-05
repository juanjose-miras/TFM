from functions.processing_functions import process_info, process_finance, merge_geodata
from functions.db_functions import setup_database, upload_info_database, upload_staging_database, merge_staging_to_finances
import pandas as pd
import numpy as np
import os
import shutil
import glob
import traceback
import openpyxl

# -- 1. CONFIGURACIÓN DE CARPETAS 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

schema = os.path.normpath(os.path.join(BASE_DIR, "..", "database", "schema.sql")) 

output_folder = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "clean_files"))
input_folder = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "unprocessed_files"))
input_folder_geodata = os.path.normpath(os.path.join(BASE_DIR,'..','data','unprocessed_geodata_files'))
save_folder = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "processed_files"))

# -- 2. BUSQUEDA DE ARCHIVOS CON LA INFORMACION FINANCIERA DE LAS EMPRESAS Y DATOS GEOESPACIALES
# Buscamos todos los archivos que terminen en .txt y .xlsx en la carpeta de entrada
files_info_companies = [
    f for ext in ('txt', 'xlsx') 
    for f in glob.glob(f"{input_folder}/*.{ext}")
    if not os.path.basename(f).startswith('~')
]

files_geodata = glob.glob(os.path.join(input_folder_geodata, "*"))

pending_files_info_companies = [
    path for path in files_info_companies
    if not os.path.exists(os.path.join(save_folder, os.path.basename(path)))
]

if not pending_files_info_companies:
    print(f"No hay archivos nuevos en la carpeta '{os.path.basename(input_folder)}'.")
else:
    print(f"Se han encontrado {len(pending_files_info_companies)} archivo(s). Iniciando ETL...")
    
    # -- 3. CREACION DE LA BASE DE DATOS
    try:
        # Crea o comprueba si la Base de Datos esta establecida
        print(setup_database(schema))
    except Exception as e:
        print(f"Problema al establecer la base de datos: {e}")
    
        
    # -- 4. PROCESAMIENTO DE ARCHIVOS DE INFO/FINANZAS

    # Archivos necesarios:
        #   - Archivo con la informacion fiscal de todas las empresas para el estudio
        #   - Archivo con la informacion financiera necesaria de todas las empresas para el estudio
        
    for file_path in pending_files_info_companies:
        file_name = os.path.basename(file_path)
        extension = file_path.split('.')[-1].lower()
        print(f"\nProcesando: {file_name}...")

        try:
            if extension == 'xlsx':
                # Procesado de archivo 'xlsx'
                df = process_finance(file_path)
                print(f"Archivo {file_name} procesado")

                # Sube los datos financieros de las empresas a la base de datos y hace un merge
                print(upload_staging_database(df))
                print(merge_staging_to_finances())

                # Creamos la ruta del archivo limpio el archivo procesado
                save_clean_file = file_path.replace("unprocessed_files", "clean_files").replace(".xlsx", "_clean.csv")
                

            elif extension == 'txt':
                # Procesado de archivo 'txt'
                df = process_info(file_path)
                print(f"Archivo {file_name} procesado")

                # Sube la información de la empresa a la base de datos
                print(upload_info_database(df))

                # Creamos la ruta del archivo limpio el archivo procesado
                save_clean_file = file_path.replace("unprocessed_files", "clean_files").replace(".txt", "_clean.csv")

            # Guardamos el archivo procesado    
            df.to_csv(save_clean_file, index=False, sep=";", encoding="utf-8-sig")

            # Hacemos una copia del archivo original en archivos procesados
            shutil.copy2(file_path, os.path.join(save_folder, file_name))

            # Borrar el archivo procesado
            os.remove(file_path)

        except Exception as e:
            # Nos avisa del error que capturó y el tipo
            print(f"ERROR con {file_name}: {type(e).__name__}: {e}")
            traceback.print_exc() 

# -- 5. PROCESAMIENTO DE ARCHIVOS DE DATOS GEOESPACIALES

# Archivos necesarios:
#   - Archivo con el numero de habitantes de la localidad
#   - Archivo con la renta per capital del pais
#   - Carpeta con los secciones censales de la localidad
#   - Archivos con todos lo locales de la localidad

if not input_folder_geodata:
    print(f"No hay archivos nuevos en la carpeta '{os.path.basename(input_folder_geodata)}'.")
else:
    try:
        df_geodata = merge_geodata(input_folder_geodata)
        print('Archivos geoespaciales procesados!')

        save_clean_file = os.path.join(output_folder, 'geo_data.csv')
        df_geodata.to_csv(save_clean_file, index=False, sep=";", encoding="utf-8-sig")

        # Iteramos sobre la lista de archivos y carpetas
        for item_path in files_geodata:
            item_name = os.path.basename(item_path)
            dest_path = os.path.join(save_folder, item_name)
            
            if os.path.isfile(item_path):
                shutil.copy2(item_path, dest_path)
                os.remove(item_path)
                
            elif os.path.isdir(item_path):
                shutil.copytree(item_path, dest_path, dirs_exist_ok=True)
                shutil.rmtree(item_path)

    except Exception as e:
        print(f"ERROR en la carpeta {os.path.basename(input_folder_geodata)}: {type(e).__name__}: {e}")

print("\n¡Todos los archivos han sido procesados!")