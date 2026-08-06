import json
import redis
from kafka import KafkaConsumer

# Configuration
BOOTSTRAP_SERVERS = ['localhost:9092']
TOPIC_NAME = 'financial-transactions'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

def get_redis_client():
    """Connects to Redis in-memory database for graph state tracking."""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        r.ping()
        print(f"[+] Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return r
    except Exception as e:
        print(f"[-] Redis connection failed: {e}")
        return None

def process_transaction_event(event, r_client):
    """
    Parses incoming event payload, updates node relationships and transaction metrics in Redis.
    Creates graph edges: (Card -> Merchant) and (Card -> IP).
    """
    tx_id = event['transaction_id']
    card_id = event['card_id']
    merchant_id = event['merchant_id']
    ip_address = event['ip_address']
    amount = float(event['amount'])
    timestamp = event['timestamp']

    # 1. Store raw transaction object in Redis hash
    r_client.hset(f"tx:{tx_id}", mapping={
        "card_id": card_id,
        "merchant_id": merchant_id,
        "ip_address": ip_address,
        "amount": amount,
        "timestamp": timestamp,
        "is_suspicious_flag": str(event.get('is_suspicious_flag', False))
    })

    # 2. Update Graph Degree & Fan-out Metrics in Redis sets
    # Track unique merchants visited by this card
    r_client.sadd(f"card:{card_id}:merchants", merchant_id)
    # Track unique IPs used by this card
    r_client.sadd(f"card:{card_id}:ips", ip_address)
    # Track cards sharing this IP address (potential fraud ring connection)
    r_client.sadd(f"ip:{ip_address}:cards", card_id)

    # 3. Calculate 1-hop graph structural stats
    merchant_count = r_client.scard(f"card:{card_id}:merchants")
    ip_shared_cards = r_client.scard(f"ip:{ip_address}:cards")

    return {
        "tx_id": tx_id,
        "card_id": card_id,
        "merchant_count": merchant_count,
        "ip_shared_cards": ip_shared_cards,
        "amount": amount
    }

def main():
    r_client = get_redis_client()
    if not r_client:
        return

    try:
        consumer = KafkaConsumer(
            TOPIC_NAME,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='fraud-graph-builder-group'
        )
        print(f"[*] Consumer listening on topic '{TOPIC_NAME}'... (Press Ctrl+C to stop)")

        for message in consumer:
            event = message.value
            metrics = process_transaction_event(event, r_client)
            
            # Highlight high-degree graph nodes or burst anomalies
            anomaly_alert = "?? [HIGH GRAPH RISK]" if (metrics['ip_shared_cards'] > 1 or metrics['amount'] > 1000) else "?? [GRAPH UPDATED]"
            print(f"{anomaly_alert} Tx: {metrics['tx_id']} | Card: {metrics['card_id']} | "
                  f"Linked Merchants: {metrics['merchant_count']} | Shared IP Cards: {metrics['ip_shared_cards']}")

    except KeyboardInterrupt:
        print("\n[!] Stopping consumer service...")

if __name__ == "__main__":
    main()
