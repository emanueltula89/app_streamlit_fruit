import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO, StringIO  # Import StringIO for text output
import locale  # Si necesitas manejar formatos de fecha/hora específicos del idioma

# --- Configuración de la página ---
# Esto define cómo aparecerá la página en la barra lateral de Streamlit
st.set_page_config(
    page_title="Análisis Inscripción de Establecimientos",
    # Título que aparecerá en el menú y en la pestaña del navegador
    page_icon="✨",  # Un ícono para esta página (puedes elegir otro emoji)
    layout="wide"  # Diseño de la página: "centered" o "wide"
)


# --- Función para cargar datos (reutilizada de tus otras páginas) ---
def cargar_datos(ruta_archivo):
    """
    Carga datos desde un archivo CSV.
    """
    try:
        df = pd.read_csv(ruta_archivo)
        return df
    except FileNotFoundError:
        st.error(
            f"Error: El archivo '{ruta_archivo}' no fue encontrado. Asegúrate de que la ruta y el nombre sean correctos.")
        return None
    except Exception as e:
        st.error(f"Ocurrió un error al cargar el CSV: {e}. Por favor, verifica el formato del archivo.")
        return None


# --- Función para crear botón de descarga a Excel (reutilizada) ---
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


# --- Nombre de tu tercer archivo CSV ---
nombre_tercer_csv = 'planilla-de-inscripción-de-establecimiento-particulares-2025-07-01.csv'

df_tercero = cargar_datos(nombre_tercer_csv)

if df_tercero is not None:
    # --- SECCIONES ELIMINADAS SEGÚN TU SOLICITUD ---
    # st.title("📄 Tablero de Análisis de Datos Adicionales")
    # st.markdown("Esta página está dedicada al análisis de un tercer conjunto de datos CSV.")
    # st.success(f"Datos cargados exitosamente desde '{nombre_tercer_csv}'.")
    # st.subheader("🔍 Vista Previa del Tercer Conjunto de Datos")
    # st.write(df_tercero.head())
    # st.header("📋 Información General de Columnas")
    # st.markdown("##### Nombres de todas las columnas:")
    # st.write(df_tercero.columns.tolist())
    # st.markdown("##### Tipos de datos y valores no nulos:")
    # buffer = StringIO()
    # df_tercero.info(buf=buffer)
    # st.text(buffer.getvalue())
    st.markdown("---")  # Mantener este separador si lo deseas, o eliminarlo también.

    # --- CONSTANTES DE NOMBRES DE COLUMNAS ESPECÍFICAS ---
    COLUMNA_INSCRIPCION_CRIADERO = 'Su establecimiento está inscripto y habilitado como criadero de fauna silvestre'
    COLUMNA_CIERVOS_CAMPO = 'Dentro de su campo los ciervos: (marque lo que corresponde).'
    COLUMNA_CIERVOS_CINCO_ANOS = 'En los últimos cinco años, el número de ciervos en su campo'
    COLUMNA_JABALI_TRES_ANOS = 'En los últimos tres años, la población de jabalí europeo:'
    COLUMNA_PUMAS_TRES_ANOS = 'En los últimos tres años, la población de pumas'
    COLUMNA_GUANACOS_VIVEN = 'En su establecimiento viven poblaciones de guanacos?'
    COLUMNA_ESPECIES_CAZA_MAYOR = 'Marque el casillero de la especies para las que solicita la práctica de caza. mayor.  Estas especies son exclusivamente para caza en establecimientos debidamente inscriptos como Criaderos de Fauna Silvestre y habilitados como Áreas de Caza Mayor.'
    COLUMNA_PORCENTAJE_CIERVOS_CAMPO = 'De las superficies total del establecimiento, qué porcentaje estima Ud. Que es utilizado por los ciervos'

    # --- ANÁLISIS AUTOMÁTICO DE COLUMNAS ---
    st.header("📊 Gráficos por Columnas (Generados Automáticamente)")

    # Lista de columnas a EXCLUIR del análisis automático de gráficos
    # Se incluyen las que tienen gráficos específicos más abajo o las que no son útiles
    columns_to_exclude_from_auto_charts = [
        'Nombre del establecimiento',
        'Ubicación del ACM',
        'Coordenada Geográfica ( punto de referencia centro del campo) Latitud y Longitud.',  # Excluida
        # Excluida
        'En los últimos 3 años, la población de guanacos',
        'Planilla completada por...',
        COLUMNA_INSCRIPCION_CRIADERO,
        COLUMNA_CIERVOS_CINCO_ANOS,
        COLUMNA_JABALI_TRES_ANOS,
        COLUMNA_PUMAS_TRES_ANOS,
        COLUMNA_GUANACOS_VIVEN,
        COLUMNA_ESPECIES_CAZA_MAYOR,
        COLUMNA_PORCENTAJE_CIERVOS_CAMPO  # Excluida
    ]

    # Iterar sobre las columnas para generar gráficos automáticamente
    for col in df_tercero.columns:
        # Excluir columnas de ID que no suelen ser útiles para gráficos de distribución
        # y las columnas solicitadas para exclusión
        if 'ID' in col.upper() or 'FECHA' in col.upper() or col in columns_to_exclude_from_auto_charts:
            continue

        # Intentar convertir a tipo numérico (float/int)
        try:
            temp_series = df_tercero[col].copy()
            temp_series_numeric = pd.to_numeric(temp_series, errors='coerce')
            if temp_series_numeric.count() / len(temp_series) > 0.8:
                st.subheader(f"Distribución de: {col}")
                fig = px.histogram(df_tercero, x=col, title=f'Distribución de {col}')
                st.plotly_chart(fig, use_container_width=True, key=f"hist_{col}")
                st.markdown("---")
                continue
        except:
            pass

        # Tratar como categórica si no es numérica y tiene pocos valores únicos
        if df_tercero[col].dtype == 'object' or df_tercero[col].nunique() < 50:
            st.subheader(f"Conteo por: {col}")
            df_tercero[col] = df_tercero[col].astype(str).str.title().str.strip()

            counts = df_tercero[col].value_counts().reset_index(name='Cantidad')
            counts.columns = [col, 'Cantidad']
            counts = counts.sort_values(by='Cantidad', ascending=False)

            if len(counts) < 100:
                with st.expander(f"Ver detalle de '{col}' (Haz clic para ver todos)"):
                    st.dataframe(counts, hide_index=True)

            top_n = min(15, len(counts))
            fig = px.bar(counts.head(top_n),
                         x=col,
                         y='Cantidad',
                         text='Cantidad',
                         title=f'Cantidad de Registros por {col} (Top {top_n})',
                         labels={col: col, 'Cantidad': 'Número de Registros'})
            fig.update_xaxes(tickangle=45)
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True, key=f"bar_{col}")
            st.markdown("---")

    # --- SECCIÓN DE ANÁLISIS DE FECHAS (si existe una columna de fecha) ---
    date_cols = [col for col in df_tercero.columns if 'FECHA' in col.upper()]

    if date_cols:
        st.header("📉 Análisis de Tendencia Temporal")
        for date_col in date_cols:
            try:
                df_tercero[date_col] = pd.to_datetime(df_tercero[date_col], errors='coerce',
                                                      dayfirst=True)
                df_tercero.dropna(subset=[date_col], inplace=True)

                if not df_tercero.empty:
                    df_tercero['Anio_Mes'] = df_tercero[date_col].dt.to_period('M').astype(str)
                    tendencia = df_tercero.groupby('Anio_Mes').size().reset_index(name='Cantidad de Registros')
                    tendencia = tendencia.sort_values(by='Anio_Mes')

                    st.subheader(f"Tendencia de Registros por Mes y Año ({date_col})")
                    fig_tendencia = px.line(tendencia,
                                            x='Anio_Mes',
                                            y='Cantidad de Registros',
                                            title=f'Cantidad de Registros a lo Largo del Tiempo ({date_col})',
                                            labels={'Anio_Mes': 'Año-Mes',
                                                    'Cantidad de Registros': 'Número de Registros'})
                    st.plotly_chart(fig_tendencia, use_container_width=True, key=f"line_{date_col}")
                    st.markdown("---")
                else:
                    st.info(f"No hay datos válidos en la columna de fecha '{date_col}' para generar la tendencia.")
            except Exception as e:
                st.warning(f"Error al procesar la columna de fecha '{date_col}': {e}. Revisa su formato.")
    else:
        st.info("No se detectó una columna de fecha para análisis de tendencia.")
    st.markdown("---")

    # --- GRÁFICOS PERSONALIZADOS (SOLICITADOS ESPECÍFICAMENTE) ---

    # 1. Cantidad de establecimientos y "Su establecimiento está inscripto y habilitado como criadero de fauna silvestre"
    st.header("📈 Inscripción y Habilitación de Criaderos")
    if COLUMNA_INSCRIPCION_CRIADERO in df_tercero.columns:
        df_tercero[COLUMNA_INSCRIPCION_CRIADERO] = df_tercero[COLUMNA_INSCRIPCION_CRIADERO].astype(
            str).str.title().str.strip()

        criadero_counts = df_tercero[COLUMNA_INSCRIPCION_CRIADERO].value_counts().reset_index(
            name='Cantidad de Establecimientos')
        criadero_counts.columns = ['Estado de Inscripción', 'Cantidad de Establecimientos']

        st.markdown("##### Cantidad de Establecimientos por Estado de Inscripción como Criadero")
        with st.expander("Ver detalle de Inscripción de Criaderos"):
            st.dataframe(criadero_counts, hide_index=True)

        # Gráfico de Torta con Porcentajes
        fig_criadero = px.pie(criadero_counts,
                              names='Estado de Inscripción',
                              values='Cantidad de Establecimientos',
                              title='Porcentaje de Establecimientos Inscriptos/Habilitados como Criadero',
                              hole=0.3,  # Para hacer un donut chart
                              labels={'Estado de Inscripción': 'Estado de Inscripción',
                                      'Cantidad de Establecimientos': 'Número de Establecimientos'})
        fig_criadero.update_traces(textinfo='percent+label')  # Muestra porcentaje y etiqueta
        st.plotly_chart(fig_criadero, use_container_width=True, key="criadero_inscripcion_chart")
    else:
        st.warning(
            f"Columna '{COLUMNA_INSCRIPCION_CRIADERO}' no encontrada. No se puede generar el gráfico de criaderos.")
    st.markdown("---")

    # 2. Cantidad de establecimiento y "Marque el casillero de la especies para las que solicita la práctica de caza. mayor. Estas especies son exclusivamente para caza en establecimientos debidamente inscriptos como Criaderos de Fauna Silvestre y habilitados como Áreas de Caza Mayor."
    st.header("🦌 Especies Solicitadas para Caza Mayor en Establecimientos")
    if COLUMNA_ESPECIES_CAZA_MAYOR in df_tercero.columns:
        df_tercero[COLUMNA_ESPECIES_CAZA_MAYOR] = df_tercero[COLUMNA_ESPECIES_CAZA_MAYOR].astype(str).str.strip()
        df_tercero[COLUMNA_ESPECIES_CAZA_MAYOR] = df_tercero[COLUMNA_ESPECIES_CAZA_MAYOR].replace(['Nan', 'nan', ''],
                                                                                                  pd.NA)
        df_tercero.dropna(subset=[COLUMNA_ESPECIES_CAZA_MAYOR], inplace=True)

        if not df_tercero.empty:
            species_exploded = df_tercero[COLUMNA_ESPECIES_CAZA_MAYOR].str.split(', ').explode()
            species_exploded = species_exploded.astype(str).str.title().str.strip()

            species_counts = species_exploded.value_counts().reset_index(name='Cantidad de Solicitudes')
            species_counts.columns = ['Especie', 'Cantidad de Solicitudes']
            species_counts = species_counts.sort_values(by='Cantidad de Solicitudes', ascending=False)

            st.markdown("##### Cantidad de Solicitudes por Especie de Caza Mayor")
            with st.expander("Ver detalle de Solicitudes de Especies"):
                st.dataframe(species_counts, hide_index=True)

            fig_especies_solicitadas = px.bar(species_counts.head(15),  # Top 15 especies solicitadas
                                              x='Especie',
                                              y='Cantidad de Solicitudes',
                                              text='Cantidad de Solicitudes',
                                              title='Especies Solicitadas para Caza Mayor en Establecimientos (Top 15)',
                                              labels={'Especie': 'Especie Solicitada',
                                                      'Cantidad de Solicitudes': 'Número de Solicitudes'})
            fig_especies_solicitadas.update_xaxes(tickangle=45)
            fig_especies_solicitadas.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig_especies_solicitadas, use_container_width=True, key="especies_caza_mayor_chart")
        else:
            st.info("No hay datos válidos en la columna de especies de caza mayor después de la limpieza.")
    else:
        st.warning(
            f"Columna '{COLUMNA_ESPECIES_CAZA_MAYOR}' no encontrada. No se puede generar el gráfico de especies de caza mayor.")
    st.markdown("---")



    # --- NUEVO GRÁFICO: En los últimos cinco años, el número de ciervos en su campo ---
    st.header("📈 Tendencia de Ciervos en los Últimos Cinco Años")
    if COLUMNA_CIERVOS_CINCO_ANOS in df_tercero.columns:
        df_tercero[COLUMNA_CIERVOS_CINCO_ANOS] = df_tercero[COLUMNA_CIERVOS_CINCO_ANOS].astype(
            str).str.title().str.strip()

        ciervos_cinco_anos_counts = df_tercero[COLUMNA_CIERVOS_CINCO_ANOS].value_counts().reset_index(
            name='Cantidad de Establecimientos')
        ciervos_cinco_anos_counts.columns = ['Tendencia de Ciervos', 'Cantidad de Establecimientos']

        st.markdown("##### Distribución de la Tendencia de Ciervos en los Últimos Cinco Años")
        with st.expander("Ver detalle de Tendencia de Ciervos"):
            st.dataframe(ciervos_cinco_anos_counts, hide_index=True)

        fig_ciervos_cinco_anos = px.pie(ciervos_cinco_anos_counts,
                                        names='Tendencia de Ciervos',
                                        values='Cantidad de Establecimientos',
                                        title='Porcentaje de Tendencia de Ciervos en los Últimos Cinco Años',
                                        hole=0.3,
                                        labels={'Tendencia de Ciervos': 'Tendencia',
                                                'Cantidad de Establecimientos': 'Número de Establecimientos'})
        fig_ciervos_cinco_anos.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_ciervos_cinco_anos, use_container_width=True, key="ciervos_cinco_anos_chart")
    else:
        st.warning(
            f"Columna '{COLUMNA_CIERVOS_CINCO_ANOS}' no encontrada. No se puede generar el gráfico de tendencia de ciervos.")
    st.markdown("---")

    # --- NUEVO GRÁFICO: Dentro de su campo o realiza algún tipo de manejo o aprovechamiento de los ciervos colorados ---
    # Esta sección fue re-habilitada y modificada a gráfico de torta con porcentajes.
    st.header("🦌 Manejo o Aprovechamiento de Ciervos Colorados")
    if COLUMNA_MANEJO_CIERVOS in df_tercero.columns:
        df_tercero[COLUMNA_MANEJO_CIERVOS] = df_tercero[COLUMNA_MANEJO_CIERVOS].astype(str).str.title().str.strip()

        manejo_ciervos_counts = df_tercero[COLUMNA_MANEJO_CIERVOS].value_counts().reset_index(
            name='Cantidad de Establecimientos')
        manejo_ciervos_counts.columns = ['Tipo de Manejo', 'Cantidad de Establecimientos']

        st.markdown("##### Distribución de Tipos de Manejo o Aprovechamiento de Ciervos Colorados")
        with st.expander("Ver detalle de Manejo de Ciervos Colorados"):
            st.dataframe(manejo_ciervos_counts, hide_index=True)

        fig_manejo_ciervos = px.pie(manejo_ciervos_counts,
                                    names='Tipo de Manejo',
                                    values='Cantidad de Establecimientos',
                                    title='Porcentaje de Manejo o Aprovechamiento de Ciervos Colorados',
                                    hole=0.3,
                                    labels={'Tipo de Manejo': 'Manejo',
                                            'Cantidad de Establecimientos': 'Número de Establecimientos'})
        fig_manejo_ciervos.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_manejo_ciervos, use_container_width=True, key="manejo_ciervos_chart")
    else:
        st.warning(
            f"Columna '{COLUMNA_MANEJO_CIERVOS}' no encontrada. No se puede generar el gráfico de manejo de ciervos.")
    st.markdown("---")

    # --- NUEVO GRÁFICO: En los últimos tres años, la población de jabalí europeo ---
    st.header("🐗 Tendencia de Población de Jabalí Europeo")
    if COLUMNA_JABALI_TRES_ANOS in df_tercero.columns:
        df_tercero[COLUMNA_JABALI_TRES_ANOS] = df_tercero[COLUMNA_JABALI_TRES_ANOS].astype(str).str.title().str.strip()

        jabali_counts = df_tercero[COLUMNA_JABALI_TRES_ANOS].value_counts().reset_index(
            name='Cantidad de Establecimientos')
        jabali_counts.columns = ['Tendencia de Población', 'Cantidad de Establecimientos']

        st.markdown("##### Distribución de la Tendencia de Población de Jabalí Europeo en los Últimos Tres Años")
        with st.expander("Ver detalle de Tendencia de Jabalí"):
            st.dataframe(jabali_counts, hide_index=True)

        fig_jabali = px.pie(jabali_counts,
                            names='Tendencia de Población',
                            values='Cantidad de Establecimientos',
                            title='Porcentaje de Tendencia de Población de Jabalí Europeo (Últimos 3 Años)',
                            hole=0.3,
                            labels={'Tendencia de Población': 'Tendencia',
                                    'Cantidad de Establecimientos': 'Número de Establecimientos'})
        fig_jabali.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_jabali, use_container_width=True, key="jabali_tendencia_chart")
    else:
        st.warning(f"Columna '{COLUMNA_JABALI_TRES_ANOS}' no encontrada. No se puede generar el gráfico de jabalí.")
    st.markdown("---")

    # --- NUEVO GRÁFICO: En los últimos tres años, la población de pumas ---
    st.header("🐆 Tendencia de Población de Pumas")
    if COLUMNA_PUMAS_TRES_ANOS in df_tercero.columns:
        df_tercero[COLUMNA_PUMAS_TRES_ANOS] = df_tercero[COLUMNA_PUMAS_TRES_ANOS].astype(str).str.title().str.strip()

        pumas_counts = df_tercero[COLUMNA_PUMAS_TRES_ANOS].value_counts().reset_index(
            name='Cantidad de Establecimientos')
        pumas_counts.columns = ['Tendencia de Población', 'Cantidad de Establecimientos']

        st.markdown("##### Distribución de la Tendencia de Población de Pumas en los Últimos Tres Años")
        with st.expander("Ver detalle de Tendencia de Pumas"):
            st.dataframe(pumas_counts, hide_index=True)

        fig_pumas = px.pie(pumas_counts,
                           names='Tendencia de Población',
                           values='Cantidad de Establecimientos',
                           title='Porcentaje de Tendencia de Población de Pumas (Últimos 3 Años)',
                           hole=0.3,
                           labels={'Tendencia de Población': 'Tendencia',
                                   'Cantidad de Establecimientos': 'Número de Establecimientos'})
        fig_pumas.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pumas, use_container_width=True, key="pumas_tendencia_chart")
    else:
        st.warning(f"Columna '{COLUMNA_PUMAS_TRES_ANOS}' no encontrada. No se puede generar el gráfico de pumas.")
    st.markdown("---")

    # --- NUEVO GRÁFICO: En su establecimiento viven poblaciones de guanacos? ---
    st.header("🐪 Poblaciones de Guanacos en Establecimientos")
    if COLUMNA_GUANACOS_VIVEN in df_tercero.columns:
        df_tercero[COLUMNA_GUANACOS_VIVEN] = df_tercero[COLUMNA_GUANACOS_VIVEN].astype(str).str.title().str.strip()

        guanacos_counts = df_tercero[COLUMNA_GUANACOS_VIVEN].value_counts().reset_index(
            name='Cantidad de Establecimientos')
        guanacos_counts.columns = ['Presencia de Guanacos', 'Cantidad de Establecimientos']

        st.markdown("##### Distribución de la Presencia de Guanacos en Establecimientos")
        with st.expander("Ver detalle de Presencia de Guanacos"):
            st.dataframe(guanacos_counts, hide_index=True)

        fig_guanacos = px.pie(guanacos_counts,
                              names='Presencia de Guanacos',
                              values='Cantidad de Establecimientos',
                              title='Porcentaje de Establecimientos con Poblaciones de Guanacos',
                              hole=0.3,
                              labels={'Presencia de Guanacos': 'Presencia',
                                      'Cantidad de Establecimientos': 'Número de Establecimientos'})
        fig_guanacos.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_guanacos, use_container_width=True, key="guanacos_chart")
    else:
        st.warning(f"Columna '{COLUMNA_GUANACOS_VIVEN}' no encontrada. No se puede generar el gráfico de guanacos.")
    st.markdown("---")

    st.subheader("Otras Secciones de Análisis Personalizadas...")
    st.markdown("Aquí puedes agregar más gráficos, tablas y análisis específicos para tu tercer archivo CSV.")
    # ... (Más código de análisis para el nuevo CSV)

    st.download_button(
        label=f"⬇️ Exportar datos completos de {nombre_tercer_csv}",
        data=to_excel(df_tercero),
        file_name=f'datos_{nombre_tercer_csv.replace(".csv", "")}_analisis.xlsx',
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.error("No se pudieron cargar los datos para esta página. Verifica el archivo y la ruta.")





