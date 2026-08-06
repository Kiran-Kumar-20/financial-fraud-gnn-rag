import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

# Configuration
BOOTSTRAP_SERVERS = ['localhost:9092']
TOPIC_NAME = 'financial-transactions'

def get_kafka_producer():
    """Initializes and returns a Kafka Producer instance with JSON serialization."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3
        )
        print(f"[+] Connected to Redpanda broker at {BOOTSTRAP_SERVERS[0]}")
        return producer
    except Exception as e:
        print(f"[-] Failed to connect to Redpanda: {e}")
        return None

def generate_transaction(is_fraud_burst=False):
    """
    Generates a realistic transaction payload.
    If is_fraud_burst is True, simulates a coordinated attack across shared IP/Merchants.
    """
    if is_fraud_burst:
        # High velocity burst pattern: suspicious IP & merchant reuse
        card_id = f"card_{random.randint(900, 999)}"
        merchant_id = "merchant_fraud_ring_99"
        ip_address = "192.168.1.66"  # Shared flagged IP
        amount = round(random.uniform(850.0, 5000.0), 2)
        transaction_type = "online_transfer"
    else:
        # Standard customer behavioral flow
        card_id = f"card_{random.randint(100, 500)}"
        merchant_id = f"merchant_{random.randint(1, 50)}"
        ip_address = f"10.0.{random.randint(1, 10)}.{random.randint(1, 255)}"
        amount = round(random.uniform(5.0, 300.0), 2)
        transaction_type = random.choice(["pos_swipe", "online_checkout", "atm_withdrawal"])

    payload = {
        "transaction_id": f"tx_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
        "card_id": card_id,
        "merchant_id": merchant_id,
        "ip_address": ip_address,
        "amount": amount,
        "transaction_type": transaction_type,
        "timestamp": datetime.utcnow().isoformat(),
        "is_suspicious_flag": is_fraud_burst
    }
    return payload

def main():
    producer = get_kafka_producer()
    if not producer:
        return

    print(f"[*] Starting live transaction stream to topic '{TOPIC_NAME}'... (Press Ctrl+C to stop)")
    tx_count = 0

    try:
        while True:
            # Simulate occasional fraud burst every ~15 transactions
            simulate_fraud = (tx_count % 15 == 0 and tx_count > 0)
            
            payload = generate_transaction(is_fraud_burst=simulate_fraud)
            producer.send(TOPIC_NAME, value=payload)
            producer.flush()
            
            tx_count += 1
            status = "?? [SUSPICIOUS BURST]" if simulate_fraud else "? [NORMAL]"
            print(f"{status} Tx #{tx_count} | ID: {payload['transaction_id']} | Card: {payload['card_id']} | Amount: ")
            
            # Stream interval
            time.sleep(0.8)

    except KeyboardInterrupt:
        print("\n[!] Stream stopped by user. Closing producer...")
        producer.close()

if __name__ == "__main__":
    main()
