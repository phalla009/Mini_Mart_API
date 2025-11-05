from flask import jsonify
from sqlalchemy import func
from model.reporting import SalesReport
from model.invoice_detail import InvoiceDetail
from model.invoice import Invoice
from model.product import Product
from model.category import Category
from model.user import User
from app import db, app
from datetime import datetime, timedelta, date
from calendar import monthrange

# ------------------- DAILY REPORT -------------------
@app.get('/sales_report/generate/daily')
def generate_daily_report():
    db.session.query(SalesReport).filter(SalesReport.report_type=='daily').delete()
    db.session.commit()

    daily_query = db.session.query(
        func.date(Invoice.create_at).label('report_date'),
        func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
        func.sum(InvoiceDetail.qty).label('total_qty'),
        func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
    ).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
    ).group_by(func.date(Invoice.create_at))

    for row in daily_query.all():
        report_date = row.report_date
        if isinstance(report_date, str):
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        db.session.add(SalesReport(
            report_type='daily',
            start_date=report_date,
            end_date=report_date,
            total_sales=row.total_sales or 0,
            total_qty=row.total_qty or 0,
            total_invoices=row.total_invoices or 0
        ))
    db.session.commit()
    reports = SalesReport.query.filter_by(report_type='daily').all()
    return jsonify([{
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat(),
        "total_sales": r.total_sales,
        "total_qty": r.total_qty,
        "total_invoices": r.total_invoices
    } for r in reports])


# ------------------- WEEKLY REPORT -------------------
@app.get('/sales_report/generate/weekly')
def generate_weekly_report():
    db.session.query(SalesReport).filter(SalesReport.report_type=='weekly').delete()
    db.session.commit()

    weekly_query = db.session.query(
        func.strftime('%Y', Invoice.create_at).label('year'),
        func.strftime('%W', Invoice.create_at).label('week'),
        func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
        func.sum(InvoiceDetail.qty).label('total_qty'),
        func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
    ).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
    ).group_by(func.strftime('%Y', Invoice.create_at), func.strftime('%W', Invoice.create_at))

    for row in weekly_query.all():
        year, week = int(row.year), int(row.week)
        week_start = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w").date()
        week_end = week_start + timedelta(days=6)
        db.session.add(SalesReport(
            report_type='weekly',
            start_date=week_start,
            end_date=week_end,
            total_sales=row.total_sales or 0,
            total_qty=row.total_qty or 0,
            total_invoices=row.total_invoices or 0
        ))
    db.session.commit()
    reports = SalesReport.query.filter_by(report_type='weekly').all()
    return jsonify([{
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat(),
        "total_sales": r.total_sales,
        "total_qty": r.total_qty,
        "total_invoices": r.total_invoices
    } for r in reports])


# ------------------- MONTHLY REPORT -------------------
@app.get('/sales_report/generate/monthly')
def generate_monthly_report():
    db.session.query(SalesReport).filter(SalesReport.report_type=='monthly').delete()
    db.session.commit()

    monthly_query = db.session.query(
        func.strftime('%Y', Invoice.create_at).label('year'),
        func.strftime('%m', Invoice.create_at).label('month'),
        func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
        func.sum(InvoiceDetail.qty).label('total_qty'),
        func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
    ).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
    ).group_by(func.strftime('%Y', Invoice.create_at), func.strftime('%m', Invoice.create_at))

    for row in monthly_query.all():
        year, month = int(row.year), int(row.month)
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
        db.session.add(SalesReport(
            report_type='monthly',
            start_date=start_date,
            end_date=end_date,
            total_sales=row.total_sales or 0,
            total_qty=row.total_qty or 0,
            total_invoices=row.total_invoices or 0
        ))
    db.session.commit()
    reports = SalesReport.query.filter_by(report_type='monthly').all()
    return jsonify([{
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat(),
        "total_sales": r.total_sales,
        "total_qty": r.total_qty,
        "total_invoices": r.total_invoices
    } for r in reports])


# ------------------- PRODUCT CRITERIA REPORT -------------------
@app.get('/sales_report/generate/product')
def generate_product_report():
    db.session.query(SalesReport).filter(SalesReport.report_type=='criteria', SalesReport.criteria_type=='product').delete()
    db.session.commit()

    today = date.today()
    product_query = db.session.query(
        Product.id.label('criteria_id'),
        Product.name.label('criteria_name'),
        func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
        func.sum(InvoiceDetail.qty).label('total_qty'),
        func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
    ).join(InvoiceDetail, InvoiceDetail.product_id == Product.id
    ).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
    ).group_by(Product.id)

    for row in product_query.all():
        db.session.add(SalesReport(
            report_type='criteria',
            criteria_type='product',
            criteria_id=row.criteria_id,
            criteria_name=row.criteria_name,
            total_sales=row.total_sales or 0,
            total_qty=row.total_qty or 0,
            total_invoices=row.total_invoices or 0,
            start_date=today,
            end_date=today
        ))
    db.session.commit()
    reports = SalesReport.query.filter_by(report_type='criteria', criteria_type='product').all()
    return jsonify([{
        "criteria_id": r.criteria_id,
        "criteria_name": r.criteria_name,
        "total_sales": r.total_sales,
        "total_qty": r.total_qty,
        "total_invoices": r.total_invoices,
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat()
    } for r in reports])


# ------------------- CATEGORY CRITERIA REPORT -------------------
@app.get('/sales_report/generate/category')
def generate_category_report():
    db.session.query(SalesReport).filter(SalesReport.report_type=='criteria', SalesReport.criteria_type=='category').delete()
    db.session.commit()

    today = date.today()
    category_query = db.session.query(
        Category.id.label('criteria_id'),
        Category.name.label('criteria_name'),
        func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
        func.sum(InvoiceDetail.qty).label('total_qty'),
        func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
    ).join(Product, Product.category_id == Category.id
    ).join(InvoiceDetail, InvoiceDetail.product_id == Product.id
    ).join(Invoice, Invoice.id == InvoiceDetail.invoice_id
    ).group_by(Category.id)

    for row in category_query.all():
        db.session.add(SalesReport(
            report_type='criteria',
            criteria_type='category',
            criteria_id=row.criteria_id,
            criteria_name=row.criteria_name,
            total_sales=row.total_sales or 0,
            total_qty=row.total_qty or 0,
            total_invoices=row.total_invoices or 0,
            start_date=today,
            end_date=today
        ))
    db.session.commit()
    reports = SalesReport.query.filter_by(report_type='criteria', criteria_type='category').all()
    return jsonify([{
        "criteria_id": r.criteria_id,
        "criteria_name": r.criteria_name,
        "total_sales": r.total_sales,
        "total_qty": r.total_qty,
        "total_invoices": r.total_invoices,
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat()
    } for r in reports])


# ------------------- USER CRITERIA REPORT -------------------
@app.get('/sales_report/generate/user')
def generate_user_report():
    db.session.query(SalesReport).filter(SalesReport.report_type=='criteria', SalesReport.criteria_type=='user').delete()
    db.session.commit()

    today = date.today()
    user_query = db.session.query(
        User.id.label('criteria_id'),
        User.name.label('criteria_name'),
        func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
        func.sum(InvoiceDetail.qty).label('total_qty'),
        func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
    ).join(Invoice, Invoice.user_id == User.id
    ).join(InvoiceDetail, InvoiceDetail.invoice_id == Invoice.id
    ).group_by(User.id)

    for row in user_query.all():
        db.session.add(SalesReport(
            report_type='criteria',
            criteria_type='user',
            criteria_id=row.criteria_id,
            criteria_name=row.criteria_name,
            total_sales=row.total_sales or 0,
            total_qty=row.total_qty or 0,
            total_invoices=row.total_invoices or 0,
            start_date=today,
            end_date=today
        ))
    db.session.commit()
    reports = SalesReport.query.filter_by(report_type='criteria', criteria_type='user').all()
    return jsonify([{
        "criteria_id": r.criteria_id,
        "criteria_name": r.criteria_name,
        "total_sales": r.total_sales,
        "total_qty": r.total_qty,
        "total_invoices": r.total_invoices,
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat()
    } for r in reports])
