from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin

metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

db = SQLAlchemy(metadata=metadata)

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'
    
    
    serialize_rules = ('-user.recipes', '-user.reviews', '-reviews.recipe', '-reviews.user.recipes', '-reviews.user.reviews')
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    prep_time = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())
    
    
    user = db.relationship('User', back_populates='recipes')
    reviews = db.relationship('Review', back_populates='recipe', cascade='all, delete-orphan')
    
    
    reviewers = association_proxy('reviews', 'user')
    
    @validates('prep_time')
    def validate_prep_time(self, key, prep_time):
        if not isinstance(prep_time, int) or prep_time <= 0:
            raise ValueError("Prep time must be a positive integer")
        return prep_time
    
    @validates('title')
    def validate_title(self, key, title):
        if not title or len(title.strip()) == 0:
            raise ValueError("Title cannot be empty")
        if len(title) > 100:
            raise ValueError("Title cannot exceed 100 characters")
        return title.strip()
    
    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if not instructions or len(instructions.strip()) == 0:
            raise ValueError("Instructions cannot be empty")
        return instructions.strip()
    
    def __repr__(self):
        return f'<Recipe {self.id}: {self.title}>'


class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    
    
    serialize_rules = ('-recipes.user', '-recipes.reviews', '-reviews.user', '-reviews.recipe', '-password_hash')
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    
    recipes = db.relationship('Recipe', back_populates='user', cascade='all, delete-orphan')
    reviews = db.relationship('Review', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Review(db.Model, SerializerMixin):
    __tablename__ = 'reviews'
    
    
    serialize_rules = ('-recipe.reviews', '-recipe.user.recipes', '-recipe.user.reviews', 
                      '-user.reviews', '-user.recipes')
    
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', back_populates='reviews')
    recipe = db.relationship('Recipe', back_populates='reviews')
    
    @validates('rating')
    def validate_rating(self, key, rating):
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValueError("Rating must be an integer between 1 and 5")
        return rating
    
    def __repr__(self):
        return f'<Review {self.id}: {self.rating} stars for Recipe {self.recipe_id}>'