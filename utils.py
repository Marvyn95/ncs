import os
import secrets
from functools import wraps
from flask import session, flash, redirect, url_for


def save_file(file, upload_folder='static/uploads'):
    if not file or file.filename == '':
        return None
    ext = os.path.splitext(file.filename)[1]
    filename = secrets.token_hex(16) + ext
    folder = os.path.join(os.getcwd(), upload_folder)
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))
    return filename

def delete_file(filename, upload_folder='static/uploads'):
    file_path = os.path.join(os.getcwd(), upload_folder, filename)
    try:
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    except FileNotFoundError:
        pass

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("userid"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function