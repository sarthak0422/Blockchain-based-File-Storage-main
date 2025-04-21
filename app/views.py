import os
import requests
from flask import (
    render_template, redirect, request,
    send_file, flash, url_for
)
from werkzeug.utils import secure_filename
from flask_login import (
    login_required, current_user,
    login_user, logout_user
)
from datetime import datetime
from app import db, login_manager
from app.models import User, File
from app.forms import LoginForm

# Configuration
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
ADDR = "http://127.0.0.1:8800"
UPLOAD_FOLDER = 'static/Uploads'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def init_app(app):
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()

            if not user:
                try:
                    new_user = User(username=form.username.data)
                    new_user.set_password(form.password.data)
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user, remember=form.remember.data)
                    flash('Account created! You are now logged in.', 'success')
                    return redirect(url_for('index'))
                except Exception:
                    db.session.rollback()
                    flash('Account creation failed. Please try again.', 'danger')
            elif user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('index'))
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
        user_files = File.query.filter_by(user_id=current_user.id).order_by(File.uploaded_at.desc()).all()

        request_tx = [{
            "user": current_user.username,
            "v_file": f.filename,
            "file_size": f.size,
            "uploaded_at": f.uploaded_at.strftime('%Y-%m-%d %H:%M'),
            "is_mined": f.is_mined,
            "blockchain_tx": f.blockchain_tx
        } for f in user_files]

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
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            if file_size > MAX_FILE_SIZE:
                flash(f'File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)', 'danger')
                return redirect("/")

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            new_file = File(
                filename=filename,
                filepath=filepath,
                user_id=current_user.id,
                size=file_size,
                is_mined=False
            )
            db.session.add(new_file)

            with open(filepath, 'rb') as f:
                file_content = f.read()

            transaction = {
                "user": current_user.username,
                "v_file": filename,
                "file_data": file_content.hex(),
                "file_size": file_size
            }

            try:
                response = requests.post(
                    f"{ADDR}/new_transaction",
                    json=transaction,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )

                if response.status_code == 201:
                    db.session.commit()
                    flash('File uploaded and transaction created! Mine a block to confirm.', 'success')
                else:
                    db.session.rollback()
                    os.remove(filepath)
                    error = response.json().get('error', response.text)
                    flash(f'Blockchain error: {error}', 'danger')

            except requests.exceptions.RequestException as e:
                db.session.rollback()
                os.remove(filepath)
                flash(f'Network error: {str(e)}', 'danger')

            return redirect("/")

        except Exception as e:
            db.session.rollback()
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            flash(f'Unexpected error: {str(e)}', 'danger')
            return redirect("/")

    @app.route("/submit/<string:filename>", methods=["GET"])
    @login_required
    def download_file(filename):
        file_record = File.query.filter_by(filename=filename, user_id=current_user.id).first()
        if not file_record:
            flash("File not found", 'danger')
            return redirect(url_for('index'))

        if not file_record.is_mined:
            flash("File not yet confirmed in blockchain. Please mine a block first.", 'warning')
            return redirect(url_for('index'))

        if not os.path.exists(file_record.filepath):
            flash("File not found on server", 'danger')
            return redirect(url_for('index'))

        try:
            return send_file(file_record.filepath, as_attachment=True)
        except Exception as e:
            flash(f"Download failed: {str(e)}", 'danger')
            return redirect(url_for('index'))

    @app.route("/mine", methods=["GET"])
    @login_required
    def mine_unconfirmed_transactions():
        try:
            # First get pending transactions
            pending_resp = requests.get(f"{ADDR}/pending_tx", timeout=5)
            pending_resp.raise_for_status()
            pending_tx = pending_resp.json().get('pending', [])

            if not pending_tx:
                flash("No transactions to mine", 'info')
                return redirect(url_for('index'))

            # Mine the block
            mine_resp = requests.get(f"{ADDR}/mine", timeout=10)
            mine_resp.raise_for_status()
            mine_data = mine_resp.json()

            if mine_data.get('message') == "New Block Forged":
                for tx in pending_tx:
                    file = File.query.filter_by(
                        filename=tx['v_file'],
                        user_id=current_user.id
                    ).first()
                    if file:
                        file.is_mined = True
                        file.blockchain_tx = str(mine_data['index'])
                db.session.commit()
                flash(f"Mined Block #{mine_data['index']} with {len(pending_tx)} transactions", 'success')
            else:
                flash(mine_data.get('message', 'Mining failed'), 'danger')

            return redirect(url_for('index'))

        except requests.exceptions.RequestException as e:
            flash(f"Mining failed: {str(e)}", 'danger')
            return redirect(url_for('index'))
