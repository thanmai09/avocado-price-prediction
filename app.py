import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Avocado Explorer", layout="wide", page_icon="🥑")


@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv("avocado.csv")

    # normalize column names to help with common dataset variations
    df.columns = [c.strip() for c in df.columns]

    # attempt to parse date column
    date_col = None
    for c in df.columns:
        if c.lower() == "date":
            date_col = c
            break
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df


def find_col(df, name):
    for c in df.columns:
        if c.lower() == name.lower():
            return c
    return None


def main():
    st.title("Avocado Explorer 🥑")
    st.markdown("Explore avocado prices and volumes with interactive filters and charts.")

    with st.sidebar:
        st.header("Data / Filters")
        uploaded = st.file_uploader("Upload CSV file (optional)", type=["csv"])
        st.write("Or use the included avocado.csv in the workspace.")

    df = load_data(uploaded)
    if df is None or df.shape[0] == 0:
        st.error("No data loaded. Upload a CSV or ensure avocado.csv exists.")
        return

    date_col = find_col(df, "Date")
    type_col = find_col(df, "type")
    region_col = find_col(df, "region")
    avg_price_col = find_col(df, "AveragePrice") or find_col(df, "averageprice")
    total_vol_col = find_col(df, "Total Volume") or find_col(df, "total volume")

    # Sidebar filters
    with st.sidebar:
        if region_col:
            regions = sorted(df[region_col].dropna().unique())
            sel_regions = st.multiselect("Region", regions, default=regions[:3])
        else:
            sel_regions = None

        if type_col:
            types = sorted(df[type_col].dropna().unique())
            sel_type = st.selectbox("Type", ["All"] + types)
        else:
            sel_type = "All"

        if date_col:
            min_date = df[date_col].min()
            max_date = df[date_col].max()
            dr = st.date_input("Date range", value=(min_date, max_date))
        else:
            dr = None

    # Apply filters
    filt = pd.Series([True] * len(df))
    if sel_regions and region_col:
        filt = filt & df[region_col].isin(sel_regions)
    if sel_type and type_col and sel_type != "All":
        filt = filt & (df[type_col] == sel_type)
    if dr and date_col:
        start, end = dr
        try:
            start = pd.to_datetime(start)
            end = pd.to_datetime(end)
            filt = filt & (df[date_col] >= start) & (df[date_col] <= end)
        except Exception:
            pass

    filtered = df[filt].copy()

    # KPIs
    col1, col2, col3 = st.columns(3)
    if avg_price_col in filtered.columns:
        with col1:
            st.metric("Avg. Price", f"${filtered[avg_price_col].mean():.2f}")
    else:
        with col1:
            st.metric("Avg. Price", "N/A")

    if total_vol_col in filtered.columns:
        with col2:
            st.metric("Total Volume", f"{filtered[total_vol_col].sum():,.0f}")
    else:
        with col2:
            st.metric("Total Volume", "N/A")

    if date_col in filtered.columns:
        with col3:
            st.metric("Rows", f"{len(filtered):,}")
    else:
        with col3:
            st.metric("Rows", f"{len(filtered):,}")

    # Charts
    st.subheader("Trends")
    if date_col and avg_price_col:
        ts = filtered.dropna(subset=[date_col, avg_price_col])
        if not ts.empty:
            agg = ts.groupby(date_col)[avg_price_col].mean().reset_index()
            fig = px.line(agg, x=date_col, y=avg_price_col, title="Average Price Over Time")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Date or AveragePrice column not found for time series chart.")

    st.subheader("Volume by Region")
    if region_col and total_vol_col:
        vol = filtered.groupby(region_col)[total_vol_col].sum().reset_index().sort_values(total_vol_col, ascending=False)
        fig2 = px.bar(vol.head(20), x=total_vol_col, y=region_col, orientation="h", title="Total Volume by Region")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Region or Total Volume column not found for volume chart.")

    # Data table and download
    st.subheader("Filtered Data")
    st.dataframe(filtered)

    csv_bytes = to_csv_bytes(filtered)
    st.download_button("Download filtered data", csv_bytes, file_name="avocado_filtered.csv", mime="text/csv")


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


if __name__ == "__main__":
    main()