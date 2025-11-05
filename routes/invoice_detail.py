import uuid
from datetime import datetime

from app import app, db
from flask import jsonify, request
from sqlalchemy import text
from model.invoice_detail import InvoiceDetail
from werkzeug.utils import secure_filename
import os

@app.get('/invoice_details')
def get_invoice_details():
    sql = text("""SELECT id.id, id.invoice_id,id.product_id,id.qty, id.price,id.subtotal ,id.create_at FROM invoice_detail as id
            JOIN product as p
            ON id.product_id = p.id
            JOIN invoice as i 
            ON id.invoice_id = i.id
    """)
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    if not rows:
        return jsonify({'message': 'No invoice details found'})
    return jsonify(rows)

@app.get('/invoice_details/list')
def get_all_invoice_details():
    sql = text("""SELECT id.id, id.invoice_id,id.product_id,id.qty, id.price,id.subtotal ,id.create_at FROM invoice_detail as id
            JOIN product as p
            ON id.product_id = p.id
            JOIN invoice as i 
            ON id.invoice_id = i.id
    """)
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    if not rows:
        return jsonify({'message': 'No invoice details found'})
    return jsonify(rows)

@app.get('/invoice_details/list/<int:id>')
def get_invoice_details_by_id(id):
    sql = text("""SELECT id.id, id.invoice_id,id.product_id,id.qty, id.price,id.subtotal ,id.create_at FROM invoice_detail as id
            JOIN product as p
            ON id.product_id = p.id
            JOIN invoice as i 
            ON id.invoice_id = i.id
            where id.id = :id
                      """)
    result = db.session.execute(sql, {'id': id}).fetchall()
    if not result:
        return jsonify({'error': 'invoice details not found'})
    rows = [dict(row._mapping) for row in result]
    return jsonify(rows)

@app.post('/invoice_details/create')
def create_invoice_details():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No invoice details provided'})
    invoice_id = data.get('invoice_id')
    product_id = data.get('product_id')
    qty = data.get('qty')
    price = data.get('price')

    if not invoice_id:
        return {'error': 'No invoice_id provided'}
    if not product_id:
        return {'error': 'No product_id provided'}
    if not qty:
        return {'error': 'No qty provided'}
    if not price:
        return {'error': 'No price provided'}

    create_at = datetime.now()
    formatted_date = create_at.strftime("%Y-%m-%d")
    display_date = create_at.strftime("%d-%m-%Y")

    if not str(invoice_id).isdigit():
        return jsonify({'error': 'invoice_id must be a number'})
    if not str(product_id).isdigit():
        return jsonify({'error': 'product_id must be a number'})
    try:
        qty = float(qty)
    except (ValueError, TypeError):
        return jsonify({'error': 'qty must be a number'})
    try:
        price = float(price)
    except (ValueError, TypeError):
        return jsonify({'error': 'price must be a number'})

    subtotal = qty * price

    sql = text("""
           INSERT INTO invoice_detail (invoice_id, product_id, qty, price, subtotal, create_at)
           VALUES (:invoice_id, :product_id, :qty, :price, :subtotal, :create_at)
       """)
    db.session.execute(sql, {
        'invoice_id': invoice_id,
        'product_id': product_id,
        'qty': qty,
        'price': price,
        'subtotal': subtotal,
        'create_at': formatted_date
    })
    db.session.commit()
    return {
        'Message': 'Invoices detail created successfully',
         'invoice_detail': {
            "invoice_id": invoice_id,
            "product_id": product_id,
            "qty": qty,
            "price": price,
            "subtotal": subtotal,
            "create_at": display_date
        }
    }

@app.put('/invoice_details/update')
def update_invoice_details():
    data = request.get_json()
    invoice_detail_id = data.get('invoice_detail_id')
    if not data:
        return jsonify({'error': 'No Invoice details provided'})
    if not invoice_detail_id:
        return jsonify({'error': 'invoice_detail_id is required'})
    invoices = InvoiceDetail.query.get(invoice_detail_id)
    if not invoices:
        return jsonify({'error': 'invoice details not found'})

    invoice_id = data.get('invoice_id')
    product_id = data.get('product_id')
    qty = data.get('qty')
    price = data.get('price')

    if not invoice_id:
        return {'error': 'No invoice_id provided'}
    if not product_id:
        return {'error': 'No product_id provided'}
    if not qty:
        return {'error': 'No qty provided'}
    if not price:
        return {'error': 'No price provided'}

    create_at = datetime.now()
    formatted_date = create_at.strftime("%Y-%m-%d")
    display_date = create_at.strftime("%d-%m-%Y")
    subtotal = qty * price
    sql = text("""
      UPDATE invoice_detail
        SET invoice_id = :invoice_id,
            product_id = :product_id,
            qty = :qty,
            price = :price,
            subtotal = :subtotal,
            create_at = :create_at
        WHERE id = :invoice_detail_id
    """)
    db.session.execute(sql, {
        'invoice_id': invoice_id,
        'product_id': product_id,
        'qty': qty,
        'price': price,
        'subtotal': subtotal,
        'create_at': formatted_date,
        "invoice_detail_id": invoice_detail_id
    })
    db.session.commit()
    return {
        'Message': 'invoice details Update successfully',
        'Invoices Detail': {
            "invoice_id": invoice_id,
            "product_id": product_id,
            "qty": qty,
            "price": price,
            "subtotal": subtotal,
            "create_at": display_date,
            "invoice_detail_id": invoice_detail_id
        }
    }

@app.delete('/invoice_details/delete')
def delete_invoice_details():
    data = request.get_json()
    invoice_detail_id = data.get('invoice_detail_id')
    if not data:
        return jsonify({'error': 'No Invoice details provided'})
    if not invoice_detail_id:
        return jsonify({'error': 'invoice_detail_id is required'})
    invoice_detail = InvoiceDetail.query.get(invoice_detail_id)
    if not invoice_detail:
        return jsonify({'error': 'invoice_detail_id not found'})

    deleted_info = {
        "invoice_detail_id": invoice_detail_id,
        'invoice_id': invoice_detail.invoice_id,
        'product_id': invoice_detail.product_id,
        'qty': invoice_detail.qty,
        'price': invoice_detail.price,
        'subtotal': invoice_detail.subtotal,
        'create_at': invoice_detail.create_at

    }
    sql = text("DELETE FROM invoice_detail  WHERE id = :invoice_detail_id")
    db.session.execute(sql, {'invoice_detail_id': invoice_detail_id})
    db.session.commit()
    return {
        'Message': 'Invoice detail Delete successfully',
        'deleted_invoice_detail': deleted_info
    }