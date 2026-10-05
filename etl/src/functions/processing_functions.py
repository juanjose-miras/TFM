from functions.utils_fuctions import get_area_of_geodf

import pandas as pd
import re
import os
import glob
import openpyxl

def process_info (file_path: str) -> pd.DataFrame:

    # Importacion del archivo
    df = pd.read_csv(
        file_path, sep=";", index_col=0, encoding="utf-16",
        dtype={
            'CNAE 2009 Primary Code': str,
            'CNAE 2009 Secondary Code(s)': str,
            'Postal Code': str
        }
    )

    # Cambia al formato fecha solo indicando el año
    df['Last available year'] = pd.to_datetime(df['Last available year'], format='%d/%m/%Y', errors='coerce').dt.year
    df['Date of Establishment'] = pd.to_datetime(df['Date of Establishment'], format='%d/%m/%Y', errors='coerce').dt.year

    # Renombre de todas las columnas
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

    # Limpieza de los valores nulos y adaptación del texto a numerico
    df['Earnings_mil_last_year'] = pd.to_numeric(df['Earnings_mil_last_year'], errors='coerce')
    df['N_emp'] = pd.to_numeric(df['N_emp'], errors='coerce')
    not_geocoded = (df['Longitude'] == 0) & (df['Latitude'] == 0)
    df.loc[not_geocoded, ['Longitude', 'Latitude']] = pd.NA

    # Limpieza de espacios y duplicados
    text_columns = df.select_dtypes(include=['object', 'str']).columns
    for col in text_columns:
        df[col] = df[col].astype(str).str.strip()

    df = df.drop_duplicates(subset=['NIF_Code'])
    df.columns = df.columns.str.lower()
        
    return df


def process_finance(file_path: str) -> pd.DataFrame:

    # Importación del archivo
    df = pd.read_excel(file_path, index_col=0)

    # Obtiene todos los nombres de las variables financieras y de las variables que estan representadas en miles
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

    # Identifica las columnas relevantes
    metric_columns = [col for col in df.columns if re.search(metrics_pattern, col)]

    # Despivota los datos de métricas de la tabla (de columnas a filas): mantiene el NIF como identificador 
    # fijo y transforma todas las columnas de métricas en una única columna
    # con su respectivo valor financiero.
    df_melt = pd.melt(
        df,
        id_vars=['NIF Code'],
        value_vars=metric_columns,
        var_name='Original_Column',
        value_name='Value'
    )

    # Extrae las metricas y el año de la columna unica y las separa en dos columnas
    # nuevas (Metric y Year)
    extracted = df_melt['Original_Column'].str.extract(
        rf'({metrics_pattern}).*?(\d{{4}})',
        flags=re.DOTALL)
    df_melt['Metric'] = extracted[0]
    df_melt['Year'] = extracted[1].astype(int)

    # Pivota y cada métrica pasa a ser su propia columna, dejando las columnas de
    # NIF Code y Year
    df_final = df_melt.pivot_table(
        index=['NIF Code', 'Year'],
        columns='Metric',
        values='Value',
        aggfunc='first'
    ).reset_index()

    # Quita el nombre "Metric" que pivot_table deja en el eje de columnas
    df_final.columns.name = None

    # Ordena las filas por NIF Code y Year
    df_final = df_final.sort_values(
        by=['NIF Code', 'Year'],
        ascending=[True, False]
    ).reset_index(drop=True)

    # Adaptamos los datos y el nombre de las columnas
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


def process_per_capita_income(file_path: str) -> pd.DataFrame:
    
    df = pd.read_excel(file_path, thousands='.', skiprows=7, nrows=55730, usecols='A:F', index_col=None)

    df.rename(columns={
        ' ' : 'sections'
    }, inplace=True)

    df['sections'] = df['sections'].str.extract(r'^(\d{10})\b')
    df = df.dropna(subset='sections').copy()
    df = df[df['sections'].str.startswith('28079')].copy()

    valores = [f for f in df.columns]
    df_melt = df.melt(
        id_vars=['sections'],
        value_vars=valores,
        var_name='year',
        value_name='per_capita_income'
    )
    df_melt = df_melt.sort_values(by=['sections','year'], ascending=[True,False]).reset_index(drop=True)

    df_melt['year'] = df_melt['year'].astype(int)
    df_melt['sections'] = df_melt['sections'].astype(str).str.strip()

    df_melt.set_index(['sections','year'], inplace=True)

    return df_melt


def process_population(file_path: str) -> pd.DataFrame:

    df_pob = pd.read_csv(file_path, thousands='.', index_col=False, encoding='utf-8', sep=';')

    df_pob['Secciones'] = df_pob['Secciones'].str.extract(r'^(\d{10})\b')
    df_pob = df_pob.dropna(subset='Secciones').copy()
    df_pob = df_pob[df_pob['Secciones'].str.startswith('28079')].copy()
    df_pob = df_pob[(df_pob['Sexo'] == 'Total') & (df_pob['Nacionalidad'] == 'Total')].copy()

    df_pob['Provincias'] = df_pob['Provincias'].str.replace(r'^\d+\s+', '', regex=True)
    df_pob['Municipios'] = df_pob['Municipios'].str.replace(r'^\d+\s+', '', regex=True)

    df_pob.drop(columns=["Sexo","Nacionalidad"], inplace=True)
    df_pob.reset_index(drop=True, inplace=True)
    df_pob.rename(columns={
        'Provincias' : 'provinces',
        'Municipios' : 'city',
        'Secciones' : 'sections',
        'Periodo' : 'year',
        'Total' : 'population'
    }, inplace=True)

    df_pob['sections'] = df_pob['sections'].astype(str).str.strip()
    df_pob['year'] = df_pob['year'].astype(int)
    df_pob['population'] = pd.to_numeric(df_pob['population'], errors='coerce')

    df_pob.set_index(['sections', 'year'], inplace=True)

    return df_pob


def process_num_company(input_folder: str) -> pd.DataFrame:

    files_path = [path for path in glob.glob(f'{input_folder}/*.csv')] 

    list_concat = []

    for file in files_path:
        df = pd.read_csv(file, sep=';', index_col=False, encoding='ISO-8859-1', on_bad_lines='skip',
        dtype={
            'id_seccion_censal_local' : str,
            'desc_situacion_local' : str,
            'desc_seccion_censal_local' : str,
            'id_distrito_local': str
        })

        df = df[df['desc_situacion_local'] == 'Abierto'].copy()

        # Convierte a texto y rellena con ceros a la izquierda hasta garantizar 5 caracteres
        df['desc_seccion_censal_local'] = df['desc_seccion_censal_local'].str.zfill(3)
        df['id_distrito_local'] = df['id_distrito_local'].str.zfill(2)

        df['sections'] = '28079' + df['id_distrito_local'] + df['desc_seccion_censal_local']

        df = df.groupby('sections').size().reset_index(name='num_company')

        # Busca el año dentro de la ruta del archivo y lo asigna a las columnas
        if match := re.search(r'\d{4}',file):
            df['year'] = match.group()
        df['year'] = df['year'].astype(int)
        df['sections'] = df['sections'].astype(str).str.strip()

        df.set_index(['sections', 'year'], inplace=True)

        list_concat.append(df)

    return pd.concat(list_concat)


def merge_geodata(input_folder: str) -> pd.DataFrame:

    files_path = [
        path for path in glob.glob(f'{input_folder}/*')
        if not os.path.basename(path).startswith('~')
        ]

    for path in files_path:
        if 'local' in path:
            df_num_companies = process_num_company(path)
        elif 'section' in path:
            df_area_section = get_area_of_geodf(path)
        elif 'population' in path:
            df_population = process_population(path)
        elif any(word in path for word in ['income','capita']):
            df_per_capita_income = process_per_capita_income(path)

    df_first_join = df_population.join([df_num_companies, df_per_capita_income], how='outer')
    df_first_join[['provinces','city']] = df_first_join.groupby('sections')[['provinces','city']].bfill()

    df_first_join.reset_index(level='year', inplace=True)

    df_geo_merge = df_first_join.join(df_area_section.set_index(['sections']), how='outer')

    df_geo_merge['densidad_hab_km2'] = (df_geo_merge['population'] / df_geo_merge['area_km2']).round(2)

    df_geo_merge.drop(columns='area_km2', inplace=True)
    df_geo_merge.reset_index(level='sections', inplace=True)

    return df_geo_merge