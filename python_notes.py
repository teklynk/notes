import os, sqlite3, uuid
from flask import Flask, request, render_template, make_response, redirect, url_for, Response, g
from flask_limiter import Limiter
from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
from functools import wraps
from cryptography.fernet import Fernet, InvalidToken
import markdown

# Check if .env exists (local mode)
LOCAL_MODE = os.path.exists('.env')
if LOCAL_MODE:
    load_dotenv()

# Generate a key using: Fernet.generate_key() and set it in .env
def ensure_encryption_key():
    # Ensure ENCRYPTION_KEY exists in .env, generate and add if missing.
    encryption_key = os.getenv('ENCRYPTION_KEY')
    if not encryption_key:
        new_key = Fernet.generate_key().decode()
        # Append to .env
        with open('.env', 'a') as env_file:
            env_file.write(f'\nENCRYPTION_KEY={new_key}\n')
        print(f"Generated new ENCRYPTION_KEY and added to .env: {new_key}")
        # Reload .env to pick up the new key
        os.environ['ENCRYPTION_KEY'] = new_key
        return new_key
    return encryption_key

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
encryption_key = ensure_encryption_key()
fernet = Fernet(encryption_key)

def get_real_ip():
    # Use Cloudflare's header if present, else fallback to remote address
    return request.headers.get('CF-Connecting-IP', request.remote_addr)

limiter = Limiter(
    app,
    key_func=get_real_ip
)

def get_db():
    # Opens a new database connection if there is none yet for the current application context.
    if 'db' not in g:
        g.db = sqlite3.connect('notes.db')
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    # Closes the database again at the end of the request.
    db = g.pop('db', None)
    if db is not None:
        db.close()

def check_auth(username, password):
    # This function is called to check if a username / password combination is valid.
    return username == os.getenv('HTTP_USER') and password == os.getenv('HTTP_PASS')

def authenticate():
    # Sends a 401 response that enables basic auth
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Only enforce auth if credentials are set in the environment
        http_user = os.getenv('HTTP_USER')
        http_pass = os.getenv('HTTP_PASS')
        if not (http_user and http_pass):
            return f(*args, **kwargs)

        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def requires_origin_check(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        allowed_domain = os.getenv('ALLOWED_DOMAIN')
        if request.method == 'POST':
            origin = request.headers.get('Origin')
            referer = request.headers.get('Referer')

            if not origin and not referer:
                return "Forbidden: Missing origin", 403
            if not ((origin and origin.startswith(allowed_domain)) or (referer and referer.startswith(allowed_domain))):
                return "Forbidden: Invalid origin", 403
        elif request.method == 'GET':
            origin = request.headers.get('Origin')
            if origin and not origin.startswith(allowed_domain):
                return "Forbidden: Invalid origin", 403

        return f(*args, **kwargs)
    return decorated

def init_db():
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Default route
@app.route('/', methods=['GET'])
@requires_auth
@requires_origin_check
@limiter.limit("60 per minute")
def list_notes():
    db = get_db()
    notes = db.execute('SELECT id, name, created_at FROM notes ORDER BY created_at DESC').fetchall()
    return render_template('index.html', notes=notes)

@app.route('/raw/<note_id>')
def raw_note(note_id):
    db = get_db()
    note = db.execute('SELECT content FROM notes WHERE id = ?', (note_id,)).fetchone()
    if note:
        try:
            # Decrypt the content
            decrypted_content = fernet.decrypt(note['content']).decode()
        except InvalidToken:
            return redirect(url_for('list_notes'))
        raw = render_template('raw.txt', content=decrypted_content)
        response = make_response(raw)
        response.headers['Content-Type'] = 'text/plain'
        return response
    else:
        return redirect(url_for('list_notes'))

@app.route('/create', methods=['GET', 'POST'])
@requires_auth
@requires_origin_check
@limiter.limit("60 per minute")
def create():
    form = NoteForm()
    if form.validate_on_submit():
        name = form.note_name.data
        content = form.note_content.data
        encrypted_content = fernet.encrypt(content.encode())
        note_id = str(uuid.uuid4())[:8]
        db = get_db()
        db.execute('INSERT INTO notes (id, name, content) VALUES (?, ?, ?)', (note_id, name, encrypted_content))
        db.commit()
        return redirect(url_for('view_note', note_id=note_id))
    return render_template('create.html', form=form)

@app.route('/edit/<note_id>', methods=['GET', 'POST'])
@requires_auth
@requires_origin_check
@limiter.limit("60 per minute")
def edit(note_id):
    db = get_db()
    note = db.execute('SELECT name, content FROM notes WHERE id = ?', (note_id,)).fetchone()
    if not note:
        return redirect(url_for('list_notes'))
    try:
        name = note['name']
        decrypted_content = fernet.decrypt(note['content']).decode()
    except InvalidToken:
        return redirect(url_for('list_notes'))

    form = NoteForm(note_name=name, note_content=decrypted_content)

    if form.validate_on_submit():
        # The decorator handles the POST check, so we can just validate the form
        name = form.note_name.data
        content = form.note_content.data
        encrypted_content = fernet.encrypt(content.encode())
        db.execute('UPDATE notes SET name = ?, content = ? WHERE id = ?', (name, encrypted_content, note_id))
        db.commit()
        return redirect(url_for('view_note', note_id=note_id))

    return render_template('edit.html', form=form, name=name, content=decrypted_content, note_id=note_id)

@app.route('/delete/<note_id>', methods=['POST'])
@requires_auth
@requires_origin_check
@limiter.limit("60 per minute")
def delete_note(note_id):
    db = get_db()
    db.execute('DELETE FROM notes WHERE id = ?', (note_id,)).fetchone()
    db.commit()
    return redirect(url_for('list_notes'))

@app.route('/<note_id>')
@requires_auth
def view_note(note_id):
    db = get_db()
    note = db.execute('SELECT name, content FROM notes WHERE id = ?', (note_id,)).fetchone()
    if note:
        try:
            name = note['name']
            # Decrypt the content
            markdown_content = fernet.decrypt(note['content']).decode()
            # Convert Markdown to HTML
            extensions = [
                'pymdownx.superfences',
                'pymdownx.tasklist',
                'pymdownx.tilde',
                'pymdownx.details',
            ]
            html_content = markdown.markdown(markdown_content, extensions=extensions)
        except InvalidToken:
            return redirect(url_for('list_notes'))
        return render_template('view.html', name=name, content=html_content, note_id=note_id)
    else:
        return redirect(url_for('list_notes'))

class NoteForm(FlaskForm):
    note_name = StringField('Note', validators=[DataRequired()])
    note_content = TextAreaField('Note', validators=[DataRequired()])

if __name__ == '__main__':
    # Create the database if it does not exist
    init_db()
    # Start the app
    app.run(debug=True, host="0.0.0.0", port=5001)