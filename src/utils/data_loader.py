import pandas as pd
import streamlit as st
import os

def get_data_path(filename):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path1 = os.path.join(base_dir, "data", "processed", filename)
    path2 = os.path.join("data", "processed", filename)
    path3 = os.path.abspath(path2)
    for p in [path1, path2, path3]:
        if os.path.exists(p):
            return p
    return None

def get_all_csvs():
    """Return a dict of {filename: DataFrame} for all CSVs in data/processed/."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    processed_dir = os.path.join(base_dir, "data", "processed")
    if not os.path.exists(processed_dir):
        processed_dir = os.path.join("data", "processed")
    result = {}
    if os.path.exists(processed_dir):
        for f in sorted(os.listdir(processed_dir)):
            if f.endswith('.csv'):
                result[f] = os.path.join(processed_dir, f)
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
