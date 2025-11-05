import uuid
from datetime import datetime

from app import app, db
from flask import jsonify, request
from sqlalchemy import text
from model import Product, Invoice
from werkzeug.utils import secure_filename
import os

@app.get('/invoices')
def get_invoices():
    sql = text("""SELECT i.id, i.invoice_number  , 'true' as active , i.customer_name,i.customer_phone,i.create_at as create_date, 
                i.total_amount,i.payment_method,i.remark , u.name as user_name FROM invoice as i
                join user as u
                on i.user_id = u.id
    """)
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    if not rows:
        return jsonify({'message': 'No invoices found'})
    return jsonify(rows)

@app.get('/invoices/list')
def get_all_invoices():
    sql = text("""SELECT i.id, i.invoice_number  , 'true' as active , i.customer_name,i.customer_phone,i.create_at as create_date, 
                i.total_amount,i.payment_method,i.remark , u.name as user_name FROM invoice as i
                join user as u
                on i.user_id = u.id
        """)
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    if not rows:
        return jsonify({'message': 'No invoices found'})
    return jsonify(rows)

@app.get('/invoices/list/<int:id>')
def get_invoice_by_id(id):
    sql = text("""SELECT i.id, i.invoice_number  , 'true' as active , i.customer_name,i.customer_phone,i.create_at as create_date, 
                i.total_amount,i.payment_method,i.remark , u.name as user_name FROM invoice as i
                join user as u
                on i.user_id = u.id
                WHERE i.id = :id
                      """)
    result = db.session.execute(sql, {'id': id}).fetchall()
    if not result:
        return jsonify({'error': 'Invoice not found'})
    rows = [dict(row._mapping) for row in result]
    return jsonify(rows)


@app.post('/invoices/create')
def create_invoices():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No Invoices provided'})
    customer_name=data.get('customer_name')
    customer_phone=data.get('customer_phone')
    total_amount=data.get('total_amount')
    payment_method=data.get('payment_method')
    remark=data.get('remark')
    user_id = data.get('user_id')

    if not customer_name:
        return {'error': 'No customer_name provided'}
    if not customer_phone:
        return {'error': 'No customer_phone provided'}
    if not total_amount:
        return {'error': 'No total_amount provided'}
    if not user_id:
        return {'error': 'No user_id provided'}
    if not payment_method:
        return {'error': 'No payment_method provided'}

    result = db.session.execute(text("SELECT MAX(invoice_number) FROM invoice"))
    max_invoice = result.fetchone()[0]
    if max_invoice:
        next_number = int(max_invoice) + 1
    else:
        next_number = 1
    invoice_number = f"{next_number:03}"

    create_at = datetime.now()
    formatted_date = create_at.strftime("%Y-%m-%d")
    display_date = create_at.strftime("%d-%m-%Y")

    if not str(user_id).isdigit():
        return jsonify({'error': ' user_id must be a number'})
    try:
        total_amount = float(total_amount)
    except (ValueError, TypeError):
        return jsonify({'error': 'total_amount must be a number'})

    sql = text("""
       INSERT INTO invoice (invoice_number, customer_name, customer_phone, create_at, 
                             total_amount, payment_method, remark, user_id)
        VALUES (:invoice_number, :customer_name, :customer_phone, :create_at, 
                :total_amount, :payment_method, :remark, :user_id)
    """)
    db.session.execute(sql, {
        "invoice_number": invoice_number,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "create_at": formatted_date,
        "total_amount": total_amount,
        "payment_method": payment_method,
        "remark": remark,
        "user_id": user_id
    })
    db.session.commit()
    return {
        'Message': 'Invoices created successfully',
        'Invoices': {
            "invoice_number": invoice_number,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "create_at": display_date,
            "total_amount": total_amount,
            "payment_method": payment_method,
            "remark": remark,
            "user_id": user_id
        }
    }

@app.put('/invoices/update')
def update_invoices():
    data = request.get_json()
    invoice_id = data.get('invoice_id')
    if not data:
        return jsonify({'error': 'No Invoices provided'})
    if not invoice_id:
        return jsonify({'error': 'Invoices ID is required'})
    invoices = Invoice.query.get(invoice_id)
    if not invoices:
        return jsonify({'error': 'Invoice not found'})

    customer_name=data.get('customer_name')
    customer_phone=data.get('customer_phone')
    total_amount=data.get('total_amount')
    payment_method=data.get('payment_method')
    remark=data.get('remark')
    user_id = data.get('user_id')

    if not customer_name:
        return {'error': 'No customer_name provided'}
    if not customer_phone:
        return {'error': 'No customer_phone provided'}
    if not total_amount:
        return {'error': 'No total_amount provided'}
    if not user_id:
        return {'error': 'No user_id provided'}
    if not payment_method:
        return {'error': 'No payment_method provided'}

    invoice_number = invoices.invoice_number
    create_at = datetime.now()
    formatted_date = create_at.strftime("%Y-%m-%d")
    display_date = create_at.strftime("%d-%m-%Y")

    if not str(user_id).isdigit():
        return jsonify({'error': ' user_id must be a number'})
    try:
        total_amount = float(total_amount)
    except (ValueError, TypeError):
        return jsonify({'error': 'total_amount must be a number'})

    sql = text("""
      UPDATE invoice
        SET customer_name = :customer_name,
            customer_phone = :customer_phone,
            total_amount = :total_amount,
            payment_method = :payment_method,
            remark = :remark,
            user_id = :user_id,
            create_at = :create_at
        WHERE id = :invoice_id
    """)
    db.session.execute(sql, {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "create_at": formatted_date,
        "total_amount": total_amount,
        "payment_method": payment_method,
        "remark": remark,
        "user_id": user_id,
        "invoice_id": invoice_id
    })
    db.session.commit()
    return {
        'Message': 'Invoices Update successfully',
        'Invoices': {
            "invoice_number": invoice_number,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "create_at": display_date,
            "total_amount": total_amount,
            "payment_method": payment_method,
            "remark": remark,
            "user_id": user_id
        }
    }

@app.delete('/invoices/delete')
def delete_invoices():
    data = request.get_json()
    invoice_id = data.get('invoice_id')
    if not data:
        return jsonify({'error': 'No Invoices provided'})
    if not invoice_id:
        return jsonify({'error': 'Invoices ID is required'})
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'})

    deleted_info = {
        'invoice_id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'customer_name': invoice.customer_name,
        'customer_phone': invoice.customer_phone,
        'total_amount': invoice.total_amount,
        'payment_method': invoice.payment_method,
        'remark': invoice.remark
    }
    sql = text("DELETE FROM invoice WHERE id = :invoice_id")
    db.session.execute(sql, {'invoice_id': invoice_id})
    db.session.commit()
    return {
        'Message': 'Invoices Delete successfully',
        'deleted_invoice': deleted_info
    }