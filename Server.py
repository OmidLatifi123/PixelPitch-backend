from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quickpitch.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Role field to distinguish users

class Investor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    personality = db.Column(db.String(120), nullable=False)
    preferences = db.Column(db.String(120), nullable=False)

class Pitch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    investor_id = db.Column(db.Integer, db.ForeignKey('investor.id'), nullable=False)

class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pitch_id = db.Column(db.Integer, db.ForeignKey('pitch.id'), nullable=False)
    result = db.Column(db.String(80), nullable=False)
    feedback = db.Column(db.Text, nullable=True)

# Routes
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the QuickPitch Backend!"})

# Register Route
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    role = data.get('role')
    email = data.get('email')
    username = data.get('username')

    if not email or not username or not role:
        return jsonify({"error": "Invalid input. Please provide all required fields."}), 400

    if role.lower() == "entrepreneur":
        user = User(username=username, email=email, role="Entrepreneur")
        db.session.add(user)
    elif role.lower() == "investor":
        investor = Investor(name=username, email=email, personality="default", preferences="default")
        db.session.add(investor)
    else:
        return jsonify({"error": "Invalid role specified."}), 400

    db.session.commit()
    return jsonify({"message": f"{role.capitalize()} registered successfully!"})

# Login Route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"error": "Invalid input. Please provide an email."}), 400

    # Check if the email exists in the User table
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"message": f"{user.role} logged in successfully!", "role": user.role})

    # Check if the email exists in the Investor table
    investor = Investor.query.filter_by(email=email).first()
    if investor:
        return jsonify({"message": "Investor logged in successfully!", "role": "Investor"})

    return jsonify({"message": "Login failed. User not found."}), 404

# Add a Pitch
@app.route('/add_pitch', methods=['POST'])
def add_pitch():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    user_id = data.get('user_id')
    investor_id = data.get('investor_id')

    if not title or not description or not user_id or not investor_id:
        return jsonify({"error": "Invalid input. Please provide all required fields."}), 400

    pitch = Pitch(title=title, description=description, user_id=user_id, investor_id=investor_id)
    db.session.add(pitch)
    db.session.commit()
    return jsonify({"message": "Pitch added successfully!"})

# List All Pitches
@app.route('/pitches', methods=['GET'])
def list_pitches():
    pitches = Pitch.query.all()
    output = []
    for pitch in pitches:
        output.append({
            "id": pitch.id,
            "title": pitch.title,
            "description": pitch.description,
            "user_id": pitch.user_id,
            "investor_id": pitch.investor_id
        })
    return jsonify(output)

if __name__ == '__main__':
    app.run(debug=True)