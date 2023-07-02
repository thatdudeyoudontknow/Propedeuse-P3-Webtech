import os
from flask import Flask, render_template, redirect, request, url_for, flash,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user 
from datetime import datetime
from werkzeug.urls import url_parse
from werkzeug.security import generate_password_hash
from flask_login import current_user
from datetime import datetime, timedelta
from functools import wraps
import secrets


app = Flask(__name__)
app.config['SECRET_KEY'] = 'X11gc3N5hb78RGyKY4qk5qHZ8aqC4Ch7'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

db = SQLAlchemy(app)
Migrate(app, db)

from bungalowpark.models import  User, Boeking, Tent 
from bungalowpark.forms import LoginForm, RegistrationForm, BoekingForm, AccountUpdateForm,wwupdateform
from functools import wraps


# Decorator function to check if the user is authenticated and query the bookings
def check_user_bookings(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        heeft_boekingen = None
        if current_user.is_authenticated:
            heeft_boekingen = Boeking.query.filter_by(userID=current_user.id).first()
        return f(heeft_boekingen=heeft_boekingen, *args, **kwargs)
    return decorated_function

# Error handler
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.is_anonymous:
                # Handle the case when the user is not logged in
                return redirect(url_for('/'))


            if 'admin' in roles and current_user.role != 'admin':
                # Handle the case when the user is not an admin
                return render_template('404.html'), 404

            if 'user' in roles and current_user.role != 'user':
                # Handle the case when the user is not a regular user
                return render_template('404.html'), 404

            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

@app.route('/')
@check_user_bookings
def index(heeft_boekingen):
    return render_template('home.html',  name=current_user , heeft_boekingen=heeft_boekingen )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'Je bent nu uitgelogd!', 'success')
    return redirect(url_for('index'))

# @app.route('/boekingen')
# @login_required
# @check_user_bookings
# def boekingen(heeft_boekingen):
#     today = datetime.now()
#     weeknummer = datetime.date(today).isocalendar()[1]
#     nieuweBoekingen = Boeking.query.filter(Boeking.userID == current_user.id, Boeking.weeknummer > weeknummer)
#     oudeBoekingen = Boeking.query.filter(Boeking.userID == current_user.id, Boeking.weeknummer <= weeknummer)
#     return render_template('boekingen.html', nieuweBoekingen=nieuweBoekingen, oudeBoekingen=oudeBoekingen, heeft_boekingen=heeft_boekingen)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user)
            flash(u'Succesvol ingelogd.', 'success')
    
            next = request.args.get('next')
            if not next or url_parse(next).netloc != '':
                next = url_for('index')
            return redirect(url_parse(next).path)
        
        else:
            flash(u'U email of wachtwoord is niet correct.', 'warning')     
    elif form.email.errors:  
        flash(u'Uw email is niet bestaand', 'warning')
    return render_template('login.html', form=form) 




@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_email = User.query.filter_by(email=form.email.data).first()
        user_username = User.query.filter_by(username=form.username.data).first()

        if user_email:
            flash(u'Dit emailadres is al in gebruik. Kies een ander emailadres.', 'warning')
        elif user_username:
            flash(u'Deze gebruikersnaam is al in gebruik. Kies een andere gebruikersnaam.', 'warning')

        else:
            user = User(email=form.email.data,
                        username=form.username.data,
                        password=form.password.data,
                        woonplaats=form.woonplaats.data,
                        huisnummer=form.huisnummer.data,
                        toevoeging=form.toevoeging.data,
                        straat=form.straat.data,
                        postcode=form.postcode.data)

            db.session.add(user)
            db.session.commit()



            flash(u'Dank voor de registratie. Er kan nu ingelogd worden! ', 'success')
            return redirect(url_for('login'))
    elif form.email.errors:
        flash(u'Dit email is incorrect')    

    elif form.postcode.errors:
        flash(u'Ongeldige postcode')
    
    elif form.woonplaats.errors:
        flash(u'Ongeldige woonplaats')
              
    elif form.straat.errors:
        flash(u'Ongeldige straatnaam')

    elif form.password.errors:
        flash(u'Wachtwoord komt niet overeen')

    return render_template('register.html', form=form)



@app.route('/1reserveringspagina', methods=['GET', 'POST'])
@login_required
@check_user_bookings
def reserveer(heeft_boekingen):
    form = BoekingForm()
    tents = Tent.query.all()
    if form.validate_on_submit():
        # Get the selected tent ID from the form
        tent = Tent.query.get(form.tent.data)

        try:
            startdatum = datetime.strptime(form.startdatum.data, '%Y-%m-%d').date()
            einddatum = datetime.strptime(form.einddatum.data, '%Y-%m-%d').date()
        except ValueError:
            flash(u'Ongeldige datumnotatie. Gebruik het formaat DD-MM-JJJJ', 'error')
            return redirect(url_for('reserveer'))

        # Check if the start date is at least 7 days from now
        min_startdatum = datetime.now().date() + timedelta(days=7)
        if startdatum < min_startdatum:
            flash(u'De startdatum moet minimaal 7 dagen in de toekomst liggen', 'error')
            return redirect(url_for('reserveer'))

        # Check if there is at least 1 day in between the start and end dates
        if (einddatum - startdatum).days < 1:
            flash(u'Er moet minimaal 1 dag tussen de start- en einddatum liggen', 'error')
            return redirect(url_for('reserveer'))

        boeking = Boeking(bungalowID="1", tent_omschrijving=tent.naam,
                          startdatum=startdatum, einddatum=einddatum, userID=current_user.id)

        db.session.add(boeking)
        db.session.commit()

        flash(u'U heeft met succes uw bungalow geboekt', 'success')
        return redirect(url_for('gebruiker'))

    return render_template('1reserveringspagina.html', name=current_user, form=form, tents=tents, heeft_boekingen=heeft_boekingen)


@app.route('/gebruiker')
@login_required
@check_user_bookings
def gebruiker(heeft_boekingen):

    bungID = Boeking.query.filter_by(userID=current_user.id).all()
    

    return render_template('gebruiker.html',name=current_user, bungID=bungID, heeft_boekingen=heeft_boekingen)




@app.route('/update_boeking', methods=['POST'])
def update_boeking():

    # Get form data
    boeking_id = request.form.get('boeking_id')
    startdatum_str = request.form.get('startdatum')
    einddatum_str = request.form.get('einddatum')

    # Check if the required fields are empty
    if not all([boeking_id, startdatum_str, einddatum_str]):
        flash(u'Ongeldige datumnotatie. Gebruik het formaat DD-MM-JJJJ', 'error')
        return  redirect('/gebruiker')

    try:
        # Parse the date strings
        startdatum = datetime.strptime(startdatum_str, '%Y-%m-%d').date()
        einddatum = datetime.strptime(einddatum_str, '%Y-%m-%d').date()

         # Retrieve the Boeking record from the database
        boeking = Boeking.query.get(boeking_id)

        if boeking:
            # Check if the logged-in user owns the Boeking record
            if current_user.id == boeking.userID:
                min_startdatum = datetime.now().date() + timedelta(days=7)
                if startdatum < min_startdatum:
                    flash(u'De startdatum moet minimaal 7 dagen in de toekomst liggen', 'error')
                    return redirect(url_for('gebruiker'))

                # Check if there is at least 1 day in between the start and end dates
                if (einddatum - startdatum).days < 1:
                    flash(u'Er moet minimaal 1 dag tussen de start- en einddatum liggen', 'error')
                    return redirect(url_for('gebruiker'))

                # Update the Boeking record
                boeking.startdatum = startdatum
                boeking.einddatum = einddatum

                # Commit the changes to the database
                db.session.commit()

                # Redirect the user to a relevant page
                return redirect('/gebruiker')
            else:
                flash("Er ging iets fout. Probeer het opnieuw.")
                return redirect('/gebruiker')
        else:
            flash(u'Boeking ID is niet bekend', 'warning')
            return redirect('/gebruiker')
    except ValueError:
        flash(u'Ongeldige datumnotatie. Gebruik het formaat DD-MM-JJJJ', 'error')
        return redirect('/gebruiker')


@app.route('/1accomidatiepagina')
@check_user_bookings

def accomidatiepagina(heeft_boekingen):
    bungnaam1 = Tent.query.filter_by(id=1).first()
    bungnaam2 = Tent.query.filter_by(id=2).first()
    bungnaam3 = Tent.query.filter_by(id=3).first()
    bungnaam4 = Tent.query.filter_by(id=4).first()
    return render_template('1accomidatiepagina.html', bungnaam1=bungnaam1, bungnaam2=bungnaam2, bungnaam3=bungnaam3, bungnaam4=bungnaam4, name=current_user, heeft_boekingen=heeft_boekingen)

@app.route('/1activiteitenpagina')
@check_user_bookings
def activiteitenpagina(heeft_boekingen):
    return render_template('1activiteitenpagina.html',name=current_user, heeft_boekingen=heeft_boekingen)

@app.route('/1blogpagina')
@check_user_bookings
def blogpagina(heeft_boekingen):
    return render_template('1blogpagina.html',name=current_user, heeft_boekingen=heeft_boekingen)

@app.route('/1contactpagina')
@check_user_bookings
def contactpagina(heeft_boekingen):
    return render_template('1contactpagina.html',name=current_user, heeft_boekingen=heeft_boekingen)

@app.route('/1faciliteitenpagina')
@check_user_bookings
def faciliteitenpagina(heeft_boekingen):
    return render_template('1faciliteitenpagina.html',name=current_user, heeft_boekingen=heeft_boekingen)



@app.route('/1informatiepagina')
@check_user_bookings
def informatiepagina(heeft_boekingen):
    return render_template('1informatiepagina.html',name=current_user, heeft_boekingen=heeft_boekingen)

@app.route('/1omgevingspagina')
@check_user_bookings
def omgevingspagina(heeft_boekingen):
    return render_template('1omgevingspagina.html',name=current_user, heeft_boekingen=heeft_boekingen)

@app.route('/1over ons-pagina')
@check_user_bookings
def over_ons_pagina(heeft_boekingen):
    return render_template('1over ons-pagina.html',name=current_user, heeft_boekingen=heeft_boekingen)

@app.route('/1reserveringspagina')
@login_required
@check_user_bookings
def reserveringspagina(heeft_boekingen):
    return render_template('1reserveringspagina.html',  name=current_user, heeft_boekingen=heeft_boekingen)


@app.route('/admin_dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    bungID = Boeking.query.filter_by().all()
    
    bunginfo = Tent.query.filter_by().all()

    # Render the HTML template and pass the data
    return render_template('admin_dashboard.html',  bungID=bungID, bunginfo=bunginfo ,name=current_user )




@app.route('/admin_boeking',methods=['POST'] )
@role_required('admin')
@login_required
def admin_boeking():
 # Get form data
    boeking_id = request.form.get('boeking_id')
    startdatum = datetime.strptime(request.form.get('startdatum'), '%Y-%m-%d').date()
    einddatum = datetime.strptime(request.form.get('einddatum'), '%Y-%m-%d').date()

    # Retrieve the Boeking record from the database
    boeking = Boeking.query.get(boeking_id)

    if boeking:
        # Update the Boeking record
        boeking.startdatum = startdatum
        boeking.einddatum = einddatum

        # Commit the changes to the database
        db.session.commit()

        # Redirect the user to a relevant page
        return redirect('/admin_dashboard')
    else:
        flash(u'Boeking ID is niet bekend', 'warning')
        return redirect('/admin_dashboard')


@app.route('/admin_tenten',methods=['POST'] )
@role_required('admin')
@login_required
def admin_tenten():
 # Get form data
    id = request.form.get('id')
    naam = request.form.get('naam')
    omschrijving = request.form.get('omschrijving')
    aantal_personen = request.form.get('aantal_personen')
    prijs_per_dag = request.form.get('prijs_per_dag')

    # Retrieve the Boeking record from the database
    tenten = Tent.query.get(id)

    if tenten:
        # Update the Boeking record
        tenten.naam = naam
        tenten.omschrijving = omschrijving
        tenten.aantal_personen = aantal_personen
        tenten.prijs_per_dag = prijs_per_dag


        # Commit the changes to the database
        db.session.commit()

        # Redirect the user to a relevant page
        return redirect('/admin_dashboard')
    else:
        flash(u'TentID is niet bekend', 'warning')
        return redirect('/admin_dashboard')


        




@app.route('/delete_boeking/<int:boeking_id>', methods=['GET', 'POST'])
@login_required
def delete_boeking(boeking_id):
    boeking = Boeking.query.get(boeking_id)

    if boeking:
        # Check if the logged-in user owns the booking
        if current_user.id == boeking.userID:
            # Delete the booking from the database
            db.session.delete(boeking)
            db.session.commit()

            flash(u'De boeking is succesvol verwijderd.', 'success')
        else:
            flash(u'Je hebt geen toestemming om deze boeking te verwijderen.', 'warning')
    else:
        flash(u'Boeking ID is niet bekend.', 'warning')

    return redirect(url_for('gebruiker'))



@app.route('/print_booking/<int:booking_id>')
@login_required

def print_booking(booking_id):
    booking = Boeking.query.get(booking_id)

    if booking:
        # Check if the logged-in user owns the booking
        if current_user.id == booking.userID:
            return render_template('print_booking.html', booking=booking)
        else:
            flash(u'You do not have permission to print this booking.', 'warning')
    else:
        flash(u'Booking ID is not found.', 'warning')

    return redirect(url_for('gebruiker'))



@app.route('/account/update', methods=['GET', 'POST'])
@login_required  # Make sure the route is accessible only to logged-in users
@check_user_bookings
def account_update(heeft_boekingen):
    form = AccountUpdateForm()

    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.username = form.username.data
        current_user.woonplaats = form.woonplaats.data
        current_user.huisnummer = form.huisnummer.data
        current_user.toevoeging = form.toevoeging.data
        current_user.straat = form.straat.data
        current_user.postcode = form.postcode.data
        db.session.commit()
        flash('Je accountinformatie is bijgewerkt!', 'success')
        return redirect(url_for('account_update'))
    
    
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.capitalize()}: {error}', 'error')

    # Pre-fill the form fields with the user's existing data
    form.email.data = current_user.email
    form.username.data = current_user.username
    form.woonplaats.data = current_user.woonplaats
    form.huisnummer.data = current_user.huisnummer
    form.toevoeging.data = current_user.toevoeging
    form.straat.data = current_user.straat
    form.postcode.data = current_user.postcode

    return render_template('account_bijwerken.html', form=form ,name=current_user, heeft_boekingen=heeft_boekingen)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate a secure token for the special link
            token = secrets.token_hex(16)

            # Store the token in the database for this user
            user.password_reset_token = token
            user.password_reset_expiration = datetime.utcnow() + timedelta(hours=1)  # The token is valid for 1 hour
            db.session.commit()

            # Display the special link on the screen
            special_link = url_for('reset_password', token=token, _external=True)
            flash(f"Link die naar de email is gestuurd: {special_link}", 'info')
        else:
            flash("Email onbekend.", 'warning')

    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = wwupdateform()
    if form.validate_on_submit():
        user = User.query.filter_by(password_reset_token=token).first()
        if user is None:
            flash('Oude link. Vraag een nieuwe aan.', 'danger')
            return redirect(url_for('forgot_password'))
        if user and user.password_reset_expiration and user.password_reset_expiration > datetime.utcnow():

            user.password_hash = generate_password_hash(form.password.data)  # Set the new password
            user.password_reset_token = None  # Clear the reset token
            user.password_reset_expiration = None  # Clear the reset expiration
            db.session.commit()

            flash('Wachtwoord is aangepast.', 'success')
            return redirect(url_for('index'))
        else:
            print("Invalid or expired token")



    return render_template('reset_password.html', form=form, token=token)


