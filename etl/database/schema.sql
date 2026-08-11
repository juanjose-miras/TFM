-- ==============================================================================
-- 1. TABLA EMPRESAS (Información estática de las empresas)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS info_empresas (
    -- Clave primaria (Obligatoria y única)
    nif_code VARCHAR(15) NOT NULL,

    company_name VARCHAR(255),
    address VARCHAR(255),
    city VARCHAR(100),
    province VARCHAR(100),
    cnae_primary_code VARCHAR(10),
    cnae_secundary_code VARCHAR(255),
    n_emp INTEGER,                         
    date_est INTEGER,                      
    last_year INTEGER,                     
    earnings_mil_last_year NUMERIC(15, 2),
    longitude NUMERIC(10, 7),
    latitude NUMERIC(10, 7),
    
    -- Establece la clave primaria
    PRIMARY KEY (nif_code)
);

-- ==============================================================================
-- 2. TABLA DE DATOS FINANCIEROS (Información financiera histórica de las empresas)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS finan_empresas (
    -- 1. Regla NOT NULL explícita
    nif_code VARCHAR(15) NOT NULL,
    year INTEGER NOT NULL,
    
    ebit NUMERIC(15, 2),
    ebitda NUMERIC(15, 2),
    economic_profitability NUMERIC(10, 4),
    financial_profitability NUMERIC(10, 4),
    indebtness NUMERIC(10, 4),
    liquidity_ratio NUMERIC(10, 4),
    operating_revenue_turnover NUMERIC(15, 2),
    p_l_for_period NUMERIC(15, 2),
    profit_margin NUMERIC(10, 4),
    sales NUMERIC(15, 2),
    total_assets NUMERIC(15, 2),
    
    -- 2. Clave primaria (Asegura que no se duplique un NIF en el mismo año)
    PRIMARY KEY (nif_code, year),
    
    -- 4. CLAVE FORÁNEA (Vincula los datos financieros con la empresa)
    CONSTRAINT fk_empresa_finanzas 
        FOREIGN KEY (nif_code) 
        REFERENCES info_empresas(nif_code)
        ON DELETE CASCADE
);

-- ==============================================================================
-- 3. TABLA STAGING (Zona de aterrizaje temporal)
-- ==============================================================================
-- Tabla intermedia sin claves primarias ni reglas estrictas. 
-- Sirve para que Python vuelque los datos masivos muy rápido por lotes (commits).
CREATE TABLE IF NOT EXISTS staging_finanzas (
    nif_code VARCHAR(15),
    year INTEGER,
    
    ebit NUMERIC(15, 2),
    ebitda NUMERIC(15, 2),
    economic_profitability NUMERIC(10, 4),
    financial_profitability NUMERIC(10, 4),
    indebtness NUMERIC(10, 4),
    liquidity_ratio NUMERIC(10, 4),
    operating_revenue_turnover NUMERIC(15, 2),
    p_l_for_period NUMERIC(15, 2),
    profit_margin NUMERIC(10, 4),
    sales NUMERIC(15, 2),
    total_assets NUMERIC(15, 2)
);