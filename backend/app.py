import os
import sqlite3
import jwt
import bcrypt
import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger

app = Flask(__name__)
CORS(app)

# Swagger Configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "RBAC Full-Stack API",
        "description": "API for Authentication and Role-Based Access Control",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
        }
    },
    "security": [
        {
            "Bearer": []
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)


SECRET_KEY = "super_secret_intern_key_change_in_prod"
DB_FILE = "rbac_app.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('User', 'Admin'))
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# Middleware to verify JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            conn = get_db_connection()
            current_user = conn.execute('SELECT * FROM users WHERE id = ?', (data['user_id'],)).fetchone()
            conn.close()
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# Middleware to verify Admin role
def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user['role'] != 'Admin':
            return jsonify({'message': 'Admin access required!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: John Doe
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: strongpassword123
            role:
              type: string
              enum: [User, Admin]
              default: User
    responses:
      201:
        description: User registered successfully
      400:
        description: Missing required fields
      409:
        description: User already exists
    """
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields (name, email, password)'}), 400
    
    role = data.get('role', 'User')
    if role not in ['User', 'Admin']:
        role = 'User'

    name = data['name']
    email = data['email']
    password = data['password']
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                     (name, email, hashed_password, role))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'User with this email already exists'}), 409
    
    conn.close()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login a user and retrieve JWT
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: strongpassword123
    responses:
      200:
        description: Successfully authenticated
        schema:
          type: object
          properties:
            token:
              type: string
            user:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                email:
                  type: string
                role:
                  type: string
      400:
        description: Missing email or password
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Could not verify', 'error': 'Missing email or password'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (data['email'],)).fetchone()
    conn.close()

    if not user:
        return jsonify({'message': 'Could not verify', 'error': 'User not found'}), 401

    if bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }
        })

    return jsonify({'message': 'Could not verify', 'error': 'Invalid password'}), 401

@app.route('/api/users/me', methods=['GET'])
@token_required
def get_me(current_user):
    """
    Get current user profile
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: Current user details
      401:
        description: Unauthorized
    """
    return jsonify({
        'id': current_user['id'],
        'name': current_user['name'],
        'email': current_user['email'],
        'role': current_user['role']
    })

@app.route('/api/users', methods=['GET'])
@token_required
@admin_required
def get_all_users(current_user):
    """
    Get all users (Admin only)
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: List of all users
      401:
        description: Unauthorized
      403:
        description: Forbidden (Admin access required)
    """
    conn = get_db_connection()
    users = conn.execute('SELECT id, name, email, role FROM users').fetchall()
    conn.close()
    
    return jsonify([dict(u) for u in users])

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(current_user, user_id):
    """
    Update a user (Admin only)
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
        description: The ID of the user to update
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            email:
              type: string
            role:
              type: string
              enum: [User, Admin]
    responses:
      200:
        description: User updated successfully
      400:
        description: Invalid data
      404:
        description: User not found
    """
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'message': 'User not found'}), 404

    new_name = data.get('name', user['name'])
    new_email = data.get('email', user['email'])
    new_role = data.get('role', user['role'])

    if new_role not in ['User', 'Admin']:
        new_role = 'User'

    try:
        conn.execute('UPDATE users SET name = ?, email = ?, role = ? WHERE id = ?',
                     (new_name, new_email, new_role, user_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'Email already in use'}), 409
        
    conn.close()
    return jsonify({'message': 'User updated successfully'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_id):
    """
    Delete a user (Admin only)
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
        description: The ID of the user to delete
    responses:
      200:
        description: User deleted successfully
      404:
        description: User not found
      400:
        description: Cannot delete yourself
    """
    if current_user['id'] == user_id:
        return jsonify({'message': 'Cannot delete your own account'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'message': 'User not found'}), 404

    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'User deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
