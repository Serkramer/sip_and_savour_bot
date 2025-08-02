import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
PAYMENT_LINK = os.getenv("PAYMENT_LINK")
UK_PHONE_PATTERN = r"^\+380\d{9}$"
EMAIL_PATTERN = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
ADMINS_STR = os.getenv("ADMINS", "")
ADMINS = [int(admin_id.strip()) for admin_id in ADMINS_STR.split(",") if admin_id.strip().isdigit()]