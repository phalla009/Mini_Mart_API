from app import db


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_name = db.Column(db.String(128))
    customer_phone = db.Column(db.String(128))
    create_at =db.Column(db.Date)
    total_amount = db.Column(db.Float)
    payment_method = db.Column(db.String(255))
    remark = db.Column(db.String(255))