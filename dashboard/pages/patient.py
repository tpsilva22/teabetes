"""
Patient explorer — Personal Health Coach.
Warm, vibrant palette. Sidebar inputs, live interactive charts.
No login required.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pages.data_utils import load_data, AGE_ORDER

# ── Warm, vibrant palette ─────────────────────────────────────────────────────
C_GREEN  = "#27ae60"
C_YELLOW = "#f39c12"
C_RED    = "#e74c3c"
C_ORANGE = "#e67e22"
C_BLUE   = "#2980b9"
C_WARM   = "#e8a87c"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="rgba(255,255,255,0.9)", size=11),
    hoverlabel=dict(bgcolor="rgba(20,20,30,0.92)", font_size=12,
                    font_family="Inter, sans-serif"),
)


def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Lora:wght@500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] > div:first-child { padding-top:1rem; }
    [data-testid="stSidebarNav"] { display: none; }

    .pat-title  { font-family:'Lora',serif; font-size:1.55rem; color:#f0a868; }
    .pat-sub    { font-size:.82rem; opacity:.45; margin-bottom:20px; margin-top:2px; }

    .status-card { border-radius:14px; padding:22px 26px; color:#fff; }
    .status-lbl  { font-size:.7rem; text-transform:uppercase; letter-spacing:.08em; opacity:.8; }
    .status-val  { font-family:'Lora',serif; font-size:2.1rem; line-height:1.15; }
    .status-desc { font-size:.84rem; opacity:.88; margin-top:6px; line-height:1.55; }

    .mpill     { background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.12);
                 border-radius:11px; padding:14px 12px; text-align:center; }
    .mpill-lbl { font-size:.68rem; text-transform:uppercase; letter-spacing:.05em;
                 opacity:.45; margin-bottom:3px; }
    .mpill-val { font-size:1.3rem; font-weight:600; color:#f0a868; }
    .mpill-ref { font-size:.66rem; opacity:.32; margin-top:2px; }

    .tip  { background:rgba(240,168,104,.08); border-left:3px solid #f0a868;
            border-radius:0 10px 10px 0; padding:11px 15px; margin-bottom:8px;
            font-size:.84rem; line-height:1.6; }
    .tip-good { background:rgba(39,174,96,.08); border-left:3px solid #27ae60; }

    .sec-title { font-family:'Lora',serif; font-size:1.05rem; color:#f0a868;
                 opacity:.9; margin:24px 0 10px;
                 border-bottom:1px solid rgba(240,168,104,.2); padding-bottom:5px; }

    .sidebar-sec { font-size:.68rem; text-transform:uppercase; letter-spacing:.08em;
                   opacity:.38; margin:16px 0 5px; }

    .wstatus-badge { display:inline-block; padding:3px 12px; border-radius:20px;
                     font-size:.78rem; font-weight:600; }
    </style>
    """, unsafe_allow_html=True)


# ── Logic ─────────────────────────────────────────────────────────────────────
def estimate_risk(age, bmi, hba1c, glucose, sbp, family, hypert, smoking, activity, diet):
    s  = min(age / 10, 7)
    s += max(0, (bmi - 18.5) * 0.8)
    s += max(0, (hba1c - 5.0) * 8)
    s += max(0, (glucose - 90) * 0.15)
    s += max(0, (sbp - 110) * 0.1)
    s += 8 if family else 0
    s += 5 if hypert else 0
    s += {"Never": 0, "Former": 3, "Current": 7}.get(smoking, 0)
    s -= min(activity / 30, 5)
    s -= min(diet * 0.4, 4)
    return round(min(max(s, 0), 100), 1)

def classify(hba1c, glucose):
    if hba1c >= 6.5 or glucose >= 126: return "Diabetes",     C_RED,    3
    if hba1c >= 5.7 or glucose >= 100: return "Pre-Diabetes", C_YELLOW, 2
    return "Sem Diabetes", C_GREEN, 1

def weight_status(bmi):
    if bmi < 18.5: return "Abaixo do Peso", "#5b9bd5"
    if bmi < 25.0: return "Peso Normal",    C_GREEN
    if bmi < 30.0: return "Excesso de Peso", C_YELLOW
    return "Obesidade", C_RED

def lifestyle_score(diet, activity, sleep, alcohol, smoking):
    act_s  = min(activity / 30, 10)
    slp_s  = max(0, min(10, 10 - abs(sleep - 8) * 2))
    alc_s  = max(0, 10 - alcohol * 2)
    smk_s  = {"Never": 10, "Former": 6, "Current": 0}.get(smoking, 5)
    return round((diet * 0.35 + act_s * 0.30 + slp_s * 0.15 + alc_s * 0.1 + smk_s * 0.1), 1)

def age_group(age):
    if age < 36:  return "Young Adult"
    if age < 51:  return "Adult"
    if age < 66:  return "Senior Adult"
    return "Elderly"

STAGE_DESC = {
    "Sem Diabetes": "Os seus valores estão dentro dos parâmetros normais. Continue com os seus bons hábitos!",
    "Pre-Diabetes": "Os seus valores estão ligeiramente elevados. Mudanças no estilo de vida podem evitar a progressão.",
    "Diabetes":     "Os seus valores sugerem diabetes. Consulte o seu médico para confirmação e plano de tratamento.",
}


# ── Components ────────────────────────────────────────────────────────────────
def pill(label, value, ref=""):
    st.markdown(f"""<div class="mpill">
        <div class="mpill-lbl">{label}</div>
        <div class="mpill-val">{value}</div>
        <div class="mpill-ref">{ref}</div>
    </div>""", unsafe_allow_html=True)

def tip(text, good=False):
    cls = "tip tip-good" if good else "tip"
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)

def axis_style(fig):
    fig.update_xaxes(showgrid=False, linecolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.07)", linecolor="rgba(255,255,255,0.1)")
    return fig


# ── Charts ────────────────────────────────────────────────────────────────────

def chart_gauge(value, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Score de Risco", "font": {"size": 12, "color": "rgba(255,255,255,0.6)"}},
        number={"font": {"size": 34, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "rgba(255,255,255,0.25)",
                     "tickfont": {"size": 8}},
            "bar":  {"color": color, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  33], "color": "rgba(39,174,96,0.15)"},
                {"range": [33, 66], "color": "rgba(243,156,18,0.15)"},
                {"range": [66,100], "color": "rgba(231,76,60,0.15)"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "value": value},
        },
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10), **PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_lifestyle_gauge(score):
    color = C_GREEN if score >= 7 else (C_YELLOW if score >= 4 else C_RED)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Score de Estilo de Vida", "font": {"size": 12, "color": "rgba(255,255,255,0.6)"}},
        number={"font": {"size": 30, "color": color}, "suffix": "/10"},
        gauge={
            "axis": {"range": [0, 10], "tickcolor": "rgba(255,255,255,0.25)",
                     "tickfont": {"size": 8}},
            "bar":  {"color": color, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  4], "color": "rgba(231,76,60,0.15)"},
                {"range": [4,  7], "color": "rgba(243,156,18,0.15)"},
                {"range": [7, 10], "color": "rgba(39,174,96,0.15)"},
            ],
        },
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10), **PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_activity_diet_bar(activity, diet, df):
    """Bullet-style bar: user value vs population median."""
    pop_act_med  = df["physical_activity_minutes_per_week"].median()
    pop_diet_med = df["diet_score"].median()

    categories = ["Atividade Física<br>(min/sem)", "Score de Dieta<br>(0-10)"]
    user_vals   = [activity, diet]
    pop_vals    = [pop_act_med, pop_diet_med]
    ref_vals    = [150, 7]

    fig = go.Figure()
    for i, (cat, uv, pv, rv) in enumerate(zip(categories, user_vals, pop_vals, ref_vals)):
        color = C_GREEN if uv >= rv else (C_YELLOW if uv >= rv * 0.6 else C_RED)
        fig.add_trace(go.Bar(
            name=cat, x=[uv], y=[cat], orientation="h",
            marker_color=color, showlegend=False,
            hovertemplate=f"<b>{cat}</b><br>O seu valor: {uv}<extra></extra>",
            text=f"{uv}", textposition="outside", textfont=dict(size=11, color=color),
        ))
        # Population median marker
        fig.add_shape(type="line",
                      x0=pv, x1=pv, y0=i-0.4, y1=i+0.4,
                      line=dict(color="rgba(255,255,255,0.5)", width=2, dash="dot"))
        # Recommended line
        fig.add_shape(type="line",
                      x0=rv, x1=rv, y0=i-0.4, y1=i+0.4,
                      line=dict(color="rgba(255,255,255,0.85)", width=2))

    fig.update_layout(
        title="O Seu Nível vs Recomendado (linha branca) e Média Populacional (pontilhado)",
        barmode="overlay", height=200,
        xaxis=dict(showgrid=False, showticklabels=False),
        margin=dict(l=140, r=60, t=50, b=10),
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_activity_glucose(df, user_activity, user_glucose):
    """Exercise effect: activity vs fasting glucose from population."""
    bins = [0, 60, 120, 180, 240, 600]
    labels = ["0-60", "60-120", "120-180", "180-240", "240+"]
    tmp = df.copy()
    tmp["act_bin"] = pd.cut(tmp["physical_activity_minutes_per_week"],
                             bins=bins, labels=labels)
    agg = tmp.groupby("act_bin", observed=True)["glucose_fasting"].median().reset_index()
    agg.columns = ["faixa", "glucose_mediana"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg["faixa"], y=agg["glucose_mediana"],
        marker_color=C_BLUE, opacity=0.7,
        hovertemplate="<b>%{x} min/sem</b><br>Glicose mediana: %{y:.1f} mg/dL<extra></extra>",
        name="Mediana população",
    ))
    # User position
    user_bin = labels[min(int(user_activity // 60), 4)]
    fig.add_hline(y=user_glucose, line_dash="dot",
                  line_color=C_WARM, line_width=2,
                  annotation_text=f"A sua glicose: {user_glucose} mg/dL",
                  annotation_font_size=10, annotation_font_color=C_WARM)
    fig.update_layout(
        title="O Poder do Exercício: Atividade vs Glicemia em Jejum",
        xaxis_title="Atividade Física (min/semana)",
        yaxis_title="Glicose em Jejum — Mediana (mg/dL)",
        height=300, margin=dict(l=50, r=10, t=50, b=50),
        **PLOTLY_LAYOUT,
    )
    axis_style(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_risk_vs_age_group(df, user_age, user_risk):
    """User risk vs their age group median."""
    grp = age_group(user_age)
    agg = df.groupby("age_groups", observed=True)["diabetes_risk_score"].median().reindex(AGE_ORDER).dropna()

    colors = [C_GREEN if g != grp else C_ORANGE for g in agg.index]
    fig = go.Figure(go.Bar(
        x=agg.index, y=agg.values,
        marker_color=colors,
        text=agg.round(1).values,
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Risco mediano: %{y:.1f}<extra></extra>",
    ))
    fig.add_hline(y=user_risk,
                  line_dash="dot", line_color=C_WARM, line_width=2,
                  annotation_text=f"O seu risco: {user_risk:.0f}",
                  annotation_font_size=10, annotation_font_color=C_WARM,
                  annotation_position="top right")
    fig.update_layout(
        title=f"O Seu Risco vs Grupo Etário (o seu grupo: {grp})",
        yaxis_title="Score de Risco Mediano",
        height=280, margin=dict(l=50, r=10, t=50, b=50),
        **PLOTLY_LAYOUT,
    )
    axis_style(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_sedentary_gauge(screen_h, activity):
    ratio = screen_h / (activity / 60 + 0.1)
    ratio = min(ratio, 20)
    color = C_GREEN if ratio < 2 else (C_YELLOW if ratio < 5 else C_RED)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(ratio, 1),
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Índice de Sedentarismo<br>(ecrã/exercício)", "font": {"size": 11, "color": "rgba(255,255,255,0.6)"}},
        number={"font": {"size": 28, "color": color}},
        gauge={
            "axis": {"range": [0, 20], "tickcolor": "rgba(255,255,255,0.25)",
                     "tickfont": {"size": 8}},
            "bar":  {"color": color, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  2], "color": "rgba(39,174,96,0.15)"},
                {"range": [2,  5], "color": "rgba(243,156,18,0.15)"},
                {"range": [5, 20], "color": "rgba(231,76,60,0.15)"},
            ],
        },
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=10), **PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    if ratio > 5:
        tip("O seu rácio ecrã/exercício está elevado. Reduzir o tempo de ecrã melhora a sensibilidade à insulina e o sono.")
    elif ratio > 2:
        tip("Rácio moderado. Tente equilibrar melhor o tempo de ecrã com atividade física.")
    else:
        tip("Excelente equilíbrio entre atividade e tempo de ecrã!", good=True)


def chart_radar_lifestyle(diet, activity, sleep, alcohol, smoking):
    cats = ["Dieta", "Exercício", "Sono", "Álcool", "Tabaco"]
    vals = [
        diet,
        min(activity / 30, 10),
        max(0, min(10, 10 - abs(sleep - 8) * 2)),
        max(0, 10 - alcohol * 2),
        {"Never": 10, "Former": 6, "Current": 0}.get(smoking, 5),
    ]
    fig = go.Figure(go.Scatterpolar(
        r=vals + [vals[0]], theta=cats + [cats[0]],
        fill="toself",
        fillcolor="rgba(240,168,104,0.18)",
        line=dict(color=C_WARM, width=2.5),
        hovertemplate="%{theta}: %{r:.1f}/10<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 10], showticklabels=True,
                            tickfont=dict(size=8), gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            bgcolor="rgba(0,0,0,0)",
        ),
        title="Perfil de Estilo de Vida",
        height=300, showlegend=False,
        margin=dict(l=40, r=40, t=50, b=20),
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def get_tips(activity, diet, sleep, smoking, alcohol, bmi, risk):
    good, warn = [], []
    if activity >= 150:
        good.append("Nível de atividade adequado. Continue a manter os 150 min/semana recomendados pela OMS.")
    else:
        warn.append(f"Atividade fisica baixa ({activity} min/sem). O objetivo e 150 min/semana. "
                    f"Pessoas ativas tem em media 30% menos risco de diabetes.")
    if diet >= 7:
        good.append("Score de dieta muito bom. Uma alimentação equilibrada é um dos maiores fatores de proteção.")
    elif diet < 5:
        warn.append("Score de dieta baixo. Reduza acucares simples e aumente fibras e vegetais. "
                    "Melhorar a dieta esta diretamente ligado a descida do IMC e do risco.")
    if 6 <= sleep <= 9:
        good.append("Horas de sono adequadas. O sono de qualidade regula as hormonas que controlam a glicose.")
    else:
        warn.append("O sono ideal é 7-8h/noite. Privação de sono aumenta a resistência à insulina.")
    if smoking == "Current":
        warn.append("Fumar aumenta significativamente o risco de complicações vasculares e metabólicas.")
    if alcohol > 7:
        warn.append("Consumo de álcool elevado. Reduzir melhora o controlo glicémico e o peso.")
    if bmi > 25:
        warn.append(f"IMC {bmi:.1f}. Uma perda de apenas 5-7% do peso corporal reduz drasticamente o risco.")
    return good, warn


# ── Main ──────────────────────────────────────────────────────────────────────
def show(back_fn):
    inject_styles()
    df = load_data()

    # Sidebar
    with st.sidebar:
        st.markdown("### Os Meus Dados")
        st.markdown('<div class="sidebar-sec">Pessoal</div>', unsafe_allow_html=True)
        age    = st.slider("Idade", 18, 90, 45)
        weight = st.number_input("Peso (kg)", 40.0, 200.0, 75.0, step=0.5)
        height = st.number_input("Altura (cm)", 140, 220, 170)
        family = st.checkbox("Histórico familiar de diabetes")
        hypert = st.checkbox("Hipertensão diagnosticada")

        st.markdown('<div class="sidebar-sec">Valores Clinicos</div>', unsafe_allow_html=True)
        hba1c       = st.slider("HbA1c (%)", 4.0, 14.0, 5.5, step=0.1,
                                 help="Hemoglobina glicada — média dos últimos 3 meses")
        glucose     = st.slider("Glicose Jejum (mg/dL)", 60, 350, 90,
                                 help="Normal: 70-100 mg/dL")
        postprandial = st.slider("Glicose Pos-Prandial (mg/dL)", 60, 400, 140,
                                  help="Após refeição — normal < 140 mg/dL")
        sbp         = st.slider("Pressao Sistolica (mmHg)", 80, 210, 120)
        chol        = st.slider("Colesterol Total (mg/dL)", 100, 380, 180)

        st.markdown('<div class="sidebar-sec">Estilo de Vida</div>', unsafe_allow_html=True)
        activity = st.slider("Atividade Fisica (min/sem)", 0, 600, 120, step=10)
        diet     = st.slider("Score de Dieta (0-10)", 0.0, 10.0, 6.0, step=0.5)
        sleep    = st.slider("Sono (h/noite)", 3.0, 12.0, 7.5, step=0.5)
        alcohol  = st.slider("Álcool (unidades/semana)", 0, 40, 2)
        screen_h = st.slider("Tempo de ecrã (h/dia)", 0.0, 16.0, 6.0, step=0.5)
        smoking  = st.selectbox("Tabaco", ["Never","Former","Current"],
                                 format_func=lambda x: {"Never":"Nunca","Former":"Ex-fumador","Current":"Fumador"}[x])

        st.markdown("---")
        if st.button("Voltar ao início", key="pat_back"):
            back_fn()

    # Derived
    bmi   = weight / ((height / 100) ** 2)
    risk  = estimate_risk(age, bmi, hba1c, glucose, sbp, family, hypert, smoking, activity, diet)
    stage, stage_color, stage_level = classify(hba1c, glucose)
    ws_label, ws_color = weight_status(bmi)
    ls_score = lifestyle_score(diet, activity, sleep, alcohol, smoking)
    grp      = age_group(age)

    # Header
    h_title, h_back = st.columns([7, 1])
    with h_title:
        st.markdown('<div class="pat-title">🩺 TeaBetes — Explorador de Saúde</div>', unsafe_allow_html=True)
        st.markdown('<div class="pat-sub">Ajuste os controlos na barra lateral — todos os gráficos atualizam em tempo real.</div>', unsafe_allow_html=True)
    with h_back:
        if st.button("← Início", key="pat_back_top"):
            back_fn()

    # ── Faixa de estado ───────────────────────────────────────────────────────
    col_status, col_gauge, col_lifestyle = st.columns([3, 2, 2])
    with col_status:
        st.markdown(f"""<div class="status-card" style="background:{stage_color}cc">
            <div class="status-lbl">Estado Estimado</div>
            <div class="status-val">{stage}</div>
            <div class="status-desc">{STAGE_DESC[stage]}</div>
        </div>""", unsafe_allow_html=True)
        # Weight status badge
        st.markdown(f"""<div style="margin-top:10px">
            <span style="font-size:.72rem;opacity:.5;text-transform:uppercase;letter-spacing:.06em">Estado de Peso &nbsp;</span>
            <span class="wstatus-badge" style="background:{ws_color}33;color:{ws_color};border:1px solid {ws_color}55">{ws_label}</span>
            <span style="font-size:.78rem;opacity:.55;margin-left:8px">IMC {bmi:.1f}</span>
        </div>""", unsafe_allow_html=True)
        # Activity level
        pct_who = min(activity / 150 * 100, 100)
        act_color = C_GREEN if activity >= 150 else (C_YELLOW if activity >= 90 else C_RED)
        st.markdown(f"""<div style="margin-top:10px">
            <span style="font-size:.72rem;opacity:.5;text-transform:uppercase;letter-spacing:.06em">Nivel de Atividade &nbsp;</span>
            <span class="wstatus-badge" style="background:{act_color}33;color:{act_color};border:1px solid {act_color}55">{activity} min/sem</span>
            <span style="font-size:.75rem;opacity:.4;margin-left:6px">{pct_who:.0f}% do objetivo OMS</span>
        </div>""", unsafe_allow_html=True)
    with col_gauge:
        chart_gauge(risk, stage_color)
    with col_lifestyle:
        chart_lifestyle_gauge(ls_score)

    # ── Metricas rapidas ──────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Os Seus Valores</div>', unsafe_allow_html=True)
    m1,m2,m3,m4,m5,m6 = st.columns(6)
    with m1: pill("HbA1c",         f"{hba1c:.1f}%",   "< 5.7% normal")
    with m2: pill("Glicose Jejum",  f"{glucose}",      "70-100 mg/dL")
    with m3: pill("IMC",            f"{bmi:.1f}",      "18.5-24.9 ideal")
    with m4: pill("P. Sistólica",   f"{sbp}",          "< 120 mmHg")
    with m5: pill("Colesterol",     f"{chol}",         "< 200 mg/dL")
    with m6: pill("Idade",          f"{age}",          f"Grupo: {grp}")

    # ── Exercicio & Sedentarismo ──────────────────────────────────────────────
    st.markdown('<div class="sec-title">Atividade & Sedentarismo</div>', unsafe_allow_html=True)
    ra1, ra2 = st.columns([3, 2])
    with ra1:
        chart_activity_glucose(df, activity, glucose)
        st.markdown(
            '<div style="font-size:.78rem;opacity:.45;margin-top:4px;padding-left:2px">'
            'A linha horizontal mostra a sua glicose. Veja como a populacao mais ativa tem niveis menores.</div>',
            unsafe_allow_html=True)
    with ra2:
        chart_sedentary_gauge(screen_h, activity)

    # ── Dieta & Atividade ─────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Dieta & Atividade vs Referencia</div>', unsafe_allow_html=True)
    chart_activity_diet_bar(activity, diet, df)

    # ── Risco por grupo etario + Radar ────────────────────────────────────────
    st.markdown('<div class="sec-title">O Seu Risco no Contexto</div>', unsafe_allow_html=True)
    rg1, rg2 = st.columns([3, 2])
    with rg1:
        chart_risk_vs_age_group(df, age, risk)
    with rg2:
        chart_radar_lifestyle(diet, activity, sleep, alcohol, smoking)

    # ── Recomendacoes ─────────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Recomendacoes Personalizadas</div>', unsafe_allow_html=True)
    good_tips, warn_tips = get_tips(activity, diet, sleep, smoking, alcohol, bmi, risk)
    if warn_tips:
        for t in warn_tips:
            tip(t, good=False)
    if good_tips:
        for t in good_tips:
            tip(t, good=True)

    st.markdown(
        "<br><small style='opacity:.28'>Ferramenta indicativa — não substitui avaliação médica profissional.</small>",
        unsafe_allow_html=True)
