#!/usr/bin/env python3

from random import randint, choice as rc
from faker import Faker
from app import app
from models import db, User, Recipe, Review

fake = Faker()

def create_users():
    """Create sample users"""
    users = []
    
    
    test_user = User(
        username='testuser',
        email='test@example.com',
        password_hash='password123'  
    )
    users.append(test_user)
    
    
    for _ in range(4):
        user = User(
            username=fake.user_name(),
            email=fake.email(),
            password_hash='password123'  
        )
        users.append(user)
    
    return users

def create_recipes(users):
    """Create sample recipes"""
    recipes = []
    
    recipe_data = [
        {
            'title': 'Classic Spaghetti Bolognese',
            'instructions': '''1. Heat olive oil in a large pan over medium heat.
2. Add onions, carrots, and celery. Cook until softened (about 5 minutes).
3. Add ground beef and cook until browned, breaking it up with a spoon.
4. Add tomato paste and cook for 1 minute.
5. Add crushed tomatoes, red wine, and herbs. Simmer for 30 minutes.
6. Cook spaghetti according to package directions.
7. Serve sauce over pasta with grated Parmesan cheese.''',
            'prep_time': 45
        },
        {
            'title': 'Creamy Chicken Curry',
            'instructions': '''1. Cut chicken into bite-sized pieces and season with salt and pepper.
2. Heat oil in a large pan and brown the chicken pieces.
3. Remove chicken and sauté onions until golden.
4. Add garlic, ginger, and curry spices. Cook for 1 minute.
5. Add coconut milk and tomatoes. Bring to a simmer.
6. Return chicken to pan and cook for 15 minutes until tender.
7. Garnish with cilantro and serve with rice.''',
            'prep_time': 30
        },
        {
            'title': 'Fresh Caesar Salad',
            'instructions': '''1. Wash and chop romaine lettuce into bite-sized pieces.
2. Make croutons by toasting bread cubes with olive oil and garlic.
3. For dressing: whisk together mayonnaise, lemon juice, Worcestershire sauce, and garlic.
4. Add grated Parmesan cheese to dressing.
5. Toss lettuce with dressing until well coated.
6. Top with croutons and additional Parmesan cheese.''',
            'prep_time': 15
        },
        {
            'title': 'Beef Stir Fry with Vegetables',
            'instructions': '''1. Slice beef thinly against the grain and marinate in soy sauce.
2. Heat wok or large pan over high heat with oil.
3. Stir-fry beef until just cooked through, then remove.
4. Add vegetables (bell peppers, broccoli, snap peas) and stir-fry until crisp-tender.
5. Return beef to pan with garlic and ginger.
6. Add sauce mixture and toss everything together.
7. Serve immediately over steamed rice.''',
            'prep_time': 25
        },
        {
            'title': 'Decadent Chocolate Cake',
            'instructions': '''1. Preheat oven to 350°F (175°C). Grease and flour cake pans.
2. Mix dry ingredients (flour, cocoa powder, sugar, baking powder) in large bowl.
3. In separate bowl, whisk together eggs, milk, oil, and vanilla.
4. Combine wet and dry ingredients until smooth.
5. Pour into prepared pans and bake for 30-35 minutes.
6. Cool completely before frosting with chocolate buttercream.
7. Decorate as desired and serve.''',
            'prep_time': 90
        },
        {
            'title': 'Grilled Fish Tacos',
            'instructions': '''1. Season fish fillets with lime juice, cumin, and chili powder.
2. Grill fish for 3-4 minutes per side until flaky.
3. Warm tortillas on the grill or in a dry pan.
4. Make slaw by mixing shredded cabbage with lime juice and cilantro.
5. Flake the grilled fish into chunks.
6. Assemble tacos with fish, slaw, and avocado slices.
7. Serve with lime wedges and hot sauce.''',
            'prep_time': 20
        }
    ]
    
    for recipe_info in recipe_data:
        recipe = Recipe(
            title=recipe_info['title'],
            instructions=recipe_info['instructions'],
            prep_time=recipe_info['prep_time'],
            user_id=rc(users).id
        )
        recipes.append(recipe)
    
    return recipes

def create_reviews(users, recipes):
    """Create sample reviews"""
    reviews = []
    
    review_comments = [
        "Absolutely delicious! My family loved it.",
        "Easy to follow recipe, great results.",
        "This turned out perfectly, will make again!",
        "Good recipe but needed a bit more seasoning.",
        "Classic dish done right. Highly recommend!",
        "Simple ingredients but amazing flavor.",
        "Perfect for a weeknight dinner.",
        "This is now my go-to recipe for this dish.",
        "Instructions were clear and easy to follow.",
        "Great comfort food, very satisfying."
    ]
    
    
    for recipe in recipes:
        num_reviews = randint(2, 4)
        reviewed_users = []
        
        for _ in range(num_reviews):
            # Don't let users review their own recipes
            available_users = [u for u in users if u.id != recipe.user_id and u not in reviewed_users]
            if available_users:
                reviewer = rc(available_users)
                reviewed_users.append(reviewer)
                
                review = Review(
                    rating=randint(3, 5),  # Mostly positive reviews
                    comment=rc(review_comments),
                    user_id=reviewer.id,
                    recipe_id=recipe.id
                )
                reviews.append(review)
    
    return reviews

if __name__ == '__main__':
    with app.app_context():
        print("🌱 Clearing existing data...")
        db.drop_all()
        db.create_all()
        
        print("👥 Creating users...")
        users = create_users()
        db.session.add_all(users)
        db.session.commit()
        
        print("🍳 Creating recipes...")
        recipes = create_recipes(users)
        db.session.add_all(recipes)
        db.session.commit()
        
        print("⭐ Creating reviews...")
        reviews = create_reviews(users, recipes)
        db.session.add_all(reviews)
        db.session.commit()
        
        print("✅ Database seeded successfully!")
        print(f"Created:")
        print(f"  - {len(users)} users")
        print(f"  - {len(recipes)} recipes")
        print(f"  - {len(reviews)} reviews")
        print("\n🔑 Test user login:")
        print("  Username: testuser")
        print("  Password: password123")