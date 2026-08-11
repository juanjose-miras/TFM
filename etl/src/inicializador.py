from etl.src.functions.processing_functions import process_txt_csv, process_xlsx_csv
import pandas as pd
import numpy as np
import os
import shutil
import glob

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
    f for ext in ('xlsx', 'txt') 
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

    # -- 3. PROCESAR CADA ARCHIVO 
    for file_path in pending_files:
        file_name = os.path.basename(file_path)
        extension = file_path.split('.')[-1].lower()
        print(f"\nProcesando: {file_name}...")

        try:
            if extension == 'xlsx':
                df = process_xlsx_csv(file_path)
                save_clean_file = file_path.replace("unprocessed_files", "clean_files").replace(".xlsx", "_clean.csv")

            elif extension == 'txt':
                df = process_txt_csv(file_path)
                save_clean_file = file_path.replace("unprocessed_files", "clean_files").replace(".txt", "_clean.csv")

            # Guardamos el archivo procesado 
            df.to_csv(save_clean_file, index=False, sep=";", encoding="utf-8-sig")

            # Hacemos una copia del archivo original en archivos procesados
            shutil.copy2(file_path, os.path.join(save_folder, file_name))

            print(f"Archivo {file_name} procesado")

        except Exception as e:
            # Si un archivo está corrupto, nos avisa pero sigue con los demás
            print(f"ERROR con {file_name}: {e}")

    print("\n¡Todos los archivos han sido procesados!")