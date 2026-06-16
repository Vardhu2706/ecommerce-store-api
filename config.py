import os
from dotenv import load_dotenv


load_dotenv()

DISCOUNT_EVERY_N = int(os.getenv('DISCOUNT_EVERY_N', 5))
DISCOUNT_PERCENTAGE = float(os.getenv('DISCOUNT_PERCENTAGE', 10.0))
ADMIN_KEY = os.getenv('ADMIN_KEY', 'secret')
RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")