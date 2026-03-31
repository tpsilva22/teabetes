"""Shared data loading. All pages import from here — CSV is cached once."""
import pandas as pd
import streamlit as st

DATA_PATH = "../data/diabetes_dataset_new_variables.csv"

STAGE_ORDER  = ["No Diabetes", "Pre-Diabetes", "Type 2", "Type 1", "Gestational"]
STAGE_COLORS = {
    "No Diabetes":  "#4e9a6f",
    "Pre-Diabetes": "#b8860b",
    "Type 2":       "#8b3a3a",
    "Type 1":       "#6b3fa0",
    "Gestational":  "#2e6b8a",
}

AGE_ORDER    = ["Young Adult", "Adult", "Senior Adult", "Elderly"]
WEIGHT_ORDER = ["Underweight", "Normal", "Overweight", "Obese"]

@st.cache_data(show_spinner="Loading data...")
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["sedentary_ratio"] = df["screen_time_hours_per_day"] / (
        df["physical_activity_minutes_per_week"] / 60 + 0.1
    )
    df["lifestyle_score"] = (
        df["diet_score"] * 0.35
        + (df["physical_activity_minutes_per_week"].clip(0, 300) / 30) * 0.30
        + (10 - (df["sedentary_ratio"].clip(0, 20) / 2)) * 0.20
        + ((df["sleep_hours_per_day"] - 4).clip(0, 5) / 0.5) * 0.15
    ).clip(0, 10).round(2)
    return df

def fmt_pct(v, d=1): return f"{v:.{d}f}%"
def fmt_num(v, d=1): return f"{v:.{d}f}"