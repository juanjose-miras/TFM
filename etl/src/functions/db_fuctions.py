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
    if _engine is None:
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
    try:
        with open(schema_path, 'r', encoding='utf-8') as file:
            sql_file = file.read()

        with engine.connect() as conection:
            conection.execute(text(sql_file))
            conection.commit()

        return "Estructura de base de datos creada/verificada con exito"
    
    except Exception as e:
        return f"Error con la preparación de la base de datos: {e}"


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

    try:
        print(f"Subiendo {len(df)} empresas a 'info_empresas'...")

        columns = list(df.columns)
        columns_sql = ', '.join(columns)
        



    except Exception as e:


    return None


def upload_staging_database(df : pd.DataFrame) -> str:
    engine = database_engine()

    try:
        print(f"Subiendo {len(df)} registros financieros a 'staging_finanzas'...")
        df.to_sql(
            name='staging_finanzas',
            con=engine,
            if_exists='append',
            index=False,
            chunksize=2000
        )

        return "Datos financieros subidos correctamente a la base de datos"
    except Exception as e:
        return f"ERROR al importar los datos a la base de datos: {e}"


def merge_staging_to_finances() -> str:
    engine=database_engine()

    try:
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

    except Exception as e:
        return f"Error al traspasar los datos de staging_finanzas a finan_empresas"

