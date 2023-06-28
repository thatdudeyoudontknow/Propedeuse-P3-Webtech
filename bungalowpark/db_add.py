from bungalowpark import db, app, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Existing code...

# Define a function to add standard data to the database
def add_standard_data():
    # Add users
    user1 = User(email='user1@example.com', username='user1', password='password1', woonplaats='City1', huisnummer=1, straat='Street1', postcode='12345')
    user2 = User(email='user2@example.com', username='user2', password=generate_password_hash(password2), woonplaats='City2', huisnummer=2, straat='Street2', postcode='67890')

    db.session.add(user1)
    db.session.add(user2)

    # Add tents
    tent1 = Tent(omschrijving='Tent1', aantal_personen=2, prijs_per_dag=50.0)
    tent2 = Tent(omschrijving='Tent2', aantal_personen=4, prijs_per_dag=100.0)

    db.session.add(tent1)
    db.session.add(tent2)

    # Commit the changes
    db.session.commit()

# Create the database tables
with app.app_context():
    db.create_all()

    # Add the standard data to the database
    add_standard_data()
