import uuid
from datetime import datetime

from app import app, db
from flask import jsonify, request
from sqlalchemy import text
from model import Product
from werkzeug.utils import secure_filename
import os


def get_full_image_url(image_path):
    if not image_path:
        return None
    return request.host_url.rstrip('/') + image_path

@app.get('/products')
@app.get('/products/list')
def get_products():
    sql = text("""
        SELECT p.id, UPPER(p.name) as product_name, 'true' as active, 
               '$' || p.price AS price, p.stock, p.description, 
               p.image, c.name as category_name, p.create_at
        FROM product AS p
        JOIN category AS c ON p.category_id = c.id
    """)
    result = db.session.execute(sql).fetchall()
    if not result:
        return jsonify({'message': 'No products found'})

    rows = []
    for row in result:
        r = dict(row._mapping)
        r['image'] = get_full_image_url(r['image'])
        rows.append(r)

    return jsonify(rows)

# --- GET product by ID ---
@app.get('/products/list/<int:id>')
def get_product_by_id(id):
    sql = text("""
        SELECT p.id, UPPER(p.name) as product_name, 'true' as active, 
               '$' || p.price AS price, p.stock, p.description, 
               p.image, c.name as category_name
        FROM product AS p
        JOIN category AS c ON p.category_id = c.id
        WHERE p.id = :id
    """)
    result = db.session.execute(sql, {'id': id}).fetchall()
    if not result:
        return jsonify({'error': 'Product not found'})

    rows = []
    for row in result:
        r = dict(row._mapping)
        r['image'] = get_full_image_url(r['image'])
        rows.append(r)

    return jsonify(rows)

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.post('/products/create')
def create_products():
    name = request.form.get('name')
    price = request.form.get('price')
    stock = request.form.get('stock')
    description = request.form.get('description')
    category_id = request.form.get('category_id')
    create_at = datetime.now()
    formatted_date = create_at.strftime("%Y-%m-%d")
    display_date = create_at.strftime("%d-%m-%Y")

    if not name:
        return {'error': 'No product name provided'}
    if not price:
        return {'error': 'No price provided'}
    if not stock:
        return {'error': 'No stock provided'}
    if not category_id:
        return {'error': 'No category_id provided'}
    try:
        price = float(price)
        stock = int(stock)
        category_id = int(category_id)
    except ValueError:
        return {'error': 'Invalid numeric value'}

    image_url = None
    if 'image' in request.files:
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = f"/{image_path.replace(os.sep, '/')}"
        else:
            return {'error': 'Invalid image file type'}
    sql = text("""
        INSERT INTO product (name, price, stock, description, image, category_id,create_at)
        VALUES (:name, :price, :stock, :description, :image, :category_id,:create_at)
    """)
    db.session.execute(sql, {
        "name": name,
        "price": price,
        "stock": stock,
        "description": description,
        "image": image_url,
        "category_id": category_id,
        "create_at": formatted_date,
    })
    db.session.commit()
    return {
        'Message': 'Product created successfully',
        'Products': {
            "name": name,
            "price": price,
            "stock": stock,
            "description": description,
            "image": image_url,
            "category_id": category_id,
            "create_at": display_date,
        }
    }

@app.put('/products/update/<int:id>')
def update_product(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({'error': 'Product not found'})

    name = request.form.get('name')
    price = request.form.get('price')
    stock = request.form.get('stock')
    description = request.form.get('description')
    category_id = request.form.get('category_id')

    if not name:
        return {'error': 'No product name provided'}
    if not price:
        return {'error': 'No price provided'}
    if not stock:
        return {'error': 'No stock provided'}
    if not category_id:
        return {'error': 'No category_id provided'}
    try:
        price = float(price)
        stock = int(stock)
        category_id = int(category_id)
    except ValueError:
        return {'error': 'Invalid numeric value'}
    image_url = None
    if 'image' in request.files:
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = f"/{image_path.replace(os.sep, '/')}"
        else:
            return {'error': 'Invalid image file type'}
    product.name = name
    product.price = price
    product.stock = stock
    product.description = description
    product.image = image_url
    product.category_id = category_id
    product.create_at = datetime.now()

    db.session.commit()
    return jsonify({
        'Message': 'Product updated successfully',
        'Product': {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock,
            'description': product.description,
            'image': product.image,
            'category_id': product.category_id,
            'create_at': product.create_at.strftime("%d-%m-%Y")


        }
    })

@app.delete('/products/delete')
def delete_product():
    data = request.get_json()
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'error': 'Product ID is required'})

    product = Product.query.get_or_404(product_id)
    if product.image:
        image_path = product.image.lstrip('/')
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(product)
    db.session.commit()

    return {
        'message': 'Product deleted successfully',
        'Product': {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock,
            'description': product.description,
            'image': product.image,
            'category_id': product.category_id,
            'create_at': product.create_at.strftime("%d-%m-%Y")
        }
    }

