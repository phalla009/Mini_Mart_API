from app import db

class SalesReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    criteria_type = db.Column(db.String(20), nullable=True)
    criteria_id = db.Column(db.Integer, nullable=True)
    criteria_name = db.Column(db.String(100), nullable=True)
    total_sales = db.Column(db.Float, nullable=False)
    total_qty = db.Column(db.Integer, nullable=False)
    total_invoices = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
