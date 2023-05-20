from bungalowpark import db, app, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user

# login_manager haalt user op
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(db.Model,UserMixin):

    __tablename__ = 'users'

    id = db.Column(db.Integer(),primary_key= True)
    email = db.Column(db.String(64), unique=True, nullable=False, index=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)

    woonplaats = db.Column(db.String(40), nullable=False)
    huisnummer = db.Column(db.Integer(), nullable=False)
    straat = db.Column(db.String(40), nullable=False)
    postcode = db.Column(db.String(6), nullable=False)



    def __init__(self, email, username,password, woonplaats,huisnummer,straat,postcode):
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.woonplaats = woonplaats
        self.huisnummer = huisnummer
        self.straat = straat
        self.postcode = postcode


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"Welkom, {self.username}"


class Boeking(db.Model):

    __tablename__ = 'reserveringen'

    id = db.Column(db.Integer(),primary_key= True)
    bungalowID =  db.Column(db.Integer(), db.ForeignKey('bungalows.id'), nullable=False)
    email = db.Column(db.Integer(), nullable=False)
    startdatum = db.Column(db.Integer(), nullable=False)
    einddatum = db.Column(db.Integer(), nullable=False)
    
    def __init__(self,startdatum,email,einddatum,bungalowID):
        self.bungalowID = bungalowID
        self.email = email
        self.startdatum = startdatum
        self.einddatum = einddatum

    def __repr__(self):
        return f"de boeking is gedaan bij {self.userID} voor week  {self.startdatum}. De bungalow is {self.bungalowID}"
    
class Bungalow(db.Model):

    __tablename__ = 'bungalows'

    id = db.Column(db.Integer(),primary_key = True)
    naam = db.Column(db.String(50), nullable=False, unique=True, index=True)
    typeID = db.Column(db.Integer(),db.ForeignKey('type.id'))
    boeking = db.relationship('Boeking', backref='bungalow' ,uselist=False)

    def __init__(self,naam,typeID):
        self.naam = naam
        self.typeID = typeID
    
    def __repr__(self):
        return f"De naam {self.naam} en het type is  { self.bungalowType.aantalPersonen}"

class BungalowType(db.Model):

    __tablename__ = 'type'

    id = db.Column(db.Integer(),primary_key= True)
    aantalPersonen = db.Column(db.Integer(), nullable=False )
    weekprijs = db.Column(db.Numeric(10,2), nullable=False)
    bungalow = db.relationship('Bungalow',backref='bungalowType',uselist=False)

    def __init__(self,aantalPersonen,weekprijs):
        self.aantalPersonen = aantalPersonen
        self.weekprijs = weekprijs

    def __repr__(self):
        return f"Dit type heeft plaats voor {self.aantalPersonen} personen en weekprijs is {self.weekprijs} "

with app.app_context():
    db.create_all()

