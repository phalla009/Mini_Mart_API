from app import db

class InvoiceDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    qty = db.Column(db.Integer)
    price = db.Column(db.Float)
    subtotal = db.Column(db.Float)
    create_at = db.Column(db.DateTime)



