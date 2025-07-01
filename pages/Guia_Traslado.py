import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import locale

# --- Configuración de la página (solo una vez y al principio) ---
st.set_page_config(
    page_title="Análisis Guía de Traslados",  # Este será el nombre que aparece en el menú
    page_icon="📊",  # Un ícono para esta página
    layout="wide"
)


# --- Función para cargar datos ---
def cargar_datos(ruta_archivo):
    """
    Carga datos desde un archivo CSV.
    """
    try:
        df = pd.read_csv(ruta_archivo)
        return df
    except FileNotFoundError:
        st.error(
            f"Error: El archivo '{ruta_archivo}' no fue encontrado en la nueva página. Asegúrate de que la ruta y el nombre sean correctos.")
        return None
    except Exception as e:
        st.error(
            f"Ocurrió un error al cargar el CSV en la nueva página: {e}. Por favor, verifica el formato del archivo.")
        return None


# --- Función para crear botón de descarga a Excel ---
def to_excel(df):
    """
    Convierte un DataFrame a formato Excel (BytesIO) para descarga.
    """
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data


st.title("📄 Tablero de Análisis de Guías de Traslado")
st.markdown("Esta página muestra análisis de los datos de guías de traslado.")
st.markdown("---")

# --- Nombre de tu nuevo archivo CSV ---
nombre_segundo_csv = 'guia_traslado_2.csv'  # Asegúrate de que este archivo exista en la raíz de tu proyecto.

df_nuevo = cargar_datos(nombre_segundo_csv)

if df_nuevo is not None:
    st.success(f"Datos cargados exitosamente desde '{nombre_segundo_csv}'.")

    st.subheader("🔍 Vista Previa del Nuevo Conjunto de Datos")
    st.write(df_nuevo.head())
    st.markdown("---")

    # --- NOMBRES DE COLUMNA DEL NUEVO CSV (¡AJUSTA ESTOS NOMBRES SEGÚN TU CSV REAL!) ---
    # Por favor, verifica que estos nombres de columna coincidan exactamente con tu archivo 'guia_traslado.csv'
    COLUMNA_ACM_GUIA_TRASLADO = 'ACM-(Área de caza mayor)'
    COLUMNA_TIPO_AREA_CAZA_MAYOR = 'Tipo de Área de Caza Mayor'
    COLUMNA_ESPECIES_EXOTICAS = 'Especies exóticas posibles de ser cazada legalmente. (Tilde lo que corresponda). '

    # --- 1. Cantidad de Guías por ACM (Área de Caza Mayor) ---
    st.header("📈 Cantidad de Guías por Área de Caza Mayor (ACM)")
    if COLUMNA_ACM_GUIA_TRASLADO in df_nuevo.columns:
        # Aseguramos que la columna sea string y normalizamos para un conteo consistente
        df_nuevo[COLUMNA_ACM_GUIA_TRASLADO] = df_nuevo[COLUMNA_ACM_GUIA_TRASLADO].astype(str).str.title().str.strip()

        guias_por_acm = df_nuevo.groupby(COLUMNA_ACM_GUIA_TRASLADO).size().reset_index(name='Cantidad de Guías')
        guias_por_acm = guias_por_acm.sort_values(by='Cantidad de Guías', ascending=False).reset_index(drop=True)

        st.markdown("##### Detalle de Guías por ACM")
        with st.expander(f"Ver los {min(10, len(guias_por_acm))} principales (Haz clic para ver todos)"):
            st.dataframe(guias_por_acm, hide_index=True)
        st.download_button(
            label=f"⬇️ Exportar Guías por ACM",
            data=to_excel(guias_por_acm),
            file_name=f'guias_por_acm_{nombre_segundo_csv.replace(".csv", "")}.xlsx',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown("##### Gráfico de Guías por ACM (Top 15)")
        top_n_acm_guias = guias_por_acm.head(15)
        fig_guias_acm = px.bar(top_n_acm_guias,
                               x=COLUMNA_ACM_GUIA_TRASLADO,
                               y='Cantidad de Guías',
                               title='Cantidad de Guías Emitidas por Área de Caza Mayor (Top 15)',
                               labels={COLUMNA_ACM_GUIA_TRASLADO: 'Área de Caza Mayor',
                                       'Cantidad de Guías': 'Número de Guías'})
        fig_guias_acm.update_xaxes(tickangle=45)
        st.plotly_chart(fig_guias_acm, use_container_width=True, key="guias_acm_chart")
    else:
        st.warning(
            f"Columna '{COLUMNA_ACM_GUIA_TRASLADO}' no encontrada en '{nombre_segundo_csv}'. No se puede generar el gráfico de Guías por ACM.")
    st.markdown("---")

    # --- 2. Cantidad de 'Tipo de Área de Caza Mayor' ---
    st.header("📊 Cantidad por Tipo de Área de Caza Mayor")
    if COLUMNA_TIPO_AREA_CAZA_MAYOR in df_nuevo.columns:
        # Aseguramos que la columna sea string y normalizamos
        df_nuevo[COLUMNA_TIPO_AREA_CAZA_MAYOR] = df_nuevo[COLUMNA_TIPO_AREA_CAZA_MAYOR].astype(
            str).str.title().str.strip()

        tipo_area_counts = df_nuevo[COLUMNA_TIPO_AREA_CAZA_MAYOR].value_counts().reset_index(name='Cantidad')
        tipo_area_counts.columns = ['Tipo de Área de Caza Mayor', 'Cantidad']
        tipo_area_counts = tipo_area_counts.sort_values(by='Cantidad', ascending=False).reset_index(drop=True)

        st.markdown("##### Detalle por Tipo de Área de Caza Mayor")
        with st.expander(f"Ver todos los Tipos de Área de Caza Mayor (Haz clic para ver todos)"):
            st.dataframe(tipo_area_counts, hide_index=True)
        st.download_button(
            label=f"⬇️ Exportar Tipos de Área de Caza Mayor",
            data=to_excel(tipo_area_counts),
            file_name=f'tipos_area_caza_{nombre_segundo_csv.replace(".csv", "")}.xlsx',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown("##### Gráfico de Distribución por Tipo de Área de Caza Mayor")
        fig_tipo_area = px.pie(tipo_area_counts,
                               names='Tipo de Área de Caza Mayor',
                               values='Cantidad',
                               title='Distribución por Tipo de Área de Caza Mayor',
                               hole=0.3,
                               width=800,
                               height=600)
        st.plotly_chart(fig_tipo_area, use_container_width=True, key="tipo_area_caza_chart")
    else:
        st.warning(
            f"Columna '{COLUMNA_TIPO_AREA_CAZA_MAYOR}' no encontrada en '{nombre_segundo_csv}'. No se puede generar el gráfico de Tipo de Área de Caza Mayor.")
    st.markdown("---")

    # --- 3. Cantidad de Especies Exóticas Posibles de Ser Cazadas Legalmente ---
    st.header("🦌 Especies Exóticas Posibles de Ser Cazadas Legalmente")
    if COLUMNA_ESPECIES_EXOTICAS in df_nuevo.columns:
        # Asumo que esta columna podría contener múltiples especies separadas por algún delimitador
        # Si es una especie por fila, value_counts es suficiente.
        # Si son múltiples, necesitaríamos un procesamiento adicional (ej. df[COLUMNA_ESPECIES_EXOTICAS].str.split(',').explode())

        # Para empezar, asumimos una especie por fila o que cada entrada es una "categoría" de especies.
        # Normalizamos el texto para un conteo consistente.
        df_nuevo[COLUMNA_ESPECIES_EXOTICAS] = df_nuevo[COLUMNA_ESPECIES_EXOTICAS].astype(str).str.title().str.strip()

        especies_counts = df_nuevo[COLUMNA_ESPECIES_EXOTICAS].value_counts().reset_index(name='Cantidad')
        especies_counts.columns = ['Especie Exótica', 'Cantidad']
        especies_counts = especies_counts.sort_values(by='Cantidad', ascending=False).reset_index(drop=True)

        st.markdown("##### Detalle de Especies Exóticas")
        with st.expander(f"Ver todas las Especies Exóticas (Haz clic para ver todos)"):
            st.dataframe(especies_counts, hide_index=True)
        st.download_button(
            label=f"⬇️ Exportar Especies Exóticas",
            data=to_excel(especies_counts),
            file_name=f'especies_exoticas_{nombre_segundo_csv.replace(".csv", "")}.xlsx',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown("##### Gráfico de Distribución de Especies Exóticas (Top 15)")
        top_n_especies = especies_counts.head(15)
        fig_especies = px.bar(top_n_especies,
                              x='Especie Exótica',
                              y='Cantidad',
                              text='Cantidad',  # ¡NUEVO! Mostrar etiquetas de valor en las barras
                              title='Distribución de Especies Exóticas Cazadas Legalmente (Top 15)',
                              labels={'Especie Exótica': 'Especie', 'Cantidad': 'Número de Registros'})
        fig_especies.update_xaxes(tickangle=45)
        fig_especies.update_traces(texttemplate='%{text}',
                                   textposition='outside')  # ¡NUEVO! Formato y posición de etiquetas
        st.plotly_chart(fig_especies, use_container_width=True, key="especies_exoticas_chart")
    else:
        st.warning(
            f"Columna '{COLUMNA_ESPECIES_EXOTICAS}' no encontrada en '{nombre_segundo_csv}'. No se puede generar el gráfico de Especies Exóticas.")
    st.markdown("---")

    st.subheader("Otras Secciones de Análisis...")
    # ... (Más código de análisis para el nuevo CSV)

    st.download_button(
        label=f"⬇️ Exportar datos completos de {nombre_segundo_csv}",
        data=to_excel(df_nuevo),
        file_name=f'datos_{nombre_segundo_csv.replace(".csv", "")}_analisis.xlsx',
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.error("No se pudieron cargar los datos para la segunda página. Verifica el archivo y la ruta.")
