import pandas as pd
import re
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import psycopg

_engine = None

def database_engine():
    global _engine
    if _engine is not None:
        return _engine

    load_dotenv()
    db_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
    )
    _engine = create_engine(db_url)
    return _engine
    


def setup_database(schema_path : str) -> str:
    engine = database_engine()

    with open(schema_path, 'r', encoding='utf-8') as file:
        sql_file = file.read()

    with engine.connect() as conection:
        conection.execute(text(sql_file))
        conection.commit()

    return "Estructura de base de datos creada/verificada con exito"
    


def reset_database() -> str:
    engine = database_engine()

    try:
        with engine.connect() as conection:
            conection.execute(text("TRUNCATE TABLE info_empresas CASCADE;"))
            conection.execute(text("TRUNCATE TABLE staging_finanzas;"))
            conection.commit()

        return "La base de datos se ha restablecido correctamente"

    except Exception as e:
        return f"Error al restablecer la base de datos: {e}"


def upload_info_database(df : pd.DataFrame) -> str:
    engine = database_engine()

    
    print(f"Subiendo {len(df)} empresas a 'info_empresas'...")

    # Convierte 'NaN' en 'None' para evitar conflictos con la Base de Datos
    df = df.where(pd.notnull(df), None)

    columns = list(df.columns)
    columns_sql = ', '.join(columns)
    values_sql =  ', '.join(f":{c}" for c in columns)
    update_sql = ', '.join(f"{c} = EXCLUDED.{c}" for c in columns if c != 'nif_code')

    upsert_sql = text(f"""
    INSERT INTO info_empresas ({columns_sql})
    VALUES ({values_sql})
    ON CONFLICT (nif_code) DO UPDATE SET {update_sql}
    """)
    
    with engine.connect() as conection:
        conection.execute(upsert_sql, df.to_dict(orient='records'))
        conection.commit()

    return "Toda la información de las empresas ha sido subida correctamente a la base de datos"

   

def upload_staging_database(df : pd.DataFrame) -> str:
    engine = database_engine()

    print(f"Subiendo {len(df)} registros financieros a 'staging_finanzas'...")

    # Convierte 'NaN' en 'None' para evitar conflictos con la Base de Datos
    df = df.where(pd.notnull(df), None)

    df.to_sql(
        name='staging_finanzas',
        con=engine,
        if_exists='append',
        index=False,
        chunksize=2000
    )

    return "Datos financieros subidos correctamente a la base de datos"



def merge_staging_to_finances() -> str:
    engine=database_engine()


    with engine.connect() as conection:
        conection.execute(text("""
            INSERT INTO finan_empresas
            SELECT * FROM staging_finanzas
            ON CONFLICT (nif_code, year) DO UPDATE SET
                ebit = EXCLUDED.ebit,
                ebitda = EXCLUDED.ebitda,
                economic_profitability = EXCLUDED.economic_profitability,
                financial_profitability = EXCLUDED.financial_profitability,
                indebtness = EXCLUDED.indebtness,
                liquidity_ratio = EXCLUDED.liquidity_ratio,
                operating_revenue_turnover = EXCLUDED.operating_revenue_turnover,
                p_l_for_period = EXCLUDED.p_l_for_period,
                profit_margin = EXCLUDED.profit_margin,
                sales = EXCLUDED.sales,
                total_assets = EXCLUDED.total_assets;
            """
        ))
        conection.execute(text("TRUNCATE TABLE staging_finanzas;"))
        conection.commit()

    return "Datos financieros almacenados en finan_empresas y staging vaciado."
