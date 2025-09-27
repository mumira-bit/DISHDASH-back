from flask import Flask, request, session, jsonify
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, User, Recipe, Review

app = Flask(__name__)
app.secret_key = b'YOUR_SECRET_KEY'  # change in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dishdash.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.update(
    SESSION_COOKIE_SECURE=True,      
    SESSION_COOKIE_SAMESITE='None',  
    SESSION_COOKIE_HTTPONLY=True
)

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

# ---- CORS Setup ----
CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",          
        "https://dishdash-7lzx.onrender.com" ,
        "https://dishdash-3ofz.onrender.com"
    ],
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        headers = response.headers
        headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        headers['Access-Control-Allow-Credentials'] = 'true'
        return response

@app.route('/')
def index():
    return {"message": "DishDash Backend running!"}

# ---- ADD THIS NEW ROUTE ----
@app.route('/check_session', methods=['GET'])
def check_session():
    print("Session data:", dict(session))  # Debug line
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            return jsonify({
                "id": user.id,
                "username": user.username, 
                "email": user.email
            }), 200
    return jsonify({"error": "Not authenticated"}), 401

# ---- ADD THIS NEW ROUTE ----
@app.route('/api/recipes', methods=['POST', 'GET'])
def handle_recipes():
    if request.method == 'POST':
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({"message": "Please log in first"}), 401
        
        data = request.get_json()
        
        # Create new recipe
        recipe = Recipe(
            title=data.get('title'),
            instructions=data.get('instructions'),
            prep_time=data.get('prep_time'),
            user_id=session['user_id']  # Link to logged-in user
        )
        
        db.session.add(recipe)
        db.session.commit()
        
        return jsonify({
            "message": "Recipe created successfully",
            "recipe": {
                "id": recipe.id,
                "title": recipe.title,
                "instructions": recipe.instructions,
                "prep_time": recipe.prep_time
            }
        }), 201
    
    elif request.method == 'GET':
        # Return all recipes (optional)
        recipes = Recipe.query.all()
        return jsonify([{
            "id": r.id,
            "title": r.title,
            "instructions": r.instructions,
            "prep_time": r.prep_time
        } for r in recipes]), 200

# ---- Login Resource ----
class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return {"message": "All fields are required"}, 400

        if User.query.filter_by(username=username).first():
            return {"message": "Username already exists"}, 400

        # Simplified password storage for demo (use bcrypt in production)
        user = User(username=username, email=email, password_hash=password)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id  # auto-login after signup

        return {"id": user.id, "username": user.username, "email": user.email}, 201

# ---- Login Resource ----
class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {"message": "Username and password required"}, 400

        user = User.query.filter_by(username=username).first()
        if user and user.password_hash == password:
            session['user_id'] = user.id
            return {"id": user.id, "username": user.username, "email": user.email}, 200
        return {"message": "Invalid credentials"}, 401

# ---- Logout Resource ----
class Logout(Resource):
    def delete(self):
        session.pop('user_id', None)
        return {"message": "Logged out successfully"}, 200

# ---- Add resources ----
api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')

if __name__ == '__main__':
    app.run(port=5002,debug=True)