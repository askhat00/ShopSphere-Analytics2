import psycopg2
import threading
import random
import time

DSN = "postgresql://postgres:dream@localhost:5433/SphereShop"

def init_db():
    try:
        conn = psycopg2.connect(DSN)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_load (
                id SERIAL PRIMARY KEY,
                value TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Test table ready")
    except Exception as e:
        print("DB init error:", e)

def worker():
    while True:
        try:
            conn = psycopg2.connect(DSN)
            cur = conn.cursor()

            op = random.choice(["select", "insert", "delete"])

            if op == "select":
                cur.execute("SELECT COUNT(*) FROM orders;")
                cur.execute("SELECT AVG(payment_value) FROM order_payments;")

            elif op == "insert":
                n = random.randint(5, 50)
                values = [(str(random.random()),) for _ in range(n)]
                cur.executemany("INSERT INTO test_load (value) VALUES (%s);", values)

            elif op == "delete":
                n = random.randint(5, 50)
                cur.execute("DELETE FROM test_load WHERE id IN (SELECT id FROM test_load ORDER BY random() LIMIT %s);", (n,))

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print("Error:", e)

        time.sleep(random.uniform(0.5, 2.0))

if __name__ == "__main__":
    init_db()
    for _ in range(6):
        threading.Thread(target=worker, daemon=True).start()

    print("Started 6 workers")
    while True:
        time.sleep(10)
