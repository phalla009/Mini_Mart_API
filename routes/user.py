import re
from app import app, db
from flask import jsonify, request
from sqlalchemy import text
from werkzeug.utils import secure_filename
import os
import uuid
from model import User

from werkzeug.security import check_password_hash, generate_password_hash
@app.get('/users')
def get_user():
    sql = text("SELECT id, UPPER(name) as name , 'true' as active , email ,image FROM user")
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    if not rows:
        return jsonify({'message': 'No users found'})
    return jsonify(rows)

@app.get('/users/list')
def get_all_users():
    sql = text("SELECT id, UPPER(name) as name , 'true' as active , email, image FROM user")
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    return jsonify(rows)

def fetch_user_by_id(user_id: int):
    sql = text("SELECT id, UPPER(name) as name , 'true' as active , email,image FROM user WHERE id = :user_id")
    result = db.session.execute(sql, {"user_id": user_id}).fetchone()
    if not result:
        return None
    return dict(result._mapping)

@app.get('/users/list/<int:user_id>')
def get_user_id(user_id: int):
    user = fetch_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'})
    return jsonify(user)

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None
@app.post('/users/create')
def create_user():
    name = request.form.get('name')
    password = request.form.get('password')
    email = request.form.get('email')
    if not name:
        return jsonify({'Error': 'No user name provided'})
    if not password:
        return jsonify({'Error': 'No password provided'})
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email format',
                        'simple':'example@gmail.com'})
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
    new_user = User(
        name=name,
        password=generate_password_hash(password),
        email=email,
        image=image_url
    )
    db.session.add(new_user)
    db.session.commit()
    return {'Message': 'User created Successfully',
            'user': {
                'id': new_user.id,
                'name': new_user.name,
                'email': new_user.email,
                'image': new_user.image
                }
            }

@app.put('/users/update/<int:id>')
def update_user(id):
    user = User.query.get(id)
    if not user:
        return {'error': 'User not found'}

    name = request.form.get('name')
    password = request.form.get('password')
    email = request.form.get('email')
    if not name:
        return jsonify({'Error': 'No user name provided'})
    if not password:
        return jsonify({'Error': 'No password provided'})
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email format',
                        'simple': 'example@gmail.com'})
    user.name = name
    user.password = password
    user.email = email

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
    user = User(
        name=name,
        password=password,
        email=email,
        image=image_url
    )
    db.session.commit()
    return {'Message': 'User Update Successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'image': user.image
            }
    }

@app.delete('/users/delete')
def delete_user():
    user = request.get_json()
    if not user or 'user_id' not in user:
        return {'error': 'user_id is required'}
    user_id = user['user_id']
    is_exists = fetch_user_by_id(user_id)
    if not is_exists:
        return {'message': 'User not found'}

    sql = text("DELETE FROM user WHERE id = :user_id")
    db.session.execute(sql, {"user_id": user_id})
    db.session.commit()

    return {
        'message': 'User deleted successfully',
        'deleted_user': is_exists
    }

