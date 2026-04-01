"""
Doctor dashboard — Clinical Insights.
Soft, professional palette. Population-level analysis with interactive Plotly charts.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pages.data_utils import load_data, fmt_pct, fmt_num, STAGE_ORDER, STAGE_COLORS, AGE_ORDER

C_BLUE    = "#3a7abf"
C_TEAL    = "#2e8b8b"
C_SAGE    = "#5a8a6a"
C_AMBER   = "#b8860b"
C_ROSE    = "#a0536e"
C_MUTED   = "rgba(255,255,255,0.45)"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="rgba(255,255,255,0.85)", size=11),
    hoverlabel=dict(bgcolor="rgba(20,20,30,0.92)", font_size=12, font_family="Inter, sans-serif"),
)

def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Lora:wght@500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebarNav"] { display: none; }
    .doc-title  { font-family:'Lora',serif; font-size:1.55rem; color:#7cb9e8; }
    .doc-sub    { font-size:.82rem; opacity:.45; margin-bottom:20px; margin-top:2px; }
    .role-badge { background:#1a5f8a; color:white; font-size:.65rem; padding:2px 9px;
                  border-radius:20px; font-weight:600; letter-spacing:.05em; margin-left:10px; vertical-align:middle; }
    .kpi         { background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.1); border-radius:12px; padding:18px 20px; }
    .kpi-label   { font-size:.7rem; text-transform:uppercase; letter-spacing:.07em; opacity:.45; margin-bottom:4px; }
    .kpi-value   { font-size:1.75rem; font-weight:600; color:#7cb9e8; line-height:1.1; }
    .kpi-sub     { font-size:.72rem; opacity:.38; margin-top:3px; }
    .kpi-alert   { color:#e8a87c; }
    .sec-title   { font-family:'Lora',serif; font-size:1.05rem; opacity:.75; margin:28px 0 12px; border-bottom:1px solid rgba(255,255,255,.08); padding-bottom:6px; }
    .clinical-note { background:rgba(58,122,191,.1); border-left:3px solid #3a7abf; border-radius:0 8px 8px 0; padding:10px 14px; font-size:.82rem; opacity:.8; line-height:1.6; margin-top:8px; }
    [data-testid="stSidebar"] > div:first-child { padding-top:1rem; }
    .sidebar-sec { font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; opacity:.38; margin:16px 0 5px; }
    </style>
    """, unsafe_allow_html=True)

def kpi(label, value, sub="", alert=False):
    cls = "kpi-value kpi-alert" if alert else "kpi-value"
    st.markdown(f"""<div class="kpi">
        <div class="kpi-label">{label}</div>
        <div class="{cls}">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def clinical_note(text):
    st.markdown(f'<div class="clinical-note">{text}</div>', unsafe_allow_html=True)

def axis_style(fig, gridcolor="rgba(255,255,255,0.07)"):
    fig.update_xaxes(showgrid=False, linecolor="rgba(255,255,255,0.1)", linewidth=1)
    fig.update_yaxes(gridcolor=gridcolor, linecolor="rgba(255,255,255,0.1)", linewidth=1)
    return fig

def chart_stage_pie(df):
    counts = df["diabetes_stage"].value_counts().reindex([s for s in STAGE_ORDER if s in df["diabetes_stage"].unique()]).dropna()
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.56,
        marker=dict(colors=[STAGE_COLORS.get(s, C_BLUE) for s in counts.index], line=dict(color="rgba(0,0,0,0.4)", width=2)),
        textinfo="label+percent", textfont=dict(size=10),
        hovertemplate="<b>%{label}</b><br>%{value:,} patients — %{percent}<extra></extra>",
    ))
    fig.update_layout(title=dict(text="Stage Distribution", font=dict(size=12)), showlegend=False, height=300, margin=dict(l=10, r=10, t=40, b=10), **PLOTLY_LAYOUT)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_age_histogram(df):
    fig = px.histogram(
        df, x="age", nbins=20,
        color_discrete_sequence=[C_BLUE],
        labels={"age": "Age", "count": "Number of Patients"},
        title="Age Distribution for Selected Stage"
    )
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_metabolic_scatter(df, sample=3000):
    s = df.sample(min(sample, len(df)), random_state=42)
    fig = px.scatter(
        s, x="insulin_resistance", y="hba1c", color="diabetes_stage",
        color_discrete_map=STAGE_COLORS, category_orders={"diabetes_stage": STAGE_ORDER},
        opacity=0.55, labels={"insulin_resistance": "Insulin Resistance (HOMA-IR)", "hba1c": "HbA1c (%)", "diabetes_stage": "Stage"},
        hover_data=["age", "bmi", "glucose_fasting"], title="Metabolic Risk Matrix",
    )
    fig.add_vline(x=2.5, line_dash="dot", line_color="rgba(255,255,255,0.25)", annotation_text="HOMA-IR 2.5 Threshold", annotation_font_size=9, annotation_font_color="rgba(255,255,255,0.45)")
    fig.add_hline(y=6.5, line_dash="dot", line_color="rgba(255,255,255,0.25)", annotation_text="HbA1c 6.5% Threshold", annotation_font_size=9, annotation_font_color="rgba(255,255,255,0.45)")
    fig.update_layout(height=400, legend_title_text="", margin=dict(l=50, r=10, t=44, b=40), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, width="stretch")

def chart_comorbidities_heatmap(df):
    agg = df.groupby("age_groups", observed=True)[["systolic_bp", "pulse_pressure", "map"]].mean().reindex(AGE_ORDER).dropna()
    fig = go.Figure(go.Heatmap(
        z=agg.values, x=["Systolic BP", "Pulse Pressure", "Mean Arterial Pressure"], y=agg.index.tolist(),
        colorscale="Blues", text=agg.round(1).values, texttemplate="%{text}", textfont=dict(size=11),
        hovertemplate="%{y} — %{x}<br><b>%{z:.1f} mmHg</b><extra></extra>", showscale=True,
    ))
    fig.update_layout(title="Blood Pressure Profile by Age Group (mmHg)", height=280, margin=dict(l=10, r=10, t=44, b=10), **PLOTLY_LAYOUT)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_family_history_boxplot(df):
    fig = px.box(
        df, x="family_history_diabetes", y="diabetes_risk_score", color="family_history_diabetes",
        color_discrete_sequence=[C_TEAL, C_ROSE],
        labels={"family_history_diabetes": "Family History", "diabetes_risk_score": "Risk Score (0-100 Points)"},
        category_orders={"family_history_diabetes": [0, 1]}, title="Impact of Family History on Risk Score"
    )
    fig.update_xaxes(ticktext=["No History", "With History"], tickvals=[0, 1], title="")
    fig.update_layout(
        height=300, showlegend=True, 
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99, title_text="History"),
        margin=dict(l=50, r=10, t=44, b=40), **PLOTLY_LAYOUT
    )
    axis_style(fig)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_risk_by_diagnosis(df):
    fig = px.violin(
        df, x="diagnosed_diabetes", y="diabetes_risk_score", color="diagnosed_diabetes",
        color_discrete_sequence=[C_SAGE, C_ROSE], box=True, points=False,
        labels={"diagnosed_diabetes": "Diagnosis Status", "diabetes_risk_score": "Risk Score (0-100 Points)"},
        title="Risk Score: Diagnosed vs Undiagnosed"
    )
    fig.update_xaxes(ticktext=["Undiagnosed", "Diagnosed"], tickvals=[0, 1], title="")
    fig.update_layout(
        height=300, showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99, title_text="Diagnosis"),
        margin=dict(l=50, r=10, t=44, b=40), **PLOTLY_LAYOUT
    )
    axis_style(fig)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_hba1c_by_stage(df):
    avg = df.groupby("diabetes_stage")["hba1c"].mean().reindex(STAGE_ORDER).dropna().reset_index()
    avg.columns = ["stage", "hba1c"]
    fig = px.bar(
        avg, x="stage", y="hba1c", color="stage", color_discrete_map=STAGE_COLORS,
        text=avg["hba1c"].round(2), labels={"stage": "", "hba1c": "Average HbA1c (%)"}, title="Average HbA1c by Stage"
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.add_hline(y=6.5, line_dash="dot", line_color="rgba(255,255,255,0.3)", annotation_text="Diagnostic threshold 6.5%", annotation_font_size=9)
    fig.update_layout(height=300, showlegend=False, margin=dict(l=50, r=10, t=44, b=40), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_corr_heatmap(df, cols):
    if not cols or len(cols) < 2:
        st.info("Please select at least 2 variables to generate the correlation heatmap.")
        return
    corr = df[cols].corr()
    fig  = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index, colorscale="RdBu_r", zmid=0, zmin=-1, zmax=1,
        text=corr.round(2).values, texttemplate="%{text}", textfont=dict(size=8),
        hovertemplate="%{y} vs %{x}<br>r = %{z:.3f}<extra></extra>", showscale=True,
    ))
    fig.update_layout(title="Correlations Between Selected Variables", height=min(440 + len(cols)*10, 800), margin=dict(l=130, r=10, t=44, b=120), **PLOTLY_LAYOUT)
    fig.update_xaxes(tickangle=-40, tickfont=dict(size=9))
    fig.update_yaxes(tickfont=dict(size=9))
    st.plotly_chart(fig, width="stretch")

def chart_variable_explorer(df, x_var, y_var, color_var, sample_n, chart_type):
    s = df.sample(min(sample_n, len(df)), random_state=42)
    color_map = STAGE_COLORS if color_var == "diabetes_stage" else None
    labels_map = {"diabetes_stage": "Stage", "diagnosed_diabetes": "Diagnosed", "age_groups": "Age Group", "weight_status": "Weight Status"}
    if chart_type == "Scatter":
        fig = px.scatter(s, x=x_var, y=y_var, color=color_var, color_discrete_map=color_map, opacity=0.55, trendline="lowess", trendline_scope="overall", trendline_color_override="rgba(255,255,255,0.6)", labels=labels_map, title=f"{x_var} vs {y_var}")
    elif chart_type == "Box":
        fig = px.box(s, x=x_var, y=y_var, color=color_var, color_discrete_map=color_map, labels=labels_map, title=f"{y_var} Distribution by {x_var}")
    elif chart_type == "Violin":
        fig = px.violin(s, x=x_var, y=y_var, color=color_var, color_discrete_map=color_map, box=True, labels=labels_map, title=f"{y_var} Density by {x_var}")
    elif chart_type == "Bar":
        fig = px.bar(s, x=x_var, y=y_var, color=color_var, color_discrete_map=color_map, labels=labels_map, title=f"{y_var} by {x_var}")
    fig.update_layout(height=400, legend_title_text="", margin=dict(l=50, r=10, t=44, b=40), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, width="stretch")

def show(logout_fn):
    inject_styles()
    df_full = load_data()

    with st.sidebar:
        st.markdown("### Filters")
        st.markdown('<div class="sidebar-sec">Population</div>', unsafe_allow_html=True)
        stages = st.multiselect("Stage", STAGE_ORDER, default=["No Diabetes"])
        
        st.markdown('<div class="sidebar-sec">Clinical</div>', unsafe_allow_html=True)
        age_range = st.slider("Age", int(df_full.age.min()), int(df_full.age.max()), (int(df_full.age.min()), int(df_full.age.max())))
        bmi_range = st.slider("BMI", float(df_full.bmi.min()), float(df_full.bmi.max()), (float(df_full.bmi.min()), float(df_full.bmi.max())), step=0.5)
        sbp_range = st.slider("Systolic BP", int(df_full.systolic_bp.min()), int(df_full.systolic_bp.max()), (int(df_full.systolic_bp.min()), int(df_full.systolic_bp.max())))
        chol_range = st.slider("Total Cholesterol", int(df_full.cholesterol_total.min()), int(df_full.cholesterol_total.max()), (int(df_full.cholesterol_total.min()), int(df_full.cholesterol_total.max())))
        
        genders = st.multiselect("Gender", sorted(df_full.gender.unique()), default=sorted(df_full.gender.unique()))
        st.markdown("---")
        if st.button("Logout", key="doc_logout"):
            logout_fn()

    df = df_full[
        df_full["diabetes_stage"].isin(stages) &
        df_full["age"].between(*age_range) &
        df_full["bmi"].between(*bmi_range) &
        df_full["systolic_bp"].between(*sbp_range) &
        df_full["cholesterol_total"].between(*chol_range) &
        df_full["gender"].isin(genders)
    ]

    col_title, col_btn = st.columns([7, 1])
    with col_title:
        st.markdown('<div class="doc-title">🩺 TeaBetes <span class="role-badge">DOCTOR</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="doc-sub">{st.session_state.name} &nbsp;·&nbsp; {len(df):,} patients in current selection</div>', unsafe_allow_html=True)
    with col_btn:
        if st.button("Logout →", key="doc_logout_top"):
            logout_fn()

    if df.empty:
        st.warning("No patients match the selected filters.")
        return

    pct_ir    = (df["insulin_resistance"] > 2.5).mean() * 100
    avg_hba1c = df["hba1c"].mean()
    avg_pp    = df["pulse_pressure"].mean() if not df.empty else 0
    pct_diag  = df["diagnosed_diabetes"].mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Insulin Resistance", fmt_pct(pct_ir), "patients with HOMA-IR > 2.5", alert=pct_ir > 40)
    with c2: kpi("Average HbA1c", fmt_num(avg_hba1c) + "%", "healthy reference < 5.7%", alert=avg_hba1c > 6.5)
    with c3: kpi("Cardiovascular Alert", fmt_num(avg_pp) + " mmHg", "mean pulse pressure in selection", alert=avg_pp > 50)
    with c4: kpi("Diagnosed", fmt_pct(pct_diag), "with diagnosed diabetes")

    st.markdown('<div class="sec-title">Metabolic Risk</div>', unsafe_allow_html=True)
    chart_metabolic_scatter(df)
    clinical_note("The upper right zone (HOMA-IR > 2.5 and HbA1c > 6.5%) represents the critical transition area where insulin resistance becomes clinically significant. Patients in this zone require intensive monitoring.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    r1a, r1b = st.columns(2)
    with r1a:
        if len(df["diabetes_stage"].unique()) > 1:
            chart_stage_pie(df)
        else:
            chart_age_histogram(df)
    with r1b:
        chart_family_history_boxplot(df)

    st.markdown('<div class="sec-title">Comorbidities & Diagnosis</div>', unsafe_allow_html=True)
    r2a, r2b = st.columns([3, 2])
    with r2a:
        chart_comorbidities_heatmap(df)
        clinical_note("Arterial stiffness increases with age — elevated pulse pressure in older adults is an independent indicator of metabolic and cardiovascular risk.")
    with r2b:
        chart_risk_by_diagnosis(df)

    st.markdown('<div class="sec-title">Detailed Clinical Analysis</div>', unsafe_allow_html=True)
    chart_hba1c_by_stage(df)
    
    st.markdown("#### Correlation Heatmap")
    all_num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    default_corr_cols = ["insulin_resistance", "hba1c", "glucose_fasting", "glucose_postprandial", "bmi", "obesity_index", "pulse_pressure", "map", "cholesterol_total", "ratio_ldl_hdl", "diabetes_risk_score"]
    selected_corr_cols = st.multiselect("Select Variables for Correlation Matrix", all_num_cols, default=default_corr_cols)
    chart_corr_heatmap(df, selected_corr_cols)

    st.markdown('<div class="sec-title">Variable Explorer</div>', unsafe_allow_html=True)
    cat_cols = ["diabetes_stage", "diagnosed_diabetes", "age_groups", "weight_status", "gender"]
    ec1, ec2, ec3, ec4, ec5 = st.columns([2, 2, 2, 2, 2])
    with ec1: x_var = st.selectbox("X-Axis", all_num_cols, index=all_num_cols.index("insulin_resistance") if "insulin_resistance" in all_num_cols else 0)
    with ec2: y_var = st.selectbox("Y-Axis", all_num_cols, index=all_num_cols.index("hba1c") if "hba1c" in all_num_cols else 0)
    with ec3: color_var = st.selectbox("Colour", cat_cols, index=cat_cols.index("diabetes_stage"))
    with ec4: chart_type = st.selectbox("Chart Type", ["Scatter", "Box", "Violin", "Bar"])
    with ec5: sample_n = st.slider("Patient Sample Size", 500, min(8000, len(df)), 2000, step=500, help="Limiting sample size improves rendering performance and prevents visual clutter.")
    
    chart_variable_explorer(df, x_var, y_var, color_var, sample_n, chart_type)

    with st.expander("Explore Raw Data"):
        cols_show = st.multiselect("Columns", list(df.columns), default=list(df.columns))
        st.dataframe(df[cols_show].head(1000), width="stretch", height=280)
        st.caption(f"{len(df):,} filtered records — showing up to 1000.")