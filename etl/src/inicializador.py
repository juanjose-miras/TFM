import pandas as pd
import numpy as np
import os
import shutil
import glob

# --- 1. CONFIGURACIÓN DE CARPETAS ---
carpeta_entrada = "1_Datos_SABI_Brutos"
carpeta_salida = "2_Resultados_Limpios"
carpeta_procesados = "3_Procesados_Archivo"

# Python crea las carpetas automáticamente si no existen
for carpeta in [carpeta_entrada, carpeta_salida, carpeta_procesados]:
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

# --- 2. BUSCAR ARCHIVOS ---
# Buscamos todos los archivos que terminen en .csv en la carpeta de entrada
archivos_pendientes = glob.glob(f"{carpeta_entrada}/*.csv")

if not archivos_pendientes:
    print(f"🤷‍♂️ No hay archivos nuevos en la carpeta '{carpeta_entrada}'.")
else:
    print(f"🚀 Se han encontrado {len(archivos_pendientes)} archivo(s). Iniciando ETL...")

    # --- 3. PROCESAR CADA ARCHIVO ---
    for ruta_archivo in archivos_pendientes:
        nombre_archivo = os.path.basename(ruta_archivo)
        print(f"\n🔄 Procesando: {nombre_archivo}...")

        try:
            # === AQUÍ EMPIEZA TU ETL ===
            # Extracción
            df = pd.read_csv(ruta_archivo, sep=";", index_col=0)

            # Transformación
            df = df.drop(columns=['Código consolidación', 'País'])
            df['Ultimo año disponible'] = pd.to_datetime(df['Ultimo año disponible'], format='%d/%m/%Y').dt.year
            df = df.rename(columns={
                'Nombre': 'Comp_Name',
                'Código NIF': 'Cod_NIF',
                'Localidad': 'City',
                'Ultimo año disponible': 'Last_year',
                'Ingresos de explotación\nmil EUR\nÚlt. año disp.': 'Earnings_mil_last_year'
            })
            
            df['Earnings_mil_last_year'] = df['Earnings_mil_last_year'].str.replace('.', '', regex=False)
            df['Earnings_mil_last_year'] = pd.to_numeric(df['Earnings_mil_last_year'], errors='coerce')
            df['City'] = df['City'].str.strip()
            df['Comp_Name'] = df['Comp_Name'].str.strip()
            df = df.drop_duplicates(subset=['Cod_NIF'])
            # === AQUÍ TERMINA TU ETL ===

            # Carga (Guardar el archivo limpio)
            ruta_guardado = os.path.join(carpeta_salida, f"Limpio_{nombre_archivo}")
            df.to_csv(ruta_guardado, index=False, sep=";", encoding="utf-8-sig")

            # Mover el archivo original al archivo de procesados para no repetirlo
            ruta_archivo_viejo = os.path.join(carpeta_procesados, nombre_archivo)
            shutil.move(ruta_archivo, ruta_archivo_viejo)

            print(f"✅ ÉXITO: Archivo limpiado y movido a procesados.")

        except Exception as e:
            # Si un archivo está corrupto, nos avisa pero sigue con los demás
            print(f"❌ ERROR con {nombre_archivo}: {e}")

    print("\n🎉 ¡Todos los archivos han sido procesados!")