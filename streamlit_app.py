from pathlib import Path

import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).with_name("inventario.csv")
REQUIRED_COLUMNS = ["colegio", "PRODUCTO", "TALLA", "INVENTARIO", "ID_BUSQUEDA"]


st.set_page_config(
    page_title="Inventario Dyunic",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_inventory() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]

    if missing:
        raise ValueError(f"Faltan columnas en inventario.csv: {', '.join(missing)}")

    df = df[REQUIRED_COLUMNS].copy()
    df["colegio"] = df["colegio"].astype(str).str.strip().str.title()
    df["PRODUCTO"] = df["PRODUCTO"].astype(str).str.strip().str.title()
    df["TALLA"] = df["TALLA"].astype(str).str.strip().str.upper()
    df["INVENTARIO"] = pd.to_numeric(df["INVENTARIO"], errors="coerce").fillna(0).astype(int)
    df["ID_BUSQUEDA"] = df["ID_BUSQUEDA"].astype(str).str.strip()

    return df


def status_for_stock(stock: int, low_limit: int, ok_limit: int) -> str:
    if stock <= 0:
        return "Agotado"
    if stock <= low_limit:
        return "Bajo"
    if stock <= ok_limit:
        return "Bien"
    return "Alto"


def status_color(status: str) -> str:
    colors = {
        "Agotado": "#dc2626",
        "Bajo": "#f97316",
        "Bien": "#16a34a",
        "Alto": "#2563eb",
    }
    return f"background-color: {colors.get(status, '#64748b')}; color: white;"


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
    }
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 55%, #0f766e 100%);
        border-radius: 10px;
        padding: 1.5rem 1.75rem;
        color: white;
        margin-bottom: 1rem;
    }
    .hero h1 {
        font-size: 2rem;
        margin: 0 0 .25rem 0;
    }
    .hero p {
        margin: 0;
        opacity: .9;
    }
    div[data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #263244;
        border-radius: 8px;
        padding: .9rem 1rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, .24);
    }
    div[data-testid="stMetricLabel"] p {
        color: #cbd5e1;
        font-weight: 700;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-weight: 800;
    }
    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin: .5rem 0 .2rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


try:
    inventory = load_inventory()
except FileNotFoundError:
    st.error("No encontré inventario.csv en el repositorio.")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()


with st.sidebar:
    st.header("Filtros")

    schools = sorted(inventory["colegio"].dropna().unique())
    products = sorted(inventory["PRODUCTO"].dropna().unique())
    sizes = sorted(inventory["TALLA"].dropna().unique())

    selected_schools = st.multiselect("Colegio", schools, placeholder="Todos")
    selected_products = st.multiselect("Producto", products, placeholder="Todos")
    selected_sizes = st.multiselect("Talla", sizes, placeholder="Todas")

    st.divider()
    st.subheader("Semáforo")
    low_limit = st.number_input("Bajo hasta", min_value=1, max_value=50, value=3, step=1)
    ok_limit = st.number_input("Bien hasta", min_value=low_limit + 1, max_value=100, value=8, step=1)


filtered = inventory.copy()

if selected_schools:
    filtered = filtered[filtered["colegio"].isin(selected_schools)]
if selected_products:
    filtered = filtered[filtered["PRODUCTO"].isin(selected_products)]
if selected_sizes:
    filtered = filtered[filtered["TALLA"].isin(selected_sizes)]

filtered["ESTADO"] = filtered["INVENTARIO"].apply(lambda stock: status_for_stock(stock, low_limit, ok_limit))

total_references = len(filtered)
total_units = int(filtered["INVENTARIO"].sum())
out_of_stock = int((filtered["INVENTARIO"] <= 0).sum())
low_stock = int(((filtered["INVENTARIO"] > 0) & (filtered["INVENTARIO"] <= low_limit)).sum())
ok_stock = int(((filtered["INVENTARIO"] > low_limit) & (filtered["INVENTARIO"] <= ok_limit)).sum())
high_stock = int((filtered["INVENTARIO"] > ok_limit).sum())

st.markdown(
    """
    <div class="hero">
        <h1>Inventario Dyunic</h1>
        <p>Vista rápida para priorizar producción por colegio, producto y talla.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)
metric_1.metric("Referencias", f"{total_references:,}")
metric_2.metric("Unidades", f"{total_units:,}")
metric_3.metric("Agotadas", f"{out_of_stock:,}")
metric_4.metric("Bajitas", f"{low_stock:,}")
metric_5.metric("Bien / alto", f"{ok_stock + high_stock:,}")

if filtered.empty:
    st.warning("No hay registros con los filtros seleccionados.")
    st.stop()

priority = filtered[filtered["ESTADO"].isin(["Agotado", "Bajo"])].sort_values(
    ["INVENTARIO", "colegio", "PRODUCTO", "TALLA"],
    ascending=[True, True, True, True],
)

left, right = st.columns([1.35, 1])

with left:
    st.markdown('<div class="section-title">Prioridad de producción</div>', unsafe_allow_html=True)
    st.caption("Primero aparecen las referencias agotadas y luego las de menor inventario.")

    priority_view = priority[["colegio", "PRODUCTO", "TALLA", "INVENTARIO", "ESTADO"]].head(80)
    st.dataframe(
        priority_view.style.map(status_color, subset=["ESTADO"]),
        use_container_width=True,
        hide_index=True,
        height=430,
    )

with right:
    st.markdown('<div class="section-title">Estado general</div>', unsafe_allow_html=True)

    status_order = ["Agotado", "Bajo", "Bien", "Alto"]
    status_summary = (
        filtered["ESTADO"]
        .value_counts()
        .reindex(status_order, fill_value=0)
        .rename_axis("Estado")
        .reset_index(name="Referencias")
    )
    st.bar_chart(status_summary, x="Estado", y="Referencias", color="#1e3a8a")

    school_risk = (
        filtered.assign(En_riesgo=filtered["ESTADO"].isin(["Agotado", "Bajo"]))
        .groupby("colegio", as_index=False)
        .agg(Referencias=("ID_BUSQUEDA", "count"), En_riesgo=("En_riesgo", "sum"), Unidades=("INVENTARIO", "sum"))
    )
    school_risk["% En riesgo"] = (school_risk["En_riesgo"] / school_risk["Referencias"] * 100).round(1)
    school_risk = school_risk.sort_values(["% En riesgo", "En_riesgo"], ascending=False).head(8)

    st.markdown('<div class="section-title">Colegios con más riesgo</div>', unsafe_allow_html=True)
    st.dataframe(school_risk, use_container_width=True, hide_index=True, height=250)

st.markdown('<div class="section-title">Resumen por producto</div>', unsafe_allow_html=True)

product_summary = (
    filtered.groupby("PRODUCTO", as_index=False)
    .agg(
        Referencias=("ID_BUSQUEDA", "count"),
        Unidades=("INVENTARIO", "sum"),
        Agotadas=("ESTADO", lambda status: (status == "Agotado").sum()),
        Bajitas=("ESTADO", lambda status: (status == "Bajo").sum()),
    )
    .sort_values(["Agotadas", "Bajitas", "Unidades"], ascending=[False, False, True])
)

st.dataframe(product_summary, use_container_width=True, hide_index=True, height=320)

st.markdown('<div class="section-title">Detalle completo</div>', unsafe_allow_html=True)
st.dataframe(
    filtered[["colegio", "PRODUCTO", "TALLA", "INVENTARIO", "ESTADO", "ID_BUSQUEDA"]]
    .sort_values(["colegio", "PRODUCTO", "TALLA"]),
    use_container_width=True,
    hide_index=True,
    height=420,
)
