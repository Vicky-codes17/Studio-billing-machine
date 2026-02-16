from flask import current_app
from models import db, Invoice
from sqlalchemy import text

def check_invoice_status():
    """Check current invoice numbering status"""
    try:
        # Get current count
        total_invoices = Invoice.query.count()
        
        if total_invoices == 0:
            return {
                'current_number': 'None',
                'next_number': '0001',
                'remaining': 2000,
                'status': 'Ready to start'
            }
        
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        if last_invoice is not None:
            next_number = last_invoice.id + 1
            current_number = last_invoice.invoice_no
        else:
            next_number = 1
            current_number = 'None'
        
        return {
            'current_number': current_number,
            'next_number': f"{next_number:04d}" if next_number <= 2000 else "LIMIT_REACHED",
            'remaining': max(0, 2000 - total_invoices),
            'status': 'Active' if next_number <= 2000 else 'Limit Reached'
        }
        
    except Exception as e:
        return {'error': str(e)}

def reset_all_invoices():
    """WARNING: This deletes ALL invoice data!"""
    try:
        # Delete all data
        db.session.execute(text("DELETE FROM item"))
        db.session.execute(text("DELETE FROM invoice"))
        db.session.execute(text("ALTER SEQUENCE invoice_id_seq RESTART WITH 1"))
        db.session.commit()
        
        return "All invoices deleted. Numbering reset to 0001."
        
    except Exception as e:
        db.session.rollback()
        return f"Error: {e}"