import os

os.environ.setdefault("SECRET_KEY", "your-secret-key-here")
os.environ.setdefault("DATABASE_URL", "your-database-url-here")
os.environ.setdefault("CLOUDINARY_URL", "cloudinary://api_key:api_secret@cloud_name")
os.environ.setdefault("EMAIL_HOST_USER", "your-email@gmail.com")
os.environ.setdefault("EMAIL_HOST_PASS", "your-gmail-app-password-here")
os.environ.setdefault("HOST", "your-deployed-host.herokuapp.com")

# local development only — do not set these in production
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("LOCALHOST", "1")
os.environ.setdefault("DEVELOPMENT", "1")
