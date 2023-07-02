from bungalowpark import db, app, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from datetime import datetime
# login_manager haalt user op
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)




class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer(),primary_key= True)
    email = db.Column(db.String(64), unique=True, nullable=False, index=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)

    woonplaats = db.Column(db.String(40), nullable=False)
    huisnummer = db.Column(db.Integer(), nullable=False)
    toevoeging = db.Column(db.String(6), nullable=True)
    straat = db.Column(db.String(40), nullable=False)
    postcode = db.Column(db.String(6), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_expiration = db.Column(db.DateTime)

    def __init__(self, email, username,password, woonplaats,huisnummer,straat,postcode,toevoeging,role='user'):
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.woonplaats = woonplaats
        self.huisnummer = huisnummer
        self.toevoeging = toevoeging
        self.straat = straat
        self.postcode = postcode
        self.role = role


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_account(self, email, username, woonplaats, huisnummer, toevoeging, straat, postcode):
        self.email = email
        self.username = username
        self.woonplaats = woonplaats
        self.huisnummer = huisnummer
        self.toevoeging = toevoeging
        self.straat = straat
        self.postcode = postcode
        db.session.commit()

    def __repr__(self):
        return f"account, {self.username}"





class Boeking(db.Model):
    __tablename__ = 'reserveringen'
    id = db.Column(db.Integer(), primary_key=True)
    bungalowID = db.Column(db.Integer(), nullable=False)
    tent_omschrijving = db.Column(db.String(100), nullable=False)
    startdatum = db.Column(db.Date(), nullable=False)
    einddatum = db.Column(db.Date(), nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, bungalowID, tent_omschrijving, startdatum, einddatum, userID):
        self.bungalowID = bungalowID
        self.tent_omschrijving = tent_omschrijving
        self.startdatum = startdatum
        self.einddatum = einddatum
        self.userID = userID

    def __repr__(self):
        return f"Boeking {self.id}: bungalow {self.bungalowID}, tent {self.tent_omschrijving}, startdatum {self.startdatum}, einddatum {self.einddatum}"

    
    


class Tent(db.Model):
    __tablename__ = 'tenten'

    id = db.Column(db.Integer(), primary_key=True)
    naam = db.Column(db.String(100), nullable=False)
    omschrijving = db.Column(db.String(1000), nullable=False)
    aantal_personen = db.Column(db.Integer(), nullable=False)
    prijs_per_dag = db.Column(db.Float(), nullable=False)

    def __init__(self,naam, omschrijving, aantal_personen, prijs_per_dag):
        self.naam = naam
        self.omschrijving = omschrijving
        self.aantal_personen = aantal_personen
        self.prijs_per_dag = prijs_per_dag

    def __repr__(self):
        return f"Tent {self.id}: {self.omschrijving}"
    
    
with app.app_context():
    db.create_all()

