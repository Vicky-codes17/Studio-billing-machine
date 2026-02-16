from models import db, Invoice, Item
from datetime import datetime
from sqlalchemy import func

def save_invoice(customer_name, customer_phone, notes, items_list):
    """Save invoice and return invoice ID"""
    try:
        # Create invoice
        invoice = Invoice(customer_name, customer_phone, notes)
        db.session.add(invoice)
        db.session.flush()  # Get the ID
        
        # Add items
        subtotal = 0.0
        tax_total = 0.0
        
        for item_data in items_list:
            item = Item(
                description=item_data['description'],
                quantity=item_data['quantity'],
                rate=item_data['rate'],
                tax_rate=item_data['tax_rate']
            )
            item.invoice_id = invoice.id
            db.session.add(item)
            
            # Calculate totals
            line_subtotal = item.quantity * item.rate
            line_tax = line_subtotal * (item.tax_rate / 100)
            subtotal += line_subtotal
            tax_total += line_tax
        
        # Update invoice totals
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_total
        invoice.grand_total = subtotal + tax_total
        
        db.session.commit()
        return invoice.id
        
    except Exception as e:
        db.session.rollback()
        raise e

def get_invoice_stats():
    """Get invoice statistics"""
    try:
        total_invoices = Invoice.query.count()
        total_amount = db.session.query(func.sum(Invoice.grand_total)).scalar() or 0
        
        return {
            "total_invoices": total_invoices,
            "total_amount": float(total_amount)
        }
    except Exception as e:
        return {"error": str(e)}

def get_invoice_with_stats(invoice_id):
    """Get invoice with item count and totals"""
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        
        # Calculate stats properly
        item_count = len(invoice.items)  # ✅ Correct: len() instead of count()
        
        return {
            "invoice": invoice,
            "item_count": item_count,
            "items": invoice.items
        }
    except Exception as e:
        return {"error": str(e)}