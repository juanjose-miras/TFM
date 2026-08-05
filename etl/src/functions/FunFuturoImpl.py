from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

def geolocalizar_coordenadas(df):
    """
    Detecta empresas sin coordenadas (Latitud/Longitud nulas) y busca 
    su ubicación exacta utilizando OpenStreetMap.
    """
    print("Iniciando motor de geolocalización espacial...")
    
    # 1. Creamos la dirección completa temporal
    df['Full_Address'] = (
        df['Street'].astype(str) + ", " + 
        df['ZIP_cod'].astype(str) + ", " + 
        df['City'].astype(str) + ", " + 
        df['Province'].astype(str) + ", España"
    )
    
    # 2. Configuramos el motor de búsqueda (1 segundo de cortesía)
    geolocator = Nominatim(user_agent="etl_tfm_analitica_espacial")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    
    # 3. Filtramos las que necesitan coordenadas
    filtro_sin_coord = df['Latitude'].isna()
    empresas_perdidas = df[filtro_sin_coord]
    
    print(f"Empresas a geolocalizar: {len(empresas_perdidas)}")
    
    # 4. Buscamos y asignamos
    for index, row in empresas_perdidas.iterrows():
        try:
            location = geocode(row['Full_Address'])
            if location:
                df.at[index, 'Latitude'] = location.latitude
                df.at[index, 'Longitude'] = location.longitude
                print(f"Éxito: {row['Company']}")
            else:
                print(f"No encontrada: {row['Full_Address']}")
        except Exception as e:
            print(f"Error de red en {row['Company']}: {e}")
            
    # 5. Limpieza final
    df = df.drop(columns=['Full_Address'])
    
    return df