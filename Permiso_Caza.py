import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime
import locale
import unicodedata
import re
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

st.set_page_config(
    page_title=" Permisos de Caza", # Este será el nombre que aparece en el menú
    page_icon="🏠", # Un ícono que aparecerá junto al nombre
    layout="wide"
)



# --- Text Normalization Function ---
def normalize_text(text):
    """Normalizes text by lowercasing, stripping, removing accents, and non-alphanumeric chars."""
    if pd.isna(text):
        return ""  # Return empty string for NaN values
    text = str(text).lower().strip()
    # Remove accents
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    # Remove characters that are not letters, numbers, spaces, or hyphens (useful for names)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return text


# --- Geocoding Function with Cache ---
# Cache to store geocoded results
_geocoding_cache = {}
# Initialize geolocator (use a unique user_agent if deploying for production)
geolocator = Nominatim(user_agent="streamlit_caza_app_v2")


def get_lat_lon_country(location_name):
    """
    Geocodes a location name and returns (latitude, longitude, country).
    Uses a cache to avoid repeated API calls and handles rate limits.
    """
    if location_name in _geocoding_cache:
        return _geocoding_cache[location_name]

    try:
        # Add a small delay to respect Nominatim's rate limit (1 request per second)
        time.sleep(1.2)  # A bit more than 1 second to be safe

        location = geolocator.geocode(location_name, addressdetails=True, language='es')
        if location:
            country = location.raw.get('address', {}).get('country', 'Desconocido')
            result = (location.latitude, location.longitude, country)
            _geocoding_cache[location_name] = result
            return result
        else:
            _geocoding_cache[location_name] = (None, None, 'Desconocido')
            return (None, None, 'Desconocido')
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        # st.warning(f"Error de geocodificación para '{location_name}': {e}. Reintentando o saltando.") # Can be uncommented for debugging
        _geocoding_cache[location_name] = (None, None, 'Desconocido')
        return (None, None, 'Desconocido')
    except Exception as e:
        # st.warning(f"Error inesperado al geocodificar '{location_name}': {e}") # Can be uncommented for debugging
        _geocoding_cache[location_name] = (None, None, 'Desconocido')
        return (None, None, 'Desconocido')


# Try to set locale for Spanish month names
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except locale.Error:
        st.warning(
            "No se pudo establecer la configuración regional en español. Los nombres de los meses pueden aparecer en inglés.")

st.set_page_config(layout="wide")


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


# --- Función para crear botón de descarga a Excel ---
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data


st.title("📊 Tablero de Análisis de Permisos de Caza - Página Principal") # Título ligeramente modificado
st.markdown("---")  # Separador para mejor apariencia

# --- Nombre de tu archivo CSV ---
nombre_nuevo_csv = 'mis_datos_maestros_final_v1.csv'

df = cargar_datos(nombre_nuevo_csv)

if df is not None:
    st.success(f"Datos cargados exitosamente desde '{nombre_nuevo_csv}'.")

    st.subheader("🔍 Vista Previa de los Datos")
    st.write(df.head())
    st.markdown("---")

    # --- NOMBRES DE COLUMNA REALES DE TU CSV ---
    COLUMNA_ACM = 'ACM-(Área de caza mayor)'
    COLUMNA_GUIA = 'Responsable Guía de Caza'
    COLUMNA_CIUDAD_ESTADO_PROVINCIA = 'Ciudad, Estado o Provincia'
    COLUMNA_CATEGORIA = 'Categoria '
    COLUMNA_FECHA_EMISION = 'Fecha '
    COLUMNA_PAIS = 'País'

    # --- FILTRADO GLOBAL DE FECHAS Y DATOS INVÁLIDOS ANTES DE CUALQUIER ANÁLISIS ---
    st.markdown("### Pre-procesamiento de Datos")
    if COLUMNA_FECHA_EMISION in df.columns:
        df[COLUMNA_FECHA_EMISION] = pd.to_datetime(df[COLUMNA_FECHA_EMISION], format='%d/%m/%Y', errors='coerce')
        df.dropna(subset=[COLUMNA_FECHA_EMISION], inplace=True)

        # Definir las fechas y valores a excluir
        fecha_excluir_nov_1964_start = datetime(1964, 11, 1)
        fecha_excluir_nov_1964_end = datetime(1964, 11, 30)
        fecha_excluir_mar_1970_start = datetime(1970, 3, 1)
        fecha_excluir_mar_1970_end = datetime(1970, 3, 31)

        # Crear una máscara para las filas a mantener (excluir fechas específicas)
        mask_fechas_a_mantener = ~ (
                ((df[COLUMNA_FECHA_EMISION] >= fecha_excluir_nov_1964_start) & (
                        df[COLUMNA_FECHA_EMISION] <= fecha_excluir_nov_1964_end)) |
                ((df[COLUMNA_FECHA_EMISION] >= fecha_excluir_mar_1970_start) & (
                        df[COLUMNA_FECHA_EMISION] <= fecha_excluir_mar_1970_end))
        )
        df = df[mask_fechas_a_mantener].copy()

        # Filtro específico para ACM (aplicado después de la carga para no modificar el original)
        if COLUMNA_ACM in df.columns:
            ACM_EXCLUSION_LIST = ['04342341992025242amccc3agar4algar']
            df['ACM_Normalizado'] = df[COLUMNA_ACM].astype(str).str.lower().str.strip()
            df = df[~df['ACM_Normalizado'].isin(ACM_EXCLUSION_LIST)].copy()
            df.drop(columns=['ACM_Normalizado'], inplace=True, errors='ignore')  # Clean up temp column
            st.info("Se han excluido entradas específicas de ACM.")

        # Filtro específico para Guías (aplicado después de la carga para no modificar el original)
        if COLUMNA_GUIA in df.columns:
            # Applying normalization *before* filtering specific exclusion list and before getting uniques
            df['Guia_Normalizado'] = df[COLUMNA_GUIA].apply(normalize_text)
            # Example problematic strings (normalize them for the list)
            GUIA_EXCLUSION_LIST = ['0-132432432243432', 'fila0', 'fila1', 'fila2',
                                   '']  # Added empty string for robustness
            df = df[~df['Guia_Normalizado'].isin(GUIA_EXCLUSION_LIST)].copy()
            st.info("Se han excluido entradas específicas de Guías y se han normalizado los nombres.")

        # --- NUEVO: Normalización de Ciudad, Estado o Provincia ---
        if COLUMNA_CIUDAD_ESTADO_PROVINCIA in df.columns:
            df['Ciudad_Estado_Provincia_Normalizada'] = df[COLUMNA_CIUDAD_ESTADO_PROVINCIA].apply(normalize_text)
            # Remove empty strings after normalization as they won't geocode
            df = df[df['Ciudad_Estado_Provincia_Normalizada'] != ''].copy()
            st.info("Se han normalizado los nombres de Ciudad, Estado o Provincia.")
        else:
            st.warning(f"Columna '{COLUMNA_CIUDAD_ESTADO_PROVINCIA}' no encontrada para normalización.")

        # --- NUEVO: Normalización de País ---
        if COLUMNA_PAIS in df.columns:
            df['Pais_Normalizado'] = df[COLUMNA_PAIS].astype(str).str.title()
            # No excluir vacíos aquí a menos que sea deseado, ya que el mapeo los corrige.
            st.info("Se ha normalizado la columna País.")
        else:
            st.warning(f"Columna '{COLUMNA_PAIS}' no encontrada para normalización.")


        if df.empty:
            st.error(
                "Después de aplicar los filtros, no quedan datos para analizar. Ajusta los filtros o verifica el CSV.")
            st.stop()
        else:
            st.info(f"Datos filtrados y listos para análisis. Quedan {len(df)} filas.")

            # --- IMPORTANT: Create derived date columns HERE, after global filtering ---
            df['Mes_Numero'] = df[COLUMNA_FECHA_EMISION].dt.month
            df['Anio'] = df[COLUMNA_FECHA_EMISION].dt.year

            # Mapeo de números de mes a nombres en español
            nombres_meses_es = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            df['Mes_Nombre'] = df['Mes_Numero'].map(nombres_meses_es)
            df['Mes_Anio_Display'] = df['Mes_Nombre'] + ' - ' + df['Anio'].astype(str)

    else:
        st.warning(f"Columna '{COLUMNA_FECHA_EMISION}' no encontrada. No se pudo aplicar el filtro de fechas.")
    st.markdown("---")

    # --- 1. Áreas de Caza Mayor (ACMs) ---
    st.header("📍 Áreas de Caza Mayor (ACMs) Únicas")
    if COLUMNA_ACM in df.columns:
        acms_unicos = pd.DataFrame(df[COLUMNA_ACM].astype(str).str.strip().dropna().unique(), columns=[COLUMNA_ACM])
        acms_unicos = acms_unicos.sort_values(by=COLUMNA_ACM).reset_index(drop=True)

        col1_acm, col2_acm = st.columns([0.7, 0.3])
        with col1_acm:
            with st.expander(f"Ver los {min(5, len(acms_unicos))} primeros ACMs (Haz clic para ver todos)"):
                st.dataframe(acms_unicos, hide_index=True)
        with col2_acm:
            st.info(f"Hay **{len(acms_unicos)}** áreas de caza mayor únicas.")  # Auto-display count
            st.download_button(
                label=f"⬇️ Exportar todos los ACMs",
                data=to_excel(acms_unicos),
                file_name=f'acms_unicos_{nombre_nuevo_csv.replace(".csv", "")}.xlsx',
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning(f"Columna '{COLUMNA_ACM}' no encontrada. Por favor, revisa el nombre de la columna.")
    st.markdown("---")

    # --- 2. Responsables/Guías de Caza ---
    st.header("👤 Responsables/Guías de Caza Únicos")
    if COLUMNA_GUIA in df.columns:
        # Use the normalized column for uniqueness, but display original if preferred.
        # 'Guia_Normalizado' should already exist from global filter section
        guias_unicos_df = pd.DataFrame(df['Guia_Normalizado'].dropna().unique(), columns=['Guía Normalizado'])
        guias_unicos_df = guias_unicos_df.sort_values(by='Guía Normalizado').reset_index(drop=True)

        col1_guia, col2_guia = st.columns([0.7, 0.3])
        with col1_guia:
            with st.expander(
                    f"Ver los {min(5, len(guias_unicos_df))} primeros Responsables/Guías (Haz clic para ver todos)"):
                st.dataframe(guias_unicos_df, hide_index=True)
        with col2_guia:
            st.info(
                f"Hay **{len(guias_unicos_df)}** responsables/guías de caza únicos (normalizados).")  # Auto-display count
            st.download_button(
                label=f"⬇️ Exportar todos los Responsables/Guías",
                data=to_excel(guias_unicos_df),
                file_name=f'guias_unicos_{nombre_nuevo_csv.replace(".csv", "")}.xlsx',
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning(f"Columna '{COLUMNA_GUIA}' no encontrada. Por favor, revisa el nombre de la columna.")
    st.markdown("---")

    # --- 3. Tabla y Gráfico de País y Mapa ---
    st.header("🌎 Análisis Geográfico de Permisos por País") # Título ajustado
    if COLUMNA_PAIS in df.columns: # Ahora usamos COLUMNA_PAIS
        # Usamos la columna normalizada para contar y agrupar
        paises_counts = df.groupby(COLUMNA_PAIS).size().reset_index(name='Cantidad') # Agrupamos por COLUMNA_PAIS
        paises_counts.columns = ['País', 'Cantidad']
        paises_counts = paises_counts.sort_values(by='Cantidad', ascending=False)

        st.markdown("##### Detalles por País")
        with st.expander(f"Ver los {min(10, len(paises_counts))} principales (Haz clic para ver todos)"):
            st.dataframe(paises_counts, hide_index=True)
        st.download_button(
            label=f"⬇️ Exportar Países",
            data=to_excel(paises_counts),
            file_name=f'paises_{nombre_nuevo_csv.replace(".csv", "")}.xlsx',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown("##### Cantidad de Permisos por País (Top 15)") # Título del gráfico ajustado
        top_n_paises = paises_counts.head(15)
        fig_paises = px.bar(top_n_paises,
                              x='País', # Eje X ahora es País
                              y='Cantidad',
                              text='Cantidad', # ¡NUEVO! Mostrar etiquetas de valor en las barras
                              title='Permisos por País (Top 15)', # Título del gráfico ajustado
                              labels={'País': 'País', 'Cantidad': 'Número de Permisos'}) # Etiquetas ajustadas
        fig_paises.update_xaxes(tickangle=45)
        fig_paises.update_traces(texttemplate='%{text}', textposition='outside') # Formato de etiquetas
        st.plotly_chart(fig_paises, use_container_width=True, key="main_pais_chart") # Key ajustada

        st.markdown("---")
        st.markdown("##### Mapa de Distribución de Permisos por País (Top 20)") # Título del mapa ajustado
        st.info(
            "Obteniendo coordenadas geográficas para las ubicaciones. Esto puede tomar un tiempo (aproximadamente 1 segundo por ubicación única).")

        # Get top 20 unique locations for geocoding
        # Ahora usamos paises_counts para obtener los países más frecuentes
        top_20_locations_map = paises_counts.head(20)['País'].tolist()

        # Geocode and prepare data for map
        geo_data_map = []
        progress_text_map = "Geocodificando países, por favor espera..."
        my_bar_map = st.progress(0, text=progress_text_map)

        for i, loc_name in enumerate(top_20_locations_map):
            lat, lon, country_from_geo = get_lat_lon_country(loc_name) # 'country_from_geo' es el país devuelto por geocodificador
            if lat is not None and lon is not None:
                cantidad = paises_counts[paises_counts['País'] == loc_name]['Cantidad'].iloc[0]
                geo_data_map.append(
                    {'Ubicación': loc_name, 'Latitud': lat, 'Longitud': lon, 'Cantidad': cantidad, 'País_Geocodificado': country_from_geo})
            my_bar_map.progress((i + 1) / len(top_20_locations_map), text=f"{progress_text_map} ({i + 1}/{len(top_20_locations_map)})")
        my_bar_map.empty()

        df_map_countries = pd.DataFrame(geo_data_map)

        if not df_map_countries.empty:
            # Create a scatter map with marker size and color by Quantity
            fig_map_countries = px.scatter_mapbox(df_map_countries,
                                        lat="Latitud",
                                        lon="Longitud",
                                        size="Cantidad",
                                        color="Cantidad",
                                        color_continuous_scale=px.colors.sequential.Reds, # ¡NUEVO! Gradiente de rojos
                                        hover_name="Ubicación",
                                        hover_data={"Cantidad": True, "País_Geocodificado": True},
                                        zoom=1,
                                        height=600,
                                        title="Distribución Geográfica de Permisos por País (Top 20 Países)", # Título del mapa ajustado
                                        mapbox_style="open-street-map")

            fig_map_countries.update_layout(mapbox_bounds={"west": -180, "east": 180, "south": -90, "north": 90})
            st.plotly_chart(fig_map_countries, use_container_width=True, key="location_map_chart_countries") # Key ajustada
        else:
            st.warning(
                "No se pudieron obtener coordenadas geográficas para generar el mapa de países. Esto puede deberse a problemas de conexión a internet o a nombres de países no reconocidos.")

        st.markdown("---")

    else:
        st.warning(
            f"Columna '{COLUMNA_PAIS}' no encontrada. Por favor, revisa el nombre de la columna.")
    st.markdown("---")


    # --- 4. Tabla y Gráfico de Categoría ---
    st.header("🏷️ Análisis por Categoría")
    if COLUMNA_CATEGORIA in df.columns:
        categoria_counts = df[COLUMNA_CATEGORIA].value_counts().reset_index()
        categoria_counts.columns = ['Categoría', 'Cantidad']
        categoria_counts = categoria_counts.sort_values(by='Cantidad', ascending=False)

        st.markdown("##### Detalles por Categoría")
        with st.expander(f"Ver todas las Categorías (Haz clic para ver todos)"):
            st.dataframe(categoria_counts, hide_index=True)
        st.download_button(
            label=f"⬇️ Exportar Categorías",
            data=to_excel(categoria_counts),
            file_name=f'categorias_{nombre_nuevo_csv.replace(".csv", "")}.xlsx',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown("##### Distribución de Categorías")
        fig_categoria = px.pie(categoria_counts,
                               names='Categoría',
                               values='Cantidad',
                               title='Distribución de Permisos por Categoría',
                               hole=0.3,
                               width=800,
                               height=600)
        st.plotly_chart(fig_categoria, use_container_width=True, key="main_categoria_chart")
    else:
        st.warning(f"Columna '{COLUMNA_CATEGORIA}' no encontrada. Por favor, revisa el nombre de la columna.")
    st.markdown("---")

    # --- Análisis Mensual y Semanal de Permisos ---
    st.header("🗓️ Análisis de Permisos por Mes y Semana")
    if COLUMNA_FECHA_EMISION in df.columns:
        try:
            if not df.empty:
                # --- Conteo por Mes ---
                permisos_por_mes = df.groupby(['Anio', 'Mes_Numero', 'Mes_Anio_Display']).size().reset_index(
                    name='Cantidad de Permisos')
                permisos_por_mes = permisos_por_mes.sort_values(by=['Anio', 'Mes_Numero']).reset_index(drop=True)

                st.markdown("##### Permisos por Mes y Año")
                st.dataframe(permisos_por_mes[['Mes_Anio_Display', 'Cantidad de Permisos']], hide_index=True)

                fig_permisos_mes = px.bar(permisos_por_mes,
                                          x='Mes_Anio_Display',
                                          y='Cantidad de Permisos',
                                          title='Permisos de Caza por Mes y Año',
                                          labels={'Mes_Anio_Display': 'Mes y Año',
                                                  'Cantidad de Permisos': 'Número de Permisos'})
                fig_permisos_mes.update_traces(width=0.5)
                st.plotly_chart(fig_permisos_mes, use_container_width=True, key="main_permisos_mes_chart")

                mes_mas_permisos = permisos_por_mes.loc[permisos_por_mes['Cantidad de Permisos'].idxmax()]
                st.info(
                    f"El mes con más permisos es **{mes_mas_permisos['Mes_Anio_Display']}** con **{mes_mas_permisos['Cantidad de Permisos']}** permisos.")

            else:
                st.info("No hay datos válidos de fechas para analizar por mes y semana.")

        except Exception as e:
            st.error(
                f"Error al procesar o graficar los permisos por mes/semana: {e}. Revisa el formato de la columna '{COLUMNA_FECHA_EMISION}'.")
    else:
        st.warning(
            f"Columna '{COLUMNA_FECHA_EMISION}' no encontrada. No se pudo generar el gráfico combinado de fechas.")
    st.markdown("---")

    # --- Gráfico Combinado de Permisos Semanales por Mes (Enero a Junio) ---
    st.header("📊 Permisos Semanales Combinados por Mes (Enero a Junio)")
    if COLUMNA_FECHA_EMISION in df.columns:
        df_grafico_combinado = df[
            (df['Mes_Numero'] >= 1) & (df['Mes_Numero'] <= 6)
            ].copy()

        if not df_grafico_combinado.empty:
            df_grafico_combinado['Dia_Del_Mes'] = df_grafico_combinado[COLUMNA_FECHA_EMISION].dt.day
            df_grafico_combinado['Semana_Del_Mes'] = ((df_grafico_combinado['Dia_Del_Mes'] - 1) // 7) + 1
            df_grafico_combinado['Semana_Etiqueta'] = 'Semana ' + df_grafico_combinado['Semana_Del_Mes'].astype(str)

            df_grafico_combinado['Mes_Semana_Label'] = df_grafico_combinado['Mes_Nombre'] + ' - ' + \
                                                       df_grafico_combinado['Semana_Etiqueta']

            permisos_mes_semana_combinado = df_grafico_combinado.groupby(
                ['Anio', 'Mes_Numero', 'Mes_Nombre', 'Semana_Del_Mes', 'Mes_Semana_Label']).size().reset_index(
                name='Cantidad de Permisos')

            permisos_mes_semana_combinado = permisos_mes_semana_combinado.sort_values(
                by=['Anio', 'Mes_Numero', 'Semana_Del_Mes'])

            fig_combined_weekly = px.bar(permisos_mes_semana_combinado,
                                         x='Mes_Semana_Label',
                                         y='Cantidad de Permisos',
                                         color='Mes_Nombre',
                                         facet_col='Anio',
                                         facet_col_wrap=2,
                                         title='Permisos de Caza por Semana dentro de cada Mes (Enero - Junio)',
                                         labels={'Mes_Semana_Label': 'Mes y Semana',
                                                 'Cantidad de Permisos': 'Número de Permisos', 'Mes_Nombre': 'Mes'},
                                         category_orders={"Mes_Semana_Label": permisos_mes_semana_combinado[
                                             'Mes_Semana_Label'].tolist()},
                                         height=600
                                         )
            fig_combined_weekly.update_xaxes(tickangle=45, showgrid=True)
            fig_combined_weekly.update_layout(
                legend_title_text='Mes',
                hovermode="x unified"
            )
            st.plotly_chart(fig_combined_weekly, use_container_width=True, key="combined_monthly_weekly_chart")
        else:
            st.info(
                "No hay datos para generar el gráfico combinado de permisos semanales por mes (Enero a Junio) después del filtrado.")
    else:
        st.warning(
            f"Columna '{COLUMNA_FECHA_EMISION}' no encontrada. No se pudo generar el gráfico combinado de fechas.")
    st.markdown("---")

else:
    st.error("No se pudieron cargar los datos. Por favor, verifica el archivo CSV y la ruta.")