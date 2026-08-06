import os
import streamlit as st
import requests

# Set page configuration
st.set_page_config(page_title="Financial Fraud Detection", layout="centered")

# Default API URL, can be overridden by environment variable for Docker
API_URL = os.getenv("API_URL", "http://localhost:8000/predict")

st.title("🛡️ Financial Fraud Detection System")
st.markdown("Enter a transaction ID below to scan for anomalous behavior using our Graph Neural Network (GNN).")

# Input field
transaction_id = st.text_input("Transaction ID", placeholder="e.g., TX-1234567890")

if st.button("Scan Transaction", type="primary"):
    if not transaction_id.strip():
        st.warning("Please enter a valid Transaction ID.")
    else:
        with st.spinner("Analyzing transaction context..."):
            try:
                # Make a request to the FastAPI backend
                payload = {"transaction_id": transaction_id.strip()}
                response = requests.post(API_URL, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    risk_score = data.get("risk_score", 0.0)
                    is_flagged = data.get("is_flagged", False)
                    sar_report = data.get("sar_report")
                    
                    st.subheader("Analysis Results")
                    
                    # Display the risk score
                    st.metric(label="GNN Risk Score", value=f"{risk_score:.2f}")
                    # Clamp progress between 0.0 and 1.0 just in case
                    st.progress(min(max(risk_score, 0.0), 1.0))
                    
                    if is_flagged:
                        st.error("🚨 **HIGH RISK TRANSACTION DETECTED** 🚨")
                        st.markdown("### Suspicious Activity Report (SAR)")
                        if sar_report:
                            st.info(sar_report)
                        else:
                            st.warning("No SAR report generated.")
                    else:
                        st.success("✅ **Transaction Safe**: No significant anomalies detected.")
                        
                elif response.status_code == 404:
                    st.error("Transaction not found. Please check the ID and try again.")
                else:
                    st.error(f"API Error {response.status_code}: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error(f"Failed to connect to the backend API at `{API_URL}`. Make sure the API is running.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
