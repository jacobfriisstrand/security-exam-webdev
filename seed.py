import x
import uuid
import time
import random
import sys
from werkzeug.security import generate_password_hash
from faker import Faker

fake = Faker()

from icecream import ic
ic.configureOutput(prefix=f'***** | ', includeContext=True)


db, cursor = x.db()


def insert_user(user):       
    q = f"""
        INSERT INTO users
        VALUES (%s, %s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s)        
        """
    values = tuple(user.values())
    cursor.execute(q, values)





try:

    ##############################
    # Insert Roles
    cursor.execute(f"""
        INSERT INTO roles (role_pk, role_name)
        VALUES ("{x.ADMIN_ROLE_PK}", "admin"), 
               ("{x.CUSTOMER_ROLE_PK}", "customer"), 
               ("{x.PARTNER_ROLE_PK}", "partner"), 
               ("{x.RESTAURANT_ROLE_PK}", "restaurant")
    """)

    ############################## 
    # Create admin user
    user_pk = str(uuid.uuid4())
    user = {
        "user_pk" : user_pk,
        "user_name" : "Jonas",
        "user_last_name" : "Blædel",
        "user_email" : "admin@fulldemo.com",
        "user_password" : generate_password_hash("password"),
        "user_image" : "profile_10.jpg",
        "user_created_at" : int(time.time()),
        "user_deleted_at" : 0,
        "user_blocked_at" : 0,
        "user_updated_at" : 0,
        "user_verified_at" : int(time.time()),
        "user_verification_key" : str(uuid.uuid4()) 
    }            
    insert_user(user)
    # Assign role to admin user
    q = f"""
        INSERT INTO users_roles (user_role_user_fk, user_role_role_fk) VALUES ("{user_pk}", 
        "{x.ADMIN_ROLE_PK}")        
        """    
    cursor.execute(q)    

    ############################## 
    # Create customer
    user_pk = "4218788d-03b7-4812-bd7d-31c8859e92d8"
    user = {
        "user_pk" : user_pk,
        "user_name" : "Jonas",
        "user_last_name" : "Lundberg",
        "user_email" : "jonas@bobles.dk",
        "user_password" : generate_password_hash("password"),
        "user_image" : "profile_11.jpg",
        "user_created_at" : int(time.time()),
        "user_deleted_at" : 0,
        "user_blocked_at" : 0,
        "user_updated_at" : 0,
        "user_verified_at" : int(time.time()),
        "user_verification_key" : str(uuid.uuid4())
    }
    insert_user(user)
   
    # Assign role to customer user
    q = f"""
        INSERT INTO users_roles (user_role_user_fk, user_role_role_fk) VALUES ("{user_pk}", 
        "{x.CUSTOMER_ROLE_PK}")        
        """    
    cursor.execute(q)


    ############################## 
    # Create partner
    user_pk = str(uuid.uuid4())
    user = {
        "user_pk" : user_pk,
        "user_name" : "John",
        "user_last_name" : "Partner",
        "user_email" : "partner@fulldemo.com",
        "user_password" : generate_password_hash("password"),
        "user_image" : "profile_12.jpg",
        "user_created_at" : int(time.time()),
        "user_deleted_at" : 0,
        "user_blocked_at" : 0,
        "user_updated_at" : 0,
        "user_verified_at" : int(time.time()),
        "user_verification_key" : str(uuid.uuid4())
    }
    insert_user(user)
    # Assign role to partner user
    q = f"""
        INSERT INTO users_roles (user_role_user_fk, user_role_role_fk) VALUES ("{user_pk}", 
        "{x.PARTNER_ROLE_PK}")        
        """    
    cursor.execute(q)

    ############################## 
    # Create restaurant
    user_pk = str(uuid.uuid4())
    user = {
        "user_pk" : user_pk,
        "user_name" : "Mc",
        "user_last_name" : "Restaurant",
        "user_email" : "restaurant@fulldemo.com",
        "user_password" : generate_password_hash("password"),
        "user_image" : "restaurant_"+ str(random.randint(1, 50)) +".jpg",
        "user_created_at" : int(time.time()),
        "user_deleted_at" : 0,
        "user_blocked_at" : 0,
        "user_updated_at" : 0,
        "user_verified_at" : int(time.time()),
        "user_verification_key" : str(uuid.uuid4())
    }
    insert_user(user)
    
    # Assign role to restaurant user
    q = f"""
        INSERT INTO users_roles (user_role_user_fk, user_role_role_fk) VALUES ("{user_pk}", 
        "{x.RESTAURANT_ROLE_PK}")        
        """    
    cursor.execute(q)


    ############################## 
    # Create 50 customer

    domains = ["example.com", "testsite.org", "mydomain.net", "website.co", "fakemail.io", "gmail.com", "hotmail.com"]
    user_password = hashed_password = generate_password_hash("password")
    for _ in range(50):
        user_pk = str(uuid.uuid4())
        user_verified_at = random.choice([0,int(time.time())])
        user = {
            "user_pk" : user_pk,
            "user_name" : fake.first_name(),
            "user_last_name" : fake.last_name(),
            "user_email" : fake.unique.user_name() + "@" + random.choice(domains),
            "user_password" : user_password,
            # user_password = hashed_password = generate_password_hash(fake.password(length=20))
            "user_image" : "profile_"+ str(random.randint(1, 100)) +".jpg",
            "user_created_at" : int(time.time()),
            "user_deleted_at" : 0,
            "user_blocked_at" : 0,
            "user_updated_at" : 0,
            "user_verified_at" : user_verified_at,
            "user_verification_key" : str(uuid.uuid4())
        }

        insert_user(user)
        cursor.execute("""INSERT INTO users_roles (
            user_role_user_fk,
            user_role_role_fk)
            VALUES (%s, %s)""", (user_pk, x.CUSTOMER_ROLE_PK))


    ############################## 
    # Create 50 partners

    user_password = hashed_password = generate_password_hash("password")
    for _ in range(50):
        user_pk = str(uuid.uuid4())
        user_verified_at = random.choice([0,int(time.time())])
        user = {
            "user_pk" : user_pk,
            "user_name" : fake.first_name(),
            "user_last_name" : fake.last_name(),
            "user_email" : fake.unique.email(),
            "user_password" : user_password,
            "user_image" : "profile_"+ str(random.randint(1, 100)) +".jpg",
            "user_created_at" : int(time.time()),
            "user_deleted_at" : 0,
            "user_blocked_at" : 0,
            "user_updated_at" : 0,
            "user_verified_at" : user_verified_at,
            "user_verification_key" : str(uuid.uuid4())
        }

        insert_user(user)

        cursor.execute("""
        INSERT INTO users_roles (
            user_role_user_fk,
            user_role_role_fk)
            VALUES (%s, %s)
        """, (user_pk, x.PARTNER_ROLE_PK))

    ############################## 
    # Create 50 restaurants
    dishes = ["Margherita Pizza", "Pepperoni Pizza", "Hawaiian Pizza", "BBQ Chicken Pizza", "Veggie Pizza", "Meat Lovers Pizza", "Four Cheese Pizza", "Seafood Pizza", "Spaghetti Carbonara", "Penne Arrabbiata", "Fettuccine Alfredo", "Lasagna", "Ravioli with Spinach and Ricotta", "Gnocchi with Pesto", "Macaroni and Cheese", "Linguine with Clam Sauce", "Beef Burger", "Cheeseburger", "Chicken Burger", "Veggie Burger", "Mushroom Swiss Burger", "Bacon Cheeseburger", "BBQ Burger", "Double Patty Burger", "Green Curry", "Pad Thai", "Red Curry", "Massaman Curry", "Tom Yum Soup", "Thai Basil Chicken", "Mango Sticky Rice", "Pineapple Fried Rice", "California Roll", "Salmon Sushi", "Tuna Sushi", "Vegetarian Sushi", "Dragon Roll", "Tempura Sushi Roll", "Philadelphia Roll", "Rainbow Roll", "Caesar Salad", "Greek Salad", "Cobb Salad", "Caprese Salad", "Quinoa Salad", "Spinach Salad with Strawberries", "Kale Salad with Lemon Dressing", "Mixed Greens with Walnuts", "Club Sandwich", "BLT Sandwich", "Turkey and Swiss Sandwich", "Chicken Avocado Sandwich", "Tuna Melt", "Grilled Cheese Sandwich", "Philly Cheesesteak", "Pulled Pork Sandwich", "Tom Kha Gai", "Thai Shrimp Salad", "Yellow Curry", "Beef Pho", "Vegetarian Pho", "Vietnamese Spring Rolls", "Chicken Satay", "Pork Dumplings", "Vegetable Dumplings", "Beef Udon Noodles", "Miso Soup", "Katsu Curry", "Salmon Teriyaki", "Shrimp Tempura", "Seaweed Salad", "Cucumber Sushi", "Avocado Sushi", "Tuna Poke Bowl", "Spaghetti Bolognese", "Shrimp Scampi", "Baked Ziti", "Stuffed Shells", "Pasta Primavera", "Pesto Pasta", "Chicken Parmesan", "Eggplant Parmesan", "Margarita Pizza", "Diavola Pizza", "Funghi Pizza", "Capricciosa Pizza", "Prosciutto Pizza", "Quattro Formaggi Pizza", "Tuna Salad", "Waldorf Salad", "Asian Chicken Salad", "Avocado Salad", "Pasta Salad", "Potato Salad", "Niçoise Salad", "Roast Beef Sandwich", "Meatball Sub", "Chicken Caesar Wrap", "Egg Salad Sandwich", "Ham and Cheese Croissant", "Focaccia Sandwich", "Falafel Wrap", "Grilled Vegetable Panini", "Fish Tacos", "BBQ Ribs", "Stuffed Bell Peppers", "Vegetable Stir-Fry", "Seafood Paella", "Shakshuka", "Eggplant Curry", "Crispy Pork Belly", "Lamb Rogan Josh", "Chicken Enchiladas", "Beef Burrito", "Veggie Burrito", "Lobster Roll", "French Onion Soup", "Chicken Noodle Soup", "Pumpkin Soup", "Clam Chowder", "Chocolate Mousse", "Tiramisu", "Lemon Tart", "Apple Pie", "Mango Sorbet", "Pavlova", "Cheesecake", "Churros", "Banoffee Pie"]
    restaurants = ['Gourmet Diner', 'Spicy Terrace', 'Elegant Bistro', 'Crispy Feast', 'Lush Diner', 'Elegant Oven', 'Hearty Cafe', 'Fresh Cafe', 'Lush Plate', 'Urban Terrace', 'Elegant Diner', 'Crispy Kitchen', 'Rustic Kitchen', 'Cozy Diner', 'Gourmet Dish', 'Lush Cafe', 'Fresh Palate', 'Elegant Buffet', 'Spicy Dish', 'Trendy Flavor', 'Rustic Table', 'Exquisite Dish', 'Tasty Pub', 'Hearty Plate', 'Urban Oven', 'Exquisite Cafe', 'Juicy Garden', 'Trendy Cafe', 'Fresh Inn', 'Hearty Oven', 'Savory Flavor', 'Urban Diner', 'Elegant Cafe', 'Hearty Dish', 'Charming Palate', 'Exquisite Flavor', 'Exquisite Fork', 'Savory Inn', 'Classic Plate', 'Exquisite Lounge', 'Classic Plate', 'Gourmet Cafe', 'Trendy Dish', 'Spicy Table', 'Classic Kitchen', 'Savory Pub', 'Elegant Diner', 'Savory Garden', 'Trendy Dish', 'Tasty Fork']



    user_password = hashed_password = generate_password_hash("password")
    for _ in range(50):
        user_pk = str(uuid.uuid4())
        user_verified_at = random.choice([0,int(time.time())])
        user = {
            "user_pk" : user_pk,
            "user_name" : random.choice(restaurants),
            "user_last_name" : "",
            "user_email" : fake.unique.email(),
            "user_password" : user_password,
            "user_image" : "restaurant_"+ str(random.randint(1, 50)) +".jpg",
            "user_created_at" : int(time.time()),
            "user_deleted_at" : 0,
            "user_blocked_at" : 0,
            "user_updated_at" : 0,
            "user_verified_at" : user_verified_at,
            "user_verification_key" : str(uuid.uuid4())
        }
        insert_user(user)

        cursor.execute("""
        INSERT INTO users_roles (
            user_role_user_fk,
            user_role_role_fk)
            VALUES (%s, %s)
        """, (user_pk, x.RESTAURANT_ROLE_PK))

        for _ in range(random.randint(1, 5)):
            item_pk = str(uuid.uuid4())
            item_title = random.choice(dishes)
            item_price = round(random.uniform(50, 150), 2)
            
            # Ensure item description has at least 10 words
            while True:
                item_description = fake.paragraph(nb_sentences=3)
                if len(item_description.split()) >= 10:
                    break

            # Insert item into the items table
            cursor.execute("""
                INSERT INTO items (
                    item_pk, item_user_fk, item_title, item_price, item_description, 
                    item_created_at, item_updated_at, item_deleted_at, item_blocked_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (item_pk, user_pk, item_title, item_price, item_description, 
                int(time.time()), 0, 0, 0))

            # Insert between 1 and 3 images for the item
            num_images = random.randint(1, 3)
            for _ in range(num_images):
                item_image_pk = str(uuid.uuid4())
                item_image = f"dish_{random.randint(1, 100)}.jpg"
                cursor.execute("""
                    INSERT INTO item_images (
                        item_image_pk, item_fk, item_image, item_image_created_at, item_image_updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (item_image_pk, item_pk, item_image, int(time.time()), int(time.time())))







    db.commit()
    print("Database seeding completed successfully")

except Exception as ex:
    ic(ex)
    if "db" in locals(): 
        db.rollback()
    print(f"Error during seeding: {str(ex)}")
    sys.exit(1)  # Exit with error code 1

finally:
    if "cursor" in locals(): cursor.close()
    if "db" in locals(): db.close()


