import json
import os
import requests
from flask import (
    render_template, redirect, request,
    send_file, flash, url_for
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    login_required, current_user,
    login_user, logout_user
)
from app import db, login_manager
from app.models import User
from app.forms import LoginForm

# Configuration
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
ADDR = "http://127.0.0.1:8800"
UPLOAD_FOLDER = 'static/Uploads'

# Global variables
request_tx = []
files = {}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_app(app):
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    def get_tx_req():
        global request_tx
        try:
            resp = requests.get(f"{ADDR}/chain", timeout=5)
            if resp.status_code == 200:
                content = []
                chain = resp.json()
                for block in chain["chain"]:
                    for trans in block["transactions"]:
                        trans["index"] = block["index"]
                        trans["hash"] = block["previous_hash"]
                        content.append(trans)
                request_tx = sorted(content, key=lambda k: k["hash"], reverse=True)
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Failed to fetch chain: {str(e)}")

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            
            if not user:
                try:
                    hashed_password = generate_password_hash(form.password.data)
                    new_user = User(username=form.username.data, password=hashed_password)
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user, remember=form.remember.data)
                    flash('Account created! You are now logged in.', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('index'))
                except Exception as e:
                    db.session.rollback()
                    flash('Account creation failed. Please try again.', 'danger')
            elif check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Login failed. Check username and password', 'danger')
        
        return render_template('login.html', title='Login', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route("/")
    @login_required
    def index():
        get_tx_req()
        return render_template("index.html",
                            title="FileStorage",
                            subtitle="Decentralized File Storage",
                            node_address=ADDR,
                            request_tx=request_tx)

    @app.route("/submit", methods=["POST"])
    @login_required
    def submit():
        if 'v_file' not in request.files:
            flash('No file selected', 'danger')
            return redirect("/")

        file = request.files['v_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect("/")

        if not allowed_file(file.filename):
            flash('File type not allowed', 'danger')
            return redirect("/")

        try:
            # Check file size without saving
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                flash(f'File too large (max {MAX_FILE_SIZE//1024//1024}MB)', 'danger')
                return redirect("/")

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save file and store path
            file.save(filepath)
            files[filename] = filepath

            # Read file content
            with open(filepath, 'rb') as f:
                file_content = f.read()

            # Prepare transaction
            transaction = {
                "user": current_user.username,
                "v_file": filename,
                "file_data": file_content.hex(),
                "file_size": file_size
            }

            # Submit to blockchain
            try:
                response = requests.post(
                    f"{ADDR}/new_transaction",
                    json=transaction,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 201:
                    flash('File uploaded and transaction created!', 'success')
                else:
                    error = response.json().get('error', response.text)
                    flash(f'Blockchain error: {error}', 'danger')
                    
            except requests.exceptions.RequestException as e:
                flash(f'Network error: {str(e)}', 'danger')
            
            return redirect("/")
            
        except Exception as e:
            flash(f'Unexpected error: {str(e)}', 'danger')
            return redirect("/")

    @app.route("/submit/<string:filename>", methods=["GET"])
    def download_file(filename):
        if filename in files:
            try:
                return send_file(files[filename], as_attachment=True)
            except Exception as e:
                flash(f"Download failed: {str(e)}", 'danger')
        flash("File not found", 'danger')
        return redirect(url_for('index'))

    @app.route("/mine", methods=["GET"])
    @login_required
    def mine_unconfirmed_transactions():
        try:
            resp = requests.get(f"{ADDR}/mine", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('transactions', 0) > 0:
                flash(f"✅ Mined Block #{data['index']} with {data['transactions']} transactions", 'success')
            else:
                flash(data.get('message', 'No transactions to mine'), 'info')
                
        except requests.exceptions.HTTPError as e:
            try:
                error_msg = e.response.json().get('error', str(e))
            except ValueError:
                error_msg = str(e)
            flash(f"⚠️ Mining failed: {error_msg}", 'danger')
        except requests.exceptions.RequestException as e:
            flash(f"⚠️ Network error: {str(e)}", 'danger')
        except Exception as e:
            flash(f"⚠️ Unexpected error: {str(e)}", 'danger')
        
        return redirect(url_for('index'))