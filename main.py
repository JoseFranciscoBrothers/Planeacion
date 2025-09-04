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
def generate_aerosoles(planeacion_VF, fareva_file, requerimiento_MP_file, month):
    print("b")

########################################################################################################################
if 'tabla_coyuntural' not in st.session_state:
    st.session_state.tabla_coyuntural = pd.DataFrame()

if 'stock_fareva' not in st.session_state:
    st.session_state.stock_fareva = pd.DataFrame()

if 'nomenclatura' not in st.session_state:
    st.session_state.nomenclatura = pd.DataFrame()

if 'tabla_aerosoles' not in st.session_state:
    st.session_state.tabla_aerosoles = pd.DataFrame()
########################################################################################################################

app_mode = st.sidebar.selectbox("Selecciona una pagina", ["Archivos Coyuntural", "Tablas Coyuntural",
                                                          "Archivos Aerosoles", "Tablas Aerosoles"])
if app_mode == "Archivos Coyuntural":
    st.title("Coyuntural")
    planeacion_VF = st.file_uploader("Insertar archivo de Planeación VF", type="xlsx")
    fareva_file = st.file_uploader("Insertar archivo de ingresos semanales de Fareva", type="xlsx")
    requerimiento_MP_file = st.file_uploader("Insertar archivo de requerimiento de MPs Coyuntural", type="xlsx")

    month = st.selectbox(
        "Selecciona el mes a planear",
        ["Elige una opción", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre",
         "Octubre", "Noviembre", "Diciembre"]
    )

    if st.button("Generar Tablas") and month != "Elige una opción":
        generate_coyuntural(planeacion_VF, fareva_file,requerimiento_MP_file, month)

if app_mode == "Tablas Coyuntural":
    st.title("Tablas Coyuntural")
    st.header("Tabla preliminar sin cubrir este mes")
    edited_df = st.data_editor(st.session_state.tabla_coyuntural, disabled=["Config", "Product Number",
                                                                            "Product Short Description","Suma","Size"])
    if st.button("Calcular MPs"):
        calculate_MP(edited_df)

    if 'tabla_MP' in st.session_state:
        st.header("Tabla de MPs")
        st.dataframe(st.session_state.tabla_MP)
        st.header("MPs Agrupados")
        st.dataframe(st.session_state.tabla_MP_group)
        st.header("MPs a ordenar")
        st.dataframe(st.session_state.df_MP_to_order)



################################################################################################################################
if app_mode == "Archivos Aerosoles":
    st.title("Aerosoles")
    planeacion_VF = st.file_uploader("Insertar archivo de Planeación VF", type="xlsx")
    fareva_file = st.file_uploader("Insertar archivo de ingresos semanales de Fareva", type="xlsx")
    requerimiento_MP_file = st.file_uploader("Insertar archivo de requerimiento de MPs Coyuntural", type="xlsx")

    month = st.selectbox(
        "Selecciona el mes a planear",
        ["Elige una opción", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre",
         "Octubre", "Noviembre", "Diciembre"]
    )

    if st.button("Generar Tablas") and month != "Elige una opción":
        generate_aerosoles(planeacion_VF, fareva_file, requerimiento_MP_file, month)

if app_mode == "Tablas Aerosoles":
    st.title("Tablas Aerosoles")
    st.header("Tabla preliminar sin cubrir este mes")

    st.data_editor(st.session_state.tabla_aerosoles)

