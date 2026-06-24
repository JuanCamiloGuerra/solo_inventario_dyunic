from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).with_name("inventario.csv")
REQUIRED_COLUMNS = ["colegio", "PRODUCTO", "TALLA", "INVENTARIO", "ID_BUSQUEDA"]


st.set_page_config(
    page_title="Inventario Dyunic",
    layout="centered",
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


def status_class(status: str) -> str:
    return {
        "Agotado": "critical",
        "Bajo": "low",
        "Bien": "ok",
        "Alto": "high",
    }.get(status, "ok")


def render_inventory_table(df: pd.DataFrame) -> None:
    rows = []

    for _, row in df.iterrows():
        status = row["ESTADO"]
        rows.append(
            f"""
            <tr>
                <td>{escape(row["colegio"])}</td>
                <td>{escape(row["ID_BUSQUEDA"])}</td>
                <td class="number">{int(row["INVENTARIO"]):,}</td>
                <td><span class="status-pill {status_class(status)}">{escape(status)}</span></td>
            </tr>
            """
        )

    st.markdown(
        f"""
        <div class="table-wrap">
            <table class="inventory-table">
                <thead>
                    <tr>
                        <th>Colegio</th>
                        <th>Referencia completa</th>
                        <th>Inv.</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <style>
    .block-container {
        max-width: 760px;
        padding: 1rem .85rem 2rem;
    }
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 55%, #0f766e 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: .9rem;
        padding: 1.1rem 1.2rem;
    }
    .hero h1 {
        font-size: 1.55rem;
        margin: 0 0 .2rem 0;
    }
    .hero p {
        font-size: .92rem;
        margin: 0;
        opacity: .92;
    }
    div[data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #263244;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, .24);
        padding: .8rem .9rem;
    }
    div[data-testid="stMetricLabel"] p {
        color: #cbd5e1;
        font-weight: 700;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-size: 1.45rem;
        font-weight: 800;
    }
    .section-title {
        font-size: 1.12rem;
        font-weight: 800;
        margin: 1rem 0 .35rem 0;
    }
    .table-wrap {
        border: 1px solid #263244;
        border-radius: 8px;
        max-height: 68vh;
        overflow: auto;
    }
    .inventory-table {
        border-collapse: collapse;
        font-size: .84rem;
        width: 100%;
    }
    .inventory-table th {
        background: #111827;
        color: #cbd5e1;
        font-weight: 800;
        padding: .55rem .5rem;
        position: sticky;
        text-align: left;
        top: 0;
        z-index: 1;
    }
    .inventory-table td {
        border-top: 1px solid #263244;
        color: #f8fafc;
        padding: .55rem .5rem;
        vertical-align: top;
    }
    .inventory-table td:nth-child(2) {
        overflow-wrap: anywhere;
    }
    .inventory-table .number {
        text-align: right;
        white-space: nowrap;
    }
    .status-pill {
        border-radius: 999px;
        color: white;
        display: inline-block;
        font-size: .76rem;
        font-weight: 800;
        padding: .18rem .5rem;
        white-space: nowrap;
    }
    .status-pill.critical {
        background: #dc2626;
    }
    .status-pill.low {
        background: #f97316;
    }
    .status-pill.ok {
        background: #16a34a;
    }
    .status-pill.high {
        background: #2563eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


try:
    inventory = load_inventory()
except FileNotFoundError:
    st.error("No encontre inventario.csv en el repositorio.")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()


st.markdown(
    """
    <div class="hero">
        <h1>Inventario Dyunic</h1>
        <p>Inventario actualizado para revisar rapido desde el celular.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Filtros", expanded=True):
    schools = ["Todos"] + sorted(inventory["colegio"].dropna().unique())
    selected_school = st.selectbox("Colegio", schools)

    id_source = inventory.copy()
    if selected_school != "Todos":
        id_source = id_source[id_source["colegio"] == selected_school]

    search_ids = sorted(id_source["ID_BUSQUEDA"].dropna().unique())
    selected_search_ids = st.multiselect("Referencia completa", search_ids, placeholder="Todas")

with st.expander("Semaforo", expanded=False):
    low_limit = st.number_input("Bajo hasta", min_value=1, max_value=50, value=3, step=1)
    ok_limit = st.number_input("Bien hasta", min_value=low_limit + 1, max_value=100, value=8, step=1)


filtered = inventory.copy()

if selected_school != "Todos":
    filtered = filtered[filtered["colegio"] == selected_school]
if selected_search_ids:
    filtered = filtered[filtered["ID_BUSQUEDA"].isin(selected_search_ids)]

if filtered.empty:
    st.warning("No hay registros con los filtros seleccionados.")
    st.stop()

summary = (
    filtered.groupby(["colegio", "ID_BUSQUEDA"], as_index=False)
    .agg(INVENTARIO=("INVENTARIO", "sum"))
    .sort_values(["INVENTARIO", "colegio", "ID_BUSQUEDA"], ascending=[True, True, True])
)
summary["ESTADO"] = summary["INVENTARIO"].apply(lambda stock: status_for_stock(stock, low_limit, ok_limit))

total_references = len(summary)
total_units = int(summary["INVENTARIO"].sum())
out_of_stock = int((summary["INVENTARIO"] <= 0).sum())
low_stock = int(((summary["INVENTARIO"] > 0) & (summary["INVENTARIO"] <= low_limit)).sum())

metric_1, metric_2 = st.columns(2)
metric_1.metric("Agotadas", f"{out_of_stock:,}")
metric_2.metric("Bajitas", f"{low_stock:,}")

metric_3, metric_4 = st.columns(2)
metric_3.metric("Referencias", f"{total_references:,}")
metric_4.metric("Unidades", f"{total_units:,}")

st.markdown('<div class="section-title">Ver detalle completo</div>', unsafe_allow_html=True)
st.caption("La columna Estado queda coloreada segun el nivel de inventario.")

detail = summary.sort_values(["INVENTARIO", "colegio", "ID_BUSQUEDA"], ascending=[True, True, True])
render_inventory_table(detail)
