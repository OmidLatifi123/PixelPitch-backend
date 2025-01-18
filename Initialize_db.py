from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quickpitch.db'  # SQLite Database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "Entrepreneur" or "Investor"
    pitches = db.relationship('Pitch', backref='user', lazy=True)

class Investor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    personality = db.Column(db.String(120), nullable=False)  # Personality traits
    preferences = db.Column(db.String(120), nullable=False)  # Preferences or interests
    pitches = db.relationship('Pitch', backref='investor', lazy=True)

class Pitch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    investor_id = db.Column(db.Integer, db.ForeignKey('investor.id'), nullable=False)

class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pitch_id = db.Column(db.Integer, db.ForeignKey('pitch.id'), nullable=False)
    result = db.Column(db.String(80), nullable=False)  # Accepted, Rejected, Pending
    feedback = db.Column(db.Text, nullable=True)  # Feedback from the AI investor

# Function to create tables
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database initialized successfully with the updated schema.")