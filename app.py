import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Accidentalidad en Bogotá 2026",
    page_icon="🚦",
    layout="wide"
)

st.title("🚦 Análisis de incidentes viales en Bogotá")
st.subheader("Periodo: 1 de enero al 30 de junio de 2026")

archivo = st.file_uploader(
    "Carga el archivo CSV de incidentes viales",
    type=["csv"]
)

if archivo is not None:

    try:
        df = pd.read_csv(archivo, encoding="utf-8", low_memory=False)

        # Limpieza de nombres de columnas
        df.columns = df.columns.str.strip()

        # Eliminar columnas completamente vacías
        df = df.dropna(axis=1, how="all")

        # Identificar columnas principales
        columna_fecha = next(
            (col for col in df.columns if col.startswith("FECHA INCIDENTE")),
            None
        )

        columna_hora = next(
            (col for col in df.columns if col.startswith("HORA INCIDENTE")),
            None
        )

        columnas_requeridas = [
            columna_fecha,
            columna_hora,
            "FUENTE",
            "LOCALIDAD",
            "TIPO DE INCIDENTE"
        ]

        if any(col is None for col in columnas_requeridas):
            st.error("El archivo no contiene todas las columnas necesarias.")
            st.write("Columnas encontradas:", list(df.columns))
            st.stop()

        # Convertir fechas
        df[columna_fecha] = pd.to_datetime(
            df[columna_fecha],
            dayfirst=True,
            errors="coerce"
        )

        # Extraer la hora
        df["HORA_NUMERICA"] = pd.to_numeric(
            df[columna_hora].astype(str).str.extract(r"(\d{1,2})")[0],
            errors="coerce"
        )

        # Limitar el periodo de estudio
        fecha_inicio = pd.Timestamp("2026-01-01")
        fecha_fin = pd.Timestamp("2026-06-30")

        df = df[
            (df[columna_fecha] >= fecha_inicio) &
            (df[columna_fecha] <= fecha_fin) &
            (df["HORA_NUMERICA"].between(0, 23))
        ].copy()

        # Limpiar información de texto
        df["LOCALIDAD"] = (
            df["LOCALIDAD"]
            .astype(str)
            .str.strip()
            .str.title()
        )

        df["TIPO DE INCIDENTE"] = (
            df["TIPO DE INCIDENTE"]
            .astype(str)
            .str.strip()
        )

        df["FUENTE"] = df["FUENTE"].astype(str).str.strip()

        # Reemplazar datos vacíos
        df["LOCALIDAD"] = df["LOCALIDAD"].replace(
            ["Nan", "None", ""], "Sin dato"
        )

        df["TIPO DE INCIDENTE"] = df["TIPO DE INCIDENTE"].replace(
            ["nan", "None", ""], "Sin dato"
        )

        # Filtros
        st.sidebar.header("Filtros de análisis")

        fecha_minima = df[columna_fecha].min().date()
        fecha_maxima = df[columna_fecha].max().date()

        fechas = st.sidebar.date_input(
            "Selecciona el periodo",
            value=(fecha_minima, fecha_maxima),
            min_value=fecha_minima,
            max_value=fecha_maxima,
            format="DD/MM/YYYY"
        )

        horas = st.sidebar.slider(
            "Selecciona el rango de horas",
            min_value=0,
            max_value=23,
            value=(0, 23)
        )

        excluir_duplicados = st.sidebar.checkbox(
            "Excluir registros marcados como duplicados",
            value=True
        )

        # Aplicar filtros
        filtrado = df.copy()

        if isinstance(fechas, tuple) and len(fechas) == 2:
            inicio = pd.Timestamp(fechas[0])
            fin = pd.Timestamp(fechas[1])

            filtrado = filtrado[
                (filtrado[columna_fecha] >= inicio) &
                (filtrado[columna_fecha] <= fin)
            ]

        filtrado = filtrado[
            filtrado["HORA_NUMERICA"].between(horas[0], horas[1])
        ]

        if excluir_duplicados:
            filtrado = filtrado[
                ~filtrado["FUENTE"].str.contains(
                    "DUPLICADO",
                    case=False,
                    na=False
                )
            ]

        # Resultados generales
        st.header("📊 Indicadores generales")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total de incidentes",
            f"{len(filtrado):,}"
        )

        col2.metric(
            "Localidades registradas",
            filtrado["LOCALIDAD"].nunique()
        )

        col3.metric(
            "Tipos de incidentes",
            filtrado["TIPO DE INCIDENTE"].nunique()
        )

        # Estadísticas con NumPy
        st.header("📈 Estadísticas por hora")

        incidentes_hora = (
            filtrado["HORA_NUMERICA"]
            .value_counts()
            .reindex(range(24), fill_value=0)
            .sort_index()
        )

        datos_hora = incidentes_hora.values

        if len(filtrado) > 0:

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Promedio",
                f"{np.mean(datos_hora):.2f}"
            )

            col2.metric(
                "Mediana",
                f"{np.median(datos_hora):.2f}"
            )

            col3.metric(
                "Desviación estándar",
                f"{np.std(datos_hora):.2f}"
            )

            col4, col5, col6 = st.columns(3)

            col4.metric(
                "Varianza",
                f"{np.var(datos_hora):.2f}"
            )

            col5.metric(
                "Rango",
                f"{np.ptp(datos_hora):.0f}"
            )

            col6.metric(
                "Percentil 50",
                f"{np.percentile(datos_hora, 50):.2f}"
            )

            hora_minima = incidentes_hora.idxmin()
            hora_maxima = incidentes_hora.idxmax()

            st.write(
                f"**Hora con menos incidentes:** {hora_minima}:00"
            )

            st.write(
                f"**Hora con más incidentes:** {hora_maxima}:00"
            )

        else:
            st.warning("No hay registros para los filtros seleccionados.")

        # Gráfico de incidentes por hora
        st.header("🕒 Incidentes por hora")

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.bar(
            incidentes_hora.index,
            incidentes_hora.values
        )

        ax.set_xlabel("Hora del día")
        ax.set_ylabel("Cantidad de incidentes")
        ax.set_title("Distribución de incidentes por hora")
        ax.set_xticks(range(24))
        ax.grid(axis="y", alpha=0.3)

        st.pyplot(fig)
        plt.close(fig)

        # Incidentes por localidad
        st.header("📍 Incidentes por localidad")

        localidad = (
            filtrado["LOCALIDAD"]
            .value_counts()
            .head(10)
        )

        fig, ax = plt.subplots(figsize=(10, 5))

        localidad.sort_values().plot(
            kind="barh",
            ax=ax
        )

        ax.set_xlabel("Cantidad de incidentes")
        ax.set_ylabel("Localidad")
        ax.set_title("Top 10 localidades con más incidentes")

        st.pyplot(fig)
        plt.close(fig)

        # Tipos de incidentes
        st.header("🚦 Tipos de incidentes")

        tipos = filtrado["TIPO DE INCIDENTE"].value_counts()

        if len(tipos) > 0:

            fig, ax = plt.subplots(figsize=(8, 8))

            ax.pie(
                tipos,
                labels=tipos.index,
                autopct="%1.1f%%",
                startangle=90
            )

            ax.set_title("Distribución por tipo de incidente")

            st.pyplot(fig)
            plt.close(fig)

        # Tabla por localidad
        st.header("📋 Resumen por localidad")

        resumen = (
            filtrado.groupby("LOCALIDAD")
            .size()
            .reset_index(name="Cantidad de incidentes")
            .sort_values(
                by="Cantidad de incidentes",
                ascending=False
            )
        )

        st.dataframe(
            resumen,
            use_container_width=True
        )

        # Tabla de registros
        st.header("🔎 Registros filtrados")

        st.dataframe(
            filtrado,
            use_container_width=True
        )

        # Descargar resultados
        csv = filtrado.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Descargar datos filtrados",
            data=csv,
            file_name="incidentes_bogota_2026.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")

else:
    st.info("Carga el archivo CSV para comenzar el análisis.")