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

C_GREEN  = "#27ae60"
C_YELLOW = "#f39c12"
C_RED    = "#e74c3c"
C_ORANGE = "#e67e22"
C_BLUE   = "#2980b9"
C_WARM   = "#e8a87c"
C_SAGE   = "#5a8a6a"
C_AMBER  = "#b8860b"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="rgba(255,255,255,0.9)", size=11),
    hoverlabel=dict(bgcolor="rgba(20,20,30,0.92)", font_size=12, font_family="Inter, sans-serif"),
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
    .mpill     { background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.12); border-radius:11px; padding:14px 12px; text-align:center; }
    .mpill-lbl { font-size:.68rem; text-transform:uppercase; letter-spacing:.05em; opacity:.45; margin-bottom:3px; }
    .mpill-val { font-size:1.3rem; font-weight:600; color:#f0a868; }
    .mpill-ref { font-size:.66rem; opacity:.32; margin-top:2px; }
    .tip  { background:rgba(240,168,104,.08); border-left:3px solid #f0a868; border-radius:0 10px 10px 0; padding:11px 15px; margin-bottom:8px; font-size:.84rem; line-height:1.6; }
    .tip-good { background:rgba(39,174,96,.08); border-left:3px solid #27ae60; }
    .sec-title { font-family:'Lora',serif; font-size:1.05rem; color:#f0a868; opacity:.9; margin:24px 0 10px; border-bottom:1px solid rgba(240,168,104,.2); padding-bottom:5px; }
    .sidebar-sec { font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; opacity:.38; margin:16px 0 5px; }
    .wstatus-badge { display:inline-block; padding:6px 14px; border-radius:20px; font-size:1.05rem; font-weight:600; margin-bottom:4px; }
    </style>
    """, unsafe_allow_html=True)

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
    if hba1c >= 6.5 or glucose >= 126: return "Diabetes", C_RED, 3
    if hba1c >= 5.7 or glucose >= 100: return "Pre-Diabetes", C_YELLOW, 2
    return "No Diabetes", C_GREEN, 1

def weight_status(bmi):
    if bmi < 18.5: return "Underweight", "#5b9bd5"
    if bmi < 25.0: return "Normal Weight", C_GREEN
    if bmi < 30.0: return "Overweight", C_YELLOW
    return "Obesity", C_RED

def lifestyle_score(diet, activity, sleep, alcohol, smoking):
    act_s  = min(activity / 30, 10)
    slp_s  = max(0, min(10, 10 - abs(sleep - 8) * 2))
    alc_s  = max(0, 10 - alcohol * 2)
    smk_s  = {"Never": 10, "Former": 6, "Current": 0}.get(smoking, 5)
    return round((diet * 0.35 + act_s * 0.30 + slp_s * 0.15 + alc_s * 0.1 + smk_s * 0.1), 1)

def age_group(age):
    if age < 36: return "Young Adult"
    if age < 51: return "Adult"
    if age < 66: return "Senior Adult"
    return "Elderly"

STAGE_DESC = {
    "No Diabetes": "Your values are within healthy parameters. Keep up the good habits!",
    "Pre-Diabetes": "Your values are slightly elevated. Lifestyle changes can prevent progression.",
    "Diabetes": "Your values suggest diabetes. Consult your doctor for confirmation and a treatment plan.",
}

def pill(label, value, ref="", tone=None):
    value_color = tone or "#f0a868"
    st.markdown(
        f'<div class="mpill"><div class="mpill-lbl">{label}</div><div class="mpill-val" style="color:{value_color}">{value}</div><div class="mpill-ref">{ref}</div></div>',
        unsafe_allow_html=True,
    )

def zone_color(zone):
    return {"good": C_SAGE, "mid": C_AMBER, "bad": C_RED}.get(zone, C_WARM)

def zone_hba1c(v):
    if v < 5.7:
        return "good"
    if v < 6.5:
        return "mid"
    return "bad"

def zone_glucose(v):
    if 70 <= v <= 100:
        return "good"
    if (60 <= v < 70) or (100 < v < 126):
        return "mid"
    return "bad"

def zone_bmi(v):
    if 18.5 <= v <= 24.9:
        return "good"
    if (17.0 <= v < 18.5) or (25.0 <= v < 30.0):
        return "mid"
    return "bad"

def zone_sbp(v):
    if v < 120:
        return "good"
    if v < 130:
        return "mid"
    return "bad"

def zone_chol(v):
    if v < 200:
        return "good"
    if v < 240:
        return "mid"
    return "bad"

def tip(text, good=False):
    cls = "tip tip-good" if good else "tip"
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)

def axis_style(fig):
    fig.update_xaxes(showgrid=False, linecolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.07)", linecolor="rgba(255,255,255,0.1)")
    return fig

def chart_gauge(value, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Risk Score", "font": {"size": 12, "color": "rgba(255,255,255,0.6)"}},
        number={"font": {"size": 34, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "rgba(255,255,255,0.25)", "tickfont": {"size": 8}},
            "bar": {"color": color, "thickness": 0.22}, "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
            "steps": [{"range": [0, 33], "color": "rgba(39,174,96,0.15)"}, {"range": [33, 66], "color": "rgba(243,156,18,0.15)"}, {"range": [66,100], "color": "rgba(231,76,60,0.15)"}],
            "threshold": {"line": {"color": color, "width": 3}, "value": value},
        },
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10), **PLOTLY_LAYOUT)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_lifestyle_gauge(score):
    color = C_GREEN if score >= 7 else (C_YELLOW if score >= 4 else C_RED)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Lifestyle Score", "font": {"size": 12, "color": "rgba(255,255,255,0.6)"}},
        number={"font": {"size": 30, "color": color}, "suffix": "/10"},
        gauge={
            "axis": {"range": [0, 10], "tickcolor": "rgba(255,255,255,0.25)", "tickfont": {"size": 8}},
            "bar": {"color": color, "thickness": 0.22}, "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
            "steps": [{"range": [0, 4], "color": "rgba(231,76,60,0.15)"}, {"range": [4, 7], "color": "rgba(243,156,18,0.15)"}, {"range": [7, 10], "color": "rgba(39,174,96,0.15)"}],
        },
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10), **PLOTLY_LAYOUT)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_activity_diet_bar(activity, diet, df):
    pop_act_med  = df["physical_activity_minutes_per_week"].median()
    pop_diet_med = df["diet_score"].median()
    categories = ["Physical Activity<br>(min/week)", "Diet Score<br>(0-10)"]
    user_vals  = [activity, diet]
    pop_vals   = [pop_act_med, pop_diet_med]
    ref_vals   = [150, 7]

    fig = go.Figure()
    y_positions = list(range(len(categories)))

    for i, (cat, uv, pv, rv) in enumerate(zip(categories, user_vals, pop_vals, ref_vals)):
        color = C_GREEN if uv >= rv else (C_YELLOW if uv >= rv * 0.6 else C_RED)
        fig.add_trace(go.Bar(
            name=cat, x=[uv], y=[i], orientation="h", marker_color=color, showlegend=False,
            hovertemplate=f"<b>{cat}</b><br>Your Value: {uv}<extra></extra>",
            text=f"{uv}", textposition="outside", textfont=dict(size=11, color=color),
        ))

        # Reference lines are regular traces so they support hover values.
        fig.add_trace(go.Scatter(
            x=[pv, pv],
            y=[i - 0.32, i + 0.32],
            mode="lines",
            line=dict(color="rgba(255,255,255,0.55)", width=2, dash="dot"),
            hovertemplate=f"<b>{cat}</b><br>Population Average: {pv:.1f}<extra></extra>",
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=[rv, rv],
            y=[i - 0.32, i + 0.32],
            mode="lines",
            line=dict(color="rgba(255,255,255,0.9)", width=2),
            hovertemplate=f"<b>{cat}</b><br>Recommended Value: {rv:.1f}<extra></extra>",
            showlegend=False,
        ))

    x_max = max(max(user_vals), max(pop_vals), max(ref_vals)) * 1.25

    fig.update_layout(
        title="Your Level vs Recommended (solid line) and Population Average (dotted)",
        barmode="overlay",
        height=220,
        xaxis=dict(showgrid=False, showticklabels=False, range=[0, x_max]),
        yaxis=dict(
            tickmode="array",
            tickvals=y_positions,
            ticktext=categories,
            range=[-0.6, len(categories) - 0.4],
            showgrid=False,
            zeroline=False,
        ),
        margin=dict(l=140, r=60, t=50, b=10), **PLOTLY_LAYOUT, hovermode="closest"
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_activity_glucose(df, user_activity, user_glucose):
    bins = [0, 60, 120, 180, 240, 600]
    labels = ["0-60", "60-120", "120-180", "180-240", "240+"]
    tmp = df.copy()
    tmp["act_bin"] = pd.cut(tmp["physical_activity_minutes_per_week"], bins=bins, labels=labels)
    agg = tmp.groupby("act_bin", observed=True)["glucose_fasting"].median().reset_index()
    agg.columns = ["bracket", "median_glucose"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg["bracket"], y=agg["median_glucose"], marker_color=C_BLUE, opacity=0.7,
        hovertemplate="<b>%{x} min/week</b><br>Median Glucose: %{y:.1f} mg/dL<extra></extra>", name="Population Median",
    ))
    fig.add_hline(y=user_glucose, line_dash="dot", line_color=C_WARM, line_width=2, annotation_text=f"Your Glucose: {user_glucose} mg/dL", annotation_font_size=10, annotation_font_color=C_WARM)
    fig.update_layout(title="Activity vs Fasting Blood Sugar", xaxis_title="Physical Activity (min/week)", yaxis_title="Median Fasting Glucose (mg/dL)", height=300, margin=dict(l=50, r=10, t=50, b=50), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_risk_vs_age_group(df, user_age, user_risk):
    grp = age_group(user_age)
    agg = df.groupby("age_groups", observed=True)["diabetes_risk_score"].median().reindex(AGE_ORDER).dropna()
    colors = [C_GREEN if g != grp else C_ORANGE for g in agg.index]
    fig = go.Figure(go.Bar(
        x=agg.index, y=agg.values, marker_color=colors, text=agg.round(1).values, textposition="outside",
        hovertemplate="<b>%{x}</b><br>Median Risk: %{y:.1f}<extra></extra>",
    ))
    fig.add_hline(y=user_risk, line_dash="dot", line_color=C_WARM, line_width=2, annotation_text=f"Your Risk: {user_risk:.0f}", annotation_font_size=10, annotation_font_color=C_WARM, annotation_position="bottom right")
    fig.update_layout(title=f"Your Risk vs Age Group (Your Group: {grp})", yaxis_title="Median Risk Score", height=280, margin=dict(l=50, r=10, t=60, b=50), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_sedentary_gauge(screen_h, activity):
    ratio = min(screen_h / (activity / 60 + 0.1), 20)
    color = C_GREEN if ratio < 2 else (C_YELLOW if ratio < 5 else C_RED)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(ratio, 1), domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Sedentary Index<br>(Screen/Exercise Ratio)", "font": {"size": 11, "color": "rgba(255,255,255,0.6)"}},
        number={"font": {"size": 28, "color": color}},
        gauge={
            "axis": {"range": [0, 20], "tickcolor": "rgba(255,255,255,0.25)", "tickfont": {"size": 8}},
            "bar": {"color": color, "thickness": 0.22}, "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
            "steps": [{"range": [0, 2], "color": "rgba(39,174,96,0.15)"}, {"range": [2, 5], "color": "rgba(243,156,18,0.15)"}, {"range": [5, 20], "color": "rgba(231,76,60,0.15)"}],
        },
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=10), **PLOTLY_LAYOUT)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_radar_lifestyle(diet, activity, sleep, alcohol, smoking):
    cats = ["Diet", "Exercise", "Sleep", "Alcohol", "Smoking"]
    vals = [diet, min(activity / 30, 10), max(0, min(10, 10 - abs(sleep - 8) * 2)), max(0, 10 - alcohol * 2), {"Never": 10, "Former": 6, "Current": 0}.get(smoking, 5)]
    fig = go.Figure(go.Scatterpolar(
        r=vals + [vals[0]], theta=cats + [cats[0]], fill="toself", fillcolor="rgba(240,168,104,0.18)",
        line=dict(color=C_WARM, width=2.5), hovertemplate="%{theta}: %{r:.1f}/10<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 10], showticklabels=True, tickfont=dict(size=8), gridcolor="rgba(255,255,255,0.1)"), angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"), bgcolor="rgba(0,0,0,0)"),
        title="Lifestyle Profile (10 is best)", height=300, showlegend=False, margin=dict(l=40, r=40, t=50, b=20), **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_bmi_percentile(bmi, df):
    fig = px.histogram(
        df, x="bmi", nbins=40, color_discrete_sequence=[C_BLUE],
        labels={"bmi": "Body Mass Index (BMI)"}, title="Your BMI in the Population Context"
    )
    fig.add_vline(x=bmi, line_dash="solid", line_color=C_WARM, line_width=3, annotation_text=f"Your BMI: {bmi:.1f}", annotation_font_color=C_WARM)
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=30), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def chart_sleep_risk(sleep, risk, df):
    agg = df.groupby("sleep_hours_per_day")["diabetes_risk_score"].mean().reset_index()
    fig = px.line(
        agg, x="sleep_hours_per_day", y="diabetes_risk_score",
        labels={"sleep_hours_per_day": "Sleep Hours", "diabetes_risk_score": "Average Risk Score"},
        title="Impact of Sleep on Average Risk"
    )
    fig.update_traces(line_color=C_BLUE, line_width=3)
    fig.add_scatter(x=[sleep], y=[risk], mode="markers", marker=dict(color=C_WARM, size=12, line=dict(width=2, color="white")), name="You", hovertemplate=f"Sleep: {sleep}h<br>Your Risk: {risk}<extra></extra>")
    fig.update_layout(height=280, showlegend=False, margin=dict(l=50, r=20, t=50, b=30), **PLOTLY_LAYOUT)
    axis_style(fig)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def get_tips(activity, diet, sleep, smoking, alcohol, bmi, risk, hba1c, sbp, chol):
    tips = []
    
    if activity >= 150: tips.append(("Adequate activity level. Keep maintaining the 150 min/week recommended by the WHO.", True))
    else: tips.append((f"Low physical activity ({activity} min/week). Goal is 150 min/week. Active people have up to 30% less diabetes risk.", False))
    
    if diet >= 7: tips.append(("Great diet score. A balanced diet is a strong protective factor.", True))
    else: tips.append(("Low diet score. Increasing fiber and vegetable intake is directly linked to lowering BMI and risk.", False))
    
    if 6 <= sleep <= 9: tips.append(("Adequate sleeping hours. Quality sleep regulates blood sugar hormones.", True))
    else: tips.append(("Ideal sleep is 7-8h/night. Sleep deprivation strongly increases insulin resistance.", False))
    
    if smoking == "Current": tips.append(("Smoking significantly increases the risk of vascular and metabolic complications.", False))
    elif smoking == "Former": tips.append(("Great job quitting smoking! Your cardiovascular risk will steadily decrease.", True))
    
    if alcohol > 7: tips.append(("High alcohol consumption. Reducing it will improve glycaemic control and aid weight loss.", False))
    
    if 18.5 <= bmi <= 24.9: tips.append(("Healthy BMI maintained. This is optimal for metabolic function.", True))
    elif bmi > 25: tips.append((f"BMI is {bmi:.1f}. A body weight loss of just 5-7% drastically reduces your risk.", False))
    
    if hba1c < 5.7: tips.append(("Excellent HbA1c levels, keeping far from the pre-diabetes threshold.", True))
    elif hba1c >= 6.5: tips.append(("HbA1c is in the diabetes range. Medical consultation is strongly advised to establish a control plan.", False))
    
    if sbp > 130: tips.append(("Elevated systolic blood pressure. Reducing sodium and managing stress can help lower this value.", False))
    
    if chol > 200: tips.append(("Total cholesterol is above 200. Consider increasing intake of omega-3s and reducing saturated fats.", False))

    tips = sorted(tips, key=lambda x: x[1])[:10]
    return tips

def show(back_fn):
    inject_styles()
    df = load_data()

    with st.sidebar:
        st.markdown("### My Health Data")
        st.markdown('<div class="sidebar-sec">Personal</div>', unsafe_allow_html=True)
        age    = st.number_input("Age (Exact Value)", 18, 120, 45, help="Enter your exact age for personal risk calculation.")
        weight = st.number_input("Weight (kg)", 40.0, 200.0, 75.0, step=0.5, help="Your current body weight.")
        height = st.number_input("Height (cm)", 140, 220, 170, help="Your height to calculate BMI.")
        family = st.checkbox("Family History of Diabetes", help="Check if parents or siblings have/had diabetes.")
        hypert = st.checkbox("Diagnosed Hypertension", help="Check if a doctor has formally diagnosed you with high blood pressure.")

        st.markdown('<div class="sidebar-sec">Clinical Values</div>', unsafe_allow_html=True)
        hba1c       = st.slider("Average Blood Sugar (HbA1c %)", 4.0, 14.0, 5.5, step=0.1, help="Glycated haemoglobin. Normal range is below 5.7%. Ask your doctor for a blood test to measure this accurately.")
        glucose     = st.slider("Fasting Blood Sugar (mg/dL)", 60, 350, 90, help="Blood sugar levels measured after fasting for at least 8 hours. Normal range: 70-100 mg/dL.")
        postprandial = st.slider("Post-Meal Sugar (mg/dL)", 60, 400, 140, help="Blood sugar levels measured 2 hours after a meal. Normal range is typically under 140 mg/dL.")
        sbp         = st.slider("Top Blood Pressure (Systolic mmHg)", 80, 210, 120, help="The top number on your blood pressure reading. E.g., if you have 120/80, this value is 120.")
        chol        = st.slider("Total Cholesterol (mg/dL)", 100, 380, 180, help="Your total cholesterol level measured via a blood test. Healthy target is < 200 mg/dL.")

        st.markdown('<div class="sidebar-sec">Lifestyle</div>', unsafe_allow_html=True)
        activity = st.slider("Physical Activity (min/week)", 0, 600, 120, step=10, help="Total minutes of moderate-to-vigorous exercise per week.")
        diet     = st.slider("Diet Quality Score (0-10)", 0.0, 10.0, 6.0, step=0.5, help="Rate how healthy your diet is from 0 (very poor) to 10 (excellent, rich in vegetables).")
        sleep    = st.slider("Sleep (h/night)", 3.0, 12.0, 7.5, step=0.5, help="Average hours of sleep per night.")
        alcohol  = st.slider("Alcohol (units/week)", 0, 40, 2, help="Number of standard alcoholic drinks per week.")
        screen_h = st.slider("Screen Time (h/day)", 0.0, 16.0, 6.0, step=0.5, help="Hours spent looking at screens outside of active physical work.")
        smoking  = st.selectbox("Smoking Status", ["Never", "Former", "Current"], help="Current relationship with tobacco.")

        st.markdown("---")
        submit = st.button("Generate My Report", width="stretch")
        if submit: st.session_state.patient_submitted = True
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Back to Home", key="pat_back"): back_fn()

    bmi   = weight / ((height / 100) ** 2)
    risk  = estimate_risk(age, bmi, hba1c, glucose, sbp, family, hypert, smoking, activity, diet)
    stage, stage_color, stage_level = classify(hba1c, glucose)
    ws_label, ws_color = weight_status(bmi)
    ls_score = lifestyle_score(diet, activity, sleep, alcohol, smoking)
    grp      = age_group(age)

    h_title, h_back = st.columns([7, 1])
    with h_title:
        st.markdown('<div class="pat-title">🩺 TeaBetes — Health Explorer</div>', unsafe_allow_html=True)
        st.markdown('<div class="pat-sub">Adjust the controls in the sidebar — all charts update in real-time.</div>', unsafe_allow_html=True)
    with h_back:
        if st.button("← Home", key="pat_back_top"): back_fn()

    if not st.session_state.get("patient_submitted", False):
        st.info("Please fill out your health details in the sidebar menu on the left, then click 'Generate My Report' to view your personalized dashboard.")
        with st.expander("How to find your clinical values?"):
            st.markdown("* **HbA1c & Cholesterol:** Standard laboratory blood test requested by your GP.\n* **Blood Sugar:** Can be measured at home with a glucometer or at your pharmacy.\n* **Blood Pressure:** Can be checked using a home monitor, at a pharmacy, or during a clinic visit.")
        return

    col_status, col_gauge, col_lifestyle = st.columns([3, 2, 2])
    with col_status:
        st.markdown(f"""<div class="status-card" style="background:{stage_color}cc">
            <div class="status-lbl">Estimated Status</div><div class="status-val">{stage}</div><div class="status-desc">{STAGE_DESC[stage]}</div></div>""", unsafe_allow_html=True)
        st.markdown(f"""<div style="margin-top:14px"><span style="font-size:.72rem;opacity:.5;text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:2px">Weight Status</span>
            <div class="wstatus-badge" style="background:{ws_color}33;color:{ws_color};border:1px solid {ws_color}55">{ws_label} &nbsp;<span style="font-size:0.8em;opacity:.7">BMI {bmi:.1f}</span></div></div>""", unsafe_allow_html=True)
        pct_who = min(activity / 150 * 100, 100)
        act_color = C_GREEN if activity >= 150 else (C_YELLOW if activity >= 90 else C_RED)
        st.markdown(f"""<div style="margin-top:10px"><span style="font-size:.72rem;opacity:.5;text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:2px">Activity Level</span>
            <div class="wstatus-badge" style="background:{act_color}33;color:{act_color};border:1px solid {act_color}55">{activity} min/week &nbsp;<span style="font-size:0.8em;opacity:.7">{pct_who:.0f}% of goal</span></div></div>""", unsafe_allow_html=True)
    with col_gauge: chart_gauge(risk, stage_color)
    with col_lifestyle: chart_lifestyle_gauge(ls_score)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Your Values</div>', unsafe_allow_html=True)
    m1,m2,m3,m4,m5,m6 = st.columns(6)
    with m1: pill("HbA1c", f"{hba1c:.1f}%", "< 5.7% normal", tone=zone_color(zone_hba1c(hba1c)))
    with m2: pill("Fasting Sugar", f"{glucose}", "70-100 mg/dL", tone=zone_color(zone_glucose(glucose)))
    with m3: pill("BMI", f"{bmi:.1f}", "18.5-24.9 ideal", tone=zone_color(zone_bmi(bmi)))
    with m4: pill("Systolic BP", f"{sbp}", "< 120 mmHg", tone=zone_color(zone_sbp(sbp)))
    with m5: pill("Cholesterol", f"{chol}", "< 200 mg/dL", tone=zone_color(zone_chol(chol)))
    with m6: pill("Age", f"{age}", f"Group: {grp}", tone=C_WARM)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Activity & Sedentary Behaviour</div>', unsafe_allow_html=True)
    ra1, ra2 = st.columns([3, 2])
    with ra1: chart_activity_glucose(df, activity, glucose)
    with ra2: chart_sedentary_gauge(screen_h, activity)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Diet & Activity vs Reference</div>', unsafe_allow_html=True)
    chart_activity_diet_bar(activity, diet, df)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Your Risk & Lifestyle Context</div>', unsafe_allow_html=True)
    rg1, rg2 = st.columns([3, 2])
    with rg1: chart_risk_vs_age_group(df, age, risk)
    with rg2: chart_radar_lifestyle(diet, activity, sleep, alcohol, smoking)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Body Mass & Sleep Impact</div>', unsafe_allow_html=True)
    rn1, rn2 = st.columns(2)
    with rn1: chart_bmi_percentile(bmi, df)
    with rn2: chart_sleep_risk(sleep, risk, df)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Personalised Recommendations</div>', unsafe_allow_html=True)
    tips_data = get_tips(activity, diet, sleep, smoking, alcohol, bmi, risk, hba1c, sbp, chol)
    for text, is_good in tips_data: tip(text, good=is_good)

    st.markdown("<br><small style='opacity:.28'>Indicative tool — does not replace professional medical advice.</small>", unsafe_allow_html=True)