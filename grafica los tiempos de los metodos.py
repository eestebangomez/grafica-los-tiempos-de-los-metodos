import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
import numpy as np

# Definir la función para buscar un archivo de base de datos
def buscar_archivos():
    """
    Esta función permite al usuario buscar y seleccionar archivos de base de datos.

    Devuelve:
        Una lista de las rutas de los archivos seleccionados o None si no se selecciona ningún archivo.
    """
    archivos_seleccionados = filedialog.askopenfilenames(
        title="Seleccionar archivos de base de datos",
        filetypes=[("Archivos SQLite", "*.db")])
    return archivos_seleccionados

# Obtener la ruta de los archivos
archivos_db = buscar_archivos()

# Verificar si se seleccionaron al menos dos archivos
if len(archivos_db) >= 2:
    # Conectar a las bases de datos
    conexiones = [sqlite3.connect(archivo) for archivo in archivos_db]

    # Leer los datos de las consultas
    data = []
    for conn, archivo in zip(conexiones, archivos_db):
        query = """
            WITH DuracionesOrdenadas AS (
            SELECT
                Metodo,
                Duracion,
                ROW_NUMBER() OVER (PARTITION BY Metodo ORDER BY Duracion) AS NumFila,
                COUNT(Duracion) OVER (PARTITION BY Metodo) AS TotalFilas
            FROM Times
            WHERE Metodo LIKE 'Recharge'
            )
            SELECT
            Metodo,
            AVG(Duracion) AS promedio,
            MIN(Duracion) AS min,
            MAX(Duracion) AS max,
            CASE
                WHEN TotalFilas % 2 = 1 THEN
                MAX(CASE WHEN NumFila = (TotalFilas + 1) / 2 THEN Duracion END)
                ELSE
                AVG(CASE WHEN NumFila IN ((TotalFilas / 2), (TotalFilas / 2 + 1)) THEN Duracion END)
            END AS mediana
            FROM DuracionesOrdenadas
            GROUP BY Metodo
        """
        df = pd.read_sql_query(query, conn)
        df['Archivo'] = os.path.basename(archivo)  # Añadir el nombre del archivo a los datos
        data.append(df)

    # Cerrar las conexiones a las bases de datos
    for conn in conexiones:
        conn.close()

    # Combinar todos los DataFrames en uno solo
    df_combined = pd.concat(data)

    # Imprimir los datos por consola
    print("Datos obtenidos:")
    print(df_combined)

    # Preparar los datos para graficar
    dispositivos = df_combined['Archivo'].unique()
    avg_values = df_combined['promedio']
    med_values = df_combined['mediana']
    min_values = df_combined['min']
    max_values = df_combined['max']
    bar_width = 0.2  # Ancho de las barras

    # Calcular las barras de error (rango entre los valores mínimo y máximo)
    error_lower = np.array(med_values) - np.array(min_values)
    error_upper = np.array(max_values) - np.array(med_values)

    # Crear el gráfico de barras
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Añadir líneas para el promedio
    ax.scatter(np.arange(len(dispositivos)), avg_values, color='red', label='Promedio', zorder=3)

    # Graficar barras para la mediana
    bars = ax.bar(np.arange(len(dispositivos)), med_values, color='lightgreen', label='Mediana', capsize=5)

    # Añadir barras de error para el rango mínimo y máximo
    ax.errorbar(np.arange(len(dispositivos)), med_values, yerr=[error_lower, error_upper], fmt='o', color='black', capsize=5, label='Rango (mínimo a máximo)')

    # Añadir etiquetas y título
    ax.set_xlabel('Dispositivos')
    ax.set_ylabel('Duracion (segundos)')
    #ax.set_title('Tiempo de ejecución en segundos por dispositivo en el Flujo de recarga de saldo positivo')
    ax.set_title('Tiempo de ejecución en segundos por dispositivo en el metodo de Recarga')
    ax.set_xticks(np.arange(len(dispositivos)))
    ax.set_xticklabels(dispositivos, rotation=45, ha='right')
    ax.legend()

    # Mostrar el gráfico
    plt.tight_layout()
    plt.show()

else:
    # No se seleccionaron al menos dos archivos
    print("Se deben seleccionar al menos dos archivos de base de datos.")
