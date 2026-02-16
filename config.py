import psycopg2
from datetime import datetime

# Flask-SQLAlchemy configuration
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:07042006@localhost:5432/photo_billing'
SECRET_KEY = 'eb7b264b2d2c54540edecf268cd387d9'

print("Database URI:", SQLALCHEMY_DATABASE_URI)

# Connection details (change to your pgAdmin/Postgres setup)
def get_connection():
    return psycopg2.connect(
        dbname="photo_billing",
        user="postgres",   
        password="07042006",
        host="localhost",
        port="5432"
    )

# Create tables (run once at start)
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id SERIAL PRIMARY KEY,
            invoice_no VARCHAR(50) UNIQUE NOT NULL,
            date DATE NOT NULL,
            customer_name VARCHAR(100),
            customer_phone VARCHAR(20),
            notes TEXT,
            total NUMERIC(10,2)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            invoice_id INT REFERENCES invoices(id) ON DELETE CASCADE,
            description VARCHAR(200),
            qty INT,
            rate NUMERIC(10,2),
            tax_percent NUMERIC(5,2),
            line_total NUMERIC(10,2)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_invoice(invoice_no, customer, phone, notes, total, items):
    conn = get_connection()
    cur = conn.cursor()

    # Insert invoice
    cur.execute("""
        INSERT INTO invoices (invoice_no, date, customer_name, customer_phone, notes, total)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
    """, (invoice_no, datetime.now().date(), customer, phone, notes, total))
    result = cur.fetchone()
    if result is None:
        cur.close()
        conn.close()
        raise Exception("Failed to insert invoice or retrieve invoice ID.")
    invoice_id = result[0]

    # Insert items
    for it in items:
        cur.execute("""
            INSERT INTO items (invoice_id, description, qty, rate, tax_percent, line_total)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (invoice_id, it['desc'], it['qty'], it['rate'], it['tax_percent'], it['line_total']))

    conn.commit()
    cur.close()
    conn.close()
    return invoice_id