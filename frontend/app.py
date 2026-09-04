import plotly.graph_objects as go
import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import json
import os

API_BASE_URL = "http://localhost:8000/api/v1/risk"

st.set_page_config(
    page_title="AI Payment Risk Manager",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean fintech UI
st.markdown("""
<style>
    .risk-score { font-size: 3rem; font-weight: bold; }
    .risk-low { color: #28a745; }
    .risk-medium { color: #ffc107; }
    .risk-high { color: #dc3545; }
    .metric-card { background-color: #f8f9fa; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    [data-testid="stSidebar"] { background-color: #f1f3f5; }
</style>
""", unsafe_allow_html=True)

def check_backend_health():
    try:
        res = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if res.status_code == 200:
            return True, True
        elif res.status_code == 503:
            return True, False
    except requests.exceptions.RequestException:
        pass
    return False, False

def load_evaluation_metrics():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "model", "evaluation.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def fetch_history(limit=50):
    try:
        res = requests.get(f"{API_BASE_URL}/history", params={"limit": limit})
        if res.status_code == 200:
            return res.json()
    except requests.exceptions.RequestException:
        pass
    return []

def fetch_analytics():
    try:
        res = requests.get(f"{API_BASE_URL}/analytics")
        if res.status_code == 200:
            return res.json()
    except requests.exceptions.RequestException:
        pass
    return None

def render_sidebar(backend_online, model_ready, eval_data):
    with st.sidebar:
        st.title("🛡️ AI Risk Manager")
        st.write("Intelligent Transaction Risk Assessment")
        
        st.markdown("---")
        st.subheader("System Status")
        st.markdown(f"**Backend:** {'🟢 ONLINE' if backend_online else '🔴 OFFLINE'}")
        st.markdown(f"**Model:** {'🟢 READY' if model_ready else '🔴 UNAVAILABLE'}")
        
        if eval_data:
            st.markdown(f"**Current Model:** {eval_data.get('model_name', 'Unknown')} v{eval_data.get('model_version', '1.0')}")
            
        st.markdown("---")
        st.subheader("Risk Policy")
        st.markdown("""
        * **LOW** (0 - 30) 🟢
          → APPROVE
        * **MEDIUM** (31 - 70) 🟡
          → ADDITIONAL VERIFICATION
        * **HIGH** (71 - 100) 🔴
          → FLAG FOR REVIEW
        """)
        
        st.caption("These thresholds are configurable prototype risk policies and do not represent Razorpay's production fraud rules.")
        
        st.markdown("---")
        st.caption("Fintech Buildathon - AI Risk Manager Track")

def load_demo(level):
    import os, json
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_transactions.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            if level in data:
                st.session_state['demo_tx'] = data[level]
                st.session_state['demo_id'] = f"TX-DEMO-{level}"
                st.session_state['demo_level'] = level
                # Increment form_key to force UI refresh of inputs
                st.session_state['form_key'] = st.session_state.get('form_key', 0) + 1

def render_analysis_tab(backend_online, model_ready):
    st.header("Transaction Analysis")
    
    if not backend_online:
        st.error("Risk analysis service is currently unavailable. Please start the FastAPI backend.")
        return
        
    if not model_ready:
        st.error("Risk analysis service is online, but the ML model is unavailable. Please ensure the model is trained.")
        return
        
    st.write("Enter transaction details to assess fraud risk.")
    
    st.markdown("### Demo Transactions")
    col_d1, col_d2, col_d3 = st.columns(3)
    if col_d1.button("Load LOW Risk Example", use_container_width=True):
        load_demo("LOW")
    if col_d2.button("Load MEDIUM Risk Example", use_container_width=True):
        load_demo("MEDIUM")
    if col_d3.button("Load HIGH Risk Example", use_container_width=True):
        load_demo("HIGH")
        
    st.caption("Demo transaction — generated from available dataset features")
    
    demo_tx = st.session_state.get('demo_tx', {})
    demo_id = st.session_state.get('demo_id', "TX-1001")
    demo_level = st.session_state.get('demo_level', None)
    
    if demo_level:
        if demo_level == "LOW":
            st.info("Demo Source: Real dataset transaction - Class 0")
        elif demo_level == "MEDIUM":
            st.warning("Demo Source: Real dataset transaction - model probability ~0.35 - 0.70")
        elif demo_level == "HIGH":
            st.error("Demo Source: Real dataset transaction - Class 1 / high model probability")
            
    # Use a unique key for the form elements to force them to update when a demo is loaded
    # We add a counter to session state to recreate inputs if the user clicks a demo button
    if 'form_key' not in st.session_state:
        st.session_state['form_key'] = 0
        
    # Whenever a demo button is clicked, Streamlit reruns. If demo_id changed, we should reflect it.
    
    with st.form("transaction_form"):
        fk = st.session_state.get('form_key', 0)
        col1, col2 = st.columns(2)
        with col1:
            tx_id = st.text_input("Transaction ID", value=demo_id, key=f"tx_{fk}")
            cust_id = st.text_input("Customer ID", value="CUST-DEMO", key=f"cust_{fk}")
            amount = st.number_input("Amount ($)", min_value=0.0, value=float(demo_tx.get("Amount", 150.00)), step=10.0, key=f"amt_{fk}")
            payment_id = st.text_input("Payment Account ID", value="", key=f"pay_{fk}")
        with col2:
            time_sec = st.number_input("Time (seconds from start)", min_value=0.0, value=float(demo_tx.get("Time", 3600.0)), step=100.0, key=f"time_{fk}")
            device_id = st.text_input("Device ID", value="", key=f"dev_{fk}")
            ip_address = st.text_input("IP Address", value="", key=f"ip_{fk}")
        
        st.markdown("#### PCA Features (V1 - V28)")
        st.caption("Since the model expects V1-V28, you can input key features below. The full 28 features are pre-loaded in the background for demo transactions.")
        
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            v1 = st.number_input("V1", value=float(demo_tx.get("V1", -1.359)), key=f"v1_{fk}")
            v2 = st.number_input("V2", value=float(demo_tx.get("V2", -0.072)), key=f"v2_{fk}")
        with col_v2:
            v3 = st.number_input("V3", value=float(demo_tx.get("V3", 2.536)), key=f"v3_{fk}")
            v4 = st.number_input("V4", value=float(demo_tx.get("V4", 1.378)), key=f"v4_{fk}")
        with col_v3:
            v5 = st.number_input("V5", value=float(demo_tx.get("V5", -0.338)), key=f"v5_{fk}")
            v14 = st.number_input("V14", value=float(demo_tx.get("V14", -0.287)), key=f"v14_{fk}")
            
        submit = st.form_submit_button("Analyze Transaction", type="primary", use_container_width=True)
            
        if submit:
            # Start with the demo tx as a base to preserve all 28 features
            payload = dict(demo_tx)
            
            # Update with whatever the user actually typed in the visible boxes
            payload.update({
                "transaction_id": tx_id,
                "customer_id": cust_id,
                "device_id": device_id if device_id else None,
                "ip_address": ip_address if ip_address else None,
                "payment_account_id": payment_id if payment_id else None,
                "Amount": amount,
                "Time": time_sec,
                "V1": v1, "V2": v2, "V3": v3, "V4": v4, "V5": v5, "V14": v14
            })
            # Save to session state so Investigate button has access to it
            st.session_state['last_payload'] = payload
            st.session_state['last_result'] = None
            st.session_state['investigation_result'] = None
            st.session_state['explanation_result'] = None
            
            with st.spinner("Analyzing transaction..."):
                try:
                    res = requests.post(f"{API_BASE_URL}/analyze", json=payload)
                    if res.status_code == 200:
                        st.session_state['last_result'] = res.json()
                    else:
                        st.error(f"Validation Error: {res.json().get('detail', 'Unknown error')}")
                except requests.exceptions.RequestException:
                    st.error("Failed to connect to the backend API.")
                    
    # Display results if available
    if st.session_state.get('last_result'):
        display_risk_result(st.session_state['last_result'])
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Investigate Risk", type="primary", use_container_width=True):
                with st.spinner("Generating AI Investigation Report..."):
                    try:
                        res = requests.post(f"{API_BASE_URL}/investigate", json=st.session_state['last_payload'])
                        if res.status_code == 200:
                            st.session_state['investigation_result'] = res.json()
                        else:
                            st.error("Failed to generate investigation report.")
                    except requests.exceptions.RequestException:
                        st.error("Failed to connect to the backend API.")
        
        with col_btn2:
            if st.button("Explain Risk", use_container_width=True):
                with st.spinner("Calculating SHAP explanations..."):
                    try:
                        res = requests.post(f"{API_BASE_URL}/explain", json=st.session_state['last_payload'])
                        if res.status_code == 200:
                            st.session_state['explanation_result'] = res.json()
                        else:
                            st.error("Failed to generate explanation.")
                    except requests.exceptions.RequestException:
                        st.error("Failed to connect to the backend API.")
                        
    # Display Explanation if available
    if st.session_state.get('explanation_result'):
        display_explanation(st.session_state['explanation_result'])
                    
    # Display Investigation if available
    if st.session_state.get('investigation_result'):
        display_investigation(st.session_state['investigation_result'])

    st.markdown("---")
    st.markdown("### Velocity Attack Simulation")
    st.caption("Simulates a sequence of rapidly escalating transactions to demonstrate the Velocity Engine.")
    if st.button("Run Velocity Attack Simulation"):
        import time
        sim_txs = [
            {"amount": 500.0, "delay": 0},
            {"amount": 700.0, "delay": 0},
            {"amount": 900.0, "delay": 0},
            {"amount": 2000.0, "delay": 0},
            {"amount": 5000.0, "delay": 0},
            {"amount": 10000.0, "delay": 0}
        ]
        sim_cust = "CUST-SIM-ATTACK"
        
        st.write(f"Simulating attack for customer: {sim_cust}")
        progress = st.progress(0)
        
        last_sim_res = None
        for idx, tx_data in enumerate(sim_txs):
            st.write(f"Sending TX {idx+1}: ...")
            sim_payload = dict(demo_tx) # use base demo
            sim_payload.update({
                "transaction_id": f"TX-SIM-{int(time.time()*1000)}-{idx}",
                "customer_id": sim_cust,
                "Amount": tx_data['amount'],
                "Time": 3600.0
            })
            
            try:
                res = requests.post(f"{API_BASE_URL}/analyze", json=sim_payload)
                if res.status_code == 200:
                    last_sim_res = res.json()
                    st.write(f"Result: ML Risk={last_sim_res.get('risk_level')}, Velocity Level={last_sim_res.get('velocity_level')}, Final Risk={last_sim_res.get('risk_level')}")
                else:
                    st.error(f"Error on TX {idx+1}")
            except Exception as e:
                st.error(f"Simulation failed: {e}")
                
            progress.progress((idx + 1) / len(sim_txs))
            time.sleep(0.5)
            
        if last_sim_res:
            st.success("Simulation Complete! Latest transaction result loaded.")
            st.session_state['last_payload'] = sim_payload
            st.session_state['last_result'] = last_sim_res
            st.rerun()


def display_explanation(explanation):
    st.markdown("---")
    st.markdown("## Why did the model make this decision?")
    
    st.info("SHAP explains how model features influenced the prediction. It does not prove that a transaction is fraudulent.")
    st.caption("V1-V28 are anonymized PCA-transformed features and do not have direct human-readable meanings.")
    
    st.markdown("### Top Risk Contributors")
    
    factors = explanation.get("top_contributors", [])
    if not factors:
        st.write("No strong contributors found.")
        return
        
    # Text display
    for i, factor in enumerate(factors):
        st.markdown(f"**{i+1}. {factor['feature_name']}**")
        st.markdown(f"*{factor['contribution'].replace('_', ' ').capitalize()}*")
        st.markdown(f"SHAP contribution: **{factor['shap_value']:+.2f}** (Feature value: {factor['feature_value']:.2f})")
        st.write("")
        
    # Plotly Chart
    names = [f['feature_name'] for f in factors][::-1]
    vals = [f['shap_value'] for f in factors][::-1]
    
    
    colors = ['#ff6b6b' if v > 0 else '#4ecdc4' for v in vals]
    
    fig = go.Figure(go.Bar(
        x=vals,
        y=names,
        orientation='h',
        marker_color=colors
    ))
    
    fig.update_layout(
        title="Top Model Contributors",
        xaxis_title="SHAP Value (Impact on Prediction)",
        yaxis_title="Feature",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_explanation(explanation):
    st.markdown("---")
    st.markdown("## Why did the model make this decision?")
    
    st.info("SHAP explains how model features influenced the prediction. It does not prove that a transaction is fraudulent.")
    st.caption("V1-V28 are anonymized PCA-transformed features and do not have direct human-readable meanings.")
    
    st.markdown("### Top Risk Contributors")
    
    factors = explanation.get("top_contributors", [])
    if not factors:
        st.write("No strong contributors found.")
        return
        
    # Text display
    for i, factor in enumerate(factors):
        st.markdown(f"**{i+1}. {factor['feature_name']}**")
        st.markdown(f"*{factor['contribution'].replace('_', ' ').capitalize()}*")
        st.markdown(f"SHAP contribution: **{factor['shap_value']:+.2f}** (Feature value: {factor['feature_value']:.2f})")
        st.write("")
        
    # Plotly Chart
    names = [f['feature_name'] for f in factors][::-1]
    vals = [f['shap_value'] for f in factors][::-1]
    
    
    colors = ['#ff6b6b' if v > 0 else '#4ecdc4' for v in vals]
    
    fig = go.Figure(go.Bar(
        x=vals,
        y=names,
        orientation='h',
        marker_color=colors
    ))
    
    fig.update_layout(
        title="Top Model Contributors",
        xaxis_title="SHAP Value (Impact on Prediction)",
        yaxis_title="Feature",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_investigation(report):
    st.markdown("---")
    st.markdown("## 🧠 AI Risk Investigation")
    
    st.markdown(f"**Risk Score:** {report['risk_score']} / 100")
    st.markdown(f"**Risk Level:** {report['risk_level']}")
    st.markdown(f"**Assessment:** {report['assessment']}")
    
    st.markdown("**Key Findings:**")
    for finding in report['key_findings']:
        st.markdown(f"- {finding}")
        
    st.markdown(f"**Recommended Action:** {report['recommended_action'].replace('_', ' ')}")
    
    st.info(f"**Confidence Note:** {report['confidence_note']}")
    st.caption(f"**Disclaimer:** {report['disclaimer']}")

def display_risk_result(result):
    st.markdown("---")
    st.subheader(f"Risk Assessment: {result.get('transaction_id', 'UNKNOWN')}")
    
    color_map = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red", "UNKNOWN": "gray", None: "gray"}
    
    # --------------------------------
    # MODEL RISK
    # --------------------------------
    st.markdown("### --------------------------------")
    st.markdown("### MODEL RISK")
    st.markdown("### --------------------------------")
    
    m_prob = result.get('risk_probability')
    m_prob = float(m_prob) if m_prob is not None else 0.0
    m_score = result.get('risk_score')
    m_score = int(m_score) if m_score is not None else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Probability:** {m_prob:.2%}")
    with col2:
        st.markdown(f"**ML Score:** {m_score}")
        
    # --------------------------------
    # VELOCITY RISK
    # --------------------------------
    st.markdown("### --------------------------------")
    st.markdown("### VELOCITY RISK")
    st.markdown("### --------------------------------")
    
    v_score = result.get('velocity_score')
    v_level = result.get('velocity_level')
    
    if v_score is not None and v_level is not None:
        v_color = color_map.get(v_level, "gray")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Velocity Score:** {v_score}")
        with c2:
            st.markdown(f"**Velocity Level:** <span style='color:{v_color};'>{v_level}</span>", unsafe_allow_html=True)
            
        v_mets = result.get('velocity_metrics') or {}
        if v_mets:
            st.markdown("**Transactions:**")
            st.markdown(f"- 1 min: {v_mets.get('transactions_1m', 0)}")
            st.markdown(f"- 5 min: {v_mets.get('transactions_5m', 0)}")
            st.markdown(f"- 15 min: {v_mets.get('transactions_15m', 0)}")
            st.markdown(f"- 1 hour: {v_mets.get('transactions_1h', 0)}")
            
            fig = go.Figure(data=[
                go.Bar(name='Transactions', x=['1m', '5m', '15m', '1h'], y=[v_mets.get('transactions_1m',0), v_mets.get('transactions_5m',0), v_mets.get('transactions_15m',0), v_mets.get('transactions_1h',0)])
            ])
            fig.update_layout(title='Transaction Frequency over Time Windows', height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Velocity Engine Unavailable or Disabled.")
        
    # --------------------------------
    # GRAPH RISK
    # --------------------------------
    st.markdown("### --------------------------------")
    st.markdown("### GRAPH RISK (Fraud Rings)")
    st.markdown("### --------------------------------")
    
    g_score = result.get('graph_score')
    g_level = result.get('graph_risk_level')
    
    if g_score is not None and g_level is not None:
        g_color = color_map.get(g_level, "gray")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Graph Score:** {g_score}")
        with c2:
            st.markdown(f"**Graph Level:** <span style='color:{g_color};'>{g_level}</span>", unsafe_allow_html=True)
            
        if result.get('cluster_id'):
            st.markdown(f"**Cluster ID:** {result.get('cluster_id')}")
            
        g_sigs = result.get('graph_signals') or []
        if g_sigs:
            for sig in g_sigs:
                st.markdown(f"- ⚠️ **{sig.get('type', 'SIGNAL')}** [{sig.get('severity', 'INFO')}]: {sig.get('description', '')}")
    else:
        st.write("Graph Engine Unavailable or Disabled.")
        
    # --------------------------------
    # FINAL DECISION
    # --------------------------------
    st.markdown("### --------------------------------")
    st.markdown("### FINAL DECISION")
    st.markdown("### --------------------------------")
    
    f_score = result.get('final_risk_score')
    if f_score is None: 
        f_score = m_score
    f_score = int(f_score)
    f_level = result.get('risk_level', 'UNKNOWN')
    f_action = result.get('recommended_action', 'REVIEW')
    f_color = color_map.get(f_level, "gray")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.markdown(f"### SCORE: {f_score}")
    with col_f2:
        st.markdown(f"### RISK: <span style='color:{f_color};'>{f_level}</span>", unsafe_allow_html=True)
    with col_f3:
        st.markdown(f"### ACTION: {f_action.replace('_', ' ')}")
        
    mode = result.get('decision_mode', 'NORMAL')
    if mode == "CIRCUIT_BREAKER":
        st.error("CIRCUIT BREAKER ACTIVATED")
    elif mode == "RULE_OVERRIDE":
        st.warning("RULE OVERRIDE ACTIVATED")
        
    st.markdown(f"**Decision Mode:** {mode}")
    st.markdown(f"**Reason:** {result.get('decision_reason', '')}")
    
    rules = result.get('triggered_rules') or []
    if rules:
        st.markdown("**Triggered Rules:**")
        for r in rules:
            st.markdown(f"- {r.get('rule_id')}: {r.get('reason')}")
            
    w_ml = result.get('ml_weight')
    w_ml = float(w_ml) if w_ml is not None else 0.5
    w_vel = result.get('velocity_weight')
    w_vel = float(w_vel) if w_vel is not None else 0.25
    w_gr = result.get('graph_weight')
    w_gr = float(w_gr) if w_gr is not None else 0.25
    st.caption(f"Weights Used - ML: {w_ml:.0%} | Velocity: {w_vel:.0%} | Graph: {w_gr:.0%}")
    st.markdown("### --------------------------------")

    # Plotly Gauge
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = f_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Risk Score Meter"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "black"},
            'steps': [
                {'range': [0, 30], 'color': "lightgreen"},
                {'range': [30, 70], 'color': "navajowhite"},
                {'range': [70, 100], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': f_score
            }
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Risk Factors Identified")
    factors = result.get("risk_factors") or []
    if factors:
        for factor in factors:
            st.markdown(f"- {factor}")
    else:
        st.write("No major risk factors identified.")
        
    with st.expander("Debug Transaction Details"):
        payload = st.session_state.get('last_payload', {})
        received_keys = [k for k in payload.keys() if k not in ('transaction_id',)]
        model_expected = ['Amount', 'Time'] + [f'V{i}' for i in range(1, 29)]
        missing = [f for f in model_expected if f not in received_keys]
        extra = [f for f in received_keys if f not in model_expected]
        
        st.write(f"**Model expected features:** {len(model_expected)}")
        st.write(f"**Received features:** {len(received_keys)}")
        st.write(f"**Missing features:** {missing}")
        st.write(f"**Extra features:** {extra}")
        st.write(f"**Model probability:** {m_prob}")
        st.write(f"**Risk score:** {m_score}")

def render_analytics_tab():
    st.header("Analytics")
    stats = fetch_analytics()
    
    if not stats or stats.get('total_transactions', 0) == 0:
        st.info("No transaction history available for analytics.")
        return
        
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transactions", stats['total_transactions'])
    col2.metric("Average Amount", f"${stats['average_amount']:.2f}")
    col3.metric("Avg Risk Score", f"{stats['average_risk_score']:.1f}")
    
    st.markdown("---")
    
    levels = stats.get('levels', {})
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Risk Level Distribution
        labels = list(levels.keys())
        values = list(levels.values())
        colors = ['lightgreen' if l == 'LOW' else 'navajowhite' if l == 'MEDIUM' else 'lightcoral' for l in labels]
        
        fig = px.pie(names=labels, values=values, title="Risk Level Distribution", 
                     color=labels, color_discrete_map={'LOW':'#28a745', 'MEDIUM':'#ffc107', 'HIGH':'#dc3545'})
        st.plotly_chart(fig, use_container_width=True)
        
    with col_chart2:
        # We don't have enough data for a robust histogram unless we fetch history
        history = fetch_history(limit=500)
        if history:
            df = pd.DataFrame(history)
            fig2 = px.histogram(df, x="risk_score", nbins=20, title="Risk Score Distribution")
            st.plotly_chart(fig2, use_container_width=True)

def render_model_performance_tab(eval_data):
    st.header("Model Performance on Held-Out Test Set")
    
    if not eval_data:
        st.info("Model evaluation data not found. Please run the Stage 2 training pipeline.")
        return
        
    metrics = eval_data.get("metrics", {})
    cm = eval_data.get("confusion_matrix", {})
    
    st.markdown(f"**Model:** {eval_data.get('model_name', 'XGBoost')}")
    st.markdown(f"**Version:** {eval_data.get('model_version', '1.0')}")
    st.markdown("**Evaluation:** Held-Out Test Set")
    
    st.markdown("---")
    st.subheader("Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Precision", f"{metrics.get('Precision', 0):.4f}")
    col2.metric("Recall", f"{metrics.get('Recall', 0):.4f}")
    col3.metric("F1-Score", f"{metrics.get('F1-Score', 0):.4f}")
    col4.metric("ROC-AUC", f"{metrics.get('ROC-AUC', 0):.4f}")
    
    st.info("Recall measures the proportion of actual fraudulent transactions detected, while precision measures how many transactions flagged by the model were actually fraudulent in the evaluation set.")
    
    st.markdown("---")
    st.subheader("Confusion Matrix")
    
    cm_df = pd.DataFrame({
        "Predicted Legitimate": [cm.get('TN', 0), cm.get('FN', 0)],
        "Predicted Fraud": [cm.get('FP', 0), cm.get('TP', 0)]
    }, index=["Actual Legitimate", "Actual Fraud"])
    
    st.table(cm_df)

def render_history_tab():
    st.header("Transaction History")
    
    history = fetch_history()
    
    if not history:
        st.info("No recent transactions found.")
        return
        
    df = pd.DataFrame(history)
    df = df[['timestamp', 'transaction_id', 'amount', 'risk_score', 'risk_level', 'recommended_action']]
    
    # Simple styling function for pandas
    def highlight_risk(val):
        color = '#28a745' if val == 'LOW' else '#ffc107' if val == 'MEDIUM' else '#dc3545' if val == 'HIGH' else 'black'
        return f'color: {color}'
        
    st.dataframe(df.style.map(highlight_risk, subset=['risk_level']), use_container_width=True)


def render_graph_tab(backend_online=True):
    st.header("Fraud Network")
    st.write("Visualizes relationships between customers, devices, IP addresses, payment accounts, and transactions to identify possible fraud rings.")
    
    if not backend_online:
        st.warning("Fraud Network data unavailable. Please make sure the backend is running.")
        return
        
    col1, col2 = st.columns(2)
    with col1:
        cust_search = st.text_input("Investigate Customer ID", value="CUST-DEMO")
        if st.button("Investigate Network"):
            with st.spinner("Fetching graph..."):
                try:
                    res = requests.get(f"{API_BASE_URL}/graph/customer/{cust_search}")
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state['graph_data'] = data
                    elif res.status_code == 503:
                        st.warning("Graph engine is disabled in backend configuration.")
                    else:
                        st.error("Graph engine returned an error.")
                except Exception as e:
                    st.error(f"Connection failed: {e}")
                    
    with col2:
        st.write("### Fraud Ring Simulation")
        st.write("Simulate a coordinated fraud attack using shared infrastructure.")
        sim_type = st.selectbox("Scenario", ["Shared Device", "Shared IP", "Shared Device & IP", "Shared Payment Account"])
        
        if st.button("Run Simulation", type="primary"):
            import time
            sim_custs = ["CUST-RING-1", "CUST-RING-2", "CUST-RING-3"]
            dev_id = "DEV-RING" if "Device" in sim_type else None
            ip_id = "10.0.0.99" if "IP" in sim_type else None
            pay_id = "ACCT-RING" if "Payment" in sim_type else None
            
            progress = st.progress(0)
            st.write(f"Executing {sim_type} simulation...")
            
            last_res = None
            for idx, cust in enumerate(sim_custs):
                payload = {
                    "transaction_id": f"TX-RING-{int(time.time()*1000)}",
                    "customer_id": cust,
                    "Amount": 1500.0,
                    "Time": 3600.0,
                    "device_id": dev_id,
                    "ip_address": ip_id,
                    "payment_account_id": pay_id,
                    # dummy ML fields
                    "V1": -1.0, "V2": 1.0, "V3": 1.0, "V4": 1.0, "V5": 1.0, "V14": -1.0
                }
                
                try:
                    res = requests.post(f"{API_BASE_URL}/analyze", json=payload)
                    if res.status_code == 200:
                        last_res = res.json()
                        st.write(f"Processed TX from {cust}. Graph Score: {last_res.get('graph_score')} ({last_res.get('graph_risk_level')})")
                except Exception:
                    st.error("API error")
                progress.progress((idx + 1) / len(sim_custs))
                
            st.success("Simulation Complete!")
            if last_res and last_res.get('cluster_id'):
                st.info(f"Detected Cluster: {last_res.get('cluster_id')}")
            
    st.markdown("---")
    
    if st.session_state.get('graph_data'):
        data = st.session_state['graph_data']
        if 'error' in data:
            st.error(data['error'])
            return
            
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        
        st.subheader(f"Network for {data.get('customer_id')}")
        st.write(f"Total Nodes: {len(nodes)} | Total Edges: {len(edges)}")
        
        if nodes and edges:
            import networkx as nx
            
            G = nx.Graph()
            for n in nodes:
                G.add_node(n['id'], label=n['label'], type=n['type'])
            for e in edges:
                G.add_edge(e['source'], e['target'], type=e['type'])
                
            pos = nx.spring_layout(G, seed=42)
            
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=1, color='#888'),
                hoverinfo='none',
                mode='lines')
                
            node_x = []
            node_y = []
            node_text = []
            node_color = []
            
            color_map = {
                'CUSTOMER': '#3498db',
                'TRANSACTION': '#2ecc71',
                'DEVICE': '#e74c3c',
                'IP': '#f1c40f',
                'PAYMENT_ACCOUNT': '#9b59b6'
            }
            
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                ntype = G.nodes[node].get('type', 'UNKNOWN')
                node_text.append(f"{ntype}: {node}")
                node_color.append(color_map.get(ntype, '#95a5a6'))
                
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=node_text,
                textposition="top center",
                marker=dict(
                    showscale=False,
                    color=node_color,
                    size=20,
                    line_width=2))
                    
            fig = go.Figure(data=[edge_trace, node_trace],
                         layout=go.Layout(
                            title="Interactive Fraud Graph",
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=20,l=5,r=5,t=40),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            )
            st.plotly_chart(fig, use_container_width=True)
        elif nodes:
            st.info(f"Entity node found ({len(nodes)} entity), but no shared relationships or connected fraud rings detected yet.")
        else:
            st.info("No entity relationships found for this customer.")
    else:
        st.info("No active graph network loaded. Enter a Customer ID above and click 'Investigate Network' or run a 'Fraud Ring Simulation' to visualize the entity graph.")

def render_decision_simulator():
    st.header("Decision Simulator")
    st.write("Test the deterministic decision engine rules, circuit breakers, and adaptive weighting.")
    
    preset = st.selectbox("Preset Scenarios", ["Manual", "NORMAL", "HIGH ML", "HIGH VELOCITY", "FRAUD RING", "MULTI-SIGNAL ATTACK"])
    
    if preset == "NORMAL":
        d_ml, d_v, d_g = 20, 10, 0
    elif preset == "HIGH ML":
        d_ml, d_v, d_g = 95, 10, 0
    elif preset == "HIGH VELOCITY":
        d_ml, d_v, d_g = 10, 85, 0
    elif preset == "FRAUD RING":
        d_ml, d_v, d_g = 10, 0, 75
    elif preset == "MULTI-SIGNAL ATTACK":
        d_ml, d_v, d_g = 65, 65, 65
    else:
        d_ml, d_v, d_g = 0, 0, 0
        
    col1, col2, col3 = st.columns(3)
    with col1:
        ml = st.slider("ML Score", 0, 100, d_ml)
    with col2:
        vel = st.slider("Velocity Score", 0, 100, d_v)
        vel_avail = st.checkbox("Velocity Available", value=True)
    with col3:
        grph = st.slider("Graph Score", 0, 100, d_g)
        grph_avail = st.checkbox("Graph Available", value=True)
        
    if st.button("Simulate Decision", type="primary"):
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from backend.services.decision_engine import decision_engine
        
        final_score, level, action, mode, rules, reason, w_ml, w_vel, w_grph = decision_engine.evaluate(
            ml, vel, vel_avail, grph, grph_avail
        )
        
        st.markdown("---")
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric("Final Score", final_score)
            st.metric("Risk Level", level)
            st.metric("Action", action)
        with col_res2:
            st.markdown(f"**Decision Mode:** {mode}")
            st.markdown(f"**Reason:** {reason}")
            if rules:
                st.markdown("**Triggered Rules:**")
                for r in rules:
                    st.error(f"{r['rule_id']} - {r['reason']}")
                    
            st.markdown(f"**Calculated Weights:** ML={w_ml:.2f}, Vel={w_vel:.2f}, Graph={w_grph:.2f}")

def inject_custom_css():
    st.markdown("""
        <style>
        /* Make sidebar dark */
        [data-testid="stSidebar"] {
            background-color: #0e1117 !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            background-color: #0e1117 !important;
        }
        /* Ensure text in sidebar is readable */
        [data-testid="stSidebar"] * {
            color: #fafafa;
        }
        /* Except for inputs which need their own styling */
        [data-testid="stSidebar"] input {
            color: #ffffff;
            background-color: #262730;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    inject_custom_css()
    st.title("AI Payment Risk Manager")
    
    backend_online, model_ready = check_backend_health()
    eval_data = load_evaluation_metrics()
    
    render_sidebar(backend_online, model_ready, eval_data)
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Analysis", "Analytics", "Model Performance", "History", "Fraud Network", "Decision Simulator"])
    
    with tab1:
        render_analysis_tab(backend_online, model_ready)
    
    with tab2:
        render_analytics_tab()
        
    with tab3:
        render_model_performance_tab(eval_data)
        
    with tab4:
        render_history_tab()

    with tab5:
        render_graph_tab(backend_online)

    with tab6:
        render_decision_simulator()

if __name__ == "__main__":
    main()

