import pandas as pd
import streamlit as st
import os

def get_data_path(filename):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path1 = os.path.join(base_dir, "data", "final", filename)
    path2 = os.path.join("data", "final", filename)
    path3 = os.path.abspath(path2)
    for p in [path1, path2, path3]:
        if os.path.exists(p):
            return p
    return None

def get_all_csvs():
    """Return a dict of {filename: DataFrame} for all CSVs in data/final/."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    final_dir = os.path.join(base_dir, "data", "final")
    if not os.path.exists(final_dir):
        final_dir = os.path.join("data", "final")
    result = {}
    if os.path.exists(final_dir):
        for f in sorted(os.listdir(final_dir)):
            if f.endswith('.csv') and not f.endswith('_raw.csv'):
                result[f] = os.path.join(final_dir, f)
    return result

@st.cache_data
def load_csv(filename):
    path = get_data_path(filename)
    if not path:
        return pd.DataFrame()
    return pd.read_csv(path)

def format_number(num):
    if pd.isna(num) or num == "-":
        return "-"
    try:
        return f"{int(float(num)):,}".replace(",", ".")
    except:
        return str(num)
