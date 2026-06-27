from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import select
import random, string
from models import User

def register_routes(app, db, bcrypt):
    @app.route('/', methods=['GET', 'POST'])
    def index():
        if not current_user.is_authenticated:
            if request.method == 'GET': # Not logged in, show sign up / login page
                return render_template('index.html')
            elif request.method == 'POST': # Trying to sign up / log in
                clicked = request.form.get('clicked')
                username = request.form.get('username')
                password = request.form.get('password')

                if clicked == 'login':
                    user = db.session.scalars(
                        select(User).where(User.username == username)).first()

                    if not user: return signin_failed() # No such username

                    if bcrypt.check_password_hash(user.password, password):
                        login_user(user)
                        return redirect(url_for('index'))
                    else: return signin_failed() # Wrong password

                elif clicked == 'signup':
                    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                    user = User(username=username, password=hashed_password) #TODO: Add email field, also possibly a confirm password field
                    db.session.add(user)
                    db.session.commit()
                    login_user(user)
                    return redirect(url_for('index'))
                
        else: # User is authenticated (has signed in)
            if request.method == 'GET': 
                if len(request.args) > 0: # Joining private room / Invalid room code
                    room_code = next(iter(request.args)) # Get first parameter
                    if room_exists(room_code):
                        session['code'] = room_code
                        return render_template('choose_avatar.html')
                    
                # Else if no arg or invalid room code, access index page witout setting room code
                session.pop('code', None)
                return render_template('choose_avatar.html')
            
            elif request.method == 'POST': # Player clicked 'Play' or 'Create private room' or invalid POST request
                clicked = request.form.get('clicked')
                car_color = request.form.get('car_color')
                car_filter = request.form.get('car_filter')

                if clicked == 'play':
                    room_code = session.get('code')
                    if not room_code: # Join a public room
                        room_code = find_room()
                        session['code'] = room_code
                    return render_template('race.html', code=session['code'], car_color=car_color, car_filter=car_filter)
                
                elif clicked == 'private':
                    session['code'] = generate_private_room()
                    return render_template('race.html', code=session['code'], car_color=car_color, car_filter=car_filter)
                
                # Else if invalid POST request, return index page
                session.pop('code', None)
                return redirect(url_for('index'))
            
    @app.route('/logout') #TODO: Add a logout button somewhere
    def logout():
        logout_user()
        return redirect(url_for('index'))
        
    def signin_failed():
        flash('Sign in failed. Please try again.')
        return redirect(url_for('index'))

    def room_exists(code):
        #TODO: Check if room code exists in database AND is open. Retuns True if it exists and is open.
        return True

    def find_room():
        #TODO: Find a public AND open room code in database. If none available, generate new code and add to db as public room.
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    def generate_private_room():
        #TODO: Generate new code and add to database as private room.
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
