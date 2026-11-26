import os

os.environ.setdefault("SECRET_KEY", "your-secret-key-here")
os.environ.setdefault("CLOUDINARY_URL", "cloudinary://api_key:api_secret@cloud_name")
os.environ.setdefault("EMAIL_HOST_USER", "your-email@gmail.com")
os.environ.setdefault("EMAIL_HOST_PASS", "your-gmail-app-password-here")

# Optional: leave DATABASE_URL unset to use a local SQLite database
# (db.sqlite3). Set it to a Postgres URL to use that database instead.
# os.environ.setdefault("DATABASE_URL", "postgres://user:password@host:5432/dbname")

# local development only — do not set these in production
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("LOCALHOST", "1")  # adds 127.0.0.1 to ALLOWED_HOSTS
os.environ.setdefault("DEVELOPMENT", "1")  # switches email backend to console output
