import pandas as pd
import re
import os

def process_txt_csv (file_path: str) -> pd.DataFrame:

    # Importacion del archivo
    df = pd.read_csv(
        file_path, sep=";", index_col=0, encoding="utf-16",
        dtype={
            'CNAE 2009 Primary Code': str,
            'CNAE 2009 Secondary Code(s)': str,
            'Postal Code': str
        }
    )

    # 1. Cambia al formato fecha solo indicando el año
    df['Last available year'] = pd.to_datetime(df['Last available year'], format='%d/%m/%Y', errors='coerce').dt.year
    df['Date of Establishment'] = pd.to_datetime(df['Date of Establishment'], format='%d/%m/%Y', errors='coerce').dt.year

    # 2. Renombre de todas las columnas
    df = df.rename(columns={
        'NIF Code': 'NIF_Code',
        'CNAE 2009 Primary Code': 'CNAE_primary_Code',
        'CNAE 2009 Secondary Code(s)': 'CNAE_secundary_Code',
        'Number of employees Last avail. yr': 'N_emp',
        'Date of Establishment': 'Date_Est',
        'Last available year': 'Last_year',
        'Operating revenue / turnover th EUR Last avail. yr': 'Earnings_mil_last_year',
        'X coordinate' : 'Longitude',
        'Y coordinate' : 'Latitude'
    })
    df.columns = [c.replace(' ','_') for c in df.columns]

    # 3. Limpieza de los valores nulos y adaptación del texto a numerico
    df['Earnings_mil_last_year'] = pd.to_numeric(df['Earnings_mil_last_year'], errors='coerce')
    df['N_emp'] = pd.to_numeric(df['N_emp'], errors='coerce')
    not_geocoded = (df['Longitude'] == 0) & (df['Latitude'] == 0)
    df.loc[not_geocoded, ['Longitude', 'Latitude']] = pd.NA

    # 4. Limpieza de espacios y duplicados
    text_columns = df.select_dtypes(include=['object', 'str']).columns
    for col in text_columns:
        df[col] = df[col].astype(str).str.strip()

    df = df.drop_duplicates(subset=['NIF_Code'])
    df.columns = df.columns.str.lower()
        
    return df


def process_xlsx_csv(file_path: str) -> pd.DataFrame:

    # -- 1. Importación del archivo
    df = pd.read_excel(file_path, index_col=0)

    # -- 2. Obtiene todos los nombres de las variables financieras y de las variables
    #       que estan representadas en miles
    metrics = list(dict.fromkeys([
        c.split('\n')[0] for c in df.columns if len(c.split('\n')) >= 3
    ]))

    metrics = sorted(metrics, key=len, reverse=True)

    metrics_in_thousands = [
        m for m in metrics
        if any(('th EUR' in col) and (m in col) for col in df.columns)
    ]

    # Construye un patrón de búsqueda múltiple a partir de la lista de métricas.
    metrics_pattern = '|'.join(re.escape(m) for m in metrics)

    # -- 3. Identifica las columnas relevantes
    metric_columns = [col for col in df.columns if re.search(metrics_pattern, col)]

    # -- 4. Despivota los datos de métricas de la tabla (de columnas a filas): mantiene el NIF como
    #        identificador fijo y transforma todas las columnas de métricas en una única columna
    #        con su respectivo valor financiero.
    df_melt = pd.melt(
        df,
        id_vars=['NIF Code'],
        value_vars=metric_columns,
        var_name='Original_Column',
        value_name='Value'
    )

    # -- 5. Extrae las metricas y el año de la columna unica y las separa en dos columnas
    #       nuevas (Metric y Year)
    extracted = df_melt['Original_Column'].str.extract(
        rf'({metrics_pattern}).*?(\d{{4}})',
        flags=re.DOTALL)
    df_melt['Metric'] = extracted[0]
    df_melt['Year'] = extracted[1].astype(int)

    # -- 6. Pivota y cada métrica pasa a ser su propia columna, dejando las columnas de
    #       NIF Code y Year
    df_final = df_melt.pivot_table(
        index=['NIF Code', 'Year'],
        columns='Metric',
        values='Value',
        aggfunc='first'
    ).reset_index()

    # Quita el nombre "Metric" que pivot_table deja en el eje de columnas
    df_final.columns.name = None

    # -- 7. Ordena las filas por NIF Code y Year
    df_final = df_final.sort_values(
        by=['NIF Code', 'Year'],
        ascending=[True, False]
    ).reset_index(drop=True)

    # -- 8. Adaptamos los datos y el nombre de las columnas
    # Fuerza las columnas con metricas financieras a numero y las que no
    # muestran valores como n.d. a NaN
    value_columns = [c for c in df_final.columns if c not in ['NIF Code', 'Year']]
    df_final[value_columns] = df_final[value_columns].apply(pd.to_numeric, errors='coerce')

    # Multiplica por 1000 las métricas que venían en "th EUR" para dejarlas en el valor real
    for col in metrics_in_thousands:
        df_final[col] = df_final[col] * 1000

    # Elimina los años que no muestran ningun dato finacieros para la optimizacion del estudio
    df_final = df_final.dropna(subset=value_columns, how='all').reset_index(drop=True)

    # Quita cualquier sufijo entre paréntesis, ej. '(%)', sustituye barras y espacios por
    # guion bajo en todos los nombres de las columnas
    df_final.columns = [re.sub(r'\s*\([^)]*\)', '', c).strip() for c in df_final.columns]
    df_final.columns = [c.replace('/', '_').replace(' ', '_') for c in df_final.columns]
    df_final.columns = [re.sub(r'_+', '_', c).strip('_') for c in df_final.columns]
    df_final.columns = df_final.columns.str.lower()

    return df_final
