from flask import Flask
from models import db, Invoice, Item
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY

db.init_app(app)

def check_and_fix_database():
    """Check database structure and fix if needed"""
    with app.app_context():
        try:
            # Try to query invoices to see if columns exist
            from sqlalchemy import text
            invoices = db.session.execute(text("SELECT * FROM invoice LIMIT 1")).fetchone()
            print("✅ Database structure looks good!")
            return True
        except Exception as e:
            print(f"❌ Database issue detected: {e}")
            
            # Check if we need to remove problematic columns
            try:
                # Check what columns exist
                from sqlalchemy import text
                result = db.session.execute(text("PRAGMA table_info(invoice)")).fetchall()
                columns = [row[1] for row in result]
                print(f"Current columns: {columns}")
                
                # If problematic columns exist, we need to recreate the table
                if 'subtotal' in columns or 'tax_amount' in columns or 'grand_total' in columns:
                    print("🔧 Fixing database structure...")
                    
                    # Create backup
                    from sqlalchemy import text
                    db.session.execute(text("""
                        CREATE TABLE invoice_backup AS 
                        SELECT id, invoice_no, customer_name, customer_phone, date, notes 
                        FROM invoice
                    """))
                    
                    # Drop and recreate tables
                    db.drop_all()
                    db.create_all()
                    
                    # Restore data
                    db.session.execute(text("""
                        INSERT INTO invoice (id, invoice_no, customer_name, customer_phone, date, notes)
                        SELECT id, invoice_no, customer_name, customer_phone, date, notes 
                        FROM invoice_backup
                    """))
                    
                    # Drop backup
                    db.session.execute(text("DROP TABLE invoice_backup"))
                    db.session.commit()
                    
                    print("✅ Database structure fixed!")
                    return True
                else:
                    # Just create missing tables
                    db.create_all()
                    print("✅ Database tables created!")
                    return True
                    
            except Exception as fix_error:
                print(f"❌ Could not fix database: {fix_error}")
                print("💡 Try deleting the database file and restarting the application")
                return False

if __name__ == "__main__":
    if check_and_fix_database():
        print("🚀 Database is ready!")
    else:
        print("💥 Database needs manual intervention")