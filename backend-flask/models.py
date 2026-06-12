from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # User Profile Data
    height = db.Column(db.Float) # cm
    weight = db.Column(db.Float) # kg
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    goal = db.Column(db.String(100)) # 'Weight Loss', etc.
    activity_level = db.Column(db.String(50))
    
    # Relationship to chat messages
    chat_messages = db.relationship('ChatMessage', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'height': self.height,
            'weight': self.weight,
            'age': self.age,
            'gender': self.gender,
            'goal': self.goal,
            'activity_level': self.activity_level
        }


class ChatMessage(db.Model):
    """Model to store chat history"""
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'ai'
    model_used = db.Column(db.String(100))  # Which model was used for AI response
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(50))  # To group messages by session

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'sender': self.sender,
            'model_used': self.model_used,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'session_id': self.session_id
        }




