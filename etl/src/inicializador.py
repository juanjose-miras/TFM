from functions.processing_functions import process_txt_csv, process_xlsx_csv
from etl.src.functions.db_functions import setup_database, upload_info_database, upload_staging_database, merge_staging_to_finances
import pandas as pd
import numpy as np
import os
import shutil
import glob
import traceback

# -- 1. CONFIGURACIÓN DE CARPETAS 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

schema = os.path.normpath(os.path.join(BASE_DIR, "..", "database", "schema.sql")) 

output_folder = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "clean_files"))
input_folder = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "unprocessed_files"))
save_folder = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "processed_files"))

os.makedirs(output_folder, exist_ok=True)
os.makedirs(input_folder, exist_ok=True)
os.makedirs(save_folder, exist_ok=True)

# -- 2. BUSQUEDA DE ARCHIVOS 
# Buscamos todos los archivos que terminen en .txt y .xlsx en la carpeta de entrada
files_xlsx_csv = [
    f for ext in ('txt', 'xlsx') 
    for f in glob.glob(f"{input_folder}/*.{ext}")
    if not os.path.basename(f).startswith('~')]

pending_files = [
    path for path in files_xlsx_csv
    if not os.path.exists(os.path.join(save_folder, os.path.basename(path)))
]

if not pending_files:
    print(f"No hay archivos nuevos en la carpeta '{os.path.basename(input_folder)}'.")
else:
    print(f"Se han encontrado {len(pending_files)} archivo(s). Iniciando ETL...")
    
    # -- 3. CREACION DE LA BASE DE DATOS
    try:
        # Crea o comprueba si la Base de Datos esta establecida
        print(setup_database(schema))
    except Exception as e:
        print(f"Problema al establecer la base de datos: {e}")
    
        
    # -- 4. PROCESAR CADA ARCHIVO 
    for file_path in pending_files:
        file_name = os.path.basename(file_path)
        extension = file_path.split('.')[-1].lower()
        print(f"\nProcesando: {file_name}...")

        try:
            if extension == 'xlsx':
                # Procesado de archivo 'xlsx'
                df = process_xlsx_csv(file_path)
                print(f"Archivo {file_name} procesado")

                # Sube los datos financieros de las empresas a la base de datos y hace un merge
                print(upload_staging_database(df))
                print(merge_staging_to_finances())

                # Creamos la ruta del archivo limpio el archivo procesado
                save_clean_file = file_path.replace("unprocessed_files", "clean_files").replace(".xlsx", "_clean.csv")
                

            elif extension == 'txt':
                # Procesado de archivo 'txt'
                df = process_txt_csv(file_path)
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

    print("\n¡Todos los archivos han sido procesados!")