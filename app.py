import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt

# 1. Título de la aplicación
st.title("Análisis Simple de Frutas")
st.write("Esta es una aplicación Streamlit que muestra datos de frutas y un gráfico.")

# 2. Cargar los datos desde el archivo CSV
ruta_csv = "frutas.csv"
try:
    df = pd.read_csv(ruta_csv)
except FileNotFoundError:
    st.error(f"Error: El archivo '{ruta_csv}' no se encontró. Asegúrate de que está en la misma carpeta que 'app.py'.")
    st.stop() # Detiene la ejecución si el archivo no se encuentra

# 3. Mostrar los datos crudos (opcional)
st.subheader("Datos Originales:")
st.dataframe(df)

# 4. Procesar los datos: Sumar las cantidades por fruta
# Agrupar por la columna 'Fruta' y sumar 'Cantidad'
df_agrupado = df.groupby('Fruta')['Cantidad'].sum().reset_index()
df_agrupado = df_agrupado.sort_values(by='Cantidad', ascending=False) # Opcional: ordenar

st.subheader("Conteo Total por Fruta:")
st.dataframe(df_agrupado)

# 5. Crear el gráfico de barras interactivo con Altair
st.subheader("Gráfico de Cantidad de Frutas (Interactivo):")

chart = alt.Chart(df_agrupado).mark_bar().encode(
    x=alt.X('Fruta', sort='-y', title="Tipo de Fruta"), # Ordena por cantidad descendente
    y=alt.Y('Cantidad', title="Cantidad Total"),
    tooltip=['Fruta', 'Cantidad'] # Esto es lo que hace que aparezca la etiqueta al pasar el mouse
).properties(
    title='Cantidad Total de Cada Fruta'
).interactive() # Permite hacer zoom y pan

st.altair_chart(chart, use_container_width=True) # Muestra el gráfico en Streamlit, ajustando al ancho del contenedor

st.markdown("---")
st.write("¡Desarrollado con Streamlit!")