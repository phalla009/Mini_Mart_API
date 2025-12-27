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

# ------------------- GENERATE SALE REPORT -------------------
def generate_report(period='daily', criteria_type='sale'):
    """
    period: 'daily', 'weekly', 'monthly', 'all'
    criteria_type: 'sale'
    """
    today = date.today()

    # ------------------- Determine date range -------------------
    if period == 'daily':
        start_date = end_date = today
    elif period == 'weekly':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'monthly':
        start_date = date(today.year, today.month, 1)
        _, last_day = monthrange(today.year, today.month)
        end_date = date(today.year, today.month, last_day)
    elif period == 'all':
        start_date = date(2000,1,1)  # earliest possible date
        end_date = today
    else:
        return jsonify({"error": "Invalid period"}), 400

    # ------------------- Delete old report for this period & criteria -------------------
    db.session.query(SalesReport).filter(
        SalesReport.report_type == period,
        SalesReport.criteria_type == criteria_type,
        SalesReport.start_date == start_date,
        SalesReport.end_date == end_date
    ).delete()
    db.session.commit()

    # ------------------- Build query -------------------
    if criteria_type == 'sale':
        query = (
            db.session.query(
                func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
                func.sum(InvoiceDetail.qty).label('total_qty'),
                func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
            )
            .join(Invoice, Invoice.id == InvoiceDetail.invoice_id)
            .filter(func.date(Invoice.create_at) >= start_date)
            .filter(func.date(Invoice.create_at) <= end_date)
        )
        result = query.first()
        total_sales = result.total_sales or 0
        total_qty = result.total_qty or 0
        total_invoices = result.total_invoices or 0

        # Insert report
        db.session.add(SalesReport(
            report_type=period,
            criteria_type='sale',
            criteria_name='Total Sales',
            total_sales=total_sales,
            total_qty=total_qty,
            total_invoices=total_invoices,
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.now()
        ))
        db.session.commit()

        report = SalesReport.query.filter_by(
            report_type=period,
            criteria_type='sale',
            start_date=start_date,
            end_date=end_date
        ).first()

        return jsonify({
            "criteria_name": report.criteria_name,
            "total_sales": report.total_sales,
            "total_qty": report.total_qty,
            "total_invoices": report.total_invoices,
            "start_date": report.start_date.isoformat(),
            "end_date": report.end_date.isoformat()
        })

@app.get('/api/sales_report/generate/daily')
def total_daily(): return generate_report('daily','sale')

@app.get('/api/sales_report/generate/weekly')
def total_weekly(): return generate_report('weekly','sale')

@app.get('/api/sales_report/generate/monthly')
def total_monthly(): return generate_report('monthly','sale')


# ------------------- PRODUCT CRITERIA REPORT -------------------
def generate_total_report(period='daily'):
    today = date.today()

    if period == 'daily':
        start_date = end_date = today
    elif period == 'weekly':
        start_date = today - timedelta(days=today.weekday())  # Monday
        end_date = start_date + timedelta(days=6)            # Sunday
    elif period == 'monthly':
        start_date = date(today.year, today.month, 1)
        _, last_day = monthrange(today.year, today.month)
        end_date = date(today.year, today.month, last_day)
    else:
        return jsonify({"error": "Invalid period"}), 400

    # Delete old report for this period
    db.session.query(SalesReport).filter(
        SalesReport.report_type == period,
        SalesReport.start_date == start_date,
        SalesReport.end_date == end_date
    ).delete()
    db.session.commit()

    # Query total sales for the period
    total_query = (
        db.session.query(
            func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
            func.sum(InvoiceDetail.qty).label('total_qty'),
            func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
        )
        .join(Invoice, Invoice.id == InvoiceDetail.invoice_id)
        .filter(func.date(Invoice.create_at) >= start_date)
        .filter(func.date(Invoice.create_at) <= end_date)
    )

    result = total_query.first()
    total_sales = result.total_sales or 0
    total_qty = result.total_qty or 0
    total_invoices = result.total_invoices or 0

    # Add report to SalesReport table
    db.session.add(SalesReport(
        report_type=period,
        criteria_type='total',
        criteria_name='All Products',
        total_sales=total_sales,
        total_qty=total_qty,
        total_invoices=total_invoices,
        start_date=start_date,
        end_date=end_date,
        created_at=datetime.now()
    ))
    db.session.commit()

    # Return the report
    report = SalesReport.query.filter_by(
        report_type=period,
        criteria_type='total',
        start_date=start_date,
        end_date=end_date
    ).first()

    return jsonify({
        "period": period,
        "start_date": report.start_date.isoformat(),
        "end_date": report.end_date.isoformat(),
        "total_sales": report.total_sales,
        "total_qty": report.total_qty,
        "total_invoices": report.total_invoices
    })
@app.get('/api/sales_report/generate/product/daily')
def generate_product_daily_report():
    return generate_total_report(period='daily')
@app.get('/api/sales_report/generate/product/weekly')
def generate_product_weekly_report():
    return generate_total_report(period='weekly')

@app.get('/api/sales_report/generate/product/monthly')
def generate_product_monthly_report():
    return generate_total_report(period='monthly')



# ------------------- CATEGORY CRITERIA REPORT -------------------

def generate_category_report(period='daily'):
    today = date.today()

    # Determine date range based on period
    if period == 'daily':
        start_date = end_date = today
    elif period == 'weekly':
        start_date = today - timedelta(days=today.weekday())  # Monday
        end_date = start_date + timedelta(days=6)            # Sunday
    elif period == 'monthly':
        start_date = date(today.year, today.month, 1)
        _, last_day = monthrange(today.year, today.month)
        end_date = date(today.year, today.month, last_day)
    else:
        return jsonify({"error": "Invalid period"}), 400

    # Delete old reports for this period
    db.session.query(SalesReport).filter(
        SalesReport.report_type == 'criteria',
        SalesReport.criteria_type == 'category',
        SalesReport.start_date == start_date,
        SalesReport.end_date == end_date
    ).delete()
    db.session.commit()

    # Query invoices grouped by category within the period
    category_query = (
        db.session.query(
            Category.id.label('criteria_id'),
            Category.name.label('criteria_name'),
            func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
            func.sum(InvoiceDetail.qty).label('total_qty'),
            func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
        )
        .join(Product, Product.category_id == Category.id)
        .join(InvoiceDetail, InvoiceDetail.product_id == Product.id)
        .join(Invoice, Invoice.id == InvoiceDetail.invoice_id)
        .filter(func.date(Invoice.create_at) >= start_date)
        .filter(func.date(Invoice.create_at) <= end_date)
        .group_by(Category.id)
    )

    # Add results to SalesReport
    for row in category_query.all():
        db.session.add(SalesReport(
            report_type='criteria',
            criteria_type='category',
            criteria_id=row.criteria_id,
            criteria_name=row.criteria_name,
            total_sales=row.total_sales or 0,
            total_qty=row.total_qty or 0,
            total_invoices=row.total_invoices or 0,
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.now()
        ))
    db.session.commit()

    # Return reports as JSON
    reports = SalesReport.query.filter_by(
        report_type='criteria',
        criteria_type='category',
        start_date=start_date,
        end_date=end_date
    ).all()

    return jsonify([{
        "criteria_id": r.criteria_id,
        "criteria_name": r.criteria_name,
        "total_sales": r.total_sales,
        "total_qty": r.total_qty,
        "total_invoices": r.total_invoices,
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat()
    } for r in reports])
@app.get('/api/sales_report/generate/category/daily')
def category_daily(): return generate_category_report('daily')

@app.get('/api/sales_report/generate/category/weekly')
def category_weekly(): return generate_category_report('weekly')

@app.get('/api/sales_report/generate/category/monthly')
def category_monthly(): return generate_category_report('monthly')


# ------------------- USER CRITERIA REPORT -------------------
def generate_user_report(period='daily'):
    today = date.today()

    # Determine date range
    if period == 'daily':
        start_date = end_date = today
    elif period == 'weekly':
        start_date = today - timedelta(days=today.weekday())  # Monday
        end_date = start_date + timedelta(days=6)            # Sunday
    elif period == 'monthly':
        start_date = date(today.year, today.month, 1)
        _, last_day = monthrange(today.year, today.month)
        end_date = date(today.year, today.month, last_day)
    else:
        return jsonify({"error": "Invalid period"}), 400

    # Delete old reports for this period
    db.session.query(SalesReport).filter(
        SalesReport.report_type == 'criteria',
        SalesReport.criteria_type == 'user',
        SalesReport.start_date == start_date,
        SalesReport.end_date == end_date
    ).delete()
    db.session.commit()

    # Query invoices grouped by user
    user_query = (
        db.session.query(
            User.id.label('criteria_id'),
            User.name.label('criteria_name'),
            func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
            func.sum(InvoiceDetail.qty).label('total_qty'),
            func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
        )
        .join(Invoice, Invoice.user_id == User.id)
        .join(InvoiceDetail, InvoiceDetail.invoice_id == Invoice.id)
        .filter(func.date(Invoice.create_at) >= start_date)
        .filter(func.date(Invoice.create_at) <= end_date)
        .group_by(User.id)
    )

    # Add reports
    for row in user_query.all():
        db.session.add(SalesReport(
            report_type='criteria',
            criteria_type='user',
            criteria_id=row.criteria_id,
            criteria_name=row.criteria_name,
            total_sales=row.total_sales or 0,
            total_qty=row.total_qty or 0,
            total_invoices=row.total_invoices or 0,
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.now()
        ))
    db.session.commit()

    # Return reports as JSON
    reports = SalesReport.query.filter_by(
        report_type='criteria',
        criteria_type='user',
        start_date=start_date,
        end_date=end_date
    ).all()

    return jsonify([{
        "criteria_id": r.criteria_id,
        "criteria_name": r.criteria_name,
        "total_sales": r.total_sales,
        "total_qty": r.total_qty,
        "total_invoices": r.total_invoices,
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat()
    } for r in reports])

@app.get('/api/sales_report/generate/user/daily')
def user_daily(): return generate_user_report('daily')

@app.get('/api/sales_report/generate/user/weekly')
def user_weekly(): return generate_user_report('weekly')

@app.get('/api/sales_report/generate/user/monthly')
def user_monthly(): return generate_user_report('monthly')
