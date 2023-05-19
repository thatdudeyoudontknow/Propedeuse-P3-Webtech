import os
from flask import Flask, render_template, redirect, request, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user 
from datetime import datetime
from werkzeug.urls import url_parse


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

from bungalowpark.models import BungalowType ,Bungalow, User, Boeking 
from bungalowpark.forms import LoginForm, Registratieformulier, BoekingForm

@app.route('/')
def index():
    bungalows = Bungalow.query.all()
    return render_template('home.html',  name=current_user, bungalows=bungalows)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'Je bent nu uitgelogd!', 'success')
    return redirect(url_for('index'))

@app.route('/boekingen')
@login_required
def boekingen():
    today = datetime.now()
    weeknummer = datetime.date(today).isocalendar()[1]
    nieuweBoekingen = Boeking.query.filter(Boeking.userID == current_user.id, Boeking.weeknummer > weeknummer)
    oudeBoekingen = Boeking.query.filter(Boeking.userID == current_user.id, Boeking.weeknummer <= weeknummer)
    return render_template('boekingen.html', nieuweBoekingen=nieuweBoekingen, oudeBoekingen=oudeBoekingen)

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
    return render_template('login.html', form=form) 


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = Registratieformulier()
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
                        straat=form.straat.data,
                        postcode=form.postcode.data)

            db.session.add(user)
            db.session.commit()

            flash(u'Dank voor de registratie. Er kan nu ingelogd worden! ', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/1reserveringspagina', methods=['GET', 'POST'])
@login_required
def reserveer():
    form = BoekingForm()
    guser = LoginForm()
    if form.validate_on_submit():
        Boeking_bungalowID = Boeking.query.filter_by(bungalowID=form.bungalowID.data).first()
        Boeking_startdatum = Boeking.query.filter_by(startdatum=form.startdatum.data).first()
        Boeking_einddatum = Boeking.query.filter_by(einddatum=form.startdatum.data).first()
        user = User.query.filter_by(email=guser.email.data).first()
        
        if user is not None and user.check_password(form.password.data):

            if user:
                boeking = Boeking(bungalowID=form.bungalowID.data,
                    email=guser.email.data,
                    startdatum=form.startdatum.data,
                    einddatum=form.einddatum.data)
            else:
                flash(u'email is niet correct', 'warning')

            db.session.add(boeking)
            db.session.commit()

            flash(u'u heeft met succes uw bungalow geboekt')
            return redirect(url_for('accomidatiepagina'))

    return render_template('1reserveringspagina.html', name=current_user, form=form, guser=guser)


@app.route('/gebruiker')
def gebruiker():
    log_email = current_user.email
    # Retrieve data from the database

    bungID = Boeking.query.filter_by(email=log_email).all()

    # Render the HTML template and pass the data
    return render_template('gebruiker.html',  bungID=bungID ,name=current_user )

@app.route('/update_boeking', methods=['POST'])
def update_boeking():
    # Get form data
    boeking_id = request.form.get('boeking_id')
    startdatum = request.form.get('startdatum')
    einddatum = request.form.get('einddatum')

    # Retrieve the Boeking record from the database
    boeking = Boeking.query.get(boeking_id)


    if boeking:
        # Check if the logged-in user owns the Boeking record
        if current_user.email == boeking.email:
            # Update the Boeking record
            boeking.startdatum = startdatum
            boeking.einddatum = einddatum

            # Commit the changes to the database
            db.session.commit()

            # Redirect the user to a relevant page
            return redirect('/gebruiker')
        else:
            abort(403)  # Return a Forbidden error
    else:
        return flash(u'Boeking ID is niet bekend', 'warning')



@app.route('/1accomidatiepagina')
def accomidatiepagina():
    return render_template('1accomidatiepagina.html',name=current_user)

@app.route('/1activiteitenpagina')
def activiteitenpagina():
    return render_template('1activiteitenpagina.html',name=current_user)

@app.route('/1blogpagina')
def blogpagina():
    return render_template('1blogpagina.html',name=current_user)

@app.route('/1contactpagina')
def contactpagina():
    return render_template('1contactpagina.html',name=current_user)

@app.route('/1faciliteitenpagina')
def faciliteitenpagina():
    return render_template('1faciliteitenpagina.html',name=current_user)

@app.route('/1homepagina')
def homepagina():
    return render_template('1homepagina.html',name=current_user)

@app.route('/1informatiepagina')
def informatiepagina():
    return render_template('1informatiepagina.html',name=current_user)

@app.route('/1omgevingspagina')
def omgevingspagina():
    return render_template('1omgevingspagina.html',name=current_user)

@app.route('/1over ons-pagina')
def over_ons_pagina():
    return render_template('1over ons-pagina.html',name=current_user)

@app.route('/1reserveringspagina')
@login_required
def reserveringspagina():
    return render_template('1reserveringspagina.html',  name=current_user)

@app.route('/test')
def test():
    selected_option = '1'
    options = ["Action", "Another action", "Something else here"]
    return render_template('test.html', options=options, selected_option=selected_option)
