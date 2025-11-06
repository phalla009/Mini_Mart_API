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
    # Get today date (no time)
    today = date.today()

    # Delete previous daily reports for today only
    db.session.query(SalesReport).filter(
        SalesReport.report_type == 'daily',
        SalesReport.start_date == today
    ).delete()
    db.session.commit()

    # Query only invoices created today
    daily_query = (
        db.session.query(
            func.date(Invoice.create_at).label('report_date'),
            func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
            func.sum(InvoiceDetail.qty).label('total_qty'),
            func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
        )
        .join(Invoice, Invoice.id == InvoiceDetail.invoice_id)
        .filter(func.date(Invoice.create_at) == today)
        .group_by(func.date(Invoice.create_at))
    )

    # Insert into SalesReport table
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
            total_invoices=row.total_invoices or 0,
            created_at=datetime.now()
        ))

    db.session.commit()

    # Return today report
    reports = SalesReport.query.filter_by(report_type='daily', start_date=today).all()
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
    # Get current year and current ISO week number
    today = date.today()
    year, week_num, _ = today.isocalendar()

    # Delete old weekly report for this week only
    db.session.query(SalesReport).filter(
        SalesReport.report_type == 'weekly',
        SalesReport.start_date >= today - timedelta(days=today.weekday()),
        SalesReport.end_date <= today + timedelta(days=6 - today.weekday())
    ).delete()
    db.session.commit()

    # Calculate week start and end dates
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)              # Sunday

    # Query only invoices in this week
    weekly_query = (
        db.session.query(
            func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
            func.sum(InvoiceDetail.qty).label('total_qty'),
            func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
        )
        .join(Invoice, Invoice.id == InvoiceDetail.invoice_id)
        .filter(func.date(Invoice.create_at) >= week_start)
        .filter(func.date(Invoice.create_at) <= week_end)
    )

    result = weekly_query.first()
    total_sales = result.total_sales or 0
    total_qty = result.total_qty or 0
    total_invoices = result.total_invoices or 0

    # Add new report for this week
    db.session.add(SalesReport(
        report_type='weekly',
        start_date=week_start,
        end_date=week_end,
        total_sales=total_sales,
        total_qty=total_qty,
        total_invoices=total_invoices,
        created_at=datetime.now()
    ))
    db.session.commit()

    # Return only current week's report
    report = SalesReport.query.filter_by(
        report_type='weekly',
        start_date=week_start,
        end_date=week_end
    ).first()

    if not report:
        return jsonify({"message": "No data found for this week"}), 404

    return jsonify({
        "start_date": report.start_date.isoformat(),
        "end_date": report.end_date.isoformat(),
        "total_sales": report.total_sales,
        "total_qty": report.total_qty,
        "total_invoices": report.total_invoices
    })


# ------------------- MONTHLY REPORT -------------------
@app.get('/sales_report/generate/monthly')
def generate_monthly_report():
    # Get current year and month
    today = date.today()
    year = today.year
    month = today.month

    # Delete old monthly report for this month only
    first_day = date(year, month, 1)
    _, last_day_num = monthrange(year, month)
    last_day = date(year, month, last_day_num)

    db.session.query(SalesReport).filter(
        SalesReport.report_type == 'monthly',
        SalesReport.start_date == first_day,
        SalesReport.end_date == last_day
    ).delete()
    db.session.commit()

    # Query only invoices from this month
    monthly_query = (
        db.session.query(
            func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
            func.sum(InvoiceDetail.qty).label('total_qty'),
            func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
        )
        .join(Invoice, Invoice.id == InvoiceDetail.invoice_id)
        .filter(func.strftime('%Y', Invoice.create_at) == str(year))
        .filter(func.strftime('%m', Invoice.create_at) == f"{month:02d}")
    )

    result = monthly_query.first()
    total_sales = result.total_sales or 0
    total_qty = result.total_qty or 0
    total_invoices = result.total_invoices or 0

    # Add report for current month
    db.session.add(SalesReport(
        report_type='monthly',
        start_date=first_day,
        end_date=last_day,
        total_sales=total_sales,
        total_qty=total_qty,
        total_invoices=total_invoices,
        created_at=datetime.now()
    ))
    db.session.commit()

    # Return only current month's report
    report = SalesReport.query.filter_by(
        report_type='monthly',
        start_date=first_day,
        end_date=last_day
    ).first()

    if not report:
        return jsonify({"message": "No data found for this month"}), 404

    return jsonify({
        "start_date": report.start_date.isoformat(),
        "end_date": report.end_date.isoformat(),
        "total_sales": report.total_sales,
        "total_qty": report.total_qty,
        "total_invoices": report.total_invoices
    })


# ------------------- PRODUCT CRITERIA REPORT -------------------
@app.get('/sales_report/generate/product')
def generate_product_report():
    today = date.today()

    # Delete old product reports for today
    db.session.query(SalesReport).filter(
        SalesReport.report_type == 'criteria',
        SalesReport.criteria_type == 'product',
        SalesReport.start_date == today,
        SalesReport.end_date == today
    ).delete()
    db.session.commit()

    # Query invoices only for today, grouped by product
    product_query = (
        db.session.query(
            Product.id.label('criteria_id'),
            Product.name.label('criteria_name'),
            func.sum(InvoiceDetail.qty * InvoiceDetail.price).label('total_sales'),
            func.sum(InvoiceDetail.qty).label('total_qty'),
            func.count(func.distinct(InvoiceDetail.invoice_id)).label('total_invoices')
        )
        .join(InvoiceDetail, InvoiceDetail.product_id == Product.id)
        .join(Invoice, Invoice.id == InvoiceDetail.invoice_id)
        .filter(func.date(Invoice.create_at) == today)
        .group_by(Product.id)
    )

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
            end_date=today,
            created_at=datetime.now()
        ))
    db.session.commit()

    # Return today's product reports
    reports = SalesReport.query.filter_by(
        report_type='criteria',
        criteria_type='product',
        start_date=today,
        end_date=today
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


# ------------------- CATEGORY CRITERIA REPORT -------------------
@app.get('/sales_report/generate/category')
def generate_category_report():
    today = date.today()

    # Delete old category reports for today
    db.session.query(SalesReport).filter(
        SalesReport.report_type == 'criteria',
        SalesReport.criteria_type == 'category',
        SalesReport.start_date == today,
        SalesReport.end_date == today
    ).delete()
    db.session.commit()

    # Query invoices only for today, grouped by category
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
        .filter(func.date(Invoice.create_at) == today)  # 👈 filter by today
        .group_by(Category.id)
    )

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
            end_date=today,
            created_at=datetime.now()
        ))
    db.session.commit()

    # Return today's category reports
    reports = SalesReport.query.filter_by(
        report_type='criteria',
        criteria_type='category',
        start_date=today,
        end_date=today
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
