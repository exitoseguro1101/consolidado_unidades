import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import re

# ======================
# CONFIGURACIÓN DE PÁGINA
# ======================
st.set_page_config(
    page_title="Consolidado de Unidades",
    page_icon="🏢",
    layout="wide"
)

# ======================
# OCULTAR BARRA SUPERIOR Y FOOTER DE STREAMLIT
# ======================
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# ======================
# ESTILOS PERSONALIZADOS
# ======================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700&display=swap');
    * { font-family: 'Nunito', sans-serif !important; }
    .stApp { background-color: #E6DDD3; color: #2E2E2E; }
    h1, h2, h3, label { color: #2E2E2E !important; font-family: 'Nunito', sans-serif !important; }
    .block-container { padding-top: 2rem; }
    .dataframe { background-color: #FFFFFF; border-radius: 10px; border: 1px solid #D1D0CB; }
    div[data-baseweb="select"] { 
        background-color: #FFFFFF; border-radius: 8px; 
        color: #2E2E2E !important; font-family: 'Nunito', sans-serif !important; 
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================
# CARGAR DATOS
# ======================
df = pd.read_excel("Consolidado_Unidades.xlsx")

# ======================
# ENCABEZADO
# ======================
col1, col2 = st.columns([1, 6])
with col1:
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    st.image("logo_Aura.png", width=120)
with col2:
    st.markdown("<h1 style='margin-bottom:0;'>Consolidado de Unidades</h1>", unsafe_allow_html=True)
    st.write("Visualización interactiva por **Comuna** y **Tipología**")

# ======================
# FILTROS
# ======================
col_f1, col_f2 = st.columns(2)
with col_f1:
    comuna_sel = st.selectbox("Selecciona una comuna:", sorted(df["COMUNA"].dropna().unique()))
with col_f2:
    tipologia_sel = st.selectbox("Selecciona una tipología:", sorted(df["TIPOLOGÍA"].dropna().unique()))

# ======================
# FILTRAR DATOS
# ======================
df_filtrado = df[(df["COMUNA"] == comuna_sel) & (df["TIPOLOGÍA"] == tipologia_sel)]

# ======================
# OBTENER "DESDE"
# ======================
if not df_filtrado.empty:
    df_desde = (
        df_filtrado.loc[df_filtrado.groupby("PROYECTO")["Real"].idxmin()]
        [["INMOBILIARIA", "PROYECTO", "N°", "SUP TOTAL (M2)", "UF/M2", "Real"]]
        .rename(columns={"Real": "Desde (UF)", "N°": "Dpto"})
    )
else:
    df_desde = pd.DataFrame(columns=["INMOBILIARIA", "PROYECTO", "Dpto", "SUP TOTAL (M2)", "UF/M2", "Desde (UF)"])

# ----------------------
# LIMPIEZA Y WRAP DE PROYECTOS
# ----------------------
df_desde["PROYECTO_RAW"] = df_desde["PROYECTO"].astype(str).replace({r'<br\s*/?>': ' '}, regex=True)

def wrap_label(text, max_chars=9):
    if not isinstance(text, str) or text.strip() == "":
        return text
    words = text.split()
    lines = []
    current = ""
    for w in words:
        if current == "":
            current = w
        else:
            if len(current + " " + w) <= max_chars:
                current += " " + w
            else:
                lines.append(current)
                current = w
    if current:
        lines.append(current)
    return "<br>".join(lines)

df_desde["PROYECTO_WRAP"] = df_desde["PROYECTO_RAW"].apply(lambda s: wrap_label(s, max_chars=9))

# ======================
# TABLA ORDENADA Y RESALTADA
# ======================
df_desde_tabla = df_desde.drop(columns=["PROYECTO_WRAP", "PROYECTO_RAW"])
df_desde_tabla["PROYECTO"] = df_desde["PROYECTO"]
df_desde_tabla = df_desde_tabla.sort_values("Desde (UF)").reset_index(drop=True)

# Seleccionar solo las 6 columnas que quieres mostrar
df_desde_tabla = df_desde_tabla[["INMOBILIARIA", "PROYECTO", "Dpto", "SUP TOTAL (M2)", "UF/M2", "Desde (UF)"]]

# Formatear valores numéricos a 2 decimales
for col in ["SUP TOTAL (M2)", "UF/M2", "Desde (UF)"]:
    df_desde_tabla[col] = df_desde_tabla[col].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")

st.write("### Valores 'Desde' por Proyecto")

if not df_desde_tabla.empty:
    min_val = df_desde_tabla["Desde (UF)"].astype(float).min()

    # Resaltar fila completa del mínimo en amarillo elegante
    def highlight_min_row(row):
        if float(row["Desde (UF)"]) == min_val:
            return ['color: #FFD700'] * len(row)
        else:
            return [''] * len(row)

    # Centrar columnas Dpto, Sup Total (m2), UF/M2, Desde (UF)
    def center_columns(s):
        return ['text-align: center'] * len(s)

    st.dataframe(
        df_desde_tabla.style.apply(highlight_min_row, axis=1)
                            .apply(center_columns, subset=["Dpto", "SUP TOTAL (M2)", "UF/M2", "Desde (UF)"]),
        use_container_width=True
    )
else:
    st.write("No hay datos para la selección actual.")

# ======================
# GRÁFICO DE BARRAS UF/M2 ORDENADO
# ======================
if not df_desde.empty:
    df_grafico = df_desde.sort_values("UF/M2").reset_index(drop=True)
    min_idx = df_grafico["UF/M2"].idxmin()

    paleta_colores = ["#2E2E2E", "#6E6353", "#8B7F74", "#A69C8F", "#5A5049", "#BFB7AD", "#7F7F7F"]
    color_minimo = "#E07A5F"

    x_order = df_grafico["PROYECTO_WRAP"].tolist()

    fig = go.Figure()
    inmobiliarias = df_grafico["INMOBILIARIA"].unique()

    for idx, inmobiliaria in enumerate(inmobiliarias):
        df_inmo = df_grafico[df_grafico["INMOBILIARIA"] == inmobiliaria]
        x = df_inmo["PROYECTO_WRAP"]
        y_vals = list(df_inmo["UF/M2"])

        colores = [paleta_colores[idx % len(paleta_colores)]] * len(df_inmo)
        for i_local, i_global in enumerate(df_inmo.index):
            if i_global == min_idx:
                colores[i_local] = color_minimo

        textos = []
        for i_local, i_global in enumerate(df_inmo.index):
            if i_global == min_idx:
                textos.append(f"<span style='background-color:#FFE5DC;padding:2px;border-radius:3px;color:black'>{y_vals[i_local]:.2f}</span>")
            else:
                textos.append(f"{y_vals[i_local]:.2f}")

        fig.add_trace(go.Bar(
            x=x,
            y=y_vals,
            text=textos,
            textposition='outside',
            texttemplate='%{text}',
            marker_color=colores,
            marker_line_color='rgba(0,0,0,0.6)',
            marker_line_width=1.5,
            name=inmobiliaria
        ))

    altura_base = 700
    incremento = max(0, (len(df_grafico) - 12) * 25)
    altura_final = altura_base + incremento

    fig.update_layout(
        barmode='group',
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2E2E2E", size=14, family="Nunito"),
        title=dict(
            text="Comparación de precios UF/m² por Proyecto",
            x=0.01,
            xanchor='left',
            font=dict(size=20, family="Nunito", color="#2E2E2E")
        ),
        yaxis=dict(
            title=dict(text="UF/m²", font=dict(family="Nunito", size=16, color="#2E2E2E")),
            tickfont=dict(family="Nunito", size=12, color="#2E2E2E"),
            gridcolor="#D1D0CB",
            zerolinecolor="#D1D0CB",
            automargin=True
        ),
        xaxis=dict(
            title=dict(text="Proyecto", font=dict(family="Nunito", size=16, color="#2E2E2E")),
            tickfont=dict(color="#2E2E2E", family="Nunito", size=11),
            tickangle=0,
            automargin=True,
            categoryorder='array',
            categoryarray=x_order
        ),
        bargap=0.18,
        margin=dict(t=120, b=240, r=150),
        height=altura_final,
        legend=dict(font=dict(family="Nunito", size=12, color="#2E2E2E"))
    )

    st.plotly_chart(fig, use_container_width=True)





































