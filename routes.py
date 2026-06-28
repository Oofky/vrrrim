from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from flask_socketio import emit, join_room, leave_room
from sqlalchemy import func, select
import random, string
from models import PlayerInRoom, Room, User

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

                    return render_template('race.html', code=session['code'])
                
                elif clicked == 'private':
                    session['code'] = generate_private_room()
                    return render_template('race.html', code=session['code'])
                
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
            room = Room(code=open_code, public=True, accessible=True)
            db.session.add(room)
            db.session.commit()
        else:
            open_code = open_room.code

        return open_code

    def generate_private_room():
        new_code = generate_unique_code()

        # Add new_code to db as private room
        room = Room(code=new_code, public=False, accessible=True)
        db.session.add(room)
        db.session.commit()

        return new_code
    
    def generate_unique_code():
        new_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) # Generate new code

        # Make sure new code does not already exist in db
        while db.session.get(Room, new_code):
            new_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        return new_code
    
    def add_this_player(code):
        plr = PlayerInRoom(
            room_code=code,
            username=current_user.username,
            car_color=session['car_color'],
            car_filter=session['car_filter']
        )
        db.session.add(plr)
        db.session.commit()
        session['plr_id'] = plr.id

    def delete_this_player():
        plr = db.session.get(PlayerInRoom, session['plr_id'])
        db.session.delete(plr)
        db.session.commit()
        session.pop('plr_id', None)

    def clear_session_data():
        session.pop('code', None)
        session.pop('car_color', None)
        session.pop('car_filter', None)

    @socketio.on('connect')
    def connect(auth=None):
        room_code = session['code']
        join_room(room_code)
        add_this_player(room_code)

        room = db.session.get(Room, room_code)
        leader_id = db.session.scalars(select(func.min(PlayerInRoom.id))).first()

        # Room size limit
        if len(room.plrs) >= 5:
            print(len(room.plrs))
            room.accessible = False
            db.session.commit()

        emit('players_bars', {
            'bars_data': get_bars_data(room), 
            'my_id': session['plr_id'],
            'leader_id': leader_id
            }, to=room_code)
        
    @socketio.on('disconnect')
    def disconnect(reason=None):
        room_code = session['code']
        leave_room(room_code)
        delete_this_player()

        room = db.session.get(Room, room_code)
        leader_id = None

        # Close room
        if len(room.plrs) == 0:
            db.session.delete(room)
            db.session.commit()
        else:
            if not room.accessible:
                # Reopen the room
                room.accessible = True
                db.session.commit()
            leader_id = db.session.scalars(select(func.min(PlayerInRoom.id))).first()

        emit('players_bars', {
            'bars_data': get_bars_data(room), 
            'my_id': 'nothing',
            'leader_id': leader_id
            }, to=room_code)

    def get_bars_data(room):
        plrs = room.plrs
        list_of_dicts = []
        for plr in plrs:
            list_of_dicts.append({
                'id': plr.id,
                'username': plr.username,
                'car_color': plr.car_color,
                'car_filter': plr.car_filter
            })
        return list_of_dicts
