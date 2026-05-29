import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path

# Define the path to the WinnerModel folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

MODEL_DIR_CLA = PROJECT_ROOT / "models" / "WinnerModel" / "Classification"
MODEL_DIR_REG = PROJECT_ROOT / "models" / "WinnerModel" / "Regression"

@st.cache_resource(show_spinner="Processing the AI engine...") # Cache the loaded models to avoid reloading on every interaction
def load_ml_components():
    #Load the models and scalers only once into memory (cache)
    try:
        clf_model = joblib.load(MODEL_DIR_CLA / "best_model_classification.pkl")
        clf_scaler = joblib.load(MODEL_DIR_CLA / "scaler_classification.pkl")
        
        reg_model = joblib.load(MODEL_DIR_REG / "best_model_regression.pkl")
        reg_scaler = joblib.load(MODEL_DIR_REG / "scaler_regression.pkl")
        
        # Store the model's original columns to preserve the exact One-Hot Encoding order
        expected_cols_clf = clf_model.feature_names_in_
        expected_cols_reg = reg_model.feature_names_in_
        
        return clf_model, clf_scaler, reg_model, reg_scaler, expected_cols_clf, expected_cols_reg
    except Exception as e:
        st.error(f"Error loading ML components: {e}")
        return None, None, None, None, None, None

def prepare_input_data(user_inputs, expected_columns, scaler):
    """
    Transform the data entered in Streamlit into the exact mathematical format
    required by the models (One-Hot Encoding + Scaling).
    """
    # Convert the input dictionary into a one-row DataFrame
    df_input = pd.DataFrame([user_inputs])
    
    # Define which categorical columns need OHE
    categorical_cols = [
        'gender', 'ethnicity', 'smoking_status', 'education_level',
        'employment_status', 'age_groups', 'weight_status', 'income_level'
    ]
    
    # Keep only the categorical columns that were actually provided in the input
    cat_cols_present = [col for col in categorical_cols if col in df_input.columns]
    
    # Apply One-Hot Encoding
    df_encoded = pd.get_dummies(df_input, columns=cat_cols_present, drop_first=True)
    
    # Align with the columns expected by the model (fill missing ones with 0)
    # This is CRITICAL because the user provides only one row, so not all dummy columns are generated.
    df_aligned = pd.DataFrame(columns=expected_columns)
    for col in expected_columns:
        if col in df_encoded.columns:
            df_aligned[col] = df_encoded[col]
        else:
            df_aligned[col] = 0 # Fill missing categories with 0
            
    # Ensure the data types are correct (float)
    df_aligned = df_aligned.astype(float)
    
    # THE FIX: Apply the scaler ONLY to the columns it was originally fitted on!
    if scaler is not None:
        scaler_cols = scaler.feature_names_in_
        df_aligned[scaler_cols] = scaler.transform(df_aligned[scaler_cols])
        
    return df_aligned

def run_predictions(user_inputs):
    """Run classification and regression for a new patient."""
    clf_model, clf_scaler, reg_model, reg_scaler, expected_cols_clf, expected_cols_reg = load_ml_components()
    
    if clf_model is None:
        return None, None
        
    # Classification prediction (diagnosis)
    X_clf = prepare_input_data(user_inputs, expected_cols_clf, clf_scaler)
    diagnosis_pred = clf_model.predict(X_clf)[0] # Returns 0 or 1
    
    # Regression prediction (risk score)
    X_reg = prepare_input_data(user_inputs, expected_cols_reg, reg_scaler)
    risk_score_pred = reg_model.predict(X_reg)[0] # Returns a float (0-100)
    
    return diagnosis_pred, risk_score_pred