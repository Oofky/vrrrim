from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from flask_socketio import join_room, leave_room, send
from sqlalchemy import select, update
import random, string
from models import Room, User

def register_routes(app, db, bcrypt, socketio):
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

                    if not user: return login_failed() # No such username

                    if bcrypt.check_password_hash(user.password, password):
                        login_user(user)
                        return redirect(url_for('index'))
                    else: return login_failed() # Wrong password

                elif clicked == 'signup':
                    if username_exists(username): return signup_failed()
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
                    if room_joinable(room_code):
                        session['code'] = room_code
                        return render_template('choose_avatar.html')
                    
                # Else if no arg or invalid room code, access index page witout setting room code
                clear_session_data()
                return render_template('choose_avatar.html')
            
            elif request.method == 'POST': # Player clicked 'Play' or 'Create private room' or invalid POST request
                clicked = request.form.get('clicked')
                car_color = request.form.get('car_color')
                car_filter = request.form.get('car_filter')

                session['car_color'] = car_color
                session['car_filter'] = car_filter

                if clicked == 'play':
                    room_code = session.get('code')
                    if not room_code: # Join a public room
                        room_code = find_room()
                        session['code'] = room_code

                    return render_template('race.html', 
                                           code=session['code'], 
                                           car_color=session['car_color'], 
                                           car_filter=session['car_filter'])
                
                elif clicked == 'private':
                    session['code'] = generate_private_room()
                    return render_template('race.html', 
                                           code=session['code'], 
                                           car_color=session['car_color'], 
                                           car_filter=session['car_filter'])
                
                # Else if invalid POST request, return index page
                clear_session_data()
                return redirect(url_for('index'))
            
    @app.route('/logout') #TODO: Add a logout button somewhere
    def logout():
        logout_user()
        return redirect(url_for('index'))
        
    def login_failed():
        flash('Your username or password is incorrect. Please try again.')
        return redirect(url_for('index'))
    
    def signup_failed():
        flash('Your username is taken. Please try another username.')
        return redirect(url_for('index'))
    
    def username_exists(name):
        return bool(db.session.scalars(select(User).where(User.username == name)).first())

    def room_joinable(code): # Returns True if room code exists in db AND is open
        return bool(db.session.scalars(select(Room).where(Room.code == code, Room.accessible == True)).first())

    def find_room():
        open_code = ''

        # Find a public AND open room code in db
        open_room = db.session.scalars(select(Room).where(Room.public == True, Room.accessible == True)).first()

        if not open_room: # If none available
            open_code = generate_unique_code()

            # Add open_code to db as public room
            room = Room(code=open_code, public=True, accessible=True, num_of_plrs=0)
            db.session.add(room)
            db.session.commit()
        else:
            open_code = open_room.code

        return open_code

    def generate_private_room():
        #TODO: remember to remove rooms from db, also update accessibility
        new_code = generate_unique_code()

        # Add new_code to db as private room
        room = Room(code=new_code, public=False, accessible=True, num_of_plrs=0)
        db.session.add(room)
        db.session.commit()

        return new_code
    
    def generate_unique_code():
        new_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) # Generate new code

        # Make sure new code does not already exist in db
        while db.session.scalars(select(Room).where(Room.code == new_code)).first():
            new_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        return new_code
    
    def incr_num_of_plrs(code):
        db.session.execute(update(Room).where(Room.code == code).values(num_of_plrs=Room.num_of_plrs + 1))
        db.session.commit()

    def clear_session_data():
        session.pop('code', None)
        session.pop('car_color', None)
        session.pop('car_filter', None)

    @socketio.on('connect')
    def connect(auth):
        room_code = session['code']
        join_room(room_code)
        incr_num_of_plrs(room_code)

        # Room size limit
        if db.session.scalars(select(Room).where(Room.code == room_code)).first().num_of_plrs >= 5:
            db.session.execute(update(Room).where(Room.code == room_code).values(accessible=False))
            db.session.commit()

        send({
            'event': 'join',
            'username': current_user.username,
            'car_color': session['car_color'],
            'car_filter': session['car_filter']
            }, to=room_code)

