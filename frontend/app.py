import streamlit as st
import requests
import plotly.graph_objects as go
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

def fetch_history():
    try:
        res = requests.get(f"{API_BASE_URL}/history")
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
        st.session_state['demo_tx'] = {"Amount": 149.62, "Time": 1000.0, "V1": -1.3598, "V2": -0.0727, "V3": 2.5363, "V4": 1.3781, "V5": -0.3383, "V14": -0.3111}
        st.session_state['demo_id'] = "TX-DEMO-LOW"
    if col_d2.button("Load MEDIUM Risk Example", use_container_width=True):
        st.session_state['demo_tx'] = {"Amount": 1.0, "Time": 3600.0, "V1": 0.0073, "V2": 2.3651, "V3": -2.6002, "V4": 1.1116, "V5": 3.2764, "V14": -5.9679}
        st.session_state['demo_id'] = "TX-DEMO-MEDIUM"
    if col_d3.button("Load HIGH Risk Example", use_container_width=True):
        st.session_state['demo_tx'] = {"Amount": 0.0, "Time": 45000.0, "V1": -2.3122, "V2": 1.9519, "V3": -1.6098, "V4": 3.9979, "V5": -0.5221, "V14": -4.2892}
        st.session_state['demo_id'] = "TX-DEMO-HIGH"
        
    st.caption("Demo transaction — generated from available dataset features")
    
    demo_tx = st.session_state.get('demo_tx', {})
    demo_id = st.session_state.get('demo_id', "TX-1001")
    
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        with col1:
            tx_id = st.text_input("Transaction ID", value=demo_id)
            amount = st.number_input("Amount ($)", min_value=0.0, value=demo_tx.get("Amount", 150.00), step=10.0)
        with col2:
            time_sec = st.number_input("Time (seconds from start)", min_value=0.0, value=demo_tx.get("Time", 3600.0), step=100.0)
        
        st.markdown("#### PCA Features (V1 - V28)")
        st.caption("Since the model expects V1-V28, you can input key features below (the rest will default to 0).")
        
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            v1 = st.number_input("V1", value=demo_tx.get("V1", -1.359))
            v2 = st.number_input("V2", value=demo_tx.get("V2", -0.072))
        with col_v2:
            v3 = st.number_input("V3", value=demo_tx.get("V3", 2.536))
            v4 = st.number_input("V4", value=demo_tx.get("V4", 1.378))
        with col_v3:
            v5 = st.number_input("V5", value=demo_tx.get("V5", -0.338))
            v14 = st.number_input("V14", value=demo_tx.get("V14", -0.287))
            
            submit = st.form_submit_button("Analyze Transaction", use_container_width=True)
            
        if submit:
            # Start with the demo tx as a base to preserve all 28 features
            payload = dict(demo_tx)
            
            # Update with whatever the user actually typed in the visible boxes
            payload.update({
                "transaction_id": tx_id,
                "Amount": amount,
                "Time": time_sec,
                "V1": v1, "V2": v2, "V3": v3, "V4": v4, "V5": v5, "V14": v14
            })
            # Save to session state so Investigate button has access to it
            st.session_state['last_payload'] = payload
            st.session_state['last_result'] = None
            st.session_state['investigation_result'] = None
            
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
        
        # Add Investigate Button
        if st.button("Investigate Risk", type="primary"):
            with st.spinner("Generating AI Investigation Report..."):
                try:
                    res = requests.post(f"{API_BASE_URL}/investigate", json=st.session_state['last_payload'])
                    if res.status_code == 200:
                        st.session_state['investigation_result'] = res.json()
                    else:
                        st.error("Failed to generate investigation report.")
                except requests.exceptions.RequestException:
                    st.error("Failed to connect to the backend API.")
                    
    # Display Investigation if available
    if st.session_state.get('investigation_result'):
        display_investigation(st.session_state['investigation_result'])

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
    st.subheader(f"Risk Assessment: {result['transaction_id']}")
    
    score = result['risk_score']
    level = result['risk_level']
    action = result['recommended_action']
    prob = result['risk_probability']
    factors = result['risk_factors']
    
    color_map = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
    level_color = color_map.get(level, "black")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"### RISK SCORE")
        st.markdown(f"<div class='risk-score' style='color:{level_color};'>{score} / 100</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"### RISK LEVEL")
        st.markdown(f"<h2 style='color:{level_color};'>{level}</h2>", unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"### RECOMMENDED ACTION")
        st.markdown(f"<h2>{action.replace('_', ' ')}</h2>", unsafe_allow_html=True)
        
    st.markdown(f"**Fraud Probability:** {prob:.2%}")
    st.markdown(f"**Model Used:** {result['model_name']} (v{result['model_version']})")
    
    # Plotly Gauge
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
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
                'value': score
            }
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Risk Factors Identified")
    if factors:
        for factor in factors:
            st.markdown(f"- {factor}")
    else:
        st.write("No major risk factors identified.")

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

def main():
    st.title("AI Payment Risk Manager")
    
    backend_online, model_ready = check_backend_health()
    eval_data = load_evaluation_metrics()
    
    render_sidebar(backend_online, model_ready, eval_data)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Analysis", "Analytics", "Model Performance", "History"])
    
    with tab1:
        render_analysis_tab(backend_online, model_ready)
    
    with tab2:
        render_analytics_tab()
        
    with tab3:
        render_model_performance_tab(eval_data)
        
    with tab4:
        render_history_tab()

if __name__ == "__main__":
    main()
