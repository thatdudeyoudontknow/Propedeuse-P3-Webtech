import os
from flask import Flask, render_template, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user 
from datetime import datetime
from werkzeug.urls import url_parse
from werkzeug.security import generate_password_hash
from flask_login import current_user
from datetime import datetime, timedelta
from functools import wraps
from datetime import datetime, timedelta

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
from bungalowpark.forms import LoginForm, RegistrationForm, BoekingForm
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

@app.route('/boekingen')
@login_required
@check_user_bookings
def boekingen(heeft_boekingen):
    print("kankk")
    today = datetime.now()
    weeknummer = datetime.date(today).isocalendar()[1]
    nieuweBoekingen = Boeking.query.filter(Boeking.userID == current_user.id, Boeking.weeknummer > weeknummer)
    oudeBoekingen = Boeking.query.filter(Boeking.userID == current_user.id, Boeking.weeknummer <= weeknummer)
    return render_template('boekingen.html', nieuweBoekingen=nieuweBoekingen, oudeBoekingen=oudeBoekingen, heeft_boekingen=heeft_boekingen)

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
        flash(u'u email is niet bestaand', 'warning')
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
        flash(u'ongeldige postcode')

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

        startdatum = datetime.strptime(form.startdatum.data, '%Y-%m-%d').date()
        einddatum = datetime.strptime(form.einddatum.data, '%Y-%m-%d').date()

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




    return render_template('1reserveringspagina.html', name=current_user, form=form, tents=tents)


@app.route('/gebruiker')
@login_required
@check_user_bookings
def gebruiker(heeft_boekingen):

    bungID = Boeking.query.filter_by(userID=current_user.id).all()
    

    return render_template('gebruiker.html', bungID=bungID, heeft_boekingen=heeft_boekingen)


    # if not heeft_boekingen:
    #     flash(u'U heeft nog geen boeking gedaan.', 'warning')
    #     return redirect(url_for('index'))

    # Render the HTML template and pass the data
    # return render_template('gebruiker.html',  bungID=bungID ,name=current_user )



@app.route('/update_boeking', methods=['POST'])
def update_boeking():
    # Get form data
    boeking_id = request.form.get('boeking_id')
    startdatum = datetime.strptime(request.form.get('startdatum'), '%Y-%m-%d').date()
    einddatum = datetime.strptime(request.form.get('einddatum'), '%Y-%m-%d').date()

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

@app.route('/1homepagina')
@check_user_bookings
def homepagina(heeft_boekingen):
    return render_template('1homepagina.html',name=current_user, heeft_boekingen=heeft_boekingen)

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


        



@app.route('/test')
def test():
    selected_option = '1'#request.form['option']
    options = ["Action", "Another action", "Something else here"]
    return render_template('test.html', options=options, selected_option=selected_option)

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

@app.route('/ww_vergetenpost', methods=['POST'])
def ww_vergetenpost():   
    email = request.form.get('email')
    code = request.form.get('code')
    new_password = request.form.get('new_password')

    user = User.query.filter_by(email=email).first()

    if user:
        print("1")
        if code == '3269':
            user.password_hash = generate_password_hash(new_password)
            # Commit the changes to the database
            db.session.commit()
            # Redirect the user to a relevant page
            return redirect('/login')
        else:
            flash(u'Verificatie Code is onjuist.')
            return redirect ("/ww_vergeten")
    else:
        print("2")
        flash(u'email niet correct', 'warning')
        return redirect ('/ww_vergeten')

    
@app.route('/ww_vergeten')
def ww_vergeten():
        return render_template('ww_vergeten.html',)


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
@app.route('/user')
@login_required
def user():
    user = User.query.filter_by(id=current_user.id).first()
    return render_template('user.html', user=user, name=current_user)

 

@app.route('/update_user',methods=['POST'] )
@login_required
def update_user():
 # Get form data
    email = request.form.get('email')
    username = request.form.get('username')
    woonplaats = request.form.get('woonplaats')
    huisnummer = request.form.get('huisnummer')
    # toevoeging = request.form.get('toevoeging')
    straat = request.form.get('straat')
    postcode = request.form.get('postcode')

    guser = User.query.filter_by(id=current_user.id).first()

    if guser:

        guser.email = email
        guser.username = username
        guser.woonplaats = woonplaats
        guser.huisnummer = huisnummer
        # guser.toevoeging = toevoeging
        guser.straat = straat
        guser.postcode = postcode

        db.session.commit()

        flash(u'uw gegevens zijn succesvol veranderd', 'warning')
        return redirect('/user')
    else:
        flash(u'Er is iets fout gegaan', 'warning')
        return redirect('/user')
