from flask import request, make_response
from functools import wraps
import mysql.connector
import uuid
import re
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from icecream import ic
ic.configureOutput(prefix=f'***** | ', includeContext=True)


class CustomException(Exception):
    def __init__(self, message, code):
        super().__init__(message)  # Initialize the base class with the message
        self.message = message  # Store additional information (e.g., error code)
        self.code = code  # Store additional information (e.g., error code)

def raise_custom_exception(error, status_code):
    raise CustomException(error, status_code)

##############################
def db():
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),      # Use environment variable or default to localhost
        user=os.getenv("DB_USER"),           # Use environment variable or default to root
        password=os.getenv("DB_PASSWORD"), # Use environment variable or default to password
        database=os.getenv("DB_NAME")     # Use environment variable or default to company
    )
    cursor = db.cursor(dictionary=True)
    return db, cursor

##############################
def no_cache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return no_cache_view

############################################################

ADMIN_ROLE_PK = "16fd2706-8baf-433b-82eb-8c7fada847da"
CUSTOMER_ROLE_PK = "c56a4180-65aa-42ec-a945-5fd21dec0538"
PARTNER_ROLE_PK = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
RESTAURANT_ROLE_PK = "9f8c8d22-5a67-4b6c-89d7-58f8b8cb4e15"
UNSPLASH_ACCESS_KEY = "tKI4eDQ1J-kv_dEhpC1gRN_JNM7DPUsPT0CskyGgnj4"

##############################
USER_NAME_MIN = 2
USER_NAME_MAX = 20
USER_NAME_REGEX = f"^.{{{USER_NAME_MIN},{USER_NAME_MAX}}}$"
def validate_user_name():
    error = f"name {USER_NAME_MIN} to {USER_NAME_MAX} characters"
    user_name = request.form.get("user_name", "").strip()
    if not re.match(USER_NAME_REGEX, user_name): raise_custom_exception(error, 400)
    return user_name

##############################
USER_LAST_NAME_MIN = 2
USER_LAST_NAME_MAX = 20
USER_LAST_NAME_REGEX = f"^.{{{USER_LAST_NAME_MIN},{USER_LAST_NAME_MAX}}}$"
def validate_user_last_name():
    error = f"last name {USER_LAST_NAME_MIN} to {USER_LAST_NAME_MAX} characters"
    user_last_name = request.form.get("user_last_name", "").strip() # None
    if not re.match(USER_LAST_NAME_REGEX, user_last_name): raise_custom_exception(error, 400)
    return user_last_name

##############################
def validate_user_email():
    user_email = request.form.get("user_email", "").strip().lower()
    if not user_email:
        raise CustomException("email is required", 400)
    
    # Ny email validering der håndterer:
    # - Subdomæner (f.eks. user@sub.domain.com)
    # - IP-adresser i domænenavn (f.eks. user@[192.168.1.1])
    # - Lokale domæner (f.eks. user@localhost)
    # - Specialtegn (f.eks. user.name+tag@domain.com)
    # - Unicode tegn i både lokaldel og domæne
    email_pattern = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    
    if not re.match(email_pattern, user_email):
        raise CustomException("invalid email format", 400)
    
    # Yderligere validering af domænedel
    domain = user_email.split('@')[1]
    if len(domain) > 255:  # Maksimal længde for domænenavn
        raise CustomException("invalid email domain", 400)
    
    return user_email

##############################
def validate_user_role():
    error = "Invalid role"
    user_role = request.form.get("user_role", "").strip()
    VALID_ROLES = {CUSTOMER_ROLE_PK, PARTNER_ROLE_PK, RESTAURANT_ROLE_PK}
    ic(user_role)
    if user_role not in VALID_ROLES:
        raise_custom_exception(error, 400)
    return user_role

##############################
USER_PASSWORD_MIN = 8
USER_PASSWORD_MAX = 50
REGEX_USER_PASSWORD = f"^.{{{USER_PASSWORD_MIN},{USER_PASSWORD_MAX}}}$"
def validate_user_password():
    error = f"password {USER_PASSWORD_MIN} to {USER_PASSWORD_MAX} characters"
    user_password = request.form.get("user_password", "").strip()
    ic(user_password)
    if not re.match(REGEX_USER_PASSWORD, user_password): raise_custom_exception(error, 400)
    return user_password

##############################
REGEX_UUID4 = "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
def validate_uuid4(uuid4 = ""):
    error = f"invalid uuid4"
    if not uuid4:
        uuid4 = request.values.get("uuid4", "").strip()
    if not re.match(REGEX_UUID4, uuid4): raise_custom_exception(error, 400)
    return uuid4

##############################
REGEX_PAGE_NUMBER = f"^([1-9][0-9]*)$"
def validate_page_number(page_number):
    error = f"page_number invalid"
    if not re.match(REGEX_PAGE_NUMBER, page_number): raise Exception(error, 400)
    return int(page_number)

##############################
# ALLOWED_ITEM_FILE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# def validate_item_image():
#     # Check if the file is in the request
#     if 'item_file' not in request.files:
#         raise_custom_exception("item_file missing", 400)

#     file = request.files.get("item_file", "")
#     if file.filename == "":
#         raise_custom_exception("item_file name invalid", 400)

#     # Validate the file extension
#     file_extension = os.path.splitext(file.filename)[1].lower()  # Get extension with a dot
#     if file_extension[1:] not in ALLOWED_ITEM_FILE_EXTENSIONS:  # Skip the dot when checking
#         raise_custom_exception("item_file invalid extension", 400)

#     # Generate a unique filename
#     filename = f"{uuid.uuid4()}{file_extension}"

#     # Ensure upload folder exists
#     if not os.path.exists(UPLOAD_ITEM_FOLDER):
#         os.makedirs(UPLOAD_ITEM_FOLDER)

#     return file, filename

##############################
UPLOAD_ITEM_FOLDER = './static/dishes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}

def validate_file_upload(file):
    if not file or file.filename == '':
        raise_custom_exception("No file uploaded", 400)

    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        raise_custom_exception("File type is not allowed.", 400)

    # Generate a secure filename
    unique_filename = f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}"
    return unique_filename


    
##############################
ITEM_TITLE_MIN = 2
ITEM_TITLE_MAX = 40
ITEM_TITLE_REGEX = f"^.{{{ITEM_TITLE_MIN},{ITEM_TITLE_MAX}}}$"
def validate_item_title():
    error = f"item title {ITEM_TITLE_MIN} to {ITEM_TITLE_MAX} characters"
    item_title = request.form.get("item_title", "").strip()
    if not re.match(ITEM_TITLE_REGEX, item_title): raise_custom_exception(error, 400)
    return item_title

##############################
ITEM_DESC_MIN = 10
ITEM_DESC_MAX = 150
ITEM_DESC_REGEX = f"^.{{{ITEM_DESC_MIN},{ITEM_DESC_MAX}}}$"
def validate_item_description():
    error = f"item description must be between {ITEM_DESC_MIN} and {ITEM_DESC_MAX} characters"
    item_description = request.form.get("item_description", "").strip()
    if not re.match(ITEM_DESC_REGEX, item_description):raise_custom_exception(error, 400)
    return item_description

##############################
PRICE_DKK_MIN = 1
PRICE_DKK_MAX = 10000
PRICE_REGEX = r"^(?!0+\.?0*$)\d+\.?\d{0,2}$"

def validate_item_price():
    error = f"price must be between {PRICE_DKK_MIN} and {PRICE_DKK_MAX} DKK"
    
    # Get price from form and handle empty/None cases
    item_price = request.form.get("item_price", "").strip()
    if not item_price:
        raise_custom_exception("Price is required", 400)
    
    # Check format using regex
    if not re.match(PRICE_REGEX, item_price):
        raise_custom_exception("Price format invalid, use numbers with max 2 decimals", 400)
    
    # Convert to float and validate range
    try:
        price_float = float(item_price)
        if price_float < PRICE_DKK_MIN or price_float > PRICE_DKK_MAX:
            raise_custom_exception(error, 400)
        
        # Return standardized format with 2 decimals
        return "{:.2f}".format(price_float)
        
    except ValueError:
        raise_custom_exception("Invalid price format", 400)


##############################
def send_verify_email(to_email, user_verification_key):
    try:

        # Email and password of the sender's Gmail account
        sender_email = "jonasblaedel27@gmail.com"
        password = "fbodthqdtlzgnecj" 

        # Receiver email address
        receiver_email = to_email
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "FoodNest"
        message["To"] = receiver_email
        message["Subject"] = "Please verify your account"

        # Body of the email
        # Body of the email with HTML template
        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #F9FAFB;
                    margin: 0;
                    padding: 0;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background-color: #FFA726;
                    padding: 20px;
                    text-align: center;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                }}
                .content {{
                    padding: 20px;
                    text-align: center;
                }}
                .content p {{
                    font-size: 16px;
                    margin: 20px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #FB8C00;
                    color: white;
                    font-size: 16px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .footer {{
                    text-align: center;
                    padding: 10px;
                    font-size: 12px;
                    color: #666;
                    background-color: #F1F1F1;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    FoodNest
                </div>
                <div class="content">
                    <p>Hello!</p>
                    <p>Thank you for joining FoodNest. Please verify your account to get started.</p>
                    <a href="http://127.0.0.1/verify/{user_verification_key}" class="button">Verify Your Account</a>
                    <p>If you didn't sign up for FoodNest, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    &copy; {time.strftime('%Y')} FoodNest. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """

        message.attach(MIMEText(body, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")

        return "email sent"
       
    except Exception as ex:
        raise_custom_exception("cannot send email", 500)
    finally:
        pass

##############################
def send_verify_delete(to_email, user_pk):
    try:

        # Email and password of the sender's Gmail account
        sender_email = "jonasblaedel27@gmail.com"
        password = "fbodthqdtlzgnecj" 

        # Receiver email address
        receiver_email = to_email
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "FoodNest"
        message["To"] = receiver_email
        message["Subject"] = "Your account has been del"

        # Body of the email
        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #F9FAFB;
                    margin: 0;
                    padding: 0;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background-color: #FFA726;
                    padding: 20px;
                    text-align: center;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                }}
                .content {{
                    padding: 20px;
                    text-align: center;
                }}
                .content p {{
                    font-size: 16px;
                    margin: 20px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #FB8C00;
                    color: white;
                    font-size: 16px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .footer {{
                    text-align: center;
                    padding: 10px;
                    font-size: 12px;
                    color: #666;
                    background-color: #F1F1F1;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    FoodNest
                </div>
                <div class="content">
                    <p>Your account has been deleted successfully.</p>
                    <p>If this action was a mistake or unauthorized, please contact our support team immediately.</p>
                    <a href="mailto:support@foodnest.com" class="button">Contact Support</a>
                </div>
                <div class="footer">
                    &copy; {time.strftime('%Y')} FoodNest. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")

        return "email sent"
       
    except Exception as ex:
        raise_custom_exception("cannot send email", 500)
    finally:
        pass
####################################################################################

def send_reset_password_email(to_email, user_reset_password_token):
    try:

        # Email and password of the sender's Gmail account
        sender_email = "jonasblaedel27@gmail.com"
        password = "fbodthqdtlzgnecj" 

        # Receiver email address
        receiver_email = to_email
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "My company name"
        message["To"] = receiver_email
        message["Subject"] = "Reset your password"

        # Body of the email
        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #F9FAFB;
                    margin: 0;
                    padding: 0;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background-color: #FFA726;
                    padding: 20px;
                    text-align: center;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                }}
                .content {{
                    padding: 20px;
                    text-align: center;
                }}
                .content p {{
                    font-size: 16px;
                    margin: 20px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #FB8C00;
                    color: white;
                    font-size: 16px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .footer {{
                    text-align: center;
                    padding: 10px;
                    font-size: 12px;
                    color: #666;
                    background-color: #F1F1F1;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    FoodNest
                </div>
                <div class="content">
                    <p>To reset your password for your FoodNest account, click the button below:</p>
                    <a href="http://127.0.0.1/reset-password/{to_email}/{user_reset_password_token}" class="button">Reset Password</a>
                    <p>If you didn't request a password reset, please ignore this email or contact our support team.</p>
                </div>
                <div class="footer">
                    &copy; {time.strftime('%Y')} FoodNest. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")

        return "email sent"
       
    except Exception as ex:
        raise_custom_exception("cannot send email", 500)
    finally:
        pass


####################################################################################

def send_user_blocked_email(to_email, user_name):
    try:

        # Email and password of the sender's Gmail account
        sender_email = "jonasblaedel27@gmail.com"
        password = "fbodthqdtlzgnecj" 

        # Receiver email address
        receiver_email = to_email
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "My company name"
        message["To"] = receiver_email
        message["Subject"] = "Your account has been blocked"

        # Body of the email
        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #F9FAFB;
                    margin: 0;
                    padding: 0;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background-color: #E53935;
                    padding: 20px;
                    text-align: center;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                }}
                .content {{
                    padding: 20px;
                    text-align: center;
                }}
                .content p {{
                    font-size: 16px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 10px;
                    font-size: 12px;
                    color: #666;
                    background-color: #F1F1F1;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #FB8C00;
                    color: white;
                    font-size: 16px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    Account Blocked - FoodNest
                </div>
                <div class="content">
                    <p>Dear {user_name},</p>
                    <p>We are sorry to inform you that your account has been blocked due to a violation of our Terms and Conditions.</p>
                    <p>If you believe this was a mistake or would like to appeal, please contact our support team.</p>
                    <a href="http://127.0.0.1/contact-support" class="button">Contact Support</a>
                </div>
                <div class="footer">
                    &copy; {time.strftime('%Y')} FoodNest. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")

        return "email sent"
       
    except Exception as ex:
        raise_custom_exception("cannot send email", 500)
    finally:
        pass

####################################################################################


def send_item_blocked_email(user_email, user_name, item_title):
    try:
        # Email and password of the sender's Gmail account
        sender_email = "jonasblaedel27@gmail.com"
        password = "fbodthqdtlzgnecj" 

        # Receiver email address
        receiver_email = user_email
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "My company name"
        message["To"] = receiver_email
        message["Subject"] = "Your account has been blocked"

        # Body of the email
        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #F9FAFB;
                    margin: 0;
                    padding: 0;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background-color: #FB8C00;
                    padding: 20px;
                    text-align: center;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                }}
                .content {{
                    padding: 20px;
                }}
                .content p {{
                    font-size: 16px;
                    margin: 10px 0;
                    line-height: 1.6;
                }}
                .footer {{
                    text-align: center;
                    padding: 10px;
                    font-size: 12px;
                    color: #666;
                    background-color: #F1F1F1;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #E53935;
                    color: white;
                    font-size: 16px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    Item Blocked Notification
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    <p>We regret to inform you that your item <strong>'{item_title}'</strong> has been blocked by the admin.</p>
                    <p>If you have any questions or require further assistance, please don't hesitate to contact our support team.</p>
                    <a href="http://127.0.0.1/contact-support" class="button">Contact Support</a>
                </div>
                <div class="footer">
                    &copy; {time.strftime('%Y')} FoodNest. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")

        return "email sent"
       
    except Exception as ex:
        raise_custom_exception("cannot send email", 500)
    finally:
        pass

####################################################################################

def send_cart_email(to_email,cart_items):
    try:

        # Email and password of the sender's Gmail account
        sender_email = "jonasblaedel27@gmail.com"
        password = "fbodthqdtlzgnecj" 

        # Create the email message
        message = MIMEMultipart()
        message["From"] = "FoodNest"
        message["To"] = to_email
        message["Subject"] = "Thank you!"

        # HTML Body of the email
        body = """
                <html>
                    <body style="font-family: Arial, sans-serif; background-color: #F9FAFB; margin: 0; padding: 0;">
                        <div style="max-width: 600px; margin: 20px auto; background-color: #FFFFFF; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">
                            <div style="background-color: #FB8C00; color: white; text-align: center; padding: 20px; font-size: 24px; font-weight: bold;">
                                FoodNest Update
                            </div>
                            <div style="padding: 20px; color: #333;">
                                <p>Hello,</p>
                                <p>We're excited to let you know that everything is set, and we're gearing up to delight you soon.</p>
                                <p>Keep an eye out, and get ready to enjoy something special. We're thrilled to serve you!</p>
                                <p>Warm regards,</p>
                                <p><strong>The FoodNest Team</strong></p>
                            </div>
                            <div style="text-align: center; padding: 10px; font-size: 12px; color: #666; background-color: #F1F1F1;">
                                &copy; {time.strftime('%Y')} FoodNest. All rights reserved.
                            </div>
                        </div>
                    </body>
                </html>
                """

        message.attach(MIMEText(body, "html"))

        # Send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, message.as_string())

        print("Email sent successfully!")
        return "Email sent successfully"
    
    except Exception as ex:
        print(f"Error sending email: {ex}")
        raise Exception("Failed to send email")


####################################################################################

def generate_copenhagen_coordinates(restaurant_names):
    # Latitude and longitude boundaries for Copenhagen
    copenhagen_lat_min = 55.65
    copenhagen_lat_max = 55.73
    copenhagen_lon_min = 12.50
    copenhagen_lon_max = 12.65

    # Generate coordinates for each restaurant
    restaurant_locations = []
    for name in restaurant_names:
        lat = round(random.uniform(copenhagen_lat_min, copenhagen_lat_max), 6)
        lon = round(random.uniform(copenhagen_lon_min, copenhagen_lon_max), 6)
        restaurant_locations.append({"name": name, "latitude": lat, "longitude": lon})
    
    return restaurant_locations
