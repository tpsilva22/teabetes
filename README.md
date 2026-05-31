# Healthcare Analytics & ML for Diabetes Risk Assessment

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?logo=scikit-learn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-Machine%20Learning-green)
![Status](https://img.shields.io/badge/Status-Completed-success)

**TeaBetes** is an advanced, data-driven Healthcare Analytics platform designed to support early diagnosis and continuous risk assessment of Diabetes. Developed on a dataset of 100,000 patient profiles, the project integrates a complete Machine Learning pipeline (from EDA and Feature Engineering to the production deployment of Ensemble models) through an interactive web application built with Streamlit.

---

## Main Features (Dashboards)

The application's architecture was designed with a separation of concerns to serve two distinct audiences:

* **Clinical Area (Doctor Dashboard):** A pure Business Intelligence environment focused on population analysis. It allows filtering cohorts, exploring latent clusters (K-Means), monitoring metabolic KPIs, and analyzing clinical correlations between variables such as Insulin Resistance, Mean Arterial Pressure (MAP), and Cardiovascular Risk.
* **Health Explorer (Patient Dashboard):** An interactive real-time simulator for Machine Learning inference. The patient inputs their clinical and lifestyle data, and the artificial intelligence instantly calculates the binary diagnosis and continuous risk score.

---

## Artificial Intelligence Architecture (Two Brains)

To reflect the complexity of human physiology, real-time inference is powered by two independent AI pipelines:

1. **The Diagnostic Engine (Bagging Logistic Regression):**
   * **Objective:** Binary classification (Positive/Negative Diagnosis).
   * **Why?** In healthcare screening, minimizing False Negatives is critical. Our classifier prioritizes the Recall metric, ensuring high sensitivity in detecting dangerous clinical thresholds.

2. **The Continuous Risk Reconstructor (Stacking Regressor):**
   * **Objective:** Diabetes Risk Estimation (Score 0-100).
   * **Composition:** A powerful meta-model combining XGBoost, Random Forest, AdaBoost, Gradient Boosting, and Linear Regression through a RidgeCV algorithm. 
   * **Why?** It holistically evaluates metabolic and cardiovascular degradation. It allows, for example, classifying a young type 1 athlete as "Diagnosed", but assigning them a very low continuous risk due to their protective lifestyle.

> **Dynamic Deployment:** Our backend (ml_utils.py) captures single-patient inputs, dynamically injects One-Hot Encoding, and automatically pads missing categorical features with zeros to perfectly align with the mathematical dimensionality (53 variables) trained in the algorithms, while also applying the original scalers (MinMaxScaler/StandardScaler).

---

## Applied Scientific Methodology

* **Feature Engineering:** Creation of complex clinical indicators such as LDL/HDL Ratio, Pulse Pressure, and a multivariable Obesity Index.
* **Dimensionality Reduction (PCA / SVD):** Analysis of the impact of compressing 53 variables into 27 components. It was empirically proven that PCA accelerates linear optimizations (e.g., Ridge, Logistic Regression), but severely degrades the performance of tree-based ensembles (Random Forest/XGBoost), which rely on the original clinical thresholds.
* **Clustering:** Application of unsupervised learning algorithms, confirming 4 latent metabolic subgroups validated via the Elbow Method and Ward linkage dendrograms.

---

## Installation and Execution (How to Run Locally)

We guarantee the project is Plug & Play through robust relative paths (pathlib). 

**Prerequisites:** Python 3.9+ installed.

1. **Clone the Repository**

    git clone https://github.com/o-teu-user/teabetes.git
    cd teabetes

2. **Install Dependencies**

    pip install -r requirements.txt

3. **Run the Application**

    streamlit run app.py

*(Streamlit will automatically open the application in your browser at http://localhost:8501)*

---

*Disclaimer: This is a project for methodological research purposes in Data Science. The prediction dashboard provides approximations based on Machine Learning and does not substitute professional medical advice or diagnosis in any way.*
