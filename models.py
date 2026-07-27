from flask_login import UserMixin
from app import db

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    def get_id(self):
        return self.uid
    
class Room(db.Model):
    __tablename__ = 'room'
    code = db.Column(db.String, primary_key=True)
    public = db.Column(db.Boolean, nullable=False)
    accessible = db.Column(db.Boolean, nullable=False)
    plrs = db.relationship('PlayerInRoom', backref='room_obj', cascade='all, delete-orphan')
    text_num = db.Column(db.Integer, nullable=False)

class PlayerInRoom(db.Model):
    __tablename__ = 'player_in_room'
    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String, db.ForeignKey('room.code'))
    socket_id = db.Column(db.String, nullable=False, unique=True)
    username = db.Column(db.String, nullable=False)
    car_color = db.Column(db.String, nullable=False)
    car_filter = db.Column(db.String, nullable=False)

class UserStats(db.Model):
    __tablename__ = 'user_stats'
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'), primary_key=True)
    total_races = db.Column(db.Integer, nullable=False)
    wins = db.Column(db.Integer, nullable=False)
    win_rate = db.Column(db.Float, nullable=False)
    best_speed = db.Column(db.Integer, nullable=False)
    user = db.relationship('User', uselist=False)