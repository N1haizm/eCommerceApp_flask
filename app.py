from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///company.db"
db = SQLAlchemy(app)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending")
    admin_comment = db.Column(db.Text)
    company_id = db.Column(
        db.Integer, db.ForeignKey('company.id'), nullable=True)
    company = db.relationship(
        'Company', backref=db.backref('problems', lazy=True))

# endpoints

@app.route('/companies/pending', methods=['GET'])
def list_pending_companies():
    pending_companies = Company.query.filter_by(status='pending').all()
    return jsonify([{'id': company.id, 'name': company.name, 'description': company.description, 'status': company.status} for company in pending_companies])

@app.route('/companies/approve/<int:company_id>', methods=['POST'])
def approve_company(company_id):
    company = Company.query.get(company_id)
    if company:
        company.status = 'approved'
        db.session.commit()
        return jsonify({'message': 'Company approved successfully'})
    else:
        return jsonify({'error': 'Company not found'}), 404

# Endpoint to reject a company
@app.route('/companies/reject/<int:company_id>', methods=['POST'])
def reject_company(company_id):
    company = Company.query.get(company_id)
    if company:
        company.status = 'rejected'
        db.session.commit()
        return jsonify({'message': 'Company rejected successfully'})
    else:
        return jsonify({'error': 'Company not found'}), 404

@app.route('/admin/create', methods=['POST'])
def create_admin_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    password_hash = generate_password_hash(password)

    new_admin = Admin(username=username, email=email, password_hash=password_hash)
    db.session.add(new_admin)
    db.session.commit()

    return jsonify({'message': 'Admin user created successfully'})

# Endpoint to list all admin users
@app.route('/admin/list', methods=['GET'])
def list_admin_users():
    admin_users = Admin.query.all()
    return jsonify([{'id': admin.id, 'username': admin.username, 'email': admin.email} for admin in admin_users])

# Endpoint to register a new user
@app.route('/register/user', methods=['POST'])
def register_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Hash the password
    password_hash = generate_password_hash(password)

    new_user = User(username=username, email=email, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'})

@app.route('/register/company', methods=['POST'])
def register_company():
    data = request.json
    name = data.get('name')
    description = data.get('description')
    password = data.get('password')
    
    password_hash = generate_password_hash(password)

    new_company = Company(name=name, description=description, password_hash=password_hash)
    db.session.add(new_company)
    db.session.commit()

    return jsonify({'message': 'Company registered successfully'})

@app.route('/login/user', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        return jsonify({'message': 'User logged in successfully'})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/login/company', methods=['POST'])
def login_company():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    company = Company.query.filter_by(email=email).first()

    if company and check_password_hash(company.password_hash, password):
        return jsonify({'message': 'Company logged in successfully'})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/problems/submit', methods=['POST'])
def submit_problem():
    data = request.json
    user_id = data.get('user_id') 
    description = data.get('description')
    company_id = data.get('company_id')
    
    # Create a new problem object
    new_problem = Problem(user_id=user_id, description=description, company_id = company_id)
    db.session.add(new_problem)
    db.session.commit()

    return jsonify({'message': 'Problem submitted successfully'})

@app.route('/problems/user/<int:user_id>', methods=['GET'])
def list_user_problems(user_id):
    user_problems = Problem.query.filter_by(user_id=user_id).all()
    return jsonify([{'id': problem.id, 'description': problem.description, 'status': problem.status, 'admin_comment': problem.admin_comment, "company_id": problem.company_id} for problem in user_problems])

@app.route('/problems/all', methods=['GET'])
def list_all_problems():
    all_problems = Problem.query.all()
    return jsonify([{'id': problem.id, 'description': problem.description, 'status': problem.status, 'admin_comment': problem.admin_comment, "company_id": problem.company_id} for problem in all_problems])

@app.route('/problems/review/<int:problem_id>', methods=['POST'])
def review_problem(problem_id):
    data = request.json
    new_status = data.get('status')
    admin_comment = data.get('admin_comment')
    problem = Problem.query.get(problem_id)
    if problem:
        if new_status:
            problem.status = new_status
        if admin_comment:
            problem.admin_comment = admin_comment
        db.session.commit()
        return jsonify({'message': 'Problem reviewed successfully'})
    else:
        return jsonify({'error': 'Problem not found'}), 404

# Endpoint to get all companies
@app.route('/companies/all', methods=['GET'])
def list_all_companies():
    all_companies = Company.query.all()
    return jsonify([{'id': company.id, 'name': company.name, 'description': company.description, 'status': company.status} for company in all_companies])

# Endpoint to list all users
@app.route('/users/all', methods=['GET'])
def list_all_users():
    all_users = User.query.all()
    return jsonify([{'id': user.id, 'username': user.username, 'email': user.email} for user in all_users])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True, host="localhost", port=5000)
