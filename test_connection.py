"""
Simple script to test database connection and setup
Run this: python test_connection.py
"""

def test_database_connection():
    try:
        print("🔍 Testing database connection...")
        
        from app import app
        with app.app_context():
            from models import db, Invoice, Item
            
            # Test database connection
            print(f"📡 Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not found')}")
            
            # Test if we can connect
            engine = db.engine
            print(f"📡 Database Type: {engine.dialect.name}")
            
            # Test table existence
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"📋 Existing tables: {tables}")
            
            if 'invoice' in tables:
                columns = [col['name'] for col in inspector.get_columns('invoice')]
                print(f"📋 Invoice columns: {columns}")
                
                # Test query
                count = Invoice.query.count()
                print(f"📊 Total invoices: {count}")
                
                if count > 0:
                    first_invoice = Invoice.query.first()
                    if first_invoice is not None:
                        print(f"📋 First invoice: {first_invoice.invoice_no}")
                    else:
                        print("📋 No invoices found.")
            
            print("✅ Database connection test successful!")
            return True
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_database_connection()