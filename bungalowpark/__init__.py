import os
from flask import Flask, render_template, redirect, request, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user 
from datetime import datetime
from werkzeug.urls import url_parse
from flask_login import current_user
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
from bungalowpark.forms import LoginForm, Registratieformulier, BoekingForm

@app.route('/')
def index():

    return render_template('home.html',  name=current_user)


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
    tents = Tent.query.all()
    if form.validate_on_submit():
        # Get the selected tent ID from the form
        tent_id = request.form.get('tent')

        # Retrieve the tent object from the database using the selected ID
        tent = Tent.query.get(tent_id)

        from datetime import datetime



        startdatum = datetime.strptime(form.startdatum.data, '%d/%m/%Y').date()   
        einddatum = datetime.strptime(form.einddatum.data, '%d/%m/%Y').date()
        # Create a new Boeking instance with the tent ID and other form data
        boeking = Boeking(bungalowID="1", tent_omschrijving=tent.omschrijving,
                          startdatum=startdatum, einddatum=einddatum, userID=current_user.id)

        # Save the new Boeking instance to the database
        db.session.add(boeking)
        db.session.commit()

        flash(u'U heeft met succes uw bungalow geboekt', 'success')
        return redirect(url_for('gebruiker'))

    return render_template('1reserveringspagina.html', name=current_user, form=form, tents=tents)




@app.route('/gebruiker')
def gebruiker():

    bungID = Boeking.query.filter_by(userID=current_user.id).all()

    # Render the HTML template and pass the data
    return render_template('gebruiker.html',  bungID=bungID ,name=current_user )



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
            # Check if the startdatum is at least 7 days in the future
            today = datetime.now().date()
            if startdatum >= today + timedelta(days=7):
                # Update the Boeking record
                boeking.startdatum = startdatum
                boeking.einddatum = einddatum

                # Commit the changes to the database
                db.session.commit()

                # Redirect the user to a relevant page
                return redirect('/gebruiker')
            else:
                flash(u'Je kunt de boeking niet meer wijzigen, omdat het minder dan 7 dagen voor de startdatum is.', 'warning')
                return redirect ('/gebruiker')
        else:
            flash ("er ging wat fout, probeer opnieuw")
            return redirect ('/gebruiker')
    else:
        flash(u'Boeking ID is niet bekend', 'warning')
        return redirect ('/gebruiker')



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
