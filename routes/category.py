from unicodedata import category

from app import app, db
from flask import jsonify, request
from sqlalchemy import text
from werkzeug.utils import secure_filename
import os
import uuid

from model import Category


@app.get('/category')
def get_category():
    sql = text("SELECT id, UPPER(name) as name , 'true' as active FROM category")
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    if not rows:
        return jsonify({'message': 'No category found'})
    return jsonify(rows)

@app.get('/category/list')
def get_all_category():
    sql = text("SELECT id, UPPER(name) as name , 'true' as active FROM category")
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    if not rows:
        return jsonify({'message': 'No category found'})
    return jsonify(rows)

@app.get('/category/list/<int:id>')
def get_category_by_id(id):
    category = Category.query.get_or_404(id)
    return jsonify({
        'id': category.id,
        'name': category.name,
    })


def sql_fetch(category_id: int):
    sql = text("SELECT id, UPPER(name) as name FROM category WHERE id = :id")
    result = db.session.execute(sql, {"id": category_id}).fetchone()
    if not result:
        return None
    return dict(result._mapping)

@app.post('/category/create')
def add_category():
    data = request.get_json()
    if 'name' not in data:
        return jsonify({
            'error': "Missing key 'name' in request"
        })
    new_category = Category(
        name=data['name'],
    )
    db.session.add(new_category)
    db.session.commit()
    add_product = sql_fetch(new_category.id)
    return jsonify({
        'message': 'Product added successfully',
        'product': add_product
    })


@app.put('/category/update')
def update_category():
    data = request.get_json()
    category_id = data.get('category_id')
    if not category_id:
        return jsonify(
            {
                'error': 'Category ID is required'
            }
        )
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'Category not found'})

    new_name = data.get('name')
    if not new_name:
        return jsonify({'error': "Missing key 'name' in request"})
    category.name = new_name
    db.session.commit()
    category_info = {
        'id': category_id,
        'name': category.name,

    }
    return jsonify({
        'message': 'Category updated successfully',
        'category': category_info
    })


@app.delete('/category/delete')
def delete_category():
    data = request.get_json()
    category_id = data.get('category_id')
    if not category_id:
        return jsonify({'error': 'Category ID is required'})
    category = Category.query.get_or_404(category_id)

    db.session.delete(category)
    db.session.commit()
    category_info = {
        'id': category.id,
        'name': category.name,

    }
    return jsonify({
        'message': 'Category deleted successfully',
        'product': category_info
    })
