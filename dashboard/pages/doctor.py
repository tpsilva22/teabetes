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

# ── Soft clinical palette ─────────────────────────────────────────────────────
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
    hoverlabel=dict(bgcolor="rgba(20,20,30,0.92)", font_size=12,
                    font_family="Inter, sans-serif"),
)


# ── Styles ────────────────────────────────────────────────────────────────────
def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Lora:wght@500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebarNav"] { display: none; }

    .doc-title  { font-family:'Lora',serif; font-size:1.55rem; color:#7cb9e8; }
    .doc-sub    { font-size:.82rem; opacity:.45; margin-bottom:20px; margin-top:2px; }
    .role-badge { background:#1a5f8a; color:white; font-size:.65rem; padding:2px 9px;
                  border-radius:20px; font-weight:600; letter-spacing:.05em;
                  margin-left:10px; vertical-align:middle; }

    .kpi         { background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.1);
                   border-radius:12px; padding:18px 20px; }
    .kpi-label   { font-size:.7rem; text-transform:uppercase; letter-spacing:.07em;
                   opacity:.45; margin-bottom:4px; }
    .kpi-value   { font-size:1.75rem; font-weight:600; color:#7cb9e8; line-height:1.1; }
    .kpi-sub     { font-size:.72rem; opacity:.38; margin-top:3px; }
    .kpi-alert   { color:#e8a87c; }

    .sec-title   { font-family:'Lora',serif; font-size:1.05rem; opacity:.75;
                   margin:28px 0 12px; border-bottom:1px solid rgba(255,255,255,.08);
                   padding-bottom:6px; }

    .clinical-note { background:rgba(58,122,191,.1); border-left:3px solid #3a7abf;
                     border-radius:0 8px 8px 0; padding:10px 14px; font-size:.82rem;
                     opacity:.8; line-height:1.6; margin-top:8px; }

    /* Sidebar */
    [data-testid="stSidebar"] > div:first-child { padding-top:1rem; }
    .sidebar-sec { font-size:.68rem; text-transform:uppercase; letter-spacing:.08em;
                   opacity:.38; margin:16px 0 5px; }
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


# ── Charts ────────────────────────────────────────────────────────────────────

def chart_stage_pie(df):
    counts = (df["diabetes_stage"]
              .value_counts()
              .reindex([s for s in STAGE_ORDER if s in df["diabetes_stage"].unique()])
              .dropna())
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values,
        hole=0.56,
        marker=dict(
            colors=[STAGE_COLORS[s] for s in counts.index],
            line=dict(color="rgba(0,0,0,0.4)", width=2),
        ),
        textinfo="label+percent",
        textfont=dict(size=10),
        hovertemplate="<b>%{label}</b><br>%{value:,} pacientes — %{percent}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Distribuicao de Estadios", font=dict(size=12)),
        showlegend=False, height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_metabolic_scatter(df, sample=3000):
    s = df.sample(min(sample, len(df)), random_state=42)
    fig = px.scatter(
        s, x="insulin_resistance", y="hba1c",
        color="diabetes_stage",
        color_discrete_map=STAGE_COLORS,
        category_orders={"diabetes_stage": STAGE_ORDER},
        opacity=0.55,
        labels={"insulin_resistance": "Resistência à Insulina (HOMA-IR)",
                "hba1c": "HbA1c (%)", "diabetes_stage": "Estádio"},
        hover_data=["age", "bmi", "glucose_fasting"],
        title="Matriz de Risco Metabólico",
    )
    # Reference lines
    fig.add_vline(x=2.5, line_dash="dot", line_color="rgba(255,255,255,0.25)",
                  annotation_text="Limiar HOMA-IR 2,5", annotation_font_size=9,
                  annotation_font_color="rgba(255,255,255,0.45)")
    fig.add_hline(y=6.5, line_dash="dot", line_color="rgba(255,255,255,0.25)",
                  annotation_text="Limiar HbA1c 6,5%", annotation_font_size=9,
                  annotation_font_color="rgba(255,255,255,0.45)")
    fig.update_layout(height=360, legend_title_text="",
                      margin=dict(l=50, r=10, t=44, b=40), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, use_container_width=True)


def chart_comorbidities_heatmap(df):
    agg = (df.groupby("age_groups", observed=True)[["systolic_bp", "pulse_pressure", "map"]]
           .mean()
           .reindex(AGE_ORDER)
           .dropna())
    fig = go.Figure(go.Heatmap(
        z=agg.values,
        x=["Pressão Sistólica", "Pressão de Pulso", "Pressão Arterial Média"],
        y=agg.index.tolist(),
        colorscale="Blues",
        text=agg.round(1).values,
        texttemplate="%{text}",
        textfont=dict(size=11),
        hovertemplate="%{y} — %{x}<br><b>%{z:.1f} mmHg</b><extra></extra>",
        showscale=True,
    ))
    fig.update_layout(
        title="Perfil de Pressão Arterial por Grupo Etário (mmHg)",
        height=280, margin=dict(l=10, r=10, t=44, b=10),
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_family_history_boxplot(df):
    fig = px.box(
        df, x="family_history_diabetes", y="diabetes_risk_score",
        color="family_history_diabetes",
        color_discrete_sequence=[C_TEAL, C_ROSE],
        labels={"family_history_diabetes": "Histórico Familiar",
                "diabetes_risk_score": "Score de Risco"},
        category_orders={"family_history_diabetes": [0, 1]},
        title="Impacto do Histórico Familiar no Score de Risco",
    )
    fig.update_xaxes(ticktext=["Sem histórico", "Com histórico"], tickvals=[0, 1])
    fig.update_layout(height=300, showlegend=False,
                      margin=dict(l=50, r=10, t=44, b=40), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_risk_by_diagnosis(df):
    fig = px.violin(
        df, x="diagnosed_diabetes", y="diabetes_risk_score",
        color="diagnosed_diabetes",
        color_discrete_sequence=[C_SAGE, C_ROSE],
        box=True, points=False,
        labels={"diagnosed_diabetes": "Diagnosticado",
                "diabetes_risk_score": "Score de Risco"},
        title="Score de Risco: Diagnosticados vs Não Diagnosticados",
    )
    fig.update_xaxes(ticktext=["Não Diagnosticado", "Diagnosticado"], tickvals=[0, 1])
    fig.update_layout(height=300, showlegend=False,
                      margin=dict(l=50, r=10, t=44, b=40), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_hba1c_by_stage(df):
    avg = (df.groupby("diabetes_stage")["hba1c"].mean()
           .reindex(STAGE_ORDER).dropna().reset_index())
    avg.columns = ["estadio", "hba1c"]
    fig = px.bar(
        avg, x="estadio", y="hba1c",
        color="estadio", color_discrete_map=STAGE_COLORS,
        text=avg["hba1c"].round(2),
        labels={"estadio": "", "hba1c": "HbA1c médio (%)"},
        title="HbA1c Médio por Estádio",
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.add_hline(y=6.5, line_dash="dot", line_color="rgba(255,255,255,0.3)",
                  annotation_text="Limiar diagnóstico 6,5%", annotation_font_size=9)
    fig.update_layout(height=300, showlegend=False,
                      margin=dict(l=50, r=10, t=44, b=40), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_corr_heatmap(df):
    cols = ["insulin_resistance", "hba1c", "glucose_fasting", "glucose_postprandial",
            "bmi", "obesity_index", "pulse_pressure", "map",
            "cholesterol_total", "ratio_ldl_hdl", "diabetes_risk_score"]
    corr = df[cols].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    z    = corr.where(~mask)
    fig  = go.Figure(go.Heatmap(
        z=z.values, x=z.columns, y=z.index,
        colorscale="RdBu_r", zmid=0, zmin=-1, zmax=1,
        text=z.round(2).values, texttemplate="%{text}",
        textfont=dict(size=8),
        hovertemplate="%{y} vs %{x}<br>r = %{z:.3f}<extra></extra>",
        showscale=True,
    ))
    fig.update_layout(
        title="Correlações entre Variáveis Metabólicas",
        height=440, margin=dict(l=130, r=10, t=44, b=120),
        **PLOTLY_LAYOUT,
    )
    fig.update_xaxes(tickangle=-40, tickfont=dict(size=9))
    fig.update_yaxes(tickfont=dict(size=9))
    st.plotly_chart(fig, use_container_width=True)


def chart_variable_explorer(df, x_var, y_var, color_var, sample_n):
    s = df.sample(min(sample_n, len(df)), random_state=42)
    color_map = STAGE_COLORS if color_var == "diabetes_stage" else None
    fig = px.scatter(
        s, x=x_var, y=y_var, color=color_var,
        color_discrete_map=color_map,
        opacity=0.55,
        trendline="lowess", trendline_scope="overall",
        trendline_color_override="rgba(255,255,255,0.6)",
        labels={"diabetes_stage": "Estádio", "diagnosed_diabetes": "Diagnosticado",
                "age_groups": "Grupo Etário", "weight_status": "Estado de Peso"},
        title=f"{x_var}  vs  {y_var}",
    )
    fig.update_layout(height=400, legend_title_text="",
                      margin=dict(l=50, r=10, t=44, b=40), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, use_container_width=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def show(logout_fn):
    inject_styles()
    df_full = load_data()

    # Sidebar
    with st.sidebar:
        st.markdown("### Filtros")
        st.markdown('<div class="sidebar-sec">Populacao</div>', unsafe_allow_html=True)
        stages = st.multiselect("Estádio", STAGE_ORDER, default=STAGE_ORDER)
        age_groups = st.multiselect("Grupo Etário",
                                    options=["Young Adult","Adult","Senior Adult","Elderly"],
                                    default=["Young Adult","Adult","Senior Adult","Elderly"])
        st.markdown('<div class="sidebar-sec">Clinico</div>', unsafe_allow_html=True)
        age_range = st.slider("Idade", int(df_full.age.min()), int(df_full.age.max()),
                              (int(df_full.age.min()), int(df_full.age.max())))
        bmi_range = st.slider("BMI", float(df_full.bmi.min()), float(df_full.bmi.max()),
                              (float(df_full.bmi.min()), float(df_full.bmi.max())), step=0.5)
        genders = st.multiselect("Género", sorted(df_full.gender.unique()),
                                 default=sorted(df_full.gender.unique()))
        st.markdown("---")
        if st.button("Logout", key="doc_logout"):
            logout_fn()

    df = df_full[
        df_full["diabetes_stage"].isin(stages) &
        df_full["age_groups"].isin(age_groups) &
        df_full["age"].between(*age_range) &
        df_full["bmi"].between(*bmi_range) &
        df_full["gender"].isin(genders)
    ]

    # Header
    col_title, col_btn = st.columns([7, 1])
    with col_title:
        st.markdown(
            '<div class="doc-title">🩺 TeaBetes <span class="role-badge">MÉDICO</span></div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="doc-sub">{st.session_state.name} &nbsp;·&nbsp; {len(df):,} pacientes na seleção atual</div>',
            unsafe_allow_html=True)
    with col_btn:
        if st.button("Logout →", key="doc_logout_top"):
            logout_fn()

    if df.empty:
        st.warning("Nenhum paciente corresponde aos filtros selecionados.")
        return

    # ── KPIs ──────────────────────────────────────────────────────────────────
    pct_ir      = (df["insulin_resistance"] > 2.5).mean() * 100
    avg_hba1c   = df["hba1c"].mean()
    avg_pp_50   = df[df["age"] > 50]["pulse_pressure"].mean()
    pct_diag    = df["diagnosed_diabetes"].mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Resistência à Insulina",
                 fmt_pct(pct_ir),
                 "pacientes com HOMA-IR > 2,5",
                 alert=pct_ir > 40)
    with c2: kpi("HbA1c Médio",
                 fmt_num(avg_hba1c) + "%",
                 "referência saudável < 5,7%",
                 alert=avg_hba1c > 6.5)
    with c3: kpi("Alerta Cardiovascular",
                 fmt_num(avg_pp_50) + " mmHg",
                 "pressão de pulso média em >50 anos",
                 alert=avg_pp_50 > 50)
    with c4: kpi("Diagnosticados",
                 fmt_pct(pct_diag),
                 "com diabetes diagnosticada")

    # ── Linha 1: Scatter metabolico + Pie estadios ────────────────────────────
    st.markdown('<div class="sec-title">Risco Metabolico</div>', unsafe_allow_html=True)
    r1a, r1b = st.columns([3, 2])
    with r1a:
        chart_metabolic_scatter(df)
        clinical_note(
            "A zona superior direita (HOMA-IR > 2.5 e HbA1c > 6.5%) representa "
            "a area critica de transicao onde a resistencia insulinica se torna "
            "clinicamente significativa. Pacientes nessa zona requerem monitorizacao intensiva."
        )
    with r1b:
        chart_stage_pie(df)
        chart_family_history_boxplot(df)

    # ── Linha 2: Comorbidades + diagnostico ──────────────────────────────────
    st.markdown('<div class="sec-title">Comorbidades & Diagnostico</div>', unsafe_allow_html=True)
    r2a, r2b = st.columns([3, 2])
    with r2a:
        chart_comorbidities_heatmap(df)
        clinical_note(
            "A rigidez arterial aumenta com a idade — a pressao de pulso elevada "
            "em adultos mais velhos e um indicador independente de risco metabolico "
            "e cardiovascular."
        )
    with r2b:
        chart_risk_by_diagnosis(df)

    # ── Linha 3: HbA1c + Correlacoes ─────────────────────────────────────────
    st.markdown('<div class="sec-title">Analise Clinica Detalhada</div>', unsafe_allow_html=True)
    chart_hba1c_by_stage(df)
    chart_corr_heatmap(df)

    # ── Explorador interativo ─────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Explorador de Variaveis</div>', unsafe_allow_html=True)

    num_cols = ["age", "bmi", "hba1c", "glucose_fasting", "glucose_postprandial",
                "insulin_resistance", "glycemia_spike", "obesity_index",
                "pulse_pressure", "map", "ratio_ldl_hdl",
                "cholesterol_total", "hdl_cholesterol", "ldl_cholesterol",
                "systolic_bp", "diastolic_bp", "diabetes_risk_score",
                "physical_activity_minutes_per_week", "diet_score",
                "sleep_hours_per_day", "screen_time_hours_per_day"]
    cat_cols = ["diabetes_stage", "diagnosed_diabetes", "age_groups",
                "weight_status", "gender"]

    ec1, ec2, ec3, ec4 = st.columns([2, 2, 2, 1])
    with ec1:
        x_var = st.selectbox("Eixo X", num_cols,
                             index=num_cols.index("insulin_resistance"))
    with ec2:
        y_var = st.selectbox("Eixo Y", num_cols,
                             index=num_cols.index("hba1c"))
    with ec3:
        color_var = st.selectbox("Cor", cat_cols,
                                 index=cat_cols.index("diabetes_stage"))
    with ec4:
        sample_n = st.slider("Amostra", 500, min(8000, len(df)), 2000, step=500)

    chart_variable_explorer(df, x_var, y_var, color_var, sample_n)

    # Raw data
    with st.expander("Explorar dados brutos"):
        cols_show = st.multiselect("Colunas", list(df.columns), default=list(df.columns[:12]))
        st.dataframe(df[cols_show].head(1000), use_container_width=True, height=280)
        st.caption(f"{len(df):,} registos filtrados — a mostrar até 1000.")
