from flask import Flask, session, render_template, redirect, url_for, request, send_from_directory, jsonify
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import x
import os
import uuid 
import time
import random
import re

from icecream import ic
ic.configureOutput(prefix=f'***** | ', includeContext=True)

def add_security_headers(response):
    # Content Security Policy
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com/leaflet/dist/leaflet.js https://unpkg.com/leaflet/dist/leaflet.css; "  # Allow inline scripts and eval for development
        "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com/leaflet/dist/leaflet.css; "  # Allow inline styles
        "img-src 'self' data: https:; "  # Allow images from self, data URIs, and HTTPS sources
        "font-src 'self' data:; "  # Allow fonts from self and data URIs
        "connect-src 'self'; "  # Allow XHR/WebSocket connections to self
        "frame-ancestors 'none'; "  # Prevent site from being embedded in iframes
        "form-action 'self'; "  # Restrict form submissions to same origin
        "base-uri 'self'; "  # Restrict base tag to same origin
        "object-src 'none'; "  # Prevent plugins
        "upgrade-insecure-requests;"  # Upgrade HTTP requests to HTTPS
    )
    
    # Add security headers
    response.headers['Content-Security-Policy'] = csp_policy
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    return response

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'  # or 'redis', etc.
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))  # Required for CSRF protection
Session(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Register the security headers middleware
app.after_request(add_security_headers)

@app.route('/health')
def health_check():
    try:
        db, cursor = x.db()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################
##############################
##############################

def _________GET_________(): pass

##############################

@app.get("/")
def view_index():
    try:
        # Safely check if the user has the "partner" or "restaurant" role
        user_roles = session.get("user", {}).get("roles", [])
        if "partner" in user_roles:
            return redirect(url_for("view_partner"))
        if "restaurant" in user_roles:
            return redirect(url_for("view_user_restaurant"))
        
        db, cursor = x.db()

        q = """ 
            SELECT * FROM users
            JOIN users_roles 
                ON user_pk = user_role_user_fk
            JOIN roles
                ON role_pk = user_role_role_fk
            WHERE role_name = 'restaurant'
            AND user_verified_at != 0
            AND user_deleted_at = 0;

        """
        cursor.execute(q)
        restaurants = cursor.fetchall()

        # Extract restaurant names
        restaurant_names = [restaurant['user_name'] for restaurant in restaurants]

        # Generate coordinates for each restaurant
        restaurant_locations = x.generate_copenhagen_coordinates(restaurant_names)

        # Pass the locations to the template
        return render_template("view_index.html", restaurant_locations = restaurant_locations, restaurants = restaurants, title="Homepage")
    
    except Exception as ex:
            ic(ex)
            if "db" in locals(): db.rollback()
            if isinstance(ex, x.CustomException): 
                toast = render_template("___toast.html", message="ex.message")
                return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", ex.code    
            if isinstance(ex, x.mysql.connector.Error):
                ic(ex)
                return "<template>System upgrating</template>", 500        
            return "<template>System under maintenance</template>", 500  
    finally:
            if "cursor" in locals(): cursor.close()
            if "db" in locals(): db.close()
##############################

@app.get("/restaurant")
def view_user_restaurant():
    try:
        if not "restaurant" in session.get("user").get("roles"): 
            return redirect(url_for("view_login"))

        user = session.get("user")
        user_pk = user.get("user_pk")
        db, cursor = x.db()

        # Query to fetch items with only one image (e.g., the first image based on item_image_created_at)
        q = """ 
            SELECT items.*, 
                   (SELECT item_images.item_image 
                    FROM item_images 
                    WHERE item_images.item_fk = items.item_pk 
                    ORDER BY item_images.item_image_created_at ASC 
                    LIMIT 1) AS image 
            FROM items
            WHERE items.item_user_fk = %s AND items.item_deleted_at = 0
        """

        # Pass user_pk as a parameter
        cursor.execute(q, (user_pk,))
        items = cursor.fetchall()

        return render_template("view_user_restaurant.html", user=user, items=items)
    
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            toast = render_template("___toast.html", message=ex.message)
            return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", ex.code    
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>System upgrating</template>", 500        
        return "<template>System under maintenance</template>", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################

@app.get("/restaurant/<user_pk>")
def view_restaurant(user_pk):
    try: 
        user_pk = x.validate_uuid4(user_pk)
        db, cursor = x.db()

        # Query to fetch items and their images
        q = """ 
            SELECT items.*, 
                   GROUP_CONCAT(item_images.item_image ORDER BY item_images.item_image_created_at ASC) AS images 
            FROM items
            LEFT JOIN item_images 
            ON items.item_pk = item_images.item_fk 
            WHERE items.item_user_fk = %s AND items.item_deleted_at = 0
            GROUP BY items.item_pk
        """
        cursor.execute(q, (user_pk,))
        items = cursor.fetchall()

        # Transform the `images` string into a list of dictionaries
        for item in items:
            item['images'] = [{'item_image': img} for img in item['images'].split(',')] if item['images'] else []

        # Query to fetch restaurant details
        q_restaurant = """ 
            SELECT user_name, user_email 
            FROM users 
            WHERE user_pk = %s
        """
        cursor.execute(q_restaurant, (user_pk,))
        restaurant = cursor.fetchone()

        if not restaurant:
            return "<template>Restaurant not found</template>", 404

        return render_template("view_restaurant.html", items=items, restaurant=restaurant)

    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        return "<template>System under maintenance</template>", 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()



##############################

@app.get("/dishes")
def view_dishes():
    try: 
        # Safely check if the user has the "partner" or "restaurant" role
        user_roles = session.get("user", {}).get("roles", [])
        if "partner" in user_roles:
            return redirect(url_for("view_partner"))
        if "restaurant" in user_roles:
            return redirect(url_for("view_user_restaurant"))
        
        db, cursor = x.db()

        # Fetch items and their images
        q = """ 
            SELECT items.*, 
                   GROUP_CONCAT(item_images.item_image) AS images 
            FROM items
            LEFT JOIN item_images ON items.item_pk = item_images.item_fk 
            WHERE items.item_deleted_at = 0
            GROUP BY items.item_pk
            LIMIT 0, 24
        """
        cursor.execute(q)
        items = cursor.fetchall()

        # Transform `images` string into a list of dictionaries if images exist
        for item in items:
            item['images'] = [{'item_image': img} for img in (item.get('images', '') or '').split(',') if img]

        return render_template("view_dishes.html", items=items, next_page=2)
    
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            toast = render_template("___toast.html", message=ex.message)
            return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", ex.code    
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>System upgrading</template>", 500        
        return "<template>System under maintenance</template>", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################

@app.get("/page/<page_number>")
def more_items(page_number):
    try:
        page_number = int(page_number)  # Ensure page_number is a valid integer
        items_per_page = 24
        offset = (page_number - 1) * items_per_page

        db, cursor = x.db()

        q = """
            SELECT items.*, 
                   GROUP_CONCAT(item_images.item_image) AS images
            FROM items
            LEFT JOIN item_images ON items.item_pk = item_images.item_fk
            WHERE items.item_deleted_at = 0
            GROUP BY items.item_pk
            LIMIT %s OFFSET %s
        """
        cursor.execute(q, (items_per_page, offset))
        items = cursor.fetchall()

        # Process images into a list of dictionaries
        for item in items:
            item['images'] = [{'item_image': img} for img in item['images'].split(',')] if item['images'] else []

        # Generate HTML for new items
        html = ""
        for item in items:
            html_item = render_template("__item_purchase.html", item=item)
            html += html_item

        # Check if more items are available
        cursor.execute("SELECT COUNT(*) FROM items WHERE item_deleted_at = 0")
        total_items = cursor.fetchone()["COUNT(*)"]

        if (offset + items_per_page) >= total_items:
            new_button = "<div class='text-center mt-4 text-gray-600'>No more items available</div>"
        else:
            new_button = render_template("___btn_get_more_items.html", next_page=page_number + 1)

        return f"""
            <template mix-target="#items" mix-bottom>
                {html}
            </template>
            <template mix-target="#btn_next_page" mix-replace>
                {new_button}
            </template>
        """

    except Exception as ex:
        ic(ex)
        if "db" in locals():
            db.rollback()
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500
        return "<template>System under maintenance</template>", 500
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
@app.get("/signup")
def view_signup():
    return render_template("view_signup.html", x=x, title="Signup")

##############################
@app.get("/add-item")
def view_add_item():
    return render_template("view_add_item.html", x=x, title="Add Item")

##############################
@app.get("/edit-item/<item_pk>")
def view_edit_item(item_pk):
    try:
        # Check if it is an admin
        if not "restaurant" in session.get("user").get("roles"): return redirect(url_for("view_login", message="Can't delete item"))

        db, cursor = x.db()

        q = """ 
            SELECT * FROM items 
            WHERE item_pk = %s
        """
        cursor.execute(q, (item_pk,))
        item = cursor.fetchone()
        return render_template("view_edit_item.html", x=x, title="Edit Item", item = item)

    except Exception as ex:
        ic(ex)
        if "db" in locals():
            db.rollback()
        if isinstance(ex, x.CustomException):
            toast = render_template("___toast.html", message=ex.message)
            return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", ex.code
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>System upgrading</template>", 500
        return "<template>System under maintenance</template>", 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()

##############################
@app.get("/admin")
@x.no_cache
def view_admin():
    try:
        # Ensure the logged-in user has the "admin" role
        if not "admin" in session.get("user").get("roles"): return redirect(url_for("view_login"))
        user = session.get("user")

        # Connect to the database and retrieve non-admin users
        db, cursor = x.db()
        q_user = """
            SELECT DISTINCT users.*, roles.role_name
            FROM users
            JOIN users_roles 
                ON users.user_pk = users_roles.user_role_user_fk
            JOIN roles 
                ON users_roles.user_role_role_fk = roles.role_pk
            WHERE roles.role_name != 'admin'
        """
        cursor.execute(q_user)
        users = cursor.fetchall()

        q_item = """
            SELECT items.*, 
                   (SELECT item_images.item_image 
                    FROM item_images 
                    WHERE item_images.item_fk = items.item_pk 
                    ORDER BY item_images.item_image_created_at ASC 
                    LIMIT 1) AS image 
            FROM items
        """
        cursor.execute(q_item)
        items = cursor.fetchall()


        if not users:
            message = "No users found."
        else:
            message = ""

        # Render the admin view with non-admin users
        return render_template("view_admin.html", users=users, user=user, items=items, message=message)

    except Exception as ex:
        ic(ex)
        if "db" in locals():
            db.rollback()
        if isinstance(ex, x.CustomException):
            toast = render_template("___toast.html", message=ex.message)
            return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", ex.code
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>System upgrading</template>", 500
        return "<template>System under maintenance</template>", 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
@app.get("/customer-profile")
def view_customer_profile ():
    user = session.get("user")
    return render_template("view_customer_profile.html", user=user, x=x, title="Customer Profile")
##############################
@app.get("/customer-profile/<user_pk>")
def view_customer_profile_delete (user_pk):
    user = session.get("user")
    if not user or user["user_pk"] != user_pk:
        return redirect(url_for("view_login"))
    return render_template("view_customer_profile_delete.html", user=user, x=x, title="Delete your profile")

##############################
@app.get("/forgot-password")
def view_forgot_password():
    return render_template("view_forgot_password.html", x=x, title="Forgot Password")


##############################
@app.get("/login")
@x.no_cache
def view_login():  
    # ic("#"*20, "VIEW_LOGIN")
    ic(session)
    # print(session, flush=True)  
    if session.get("user"):
        if len(session.get("user").get("roles")) > 1:
            return redirect(url_for("view_choose_role")) 
        if "admin" in session.get("user").get("roles"):
            return redirect(url_for("view_admin"))
        if "restaurant" in session.get("user").get("roles"):
            return redirect(url_for("view_user_restaurant"))
        if "customer" in session.get("user").get("roles"):
            return redirect(url_for("view_customer")) 
        if "partner" in session.get("user").get("roles"):
            return redirect(url_for("view_partner"))         
    return render_template("view_login.html", x=x, title="Login", message=request.args.get("message", ""))

##############################

@app.get("/verify/<verification_key>")
@x.no_cache
def verify_user(verification_key):
    try:
        ic(verification_key)
        verification_key = x.validate_uuid4(verification_key)
        user_verified_at = int(time.time())

        db, cursor = x.db()
        q = """ UPDATE users 
                SET user_verified_at = %s 
                WHERE user_verification_key = %s"""
        cursor.execute(q, (user_verified_at, verification_key))
        if cursor.rowcount != 1: x.raise_custom_exception("cannot verify account", 400)
        db.commit()
        return redirect(url_for("view_login", message="User verified, please login"))

    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): return ex.message, ex.code    
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "Database under maintenance", 500        
        return "System under maintenance", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################

@app.get("/reset-password/<user_email>/<reset_password_token>")
@x.no_cache
def view_reset_password(user_email, reset_password_token):
    try:
        ic(user_email, reset_password_token)
        user_email = user_email.strip().lower()
        ic(user_email)

        reset_password_token = x.validate_uuid4(reset_password_token)

        session["reset_email"] = user_email
        
        return render_template("view_reset_password.html", x=x, title="Reset password")

    except Exception as ex:
        pass
    finally:
        pass


##############################
@app.get("/customer")
@x.no_cache
def view_customer():
    if not session.get("user", ""): 
        return redirect(url_for("view_login"))
    user = session.get("user")
    if len(user.get("roles", "")) > 1:
        return redirect(url_for("view_choose_role"))
    return redirect(url_for("view_index"))

##############################

@app.get("/partner")
@x.no_cache
def view_partner():

    if not "partner" in session.get("user","").get("roles"):
        return redirect(url_for("view_login"))


    return redirect(url_for("view_customer_profile"))




###############################################
@app.get("/search")
def view_search():
    try:
        # Safely check if the user has the "partner" or "restaurant" role
        user_roles = session.get("user", {}).get("roles", [])
        if "partner" in user_roles:
            return redirect(url_for("view_partner"))
        if "restaurant" in user_roles:
            return redirect(url_for("view_user_restaurant"))
        
        # Get the search query from the URL parameters
        search_query = request.args.get('q', '').strip()
        ic(search_query)

        db, cursor = x.db()

        # Query to search for items by title
        cursor.execute("""
            SELECT items.*, 
                GROUP_CONCAT(item_images.item_image) AS images 
            FROM items
            LEFT JOIN item_images 
                ON items.item_pk = item_images.item_fk 
            WHERE items.item_deleted_at = 0 
            AND LOWER(items.item_title) LIKE LOWER(%s)
            GROUP BY items.item_pk
            LIMIT 12
        """, (f"%{search_query}%",))
        items = cursor.fetchall()

        for item in items:
            item['images'] = [{'item_image': img} for img in (item.get('images', '') or '').split(',') if img]


        # Query to search for users with the 'restaurant' role
        cursor.execute("""
            SELECT users.* 
            FROM users 
            JOIN users_roles ON users.user_pk = users_roles.user_role_user_fk
            JOIN roles ON users_roles.user_role_role_fk = roles.role_pk
            WHERE roles.role_name = 'restaurant' 
            AND users.user_deleted_at = 0
            AND (LOWER(users.user_name) LIKE LOWER(%s)
                 OR LOWER(users.user_email) LIKE LOWER(%s))
            LIMIT 8
        """, (f"%{search_query}%", f"%{search_query}%"))
        restaurants = cursor.fetchall()

        # Render the search results
        return render_template("view_search.html", 
                               title="Search Results", 
                               items=items, 
                               restaurants=restaurants,
                               search_query=search_query)

    except Exception as ex:
        # Handle errors and rollback if necessary
        ic(ex)
        if "db" in locals(): db.rollback()
        return render_template("view_search.html", 
                               title="Search Error", 
                               error="An error occurred while searching")
    finally:
        # Close the database connection
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################
@app.get("/cart")
def view_cart():

    # Safely check if the user has the "partner" or "restaurant" role
    user_roles = session.get("user", {}).get("roles", [])
    if "partner" in user_roles:
        return redirect(url_for("view_partner"))
    if "restaurant" in user_roles:
        return redirect(url_for("view_user_restaurant"))    
    
    cart_items = session.get("cart_items", [])
    total_price = sum(item["item_price"] for item in cart_items)

    return render_template("view_cart.html", cart_items = cart_items, total_price = total_price)


##############################
@app.get("/thank-you")
def view_thank_you():    
    return render_template("view_thank_you.html", title="Thank you")


##############################
##############################
##############################

def _________POST_________(): pass

##############################

@app.post("/logout")
def logout():
    session.pop("user", None)
    session.pop("cart_items", None)
    session.modified = True
 
    return redirect(url_for("view_login"))

############################################################
@app.post("/signup")
@x.no_cache
def signup():
    try:
        user_role = x.validate_user_role()
        user_name = x.validate_user_name()
        user_last_name = x.validate_user_last_name()
        user_email = x.validate_user_email()
        user_password = x.validate_user_password()
        hashed_password = generate_password_hash(user_password)
        
        user_pk = str(uuid.uuid4())
        user_avatar = "profile_"+ str(random.randint(1, 100)) +".jpg"
        user_created_at = int(time.time())
        user_deleted_at = 0
        user_blocked_at = 0
        user_updated_at = 0
        user_verified_at = 0
        user_verification_key = str(uuid.uuid4())

        db, cursor = x.db()
        q = 'INSERT INTO users VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(q, (user_pk, user_name, user_last_name, user_email, 
                           hashed_password, user_avatar, user_created_at, user_deleted_at, user_blocked_at, 
                           user_updated_at, user_verified_at, user_verification_key))
        
        q = 'INSERT INTO users_roles VALUES(%s, %s)'
        cursor.execute(q, (user_pk, user_role))
        
        x.send_verify_email(user_email, user_verification_key)
        
        db.commit()

        return """<template mix-redirect="login?message=please+verify+your+email"></template>""", 201
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()

        # My own exception
        if isinstance(ex, x.CustomException):
            ic(x.CustomException)
            toast = render_template("___toast.html", message=ex.message)
            return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", ex.code
        
        # Database exception
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            if "users.user_email" in str(ex):
                toast = render_template("___toast.html", message="email not available")
                return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", 400
            return "<template>System upgrading</template>", 500  
      
        # Any other exception
        return """<template mix-target="#toast" mix-bottom>System under maintenance</template>""", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

############################################################
@app.post("/forgot-password")
@x.no_cache
def forgot_password():
    try:
        user_email = x.validate_user_email()
        user_reset_password_token = str(uuid.uuid4())

        db, cursor = x.db()
        q = 'SELECT * FROM users WHERE user_email = %s'
        cursor.execute(q, (user_email,))
        
        x.send_reset_password_email(user_email, user_reset_password_token)
        
        db.commit()

        return """<template></template>""", 201
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()

        # My own exception
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        
        # Database exception
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            if "users.user_email" in str(ex):
                return """<template mix-target="#toast" mix-bottom>email not available</template>""", 400
            return "<template>System upgrading</template>", 500  
      
        # Any other exception
        return """<template mix-target="#toast" mix-bottom>System under maintenance</template>""", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()



############################################################

@app.post("/login")
def login():
    try:

        user_email = x.validate_user_email()
        user_password = x.validate_user_password()

        db, cursor = x.db()
        q = """ 
            SELECT * FROM users 
            JOIN users_roles 
            ON user_pk = user_role_user_fk 
            JOIN roles
            ON role_pk = user_role_role_fk
            WHERE user_email = %s AND user_verified_at != 0 AND user_deleted_at = 0
            """
        cursor.execute(q, (user_email,))
        rows = cursor.fetchall()
        if not rows:
            toast = render_template("___toast.html", message="user not registered")
            return f"""<template mix-target="#toast">{toast}</template>""", 400     
        if not check_password_hash(rows[0]["user_password"], user_password):
            toast = render_template("___toast.html", message="invalid credentials")
            return f"""<template mix-target="#toast">{toast}</template>""", 401
        roles = []
        for row in rows:
            roles.append(row["role_name"])
            
        user = {
            "user_pk": rows[0]["user_pk"],
            "user_name": rows[0]["user_name"],
            "user_last_name": rows[0]["user_last_name"],
            "user_email": rows[0]["user_email"],
            "roles": roles,
        }
        ic(user)
        session["user"] = user
        if len(roles) == 1:
            return f"""<template mix-redirect="/{roles[0]}"></template>"""
        return f"""<template mix-redirect="/choose-role"></template>"""
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        # My own exception
        if isinstance(ex, x.CustomException):
            toast = render_template("___toast.html", message=ex.message)
            return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", ex.code
        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>System upgrating</template>", 500        
        return "<template>System under maintenance</template>", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

############################################################       
@app.post("/reset-password")
@x.no_cache
def reset_password():
    try:
        user_password = x.validate_user_password()
        new_password = user_password
    
        confirm_password = request.form.get("confirm_password", "").strip()

        user_updated_at = int(time.time())

        if new_password != confirm_password:
            x.raise_custom_exception("Passwords do not match", 400)

        user_email = session.get("reset_email")  # Example: email stored in session
        ic(user_email)
        if not user_email:
            x.raise_custom_exception("Invalid reset session. Please try again.", 400)

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        # Update the user's password in the database
        db, cursor = x.db()
        q = """ UPDATE users 
                SET user_password = %s, user_updated_at = %s 
                WHERE user_email = %s"""
        cursor.execute(q, (hashed_password, user_updated_at, user_email))
        if cursor.rowcount != 1:
            x.raise_custom_exception("Unable to reset password. Please try again.", 500)

        db.commit()

        return """<template mix-redirect="/login"></template>"""
        # return redirect(url_for("view_login", message="Password has been reset.")), 201

    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()

        # My own exception
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        
        # Database exception
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            if "users.user_email" in str(ex):
                return """<template mix-target="#toast" mix-bottom>email not available</template>""", 400
            return "<template>System upgrading</template>", 500  
      
        # Any other exception
        return """<template mix-target="#toast" mix-bottom>System under maintenance</template>""", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


###########################################
@app.post("/create-item")
def create_item():
    try:
        user_restaurant = session.get("user")
        if not user_restaurant:
            return redirect(url_for("view_login"))  

        user_pk = user_restaurant.get("user_pk")

        # Validate inputs
        item_title = x.validate_item_title()
        item_price = x.validate_item_price()
        item_description = x.validate_item_description()

        files = []
        for i in range(1, 4):  # Support up to 3 images
            file = request.files.get(f'item_file{i}')
            if i == 1 and (not file or file.filename == ''):  # Ensure the first file is mandatory
                raise x.CustomException("File 1 is required", 400)
            if file and file.filename != '':
                # Validate file
                filename = x.validate_file_upload(file)

                # Ensure the upload folder exists
                if not os.path.exists(x.UPLOAD_ITEM_FOLDER):
                    os.makedirs(x.UPLOAD_ITEM_FOLDER)

                # Save file
                file_path = os.path.join(x.UPLOAD_ITEM_FOLDER, filename)
                file.save(file_path)

                files.append(filename)

        # Prepare item data
        item_pk = str(uuid.uuid4())
        item_user_fk = user_pk
        item_created_at = int(time.time())
        item_updated_at = 0
        item_deleted_at = 0
        item_blocked_at = 0 

        # Database connection
        db, cursor = x.db()

        # Insert item data into the `items` table
        q_items = '''INSERT INTO items 
                     (item_pk, item_user_fk, item_title, item_description, item_price, item_created_at, item_updated_at, item_deleted_at, item_blocked_at) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        cursor.execute(q_items, (item_pk, item_user_fk, item_title, item_description, item_price, item_created_at, item_updated_at, item_deleted_at, item_blocked_at))

        # Insert image data into the `item_images` table
        q_images = '''INSERT INTO item_images 
                      (item_image_pk, item_fk, item_image, item_image_created_at, item_image_updated_at) 
                      VALUES (%s, %s, %s, %s, %s)'''
        for filename in files:
            cursor.execute(q_images, (str(uuid.uuid4()), item_pk, filename, int(time.time()), 0))

        # Commit changes
        db.commit()

        toast = render_template("___toast.html", message="Item uploaded successfully")
        return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", 201  

    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            if "users.user_email" in str(ex):
                return """<template mix-target="#toast" mix-bottom>email not available</template>""", 400
            return "<template>System upgrading</template>", 500  
        return """<template mix-target="#toast" mix-bottom>System under maintenance</template>""", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################
@app.post("/search")
def search():
    search_query = request.form.get('q', '').strip() 
    return redirect(url_for("view_search", q=search_query))



#############################
@app.post("/add-to-cart/<item_pk>")
def add_to_cart(item_pk):
    try:
        item_pk = x.validate_uuid4(item_pk)
        db, cursor = x.db()

        # Query to select the item and one associated image
        q = """
            SELECT items.*, 
                   (SELECT item_images.item_image 
                    FROM item_images 
                    WHERE item_images.item_fk = items.item_pk 
                    ORDER BY item_images.item_image_created_at ASC 
                    LIMIT 1) AS item_image
            FROM items 
            WHERE items.item_pk = %s
        """
        cursor.execute(q, (item_pk,))
        item = cursor.fetchone()

        if not item:
            return "Item not found", 404

        # Initialize cart_items if it doesn't exist
        if "cart_items" not in session:
            session["cart_items"] = []

        # Add the item to the cart
        session["cart_items"].append({
            "item_pk": item["item_pk"],
            "item_title": item["item_title"],
            "item_price": item["item_price"],
            "item_image": item["item_image"],
        })

        return """
                    <template mix-redirect="/cart"></template>
               """

    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        if isinstance(ex, x.mysql.connector.Error):
            if "users.user_email" in str(ex): 
                return "<template>email not available</template>", 400
            return "<template>System upgrading</template>", 500        
        return "<template>System under maintenance</template>", 500    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################
@app.post("/remove-from-cart/<item_pk>")
def remove_from_cart(item_pk):
    try:
        item_pk = x.validate_uuid4(item_pk)

        if "cart_items" in session:
            # Filter out the item to remove
            session["cart_items"] = [
                item for item in session["cart_items"] if item["item_pk"] != item_pk
            ]

        return """
            <template mix-redirect="cart"></template>
        """
    except Exception as ex:
        ic(ex)
        return "<template>System under maintenance</template>", 500
    finally:pass

##############################
@app.post("/checkout-mail")
def check_out_mail():
    try:
        user_email = session.get("user").get("user_email")
        cart_items = session.get("cart_items")
        ic(user_email)

        x.send_cart_email(user_email, cart_items)

        session.pop("cart_items", None)

        return """
            <template mix-redirect="thank-you"></template>
        """
    except Exception as ex:
        ic(ex)
        return "<template>System under maintenance</template>", 500
    finally:pass

  


##############################
##############################
##############################

def _________PUT_________(): pass

##############################

@app.put("/customer-profile")
def customer_update():
    try:
        if not session.get("user"): 
            x.raise_custom_exception("please login", 401)

        # Get the user primary key from the session
        user_pk = session.get("user").get("user_pk")

        # Validate input fields
        user_name = x.validate_user_name()
        user_last_name = x.validate_user_last_name()
        user_email = x.validate_user_email()

        user_updated_at = int(time.time())

        # Update the user's details in the database
        db, cursor = x.db()
        q_update = """ UPDATE users
                       SET user_name = %s, user_last_name = %s, user_email = %s, user_updated_at = %s
                       WHERE user_pk = %s
                   """
        cursor.execute(q_update, (user_name, user_last_name, user_email, user_updated_at, user_pk))
        ic(cursor.rowcount)
        if cursor.rowcount != 1: 
            x.raise_custom_exception("cannot update user", 401)

        # Fetch the updated user details from the database
        q_fetch = """ SELECT user_pk, user_name, user_last_name, user_email 
                      FROM users 
                      WHERE user_pk = %s
                  """
        cursor.execute(q_fetch, (user_pk,))
        user = cursor.fetchone()
        if not user:
            x.raise_custom_exception("user not found after update", 500)

        # Update the session with the new user data
        session["user"] = {
            "user_pk": user["user_pk"],
            "user_name": user["user_name"],
            "user_last_name": user["user_last_name"],
            "user_email": user["user_email"],
        }

        #toast = render_template("___toast.html", message="You updated your profile")


        db.commit()
        return f"""<template mix-redirect="customer-profile"></template>"""
    
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        if isinstance(ex, x.mysql.connector.Error):
            if "users.user_email" in str(ex): 
                return "<template>email not available</template>", 400
            return "<template>System upgrading</template>", 500        
        return "<template>System under maintenance</template>", 500    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################

@app.put("/customer-profile/<user_pk>")
def user_delete(user_pk):
    try:
        # Check if user is logged in
        if not session.get("user", ""): 
            return redirect(url_for("view_login"))


        # Validate the user_pk and retrieve password from form
        user_pk = x.validate_uuid4(user_pk)
        user_password = x.validate_user_password()
        ic(user_password)
        if not user_password:
            x.raise_custom_exception("Password is required.", 400)

        # Fetch user from database
        db, cursor = x.db()
        q_select = "SELECT * FROM users WHERE user_pk = %s"
        cursor.execute(q_select, (user_pk,))
        user = cursor.fetchone()

        # Compare provided password with the stored password
        stored_password = user["user_password"]
        user_email = user["user_email"]
        if not check_password_hash(stored_password, user_password):
            x.raise_custom_exception("Incorrect password.", 403)

        # Update user_deleted_at to mark the account as deleted
        user_deleted_at = int(time.time())
        q_update = "UPDATE users SET user_deleted_at = %s WHERE user_pk = %s"
        cursor.execute(q_update, (user_deleted_at, user_pk))
        if cursor.rowcount != 1:
            x.raise_custom_exception("Cannot delete user.", 400)
        
        x.send_verify_delete(user_email, user_pk)

        session.pop("user", None)

        db.commit()
        return """<template mix-redirect="login?=User+deleted">User deleted</template>"""

    except Exception as ex:
        ic(ex)
        if "db" in locals(): 
            db.rollback()
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500        
        return "<template>System under maintenance</template>", 500  
    
    finally:
        if "cursor" in locals(): 
            cursor.close()
        if "db" in locals(): 
            db.close()

############################################################
@app.put("/users/block/<user_pk>")
def user_block(user_pk):
    try:        
        if not "admin" in session.get("user").get("roles"): return redirect(url_for("view_login"))
        user_pk = x.validate_uuid4(user_pk)
        user_blocked_at = int(time.time())
        user_updated_at = int(time.time())
        user = {
            "user_pk" : user_pk,
            "user_blocked_at" : user_blocked_at,
            "user_updated_at" : user_updated_at
        }
        db, cursor = x.db()
        q = 'UPDATE users SET user_blocked_at = %s, user_updated_at = %s WHERE user_pk = %s'
        cursor.execute(q, (user_blocked_at, user_updated_at, user_pk))
        if cursor.rowcount != 1: x.raise_custom_exception("cannot block user", 400)
        btn_unblock = render_template("___btn_unblock_user.html", user=user)

        q_select = 'SELECT * FROM users WHERE user_pk = %s'
        cursor.execute(q_select, (user_pk,))
        user = cursor.fetchone()

        user_name = user['user_name']
        user_email = user['user_email']

        x.send_user_blocked_email(user_email, user_name)


        db.commit()
        return f"""<template mix-target="#block-{user_pk}"
                    mix-replace>{btn_unblock}</template>"""
    
    except Exception as ex:
        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500        
        return "<template>System under maintenance</template>", 500  
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


############################################################
@app.put("/users/unblock/<user_pk>")
def user_unblock(user_pk):
    try:
        if not "admin" in session.get("user").get("roles"): return redirect(url_for("view_login"))
        user_pk = x.validate_uuid4(user_pk)
        user_blocked_at = 0
        user = {
            "user_pk" : user_pk,
            "user_blocked_at" : user_blocked_at
        }
        db, cursor = x.db()
        q = 'UPDATE users SET user_blocked_at = %s WHERE user_pk = %s'
        cursor.execute(q, (user_blocked_at, user_pk))
        if cursor.rowcount != 1: x.raise_custom_exception("cannot unblock user", 400)
        btn_block = render_template("___btn_block_user.html", user=user)

        db.commit()
        return f"""<template mix-target="#unblock-{user_pk}"
                    mix-replace>{btn_block}</template>"""
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500        
        return "<template>System under maintenance</template>", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

############################################################
@app.put("/items/block/<item_pk>")
def item_block(item_pk):
    try:
        # Ensure user is an admin
        if not "admin" in session.get("user").get("roles"):
            return redirect(url_for("view_login"))
        
        # Validate input
        item_pk = x.validate_uuid4(item_pk)
        item_blocked_at = int(time.time())
        item_updated_at = int(time.time())
        item = {
            "item_pk": item_pk,
            "item_blocked_at": item_blocked_at,
            "item_updated_at": item_updated_at
        }

        # Database connection
        db, cursor = x.db()

        # Update the item to mark it as blocked
        q_update = 'UPDATE items SET item_blocked_at = %s, item_updated_at = %s WHERE item_pk = %s'
        cursor.execute(q_update, (item_blocked_at, item_updated_at, item_pk))
        if cursor.rowcount != 1:
            x.raise_custom_exception("Cannot block item", 400)

        # Query to join items and users to get user email and name
        q_select = '''
            SELECT items.item_title, users.user_name, users.user_email 
            FROM items 
            JOIN users ON items.item_user_fk = users.user_pk
            WHERE items.item_pk = %s
        '''
        cursor.execute(q_select, (item_pk,))
        result = cursor.fetchone()

        if not result:
            x.raise_custom_exception("Item not found", 404)

        # Extract details for email
        item_title = result['item_title']
        user_name = result['user_name']
        user_email = result['user_email']

        # Send email notification to the user
        x.send_item_blocked_email(user_email, user_name, item_title)

        # Render the unblock button
        btn_unblock = render_template("___btn_unblock_item.html", item=item)

        # Commit changes to the database
        db.commit()

        # Return the unblock button
        return f"""<template mix-target="#block-{item_pk}"
                    mix-replace>{btn_unblock}</template>"""
    
    except Exception as ex:
        ic(ex)
        if "db" in locals():
            db.rollback()
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500        
        return "<template>System under maintenance</template>", 500  
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()

###############################################
@app.put("/items/unblock/<item_pk>")
def item_unblock(item_pk):
    try:
        # Ensure user is an admin
        if not "admin" in session.get("user").get("roles"):
            return redirect(url_for("view_login"))

        # Validate item_pk
        item_pk = x.validate_uuid4(item_pk)
        item_blocked_at = 0
        item = {
            "item_pk": item_pk,
            "item_blocked_at": item_blocked_at
        }

        # Database connection
        db, cursor = x.db()

        # Update item to mark it as unblocked
        q_update = 'UPDATE items SET item_blocked_at = %s WHERE item_pk = %s'
        cursor.execute(q_update, (item_blocked_at, item_pk))
        if cursor.rowcount != 1:
            x.raise_custom_exception("Cannot unblock item", 400)

        # Render the block button
        btn_block = render_template("___btn_block_item.html", item=item)

        # Commit changes to the database
        db.commit()

        # Return the block button to replace the unblock button
        return f"""<template mix-target="#unblock-{item_pk}"
                    mix-replace>{btn_block}</template>"""

    except Exception as ex:
        ic(ex)
        if "db" in locals():
            db.rollback()
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500        
        return "<template>System under maintenance</template>", 500  

    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()



###############################################
@app.put("/users/<user_pk>")
def admin_delete(user_pk):
    try:
        # Ensure the user is logged in and the provided user_pk matches the session user
        # Check if it is dmin
        if not "admin" in session.get("user").get("roles"): 
            return redirect(url_for("view_login"))

        user_pk = x.validate_uuid4(user_pk)
        user_deleted_at = int(time.time())

        db, cursor = x.db()

        q = "UPDATE users SET user_deleted_at = %s WHERE user_pk = %s"
        cursor.execute(q, (user_pk,))
        user = cursor.fetchone()

        if not user:
            x.raise_custom_exception("User does not exist", 404)

        user_email = user["user_email"]
        x.send_verify_delete(user_email, user_pk)

        db.commit()
        return """<template mix-redirect="login?=User+delete+request+sent+to+email+for+verification">User delete request sent for verification</template>"""
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500        
        return "<template>System under maintenance</template>", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

###############################################
@app.put("/edit-item/<item_pk>")
def edit_item(item_pk):
    try:
        # Check if the user has a restaurant role
        user = session.get("user")
        if not user or "restaurant" not in user.get("roles", []):
            return redirect(url_for("view_login"))

        # Validate inputs
        item_pk = x.validate_uuid4(item_pk)
        item_title = x.validate_item_title()
        item_price = x.validate_item_price()
        item_description = x.validate_item_description()

        # Process uploaded files (optional)
        files = []  # List to hold uploaded file names
        for i in range(1, 4):
            file = request.files.get(f'item_file{i}')
            if file and file.filename != '':
                filename = x.validate_file_upload(file)

                # Ensure the upload folder exists
                if not os.path.exists(x.UPLOAD_ITEM_FOLDER):
                    os.makedirs(x.UPLOAD_ITEM_FOLDER)

                # Save the file in the specified directory
                file_path = os.path.join(x.UPLOAD_ITEM_FOLDER, filename)
                file.save(file_path)

                files.append(filename)  # Add the filename to the list

        item_updated_at = int(time.time())

        # Update item in the database
        db, cursor = x.db()

        # Update `items` table
        q_update_item = """
            UPDATE items
            SET item_title = %s, 
                item_price = %s, 
                item_description = %s, 
                item_updated_at = %s
            WHERE item_pk = %s
        """
        cursor.execute(q_update_item, (item_title, item_price, item_description, item_updated_at, item_pk))

        # Ensure the item exists
        if cursor.rowcount == 0:
            raise x.CustomException("Item not found", 404)

        # Handle images in the `item_images` table
        if files:
            # Delete existing images for this item
            q_delete_images = "DELETE FROM item_images WHERE item_fk = %s"
            cursor.execute(q_delete_images, (item_pk,))

            # Insert new images
            for filename in files:
                item_image_pk = str(uuid.uuid4())
                q_insert_image = """
                    INSERT INTO item_images (item_image_pk, item_fk, item_image, item_image_created_at, item_image_updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(q_insert_image, (item_image_pk, item_pk, filename, int(time.time()), int(time.time())))

        db.commit()

        toast = render_template("___toast.html", message="Item updated successfully")
        return f"""<template mix-target="#toast" mix-bottom>{toast}</template>""", 200

    except Exception as ex:
        ic(ex)
        if "db" in locals():
            db.rollback()
        if isinstance(ex, x.CustomException):
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500
        return "<template>System under maintenance</template>", 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


#############################################################

@app.put("/delete-item/<item_pk>")
def item_delete(item_pk):
    try:
        item_pk = x.validate_uuid4(item_pk)
        item_deleted_at = int(time.time())
        db, cursor = x.db()
        q = 'UPDATE items SET item_deleted_at = %s WHERE item_pk = %s'
        cursor.execute(q, (item_deleted_at, item_pk))
        if cursor.rowcount != 1: x.raise_custom_exception("cannot delete item", 400)
        db.commit()
        return """<template mix-redirect="/restaurant"></template>"""
    
    except Exception as ex:

        ic(ex)
        if "db" in locals(): db.rollback()
        if isinstance(ex, x.CustomException): 
            return f"""<template mix-target="#toast" mix-bottom>{ex.message}</template>""", ex.code        
        if isinstance(ex, x.mysql.connector.Error):
            ic(ex)
            return "<template>Database error</template>", 500        
        return "<template>System under maintenance</template>", 500  
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()