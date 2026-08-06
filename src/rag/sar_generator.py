import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

class SARGenerator:
    def __init__(self):
        # Initialize the new Google GenAI SDK client
        # It automatically picks up GEMINI_API_KEY from the environment
        self.client = genai.Client()

    def generate_sar(self, transaction_id: str, merchant_count: int, shared_ips: int, gnn_risk_score: float) -> str:
        prompt = f"""
        Act as an expert financial compliance officer. Write a short, professional Suspicious Activity Report (SAR) narrative for the following transaction. 
        Explain why the transaction is considered high-risk based on the provided graph database metrics and the Graph Neural Network (GNN) risk score.
        
        Transaction Details:
        - Transaction ID: {transaction_id}
        - Unique merchants connected to this card: {merchant_count}
        - Number of distinct cards sharing this transaction's IP address: {shared_ips}
        - GNN Risk Score: {gnn_risk_score:.2f} (Scale 0.0 to 1.0, where >0.75 is flagged as suspicious)
        
        The report should be concise, professional, and focus on the structural anomalies indicated by the graph metrics. For example, explain how the high number of connected merchants or multiple cards sharing an IP might indicate card testing or a coordinated fraud ring.
        """
        
        response = self.client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
        )
        
        return response.text

if __name__ == '__main__':
    generator = SARGenerator()
    
    # Dummy high-risk data
    dummy_tx_id = "TX-9988776655"
    dummy_merchant_count = 145
    dummy_shared_ips = 18
    dummy_risk_score = 0.94
    
    print(f"Generating SAR for Transaction: {dummy_tx_id}...")
    try:
        sar_report = generator.generate_sar(
            transaction_id=dummy_tx_id,
            merchant_count=dummy_merchant_count,
            shared_ips=dummy_shared_ips,
            gnn_risk_score=dummy_risk_score
        )
        print("\n--- Suspicious Activity Report (SAR) ---")
        print(sar_report)
        print("----------------------------------------")
    except Exception as e:
        print(f"Error generating SAR: {e}")
