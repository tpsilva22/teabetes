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
    return "No Diabetes", C_GREEN, 1

def weight_status(bmi):
    if bmi < 18.5: return "Underweight", "#5b9bd5"
    if bmi < 25.0: return "Normal Weight",    C_GREEN
    if bmi < 30.0: return "Overweight", C_YELLOW
    return "Obesity", C_RED

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
    "No Diabetes": "Your values are within healthy parameters. Keep up the good habits!",
    "Pre-Diabetes": "Your values are slightly elevated. Lifestyle changes can prevent progression.",
    "Diabetes":     "Your values suggest diabetes. Consult your doctor for confirmation and a treatment plan.",
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
        title={"text": "Risk Score", "font": {"size": 12, "color": "rgba(255,255,255,0.6)"}},
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
        title={"text": "Lifestyle Score", "font": {"size": 12, "color": "rgba(255,255,255,0.6)"}},
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
    pop_act_med  = df["physical_activity_minutes_per_week"].median()
    pop_diet_med = df["diet_score"].median()

    categories = ["Physical Activity<br>(min/week)", "Diet Score<br>(0-10)"]
    user_vals   = [activity, diet]
    pop_vals    = [pop_act_med, pop_diet_med]
    ref_vals    = [150, 7]

    fig = go.Figure()
    for i, (cat, uv, pv, rv) in enumerate(zip(categories, user_vals, pop_vals, ref_vals)):
        color = C_GREEN if uv >= rv else (C_YELLOW if uv >= rv * 0.6 else C_RED)
        fig.add_trace(go.Bar(
            name=cat, x=[uv], y=[cat], orientation="h",
            marker_color=color, showlegend=False,
            hovertemplate=f"<b>{cat}</b><br>Your Value: {uv}<extra></extra>",
            text=f"{uv}", textposition="outside", textfont=dict(size=11, color=color),
        ))
        fig.add_shape(type="line",
                      x0=pv, x1=pv, y0=i-0.4, y1=i+0.4,
                      line=dict(color="rgba(255,255,255,0.5)", width=2, dash="dot"))
        fig.add_shape(type="line",
                      x0=rv, x1=rv, y0=i-0.4, y1=i+0.4,
                      line=dict(color="rgba(255,255,255,0.85)", width=2))

    fig.update_layout(
        title="Your Level vs Recommended (solid white) and Population Average (dotted)",
        barmode="overlay", height=200,
        xaxis=dict(showgrid=False, showticklabels=False),
        margin=dict(l=140, r=60, t=50, b=10),
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_activity_glucose(df, user_activity, user_glucose):
    bins = [0, 60, 120, 180, 240, 600]
    labels = ["0-60", "60-120", "120-180", "180-240", "240+"]
    tmp = df.copy()
    tmp["act_bin"] = pd.cut(tmp["physical_activity_minutes_per_week"],
                             bins=bins, labels=labels)
    agg = tmp.groupby("act_bin", observed=True)["glucose_fasting"].median().reset_index()
    agg.columns = ["bracket", "median_glucose"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg["bracket"], y=agg["median_glucose"],
        marker_color=C_BLUE, opacity=0.7,
        hovertemplate="<b>%{x} min/week</b><br>Median Glucose: %{y:.1f} mg/dL<extra></extra>",
        name="Population Median",
    ))
    user_bin = labels[min(int(user_activity // 60), 4)]
    fig.add_hline(y=user_glucose, line_dash="dot",
                  line_color=C_WARM, line_width=2,
                  annotation_text=f"Your Glucose: {user_glucose} mg/dL",
                  annotation_font_size=10, annotation_font_color=C_WARM)
    fig.update_layout(
        title="The Power of Exercise: Activity vs Fasting Blood Sugar",
        xaxis_title="Physical Activity (min/week)",
        yaxis_title="Median Fasting Glucose (mg/dL)",
        height=300, margin=dict(l=50, r=10, t=50, b=50),
        **PLOTLY_LAYOUT,
    )
    axis_style(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def chart_risk_vs_age_group(df, user_age, user_risk):
    grp = age_group(user_age)
    agg = df.groupby("age_groups", observed=True)["diabetes_risk_score"].median().reindex(AGE_ORDER).dropna()

    colors = [C_GREEN if g != grp else C_ORANGE for g in agg.index]
    fig = go.Figure(go.Bar(
        x=agg.index, y=agg.values,
        marker_color=colors,
        text=agg.round(1).values,
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Median Risk: %{y:.1f}<extra></extra>",
    ))
    fig.add_hline(y=user_risk,
                  line_dash="dot", line_color=C_WARM, line_width=2,
                  annotation_text=f"Your Risk: {user_risk:.0f}",
                  annotation_font_size=10, annotation_font_color=C_WARM,
                  annotation_position="bottom right")
    fig.update_layout(
        title=f"Your Risk vs Age Group (Your Group: {grp})",
        yaxis_title="Median Risk Score",
        height=280, margin=dict(l=50, r=10, t=60, b=50),
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
        title={"text": "Sedentary Index<br>(Screen/Exercise Ratio)", "font": {"size": 11, "color": "rgba(255,255,255,0.6)"}},
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
        tip("Your screen-to-exercise ratio is high. Reducing screen time helps improve insulin sensitivity and sleep.")
    elif ratio > 2:
        tip("Moderate ratio. Try to balance screen time with physical activity.")
    else:
        tip("Excellent balance between activity and screen time!", good=True)


def chart_radar_lifestyle(diet, activity, sleep, alcohol, smoking):
    cats = ["Diet", "Exercise", "Sleep", "Alcohol", "Smoking"]
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
        title="Lifestyle Profile",
        height=300, showlegend=False,
        margin=dict(l=40, r=40, t=50, b=20),
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def get_tips(activity, diet, sleep, smoking, alcohol, bmi, risk):
    good, warn = [], []
    if activity >= 150:
        good.append("Adequate activity level. Keep maintaining the 150 min/week recommended by the WHO.")
    else:
        warn.append(f"Low physical activity ({activity} min/week). The goal is 150 min/week. "
                    f"Active people have on average 30% less risk of diabetes.")
    if diet >= 7:
        good.append("Great diet score. A balanced diet is one of the strongest protection factors.")
    elif diet < 5:
        warn.append("Low diet score. Reduce simple sugars and increase fibres and vegetables. "
                    "Improving your diet is directly linked to lowering your BMI and risk.")
    if 6 <= sleep <= 9:
        good.append("Adequate sleeping hours. Quality sleep regulates hormones that control blood sugar.")
    else:
        warn.append("Ideal sleep is 7-8h/night. Sleep deprivation increases insulin resistance.")
    if smoking == "Current":
        warn.append("Smoking significantly increases the risk of vascular and metabolic complications.")
    if alcohol > 7:
        warn.append("High alcohol consumption. Reducing it will improve glycaemic control and weight.")
    if bmi > 25:
        warn.append(f"BMI {bmi:.1f}. A body weight loss of just 5-7% drastically reduces your risk.")
    return good, warn


# ── Main ──────────────────────────────────────────────────────────────────────
def show(back_fn):
    inject_styles()
    df = load_data()

    # Sidebar
    with st.sidebar:
        st.markdown("### My Health Data")
        st.markdown('<div class="sidebar-sec">Personal</div>', unsafe_allow_html=True)
        age    = st.slider("Age", 18, 90, 45)
        weight = st.number_input("Weight (kg)", 40.0, 200.0, 75.0, step=0.5)
        height = st.number_input("Height (cm)", 140, 220, 170)
        family = st.checkbox("Family History of Diabetes")
        hypert = st.checkbox("Diagnosed Hypertension")

        st.markdown('<div class="sidebar-sec">Clinical Values</div>', unsafe_allow_html=True)
        hba1c       = st.slider("Average Blood Sugar (HbA1c %)", 4.0, 14.0, 5.5, step=0.1,
                                 help="Glycated haemoglobin — shows your average blood sugar levels over the past 2-3 months. Normal range is below 5.7%. Ask your doctor for a blood test to measure this accurately.")
        glucose     = st.slider("Fasting Blood Sugar (mg/dL)", 60, 350, 90,
                                 help="Blood sugar levels measured after fasting for at least 8 hours. Normal range: 70-100 mg/dL.")
        postprandial = st.slider("Post-Meal Sugar (mg/dL)", 60, 400, 140,
                                  help="Blood sugar levels measured 2 hours after a meal. Normal range is typically under 140 mg/dL.")
        sbp         = st.slider("Top Blood Pressure Number (Systolic mmHg)", 80, 210, 120,
                                  help="The top number on your blood pressure reading. E.g., if you have 120/80, this value is 120.")
        chol        = st.slider("Total Cholesterol (mg/dL)", 100, 380, 180,
                                  help="Your total cholesterol level measured via a blood test. A healthy target is typically under 200 mg/dL.")

        st.markdown('<div class="sidebar-sec">Lifestyle</div>', unsafe_allow_html=True)
        activity = st.slider("Physical Activity (min/week)", 0, 600, 120, step=10)
        diet     = st.slider("Diet Quality Score (0-10)", 0.0, 10.0, 6.0, step=0.5,
                              help="Rate how healthy your diet is from 0 (very poor) to 10 (excellent, rich in vegetables, lean proteins, and whole grains).")
        sleep    = st.slider("Sleep (h/night)", 3.0, 12.0, 7.5, step=0.5)
        alcohol  = st.slider("Alcohol (units/week)", 0, 40, 2)
        screen_h = st.slider("Screen Time (h/day)", 0.0, 16.0, 6.0, step=0.5)
        smoking  = st.selectbox("Smoking Status", ["Never", "Former", "Current"])

        st.markdown("---")
        
        submit = st.button("Generate My Report", use_container_width=True)
        if submit:
            st.session_state.patient_submitted = True
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Back to Home", key="pat_back"):
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
        st.markdown('<div class="pat-title">🩺 TeaBetes — Health Explorer</div>', unsafe_allow_html=True)
        st.markdown('<div class="pat-sub">Adjust the controls in the sidebar — all charts update in real-time.</div>', unsafe_allow_html=True)
    with h_back:
        if st.button("← Home", key="pat_back_top"):
            back_fn()

    if not st.session_state.get("patient_submitted", False):
        st.info("Please fill out your health details in the sidebar menu on the left, then click 'Generate My Report' to view your personalized dashboard.")
        
        with st.expander("How to find your clinical values?"):
            st.markdown("""
            * **HbA1c & Cholesterol:** These are obtained through a standard laboratory blood test requested by your GP.
            * **Blood Sugar:** Can be measured at home with a glucometer or at your local pharmacy.
            * **Blood Pressure:** Can be checked using a home blood pressure monitor, at a pharmacy, or during a routine clinic visit.
            """)
        return

    # ── Status Banner ─────────────────────────────────────────────────────────
    col_status, col_gauge, col_lifestyle = st.columns([3, 2, 2])
    with col_status:
        st.markdown(f"""<div class="status-card" style="background:{stage_color}cc">
            <div class="status-lbl">Estimated Status</div>
            <div class="status-val">{stage}</div>
            <div class="status-desc">{STAGE_DESC[stage]}</div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown(f"""<div style="margin-top:10px">
            <span style="font-size:.72rem;opacity:.5;text-transform:uppercase;letter-spacing:.06em">Weight Status &nbsp;</span>
            <span class="wstatus-badge" style="background:{ws_color}33;color:{ws_color};border:1px solid {ws_color}55">{ws_label}</span>
            <span style="font-size:.78rem;opacity:.55;margin-left:8px">BMI {bmi:.1f}</span>
        </div>""", unsafe_allow_html=True)
        
        pct_who = min(activity / 150 * 100, 100)
        act_color = C_GREEN if activity >= 150 else (C_YELLOW if activity >= 90 else C_RED)
        st.markdown(f"""<div style="margin-top:10px">
            <span style="font-size:.72rem;opacity:.5;text-transform:uppercase;letter-spacing:.06em">Activity Level &nbsp;</span>
            <span class="wstatus-badge" style="background:{act_color}33;color:{act_color};border:1px solid {act_color}55">{activity} min/week</span>
            <span style="font-size:.75rem;opacity:.4;margin-left:6px">{pct_who:.0f}% of WHO goal</span>
        </div>""", unsafe_allow_html=True)
    with col_gauge:
        chart_gauge(risk, stage_color)
    with col_lifestyle:
        chart_lifestyle_gauge(ls_score)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Quick Metrics ─────────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Your Values</div>', unsafe_allow_html=True)
    m1,m2,m3,m4,m5,m6 = st.columns(6)
    with m1: pill("HbA1c",         f"{hba1c:.1f}%",   "< 5.7% normal")
    with m2: pill("Fasting Sugar", f"{glucose}",      "70-100 mg/dL")
    with m3: pill("BMI",            f"{bmi:.1f}",     "18.5-24.9 ideal")
    with m4: pill("Systolic BP",    f"{sbp}",         "< 120 mmHg")
    with m5: pill("Cholesterol",    f"{chol}",        "< 200 mg/dL")
    with m6: pill("Age",            f"{age}",         f"Group: {grp}")

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Exercise & Sedentary ──────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Activity & Sedentary Behaviour</div>', unsafe_allow_html=True)
    ra1, ra2 = st.columns([3, 2])
    with ra1:
        chart_activity_glucose(df, activity, glucose)
        st.markdown(
            '<div style="font-size:.78rem;opacity:.45;margin-top:4px;padding-left:2px">'
            'The horizontal line shows your glucose level. Notice how the more active population tends to have lower levels.</div>',
            unsafe_allow_html=True)
    with ra2:
        chart_sedentary_gauge(screen_h, activity)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Diet & Activity ───────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Diet & Activity vs Reference</div>', unsafe_allow_html=True)
    chart_activity_diet_bar(activity, diet, df)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Age Group Risk & Radar ────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Your Risk in Context</div>', unsafe_allow_html=True)
    rg1, rg2 = st.columns([3, 2])
    with rg1:
        chart_risk_vs_age_group(df, age, risk)
    with rg2:
        chart_radar_lifestyle(diet, activity, sleep, alcohol, smoking)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Recommendations ───────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Personalised Recommendations</div>', unsafe_allow_html=True)
    good_tips, warn_tips = get_tips(activity, diet, sleep, smoking, alcohol, bmi, risk)
    if warn_tips:
        for t in warn_tips:
            tip(t, good=False)
    if good_tips:
        for t in good_tips:
            tip(t, good=True)

    st.markdown(
        "<br><small style='opacity:.28'>Indicative tool — does not replace professional medical advice.</small>",
        unsafe_allow_html=True)