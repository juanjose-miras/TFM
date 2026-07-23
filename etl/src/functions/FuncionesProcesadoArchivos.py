import pandas as pd

def ProcesadoLimpieza_txt_csv (ruta_archivo: str):

    # Importacion del archivo
    df = pd.read_csv(
        ruta_archivo, sep=";", index_col=0, encoding="utf-16",
        dtype={
            'Código primario CNAE 2009': str,
            'Código(s) segundario(s) CNAE 2009': str
        }
    )

    # 1. Cambia al formato fecha solo indicando el año
    df['Ultimo año disponible'] = pd.to_datetime(df['Ultimo año disponible'], format='%d/%m/%Y', errors='coerce').dt.year
    df['Fecha constitución'] = pd.to_datetime(df['Fecha constitución'], format='%d/%m/%Y', errors='coerce').dt.year

    # 2. Renombre de todas las columnas
    df = df.rename(columns={
        'Nombre': 'Company',
        'Código NIF': 'NIF_cod',
        'Calle' : 'Street',
        'Código postal' : 'ZIP_cod',
        'Localidad': 'City',
        'Provincia' : 'Province',
        'Código primario CNAE 2009' : 'CNAE_primary',
        'Código(s) segundario(s) CNAE 2009' : 'CNAE_secundary',
        'Número empleados Últ. año disp.' : 'N_emp',
        'Fecha constitución' : 'Date_Inc',
        'Ultimo año disponible': 'Last_year',
        'Ingresos de explotación mil EUR Últ. año disp.': 'Earnings_mil_last_year'
    })

    # 3. Limpieza de los valores nulos y adaptación del texto a numerico
    # df['Earnings_mil_last_year'] = df['Earnings_mil_last_year'].str.replace('.', '', regex=False)
    df['Earnings_mil_last_year'] = pd.to_numeric(df['Earnings_mil_last_year'], errors='coerce')
    df['N_emp'] = pd.to_numeric(df['N_emp'], errors='coerce')

    # 4. Limpieza de espacios y duplicados
    columnas_texto = df.select_dtypes(include=['object','str']).columns
    for col in columnas_texto:
        df[col] = df[col].astype(str).str.strip()

    df = df.drop_duplicates(subset=['NIF_cod'])

    # Exportacion del archivo .txt a .csv a la carpeta ArchivosProcesados
    archivo_limpio = ruta_archivo.replace("ArchivosSinProcesar", "ArchivosProcesados").replace(".txt", "_limpio.csv")
    df.to_csv(archivo_limpio, index=False, sep=";", encoding="utf-8-sig")

    return None
