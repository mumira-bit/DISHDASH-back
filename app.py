
from flask import Flask, request, jsonify, session
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, User, Recipe, Review  
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dishdash.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key-here'  


db.init_app(app)
migrate = Migrate(app, db)
CORS(app)




@app.route('/signup', methods=["POST"])  
def sign_up():
    data = request.get_json()

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():  # Fixed typo
        return jsonify({'error': 'Email already exists'}), 409
    
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=data['password']  
    )
    
    db.session.add(new_user)
    db.session.commit()
    session['user_id'] = new_user.id  
    return jsonify(new_user.to_dict()), 201




@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.authenticate(data['password']):
        session['user_id'] = user.id
        return jsonify(user.to_dict())
    
    return jsonify({'error': 'Invalid credentials'}), 401



@app.route('/logout', methods=['DELETE'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200



@app.route('/check_session', methods=['GET'])
def check_session():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        return jsonify(user.to_dict())
    return jsonify({'error': 'Not logged in'}), 401


@app.route('/recipes', methods=['GET'])
def get_all_recipes():
    recipes = Recipe.query.all()
    return jsonify([recipe.to_dict() for recipe in recipes])

@app.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return jsonify(recipe.to_dict())

@app.route('/recipes', methods=['POST'])
def create_recipe():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.get_json()
    new_recipe = Recipe(
        title=data['title'],
        instructions=data['instructions'],
        prep_time=data['prep_time'],
        image_url=data.get('image_url'),
        user_id=session['user_id']
    )
    
    db.session.add(new_recipe)
    db.session.commit()
    return jsonify(new_recipe.to_dict()), 201

@app.route('/recipes/<int:recipe_id>', methods=['PATCH'])
def update_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if recipe.user_id != session.get('user_id'):
        return jsonify({'error': 'Not authorized'}), 403
        
    data = request.get_json()
    if 'title' in data: recipe.title = data['title']
    if 'instructions' in data: recipe.instructions = data['instructions']
    if 'prep_time' in data: recipe.prep_time = data['prep_time']
    if 'image_url' in data: recipe.image_url = data['image_url']
    
    db.session.commit()
    return jsonify(recipe.to_dict())

@app.route('/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if recipe.user_id != session.get('user_id'):
        return jsonify({'error': 'Not authorized'}), 403
        
    db.session.delete(recipe)
    db.session.commit()
    return jsonify({'message': 'Recipe deleted successfully'}), 200


@app.route('/recipes/<int:recipe_id>/reviews', methods=['GET'])
def get_recipe_reviews(recipe_id):
    reviews = Review.query.filter_by(recipe_id=recipe_id).all()
    return jsonify([review.to_dict() for review in reviews])

@app.route('/recipes/<int:recipe_id>/reviews', methods=['POST'])
def create_review(recipe_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.get_json()
    new_review = Review(
        rating=data['rating'],
        comment=data.get('comment', ''),
        user_id=session['user_id'],
        recipe_id=recipe_id
    )
    
    db.session.add(new_review)
    db.session.commit()
    return jsonify(new_review.to_dict()), 201



@app.route('/')
def home():
    return jsonify({'message': 'API is working!'})







if __name__ == '__main__':
 with app.app_context():
    db.create_all()
    app.run(port=5002, debug=True)

