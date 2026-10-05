import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import glob

def get_area_of_geodf(filepath : str) -> pd.DataFrame:

    file = glob.glob(f'{filepath}/*.shp')[0]

    df_sections = gpd.read_file(file)

    df_sections.rename(columns={
        'CUSEC' : 'sections'
    },inplace=True)

    df_sections = df_sections[df_sections['sections'].str.startswith('28079')].copy()

    # Proyectamos a metros
    if df_sections.crs != 'EPSG:25830':
        df_sections = df_sections.to_crs('EPSG:25830')

    df_sections['area_km2'] = df_sections.area / 1000000
    df_sections['sections'] = df_sections['sections'].astype(str).str.strip()


    return df_sections[['sections','area_km2']]

   