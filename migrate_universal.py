"""
Universal database migration script that works with any database type
Run this: python migrate_universal.py
"""

from app import app
from models import db, Invoice, Item
from sqlalchemy import text, inspect, MetaData
import traceback

def migrate_database():
    """Universal migration that works with any database"""
    
    with app.app_context():
        try:
            print("🔄 Starting Universal Database Migration...")
            print("=" * 50)
            
            # Check database type
            engine = db.engine
            db_type = engine.dialect.name
            print(f"📡 Database Type: {db_type}")
            print(f"📡 Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Create metadata and reflect existing tables
            metadata = MetaData()
            
            try:
                metadata.reflect(bind=engine)
                existing_tables = list(metadata.tables.keys())
                print(f"📋 Existing tables: {existing_tables}")
            except Exception as e:
                print(f"⚠️  Could not reflect database: {e}")
                existing_tables = []
            
            # Check if invoice table exists
            if 'invoice' not in existing_tables:
                print("❌ Invoice table doesn't exist. Creating all tables...")
                try:
                    db.create_all()
                    print("✅ All tables created successfully!")
                    print("🚀 You can now run: python app.py")
                    return
                except Exception as e:
                    print(f"❌ Failed to create tables: {e}")
                    return
            
            # Use SQLAlchemy inspector to check current schema
            try:
                inspector = inspect(engine)
                current_columns = [col['name'] for col in inspector.get_columns('invoice')]
                print(f"📋 Current invoice columns: {current_columns}")
            except Exception as e:
                print(f"❌ Could not inspect invoice table: {e}")
                # Try a direct query approach
                try:
                    with engine.connect() as conn:
                        if db_type == 'sqlite':
                            result = conn.execute(text("PRAGMA table_info(invoice)"))
                            current_columns = [row[1] for row in result.fetchall()]
                        elif db_type == 'postgresql':
                            result = conn.execute(text("""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = 'invoice'
                            """))
                            current_columns = [row[0] for row in result.fetchall()]
                        else:
                            print(f"❌ Unsupported database type for column inspection: {db_type}")
                            return
                    print(f"📋 Current invoice columns (direct query): {current_columns}")
                except Exception as e2:
                    print(f"❌ Could not get columns via direct query: {e2}")
                    return
            
            # Define required columns
            required_columns = {
                'subtotal': 'REAL DEFAULT 0.0',
                'tax_amount': 'REAL DEFAULT 0.0', 
                'grand_total': 'REAL DEFAULT 0.0'
            }
            
            # Check which columns are missing
            missing_columns = []
            for col_name in required_columns:
                if col_name not in current_columns:
                    missing_columns.append(col_name)
            
            if not missing_columns:
                print("ℹ️  All required columns already exist!")
                
                # Test if we can query invoices
                try:
                    test_invoice = Invoice.query.first()
                    print("✅ Database schema is working correctly!")
                    
                    # Also migrate invoice numbers to new format
                    migrate_invoice_numbers()
                    return
                except Exception as e:
                    print(f"⚠️  Schema issue detected: {e}")
                    print("Continuing with migration...")
            
            # Add missing columns
            if missing_columns:
                print(f"➕ Adding missing columns: {missing_columns}")
                
                with engine.connect() as conn:
                    trans = conn.begin()
                    try:
                        for col_name in missing_columns:
                            col_def = required_columns[col_name]
                            
                            # Adjust column definition for different databases
                            if db_type == 'sqlite':
                                sql_cmd = f"ALTER TABLE invoice ADD COLUMN {col_name} {col_def}"
                            elif db_type == 'postgresql':
                                sql_cmd = f"ALTER TABLE invoice ADD COLUMN {col_name} {col_def}"
                            elif db_type == 'mysql':
                                sql_cmd = f"ALTER TABLE invoice ADD COLUMN {col_name} {col_def.replace('REAL', 'DECIMAL(10,2)')}"
                            else:
                                sql_cmd = f"ALTER TABLE invoice ADD COLUMN {col_name} {col_def}"
                            
                            print(f"   🔧 Executing: {sql_cmd}")
                            conn.execute(text(sql_cmd))
                            print(f"   ✅ Added column: {col_name}")
                        
                        trans.commit()
                        print("✅ Column addition completed!")
                        
                    except Exception as e:
                        trans.rollback()
                        print(f"❌ Failed to add columns: {e}")
                        return
                
                # Calculate totals for existing invoices
                print("\n🔄 Calculating totals for existing invoices...")
                
                try:
                    # Get all invoices and calculate their totals
                    invoices = Invoice.query.all()
                    print(f"📊 Found {len(invoices)} invoices to update")
                    
                    for invoice in invoices:
                        try:
                            subtotal = 0.0
                            tax_total = 0.0
                            
                            for item in invoice.items:
                                if item.quantity and item.rate:
                                    line_subtotal = float(item.quantity) * float(item.rate)
                                    line_tax = line_subtotal * (float(item.tax_rate or 0) / 100)
                                    subtotal += line_subtotal
                                    tax_total += line_tax
                            
                            # Update invoice totals
                            invoice.subtotal = subtotal
                            invoice.tax_amount = tax_total
                            invoice.grand_total = subtotal + tax_total
                            
                            print(f"   📋 {invoice.invoice_no}: ₹{invoice.grand_total:.2f}")
                            
                        except Exception as e:
                            print(f"   ⚠️  Error calculating totals for {invoice.invoice_no}: {e}")
                    
                    # Save all changes
                    db.session.commit()
                    print("✅ All invoice totals updated successfully!")
                    
                except Exception as e:
                    print(f"❌ Error updating invoice totals: {e}")
                    db.session.rollback()
            
            # Migrate invoice numbers to new format
            migrate_invoice_numbers()
            
            # Final verification
            print("\n🔍 Final Verification...")
            try:
                test_invoices = Invoice.query.limit(3).all()
                if test_invoices:
                    for invoice in test_invoices:
                        print(f"✅ {invoice.invoice_no}: ₹{invoice.grand_total:.2f}")
                else:
                    print("ℹ️  No invoices found for verification")
                
                print("\n🎉 Migration completed successfully!")
                print("🚀 You can now run: python app.py")
                
            except Exception as e:
                print(f"❌ Verification failed: {e}")
                print("The migration may have been partially successful.")
                print("Try running the app to see if it works: python app.py")
            
        except Exception as e:
            print(f"❌ Migration failed with error: {e}")
            print("\n📋 Full error traceback:")
            traceback.print_exc()
            
            print("\n🔧 Troubleshooting suggestions:")
            print("1. Check your database connection in config.py")
            print("2. Ensure database user has ALTER permissions")
            print("3. Try creating a fresh database by deleting instance/billing.db")
            print("4. Check if database server is running")
            print("5. Run: python -c 'from app import app; print(app.config[\"SQLALCHEMY_DATABASE_URI\"])'")

def migrate_invoice_numbers():
    """Update existing invoice numbers to use leading zeros format"""
    try:
        print("\n🔄 Migrating invoice numbers to new format...")
        
        # Get all invoices ordered by ID
        invoices = Invoice.query.order_by(Invoice.id.asc()).all()
        
        if not invoices:
            print("ℹ️  No invoices found to migrate")
            return
        
        print(f"📋 Found {len(invoices)} invoices to migrate")
        
        updates_made = 0
        for i, invoice in enumerate(invoices, 1):
            old_number = invoice.invoice_no
            new_number = f"INV-{i:04d}"
            
            # Only update if format is different
            if old_number != new_number:
                invoice.invoice_no = new_number
                updates_made += 1
                print(f"   📝 Updated: {old_number} → {new_number}")
        
        if updates_made > 0:
            # Commit all changes
            db.session.commit()
            print(f"✅ Successfully migrated {updates_made} invoice numbers!")
        else:
            print("ℹ️  All invoice numbers already in correct format")
        
        # Show final status
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        if last_invoice:
            print(f"📊 Last invoice number: {last_invoice.invoice_no}")
            next_number = int(last_invoice.invoice_no.split('-')[1]) + 1
            print(f"🔮 Next invoice will be: INV-{next_number:04d}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Invoice number migration failed: {e}")

if __name__ == "__main__":
    migrate_database()