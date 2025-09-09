import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
import numpy as np
import streamlit as st

st.set_page_config(layout="wide")


########################################################################################################################
def preprocess_VF(excel, month):
    month_dict = {
        "Enero": "Suma de ene",
        "Febrero": "Suma de feb",
        "Marzo": "Suma de mar",
        "Abril": "Suma de abr",
        "Mayo": "Suma de may",
        "Junio": "Suma de jun",
        "Julio": "Suma de jul",
        "Agosto": "Suma de ago",
        "Septiembre": "Suma de sep",
        "Octubre": "Suma de oct",
        "Noviembre": "Suma de nov",
        "Diciembre": "Suma de dic"
    }
    ## Procesamiento de VF
    df = pd.read_excel(excel, sheet_name="Pivot", skiprows=3)
    df = df.loc[df["Line"] == "LMAQ-FAR"]
    df = df[["Config", "Product Number", "Product Short Description", month_dict[month]]]
    df = df.dropna(subset=[month_dict[month]])
    df = df.loc[df["Config"].isin(
        ["FRUCTIS 10N1 300ML", "TARRO CTT 300G_RINSE AND NO RINSE HAIR CAREÂ\xa0", "TARRO GEL 600G_STYLING GEL"])]
    df.columns = ["Config", "Product Number", "Product Short Description", "Suma"]
    return df

def preprocess_Far(excel):
    df = pd.read_excel(excel,sheet_name="STOCK",skiprows=5)
    df = df.loc[df["Tipo"] == "MP"]
    df = df.loc[df["Armazem"] != 10]
    df = df.loc[df["SEMAFORO DE CADUCIDAD"] != "CADUCADO"]
    df["Produto"] = df["Produto"].str.replace('LO', '', regex=False)
    df["Produto"] = df["Produto"].str.upper()
    df = df.groupby('Produto', as_index=False)[['Qtde']].sum()
    df.columns = ["Codigo Fareva", "Cantidad Fareva"]

    return df


def preprocess_nomen(excel):
    df = pd.read_excel(excel,sheet_name="nomenclatura",skiprows=0)
    df = df[["Código Comercial", "Código Inds.","Cód. Jugo","Cant. Enlace"]]
    df = df.dropna()
    df = df.drop_duplicates()
    df.columns = ["Codigo Comercial", "Codigo Inds.","Cod. Jugo","Cant. Enlace"]
    df["Cod. Jugo"] = df["Cod. Jugo"].astype(str)
    df["Cod. Jugo"] = df["Cod. Jugo"].str.upper()
    print(df)

    return df


def generate_coyuntural(planeacion_VF,fareva_file, requerimiento_MP_file,  month):
    with st.spinner("Esperando ..."):

        VF = preprocess_VF(planeacion_VF, month)
        stock_fareva = preprocess_Far(fareva_file)
        size = pd.DataFrame({
            'Config': ['FRUCTIS 10N1 300ML', 'TARRO CTT 300G_RINSE AND NO RINSE HAIR CAREÂ\xa0',
                       'TARRO GEL 600G_STYLING GEL'],
            'Size': [33000, 33000, 16000]
        })
        nomenclatura = preprocess_nomen(requerimiento_MP_file)


        st.session_state.stock_fareva = stock_fareva
        st.session_state.nomenclatura = nomenclatura

        df_lotes = pd.merge(VF, size, on='Config', how='inner')
        df_lotes["Lotes"] = np.ceil((df_lotes["Suma"] / df_lotes["Size"]) - 0.1)

        st.session_state.tabla_coyuntural = df_lotes

    st.success("Tablas generadas exitosamente")


def calculate_MP(df):
    stock_fareva = st.session_state.stock_fareva
    nomenclatura = st.session_state.nomenclatura
    df = df[["Product Number","Size","Lotes"]]

    df_MP = pd.merge(df,nomenclatura, how="left",left_on="Product Number", right_on="Codigo Comercial" )
    df_MP["Cantidad total"] = df_MP["Lotes"] * df_MP["Cant. Enlace"]
    df_MP_group = df_MP.groupby('Cod. Jugo', as_index=False)[['Cantidad total']].sum()
    df_MP_group.columns =["Codigo Requerido", "Cantidad Requerida"]

    print(stock_fareva)
    print(df_MP_group)

    st.session_state.tabla_MP = df_MP
    st.session_state.tabla_MP_group = df_MP_group

    df_MP_to_order = pd.merge( df_MP_group, stock_fareva, how="left", left_on="Codigo Requerido", right_on="Codigo Fareva")
    df_MP_to_order = df_MP_to_order.loc[df_MP_to_order["Codigo Requerido"] != "511S"]
    df_MP_to_order = df_MP_to_order.fillna(0)
    df_MP_to_order["Cantidad a ordenar"] = df_MP_to_order["Cantidad Fareva"] - df_MP_to_order["Cantidad Requerida"]
    print(df_MP_to_order.loc[df_MP_to_order["Cantidad a ordenar"]<0])
    st.session_state.df_MP_to_order = df_MP_to_order.loc[df_MP_to_order["Cantidad a ordenar"]<0]




########################################################################################################################
def preprocess_aeroVF(excel, month):
    month_dict = {
        "Enero": "Suma de ene",
        "Febrero": "Suma de feb",
        "Marzo": "Suma de mar",
        "Abril": "Suma de abr",
        "Mayo": "Suma de may",
        "Junio": "Suma de jun",
        "Julio": "Suma de jul",
        "Agosto": "Suma de ago",
        "Septiembre": "Suma de sep",
        "Octubre": "Suma de oct",
        "Noviembre": "Suma de nov",
        "Diciembre": "Suma de dic"
    }
    ## Procesamiento de VF
    df = pd.read_excel(excel, sheet_name="Pivot", skiprows=3)
    df = df.loc[df["Line"] == "LMAQ-FAR"]
    df = df[["Config", "Product Number", "Product Short Description", month_dict[month]]]
    df = df.dropna(subset=[month_dict[month]])
    df = df.loc[df["Config"].isin(
        [ 'SPRAY 150ML_MEN DEODORANTS', 'SPRAY 150ML_WOMEN DEODORANTS'])]
    df.columns = ["Config", "Product Number", "Product Short Description", "Suma"]
    return df

def preprocess_aeroFar(excel):
    df = pd.read_excel(excel,sheet_name="STOCK",skiprows=5)
    df = df.loc[df["Tipo"] == "MP"]
    df = df.loc[df["Armazem"] != 10]
    df = df.loc[df["SEMAFORO DE CADUCIDAD"] != "CADUCADO"]
    df["Produto"] = df["Produto"].str.replace('LO', '', regex=False)
    df["Produto"] = df["Produto"].str.upper()
    df = df.groupby('Produto', as_index=False)[['Qtde']].sum()
    df.columns = ["Codigo Fareva", "Cantidad Fareva"]

    return df

def preprocess_aeronomen(excel):
    df = pd.read_excel(excel,sheet_name="nomenclatura",skiprows=0)
    df = df[["acs","Código Inds.","Cód. Jugo","Cant. Enlace"]]
    df = df.dropna()
    df = df.drop_duplicates()
    df.columns = ["Codigo Comercial", "Codigo Inds.","Cod. Jugo","Cant. Enlace"]
    df["Cod. Jugo"] = df["Cod. Jugo"].astype(str)
    df["Cod. Jugo"] = df["Cod. Jugo"].str.upper()
    print(df)

    return df



def generate_aerosoles(planeacion_VF, fareva_file, requerimiento_MP_file, month):
    with st.spinner("Esperando ..."):
        VF = preprocess_aeroVF(planeacion_VF, month)
        stock_fareva = preprocess_aeroFar(fareva_file)
        size = pd.DataFrame({
            'Config': ['SPRAY 150ML_MEN DEODORANTS', 'SPRAY 150ML_WOMEN DEODORANTS'],
            'Size': [32000, 76000]
        })

        nomenclatura = preprocess_aeronomen(requerimiento_MP_file)


        st.session_state.stock_aero_fareva = stock_fareva
        st.session_state.aero_nomenclatura = nomenclatura

        df_lotes = pd.merge(VF, size, on='Config', how='inner')
        df_lotes["Lotes"] = np.ceil((df_lotes["Suma"] / df_lotes["Size"]) - 0.1)

        st.session_state.tabla_aerosoles = df_lotes

    st.success("Tablas generadas exitosamente")


def calculate_MP_aero(df):
    stock_fareva = st.session_state.stock_aero_fareva
    nomenclatura = st.session_state.aero_nomenclatura
    df = df[["Product Number","Size","Lotes"]]

    df_MP = pd.merge(df,nomenclatura, how="left",left_on="Product Number", right_on="Codigo Comercial" )
    df_MP = df_MP.dropna(subset=["Codigo Comercial"])
    df_MP["Cantidad total"] = df_MP["Lotes"] * df_MP["Cant. Enlace"]
    df_MP_group = df_MP.groupby('Cod. Jugo', as_index=False)[['Cantidad total']].sum()
    df_MP_group.columns =["Codigo Requerido", "Cantidad Requerida"]

    #print(stock_fareva)
    #print(df_MP_group)

    st.session_state.aero_tabla_MP = df_MP
    st.session_state.aero_tabla_MP_group = df_MP_group

    df_MP_to_order = pd.merge( df_MP_group, stock_fareva, how="left", left_on="Codigo Requerido", right_on="Codigo Fareva")
    df_MP_to_order = df_MP_to_order.loc[df_MP_to_order["Codigo Requerido"] != "511S"]
    df_MP_to_order = df_MP_to_order.fillna(0)
    df_MP_to_order["Cantidad a ordenar"] = df_MP_to_order["Cantidad Fareva"] - df_MP_to_order["Cantidad Requerida"]
    #print(df_MP_to_order.loc[df_MP_to_order["Cantidad a ordenar"]<0])
    st.session_state.aero_df_MP_to_order = df_MP_to_order.loc[df_MP_to_order["Cantidad a ordenar"]<0]

########################################################################################################################
# Configuración de página y estilo
st.set_page_config(
    page_title="Planificación de Materias Primas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejorar la apariencia
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #3498db;
    }
    .section-header {
        color: #2980b9;
        padding: 0.5rem 0;
        margin: 1rem 0;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #2980b9;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .sidebar .css-1d391kg {
        padding-top: 1rem;
    }
    .stAlert {
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Mantenemos las funciones de procesamiento sin cambios
# [Todas las funciones existentes...]

# Variables de estado
if 'tabla_coyuntural' not in st.session_state:
    st.session_state.tabla_coyuntural = pd.DataFrame()

if 'stock_fareva' not in st.session_state:
    st.session_state.stock_fareva = pd.DataFrame()

if 'nomenclatura' not in st.session_state:
    st.session_state.nomenclatura = pd.DataFrame()

if 'tabla_aerosoles' not in st.session_state:
    st.session_state.tabla_aerosoles = pd.DataFrame()

if 'stock_aero_fareva' not in st.session_state:
    st.session_state.stock_aero_fareva = pd.DataFrame()

if 'aero_nomenclatura' not in st.session_state:
    st.session_state.aero_nomenclatura = pd.DataFrame()

# Barra lateral mejorada
with st.sidebar:
    st.markdown('<div style="text-align: center; margin-bottom: 1rem;"><h3>Planificación de MPs</h3></div>',
                unsafe_allow_html=True)
    st.markdown("---")

    app_mode = st.radio(
        "Navegación",
        ["📄 Archivos Coyuntural", "📊 Tablas Coyuntural", "📄 Archivos Aerosoles", "📊 Tablas Aerosoles"],
        key="navigation"
    )

    st.markdown("---")
    st.markdown("### Información")
    st.info("Esta aplicación permite planificar y calcular los requerimientos de materias primas.")

# Contenido principal
if "Archivos Coyuntural" in app_mode:
    st.markdown('<h1 class="main-header">Planificación Coyuntural</h1>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">Archivos de entrada</h3>', unsafe_allow_html=True)
        planeacion_VF = st.file_uploader("📎 Archivo de Planeación VF", type="xlsx",
                                         help="Carga el archivo de planeación VF en formato Excel")
        fareva_file = st.file_uploader("📎 Ingresos semanales de Fareva", type="xlsx",
                                       help="Carga el archivo de ingresos semanales en formato Excel")
        requerimiento_MP_file = st.file_uploader("📎 Requerimiento de MPs Coyuntural", type="xlsx",
                                                 help="Carga el archivo de requerimientos en formato Excel")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">Parámetros</h3>', unsafe_allow_html=True)

        month = st.selectbox(
            "🗓️ Mes a planear",
            ["Elige una opción", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        )

        all_files_uploaded = planeacion_VF and fareva_file and requerimiento_MP_file
        if not all_files_uploaded:
            st.warning("Por favor, carga todos los archivos necesarios")

        generate_button = st.button("✅ Generar Tablas",
                                    disabled=(not all_files_uploaded or month == "Elige una opción"))

        if generate_button:
            generate_coyuntural(planeacion_VF, fareva_file, requerimiento_MP_file, month)
        st.markdown('</div>', unsafe_allow_html=True)

elif "Tablas Coyuntural" in app_mode:
    st.markdown('<h1 class="main-header">Análisis de Datos Coyuntural</h1>', unsafe_allow_html=True)

    if st.session_state.tabla_coyuntural.empty:
        st.warning(
            "No hay datos disponibles. Por favor, genera las tablas primero en la sección 'Archivos Coyuntural'.")
    else:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">Tabla preliminar sin cubrir este mes</h3>', unsafe_allow_html=True)
        edited_df = st.data_editor(
            st.session_state.tabla_coyuntural,
            disabled=["Config", "Product Number", "Product Short Description", "Suma", "Size"],
            use_container_width=True,
            hide_index=True
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            calculate_button = st.button("🧮 Calcular MPs")
        st.markdown('</div>', unsafe_allow_html=True)

        if calculate_button:
            calculate_MP(edited_df)

        if 'tabla_MP' in st.session_state:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<h3 class="section-header">Tabla de MPs</h3>', unsafe_allow_html=True)
                st.dataframe(st.session_state.tabla_MP, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<h3 class="section-header">MPs Agrupados</h3>', unsafe_allow_html=True)
                st.dataframe(st.session_state.tabla_MP_group, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">MPs a ordenar</h3>', unsafe_allow_html=True)

            # Métricas importantes
            if not st.session_state.df_MP_to_order.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Total de MPs a ordenar",
                        f"{len(st.session_state.df_MP_to_order)}"
                    )
                with col2:
                    st.metric(
                        "Faltante más crítico",
                        f"{abs(st.session_state.df_MP_to_order['Cantidad a ordenar'].min()):.0f}"
                    )
                with col3:
                    st.metric(
                        "Códigos sin stock",
                        f"{len(st.session_state.df_MP_to_order[st.session_state.df_MP_to_order['Cantidad Fareva'] == 0])}"
                    )

            st.dataframe(st.session_state.df_MP_to_order, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif "Archivos Aerosoles" in app_mode:
    st.markdown('<h1 class="main-header">Planificación de Aerosoles</h1>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">Archivos de entrada</h3>', unsafe_allow_html=True)
        planeacion_aero_VF = st.file_uploader("📎 Archivo de Planeación VF", type="xlsx",
                                              help="Carga el archivo de planeación VF en formato Excel")
        fareva_aero_file = st.file_uploader("📎 Ingresos semanales de Fareva", type="xlsx",
                                            help="Carga el archivo de ingresos semanales en formato Excel")
        requerimiento_aero_MP_file = st.file_uploader("📎 Archivo de Aerosoles", type="xlsx",
                                                      help="Carga el archivo de aerosoles en formato Excel")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">Parámetros</h3>', unsafe_allow_html=True)

        aero_month = st.selectbox(
            "🗓️ Mes a planear",
            ["Elige una opción", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
            key="aero_month"
        )

        all_files_uploaded = planeacion_aero_VF and fareva_aero_file and requerimiento_aero_MP_file
        if not all_files_uploaded:
            st.warning("Por favor, carga todos los archivos necesarios")

        generate_button = st.button("✅ Generar Tablas",
                                    disabled=(not all_files_uploaded or aero_month == "Elige una opción"))

        if generate_button:
            generate_aerosoles(planeacion_aero_VF, fareva_aero_file, requerimiento_aero_MP_file, aero_month)
        st.markdown('</div>', unsafe_allow_html=True)

elif "Tablas Aerosoles" in app_mode:
    st.markdown('<h1 class="main-header">Análisis de Datos de Aerosoles</h1>', unsafe_allow_html=True)

    if st.session_state.tabla_aerosoles.empty:
        st.warning("No hay datos disponibles. Por favor, genera las tablas primero en la sección 'Archivos Aerosoles'.")
    else:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">Tabla preliminar sin cubrir este mes</h3>', unsafe_allow_html=True)
        edited_aero_df = st.data_editor(
            st.session_state.tabla_aerosoles,
            disabled=["Config", "Product Number", "Product Short Description", "Suma", "Size"],
            use_container_width=True,
            hide_index=True
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            calculate_button = st.button("🧮 Calcular MPs")
        st.markdown('</div>', unsafe_allow_html=True)

        if calculate_button:
            calculate_MP_aero(edited_aero_df)

        if 'aero_tabla_MP' in st.session_state:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<h3 class="section-header">Tabla de MPs</h3>', unsafe_allow_html=True)
                st.dataframe(st.session_state.aero_tabla_MP, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<h3 class="section-header">MPs Agrupados</h3>', unsafe_allow_html=True)
                st.dataframe(st.session_state.aero_tabla_MP_group, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header">MPs a ordenar</h3>', unsafe_allow_html=True)

            # Métricas importantes
            if not st.session_state.aero_df_MP_to_order.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Total de MPs a ordenar",
                        f"{len(st.session_state.aero_df_MP_to_order)}"
                    )
                with col2:
                    st.metric(
                        "Faltante más crítico",
                        f"{abs(st.session_state.aero_df_MP_to_order['Cantidad a ordenar'].min()):.0f}"
                    )
                with col3:
                    st.metric(
                        "Códigos sin stock",
                        f"{len(st.session_state.aero_df_MP_to_order[st.session_state.aero_df_MP_to_order['Cantidad Fareva'] == 0])}"
                    )

            st.dataframe(st.session_state.aero_df_MP_to_order, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

# Pie de página
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #ddd; color: #666;">
    <small>Aplicación de Planificación de Materias Primas | v1.0</small>
</div>
""", unsafe_allow_html=True)