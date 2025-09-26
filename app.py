from flask import Flask, request, session, jsonify
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, Recipe, User, Review
import os

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'  # Change this in production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dishdash.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)

# FIXED: Enable CORS for both possible frontend origins
CORS(app, 
     supports_credentials=True, 
     origins=["http://localhost:3000", "http://localhost:5173"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

# Test route to check if server is working
@app.route('/')
def index():
    return {"message": "DishDash Backend is running!", "status": "OK"}

# Authentication decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return {'message': 'Authentication required'}, 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def owner_required(f):
    def decorated_function(self, id, *args, **kwargs):
        if 'user_id' not in session:
            return {'message': 'Authentication required'}, 401
        
        recipe = Recipe.query.get(id)
        if not recipe:
            return {'message': 'Recipe not found'}, 404
            
        if recipe.user_id != session['user_id']:
            return {'message': 'Permission denied. You can only modify your own recipes'}, 403
            
        return f(self, id, *args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

class Recipes(Resource):
    def get(self):
        """GET /recipes - List all recipes"""
        try:
            recipes = Recipe.query.all()
            recipe_list = []
            
            for recipe in recipes:
                recipe_data = {
                    'id': recipe.id,
                    'title': recipe.title,
                    'instructions': recipe.instructions,
                    'prep_time': recipe.prep_time,
                    'user_id': recipe.user_id,
                    'created_at': recipe.created_at.isoformat() if recipe.created_at else None,
                    'user': {
                        'id': recipe.user.id,
                        'username': recipe.user.username
                    } if recipe.user else None
                }
                recipe_list.append(recipe_data)
            
            return recipe_list, 200
        except Exception as e:
            return {'message': f'Error retrieving recipes: {str(e)}'}, 500
    
    @login_required
    def post(self):
        """POST /recipes - Create a new recipe (auth required)"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['title', 'instructions', 'prep_time']
            for field in required_fields:
                if field not in data:
                    return {'message': f'Missing required field: {field}'}, 400
            
            # Create new recipe
            recipe = Recipe(
                title=data['title'],
                instructions=data['instructions'],
                prep_time=data['prep_time'],
                user_id=session['user_id']
            )
            
            db.session.add(recipe)
            db.session.commit()
            
            # Return recipe data manually to avoid serialization issues
            recipe_data = {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'prep_time': recipe.prep_time,
                'user_id': recipe.user_id,
                'created_at': recipe.created_at.isoformat() if recipe.created_at else None,
                'user': {
                    'id': recipe.user.id,
                    'username': recipe.user.username
                } if recipe.user else None
            }
            
            return recipe_data, 201
            
        except ValueError as e:
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating recipe: {str(e)}'}, 500

class RecipeById(Resource):
    def get(self, id):
        """GET /recipes/<id> - Show one recipe (with reviews)"""
        try:
            recipe = Recipe.query.get(id)
            if not recipe:
                return {'message': 'Recipe not found'}, 404
            
            # Manual serialization to avoid circular references
            recipe_data = {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'prep_time': recipe.prep_time,
                'user_id': recipe.user_id,
                'created_at': recipe.created_at.isoformat() if recipe.created_at else None,
                'user': {
                    'id': recipe.user.id,
                    'username': recipe.user.username
                } if recipe.user else None,
                'reviews': [
                    {
                        'id': review.id,
                        'rating': review.rating,
                        'comment': review.comment,
                        'created_at': review.created_at.isoformat() if review.created_at else None,
                        'user': {
                            'id': review.user.id,
                            'username': review.user.username
                        }
                    }
                    for review in recipe.reviews
                ]
            }
            
            return recipe_data, 200
            
        except Exception as e:
            return {'message': f'Error retrieving recipe: {str(e)}'}, 500
    
    @owner_required
    def patch(self, id):
        """PATCH /recipes/<id> - Edit (auth & owner-only)"""
        try:
            recipe = Recipe.query.get(id)
            data = request.get_json()
            
            # Update only provided fields
            if 'title' in data:
                recipe.title = data['title']
            if 'instructions' in data:
                recipe.instructions = data['instructions']
            if 'prep_time' in data:
                recipe.prep_time = data['prep_time']
            
            db.session.commit()
            
            # Return updated recipe data
            recipe_data = {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'prep_time': recipe.prep_time,
                'user_id': recipe.user_id,
                'created_at': recipe.created_at.isoformat() if recipe.created_at else None,
                'user': {
                    'id': recipe.user.id,
                    'username': recipe.user.username
                } if recipe.user else None
            }
            
            return recipe_data, 200
            
        except ValueError as e:
            db.session.rollback()
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error updating recipe: {str(e)}'}, 500
    
    @owner_required
    def delete(self, id):
        """DELETE /recipes/<id> - Delete (auth & owner-only)"""
        try:
            recipe = Recipe.query.get(id)
            db.session.delete(recipe)
            db.session.commit()
            return {'message': 'Recipe deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error deleting recipe: {str(e)}'}, 500

# Authentication routes
class CheckSession(Resource):
    def get(self):
        """Check if user is logged in"""
        print(f"Session check - session data: {dict(session)}")  # Debug log
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }, 200
        return {'message': 'No active session'}, 401

class Login(Resource):
    def post(self):
        """Login user"""
        try:
            data = request.get_json()
            print(f"Login attempt: {data}")  # Debug log
            
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return {'message': 'Username and password required'}, 400
            
            user = User.query.filter_by(username=username).first()
            
            # In production, use proper password hashing (bcrypt)
            if user and user.password_hash == password:  # Simplified for demo
                session['user_id'] = user.id
                print(f"Login successful for user: {user.username}")  # Debug log
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }, 200
            else:
                return {'message': 'Invalid credentials'}, 401
                
        except Exception as e:
            print(f"Login error: {e}")  # Debug log
            return {'message': f'Login error: {str(e)}'}, 500

class Logout(Resource):
    def delete(self):
        """Logout user"""
        if 'user_id' in session:
            del session['user_id']
            return {'message': 'Logged out successfully'}, 200
        return {'message': 'No active session'}, 400
    



    # Add these classes to your app.py file, before the api.add_resource lines

class Reviews(Resource):
    def get(self, recipe_id):
        """GET /recipes/<id>/reviews - Get all reviews for a recipe"""
        try:
            recipe = Recipe.query.get(recipe_id)
            if not recipe:
                return {'message': 'Recipe not found'}, 404
                
            reviews = Review.query.filter_by(recipe_id=recipe_id).all()
            review_list = []
            
            for review in reviews:
                review_data = {
                    'id': review.id,
                    'rating': review.rating,
                    'comment': review.comment,
                    'created_at': review.created_at.isoformat() if review.created_at else None,
                    'user': {
                        'id': review.user.id,
                        'username': review.user.username
                    } if review.user else None
                }
                review_list.append(review_data)
            
            return review_list, 200
        except Exception as e:
            return {'message': f'Error retrieving reviews: {str(e)}'}, 500
    
    @login_required
    def post(self, recipe_id):
        """POST /recipes/<id>/reviews - Create a new review"""
        try:
            recipe = Recipe.query.get(recipe_id)
            if not recipe:
                return {'message': 'Recipe not found'}, 404
            
            data = request.get_json()
            
            # Validate required fields
            if 'rating' not in data or 'comment' not in data:
                return {'message': 'Rating and comment are required'}, 400
            
            # Check if user already reviewed this recipe
            existing_review = Review.query.filter_by(
                user_id=session['user_id'], 
                recipe_id=recipe_id
            ).first()
            
            if existing_review:
                return {'message': 'You have already reviewed this recipe'}, 400
            
            # Don't let users review their own recipes
            if recipe.user_id == session['user_id']:
                return {'message': 'You cannot review your own recipe'}, 400
            
            # Create new review
            review = Review(
                rating=data['rating'],
                comment=data['comment'],
                user_id=session['user_id'],
                recipe_id=recipe_id
            )
            
            db.session.add(review)
            db.session.commit()
            
            # Return review data
            review_data = {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat() if review.created_at else None,
                'user': {
                    'id': review.user.id,
                    'username': review.user.username
                } if review.user else None
            }
            
            return review_data, 201
            
        except ValueError as e:
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating review: {str(e)}'}, 500

class ReviewById(Resource):
    @login_required
    def patch(self, recipe_id, review_id):
        """PATCH /recipes/<recipe_id>/reviews/<review_id> - Edit review (owner only)"""
        try:
            review = Review.query.get(review_id)
            if not review:
                return {'message': 'Review not found'}, 404
            
            if review.user_id != session['user_id']:
                return {'message': 'You can only edit your own reviews'}, 403
            
            data = request.get_json()
            
            if 'rating' in data:
                review.rating = data['rating']
            if 'comment' in data:
                review.comment = data['comment']
            
            db.session.commit()
            
            review_data = {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat() if review.created_at else None,
                'user': {
                    'id': review.user.id,
                    'username': review.user.username
                } if review.user else None
            }
            
            return review_data, 200
            
        except ValueError as e:
            db.session.rollback()
            return {'message': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error updating review: {str(e)}'}, 500
    
    @login_required
    def delete(self, recipe_id, review_id):
        """DELETE /recipes/<recipe_id>/reviews/<review_id> - Delete review (owner only)"""
        try:
            review = Review.query.get(review_id)
            if not review:
                return {'message': 'Review not found'}, 404
            
            if review.user_id != session['user_id']:
                return {'message': 'You can only delete your own reviews'}, 403
            
            db.session.delete(review)
            db.session.commit()
            return {'message': 'Review deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error deleting review: {str(e)}'}, 500




api.add_resource(Reviews, '/recipes/<int:recipe_id>/reviews')
api.add_resource(ReviewById, '/recipes/<int:recipe_id>/reviews/<int:review_id>')
api.add_resource(Recipes, '/recipes')
api.add_resource(RecipeById, '/recipes/<int:id>')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')

if __name__ == '__main__':
    app.run(port=5002, debug=True)