from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    subtotal = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    grand_total = db.Column(db.Float, default=0.0)
    
    items = db.relationship('Item', backref='invoice', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, customer_name, customer_phone=None, notes=None):
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.notes = notes
        self.invoice_no = self.generate_invoice_number()
    
    def generate_invoice_number(self):
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        if last_invoice:
            last_number = int(last_invoice.invoice_no.split('-')[1])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"INV-{new_number:04d}"
    
    @property
    def item_count(self):
        """Get count of items safely"""
        return len(self.items)
    
    @staticmethod
    def reset_invoice_counter():
        try:
            Item.query.delete()
            Invoice.query.delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error resetting invoices: {e}")
            return False

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    rate = db.Column(db.Float, nullable=False)
    tax_rate = db.Column(db.Float, default=0.0)
    
    def __init__(self, description, quantity, rate, tax_rate=0.0):
        self.description = description
        self.quantity = quantity
        self.rate = rate
        self.tax_rate = tax_rate
    
    @property
    def line_total(self):
        """Calculate line total including tax"""
        subtotal = self.quantity * self.rate
        tax_amount = subtotal * (self.tax_rate / 100)
        return subtotal + tax_amount