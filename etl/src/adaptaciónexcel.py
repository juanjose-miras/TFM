import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='xlrd')

prueba = pd.read_csv("Empresas_Aguilas.csv", sep=";")

print(prueba['Nombre'].head(20))

