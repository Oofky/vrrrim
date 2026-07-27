from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from flask_socketio import emit, join_room, leave_room
from pathlib import Path
from sqlalchemy import func, select
import random, re, string, time
from models import PlayerInRoom, Room, User

def register_routes(app, db, bcrypt, socketio):

    NUM_OF_TEXTS = 10
    text_path_f = lambda x: Path(__file__).parent / 'backend' / 'texts' / ('text'+str(x))

    # Flask routes

    valid_username = re.compile(r'^\w{4,20}$') # 4-20 characters of alphanumeric and _, same as what the html input allows

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
                    user = db.session.scalar(select(User).where(User.username == username))
                    if not user: return login_failed() # No such username
                    if bcrypt.check_password_hash(user.password, password):
                        login_user(user)
                    else: return login_failed() # Wrong password

                elif clicked == 'signup':
                    if username_exists(username): return signup_failed_taken()
                    if not valid_username.match(username): return signup_failed_char()
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
                    
                    texts = get_texts(session['code'])
                    return render_template('race.html', 
                                           code=session['code'], 
                                           input_text=texts[0], 
                                           output_text=texts[1])
                
                elif clicked == 'private':
                    session['code'] = generate_private_room()
                    texts = get_texts(session['code'])
                    return render_template('race.html', 
                                           code=session['code'], 
                                           input_text=texts[0], 
                                           output_text=texts[1])
                
                # Else if invalid POST request, return index page
                clear_session_data()
                return redirect(url_for('index'))
            
    @app.route('/logout') # logout button in choose_avatar.html 
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/statistics')
    def statistics():
        if not current_user.is_authenticated: # not needed because you can't access this page without logging in, but just in case
            return redirect(url_for('index'))

        # TODO: to query the database for the user's statistics and pass them to the template
        user_stats = {
            'total_races': 12,
            'wins': 5,
            'win_rate': 41.7,
            'best_speed': '78 WPM'
        }

        # TODO: query your DB for top players - MUST SORT BY WINS DESCENDING, THEN BEST SPEED DESCENDING, THEN TOTAL RACES DESCENDING, THEN USERNAME ASCENDING
        global_leaderboard = [
            {'username': 'maxverstappen', 'wins': 20, 'best_speed': '95 WPM', 'total_races': 30},
            {'username': current_user.username, 'wins': 5, 'best_speed': '78 WPM', 'total_races': 12},
            {'username': 'kimiantonelli', 'wins': 15, 'best_speed': '67 WPM', 'total_races': 25},
            {'username': 'bearmanOLIVER', 'wins': 10, 'best_speed': '67 WPM', 'total_races': 81},
        ]
        
        return render_template('statistics.html', user_stats=user_stats, global_leaderboard=global_leaderboard)

    # Helper functions for Flask routes
    
    def login_failed():
        flash('Your username or password is incorrect. Please try again.')
        return redirect(url_for('index'))
    
    def signup_failed_taken():
        flash('Your username is taken. Please try another username.')
        return redirect(url_for('index'))
    
    def signup_failed_char():
        flash('Your username has invalid characters. Please try another username with only alphabet, numbers, and underscore.')
        return redirect(url_for('index'))
    
    def username_exists(name):
        return bool(db.session.scalar(select(User).where(User.username == name)))

    def room_joinable(code): # Returns True if room code exists in db AND is open
        return bool(db.session.scalar(select(Room).where(Room.code == code, Room.accessible == True)))
    
    def clear_session_data():
        session.pop('code', None)
        session.pop('car_color', None)
        session.pop('car_filter', None)

    def find_room():
        open_code = ''

        # Find a public AND open room code in db
        open_room = db.session.scalar(select(Room).where(Room.public == True, Room.accessible == True))

        if not open_room: # If none available
            open_code = generate_unique_code()

            # Add open_code to db as public room
            room = Room(code=open_code, public=True, accessible=True, text_num=random.randint(0, NUM_OF_TEXTS-1))
            db.session.add(room)
            db.session.commit()
        else:
            open_code = open_room.code

        return open_code
    
    def generate_unique_code():
        new_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) # Generate new code

        # Make sure new code does not already exist in db
        while db.session.get(Room, new_code):
            new_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        return new_code

    def generate_private_room():
        new_code = generate_unique_code()

        # Add new_code to db as private room
        room = Room(code=new_code, public=False, accessible=True, text_num=random.randint(0, NUM_OF_TEXTS-1))
        db.session.add(room)
        db.session.commit()

        return new_code
    
    def get_texts(room_code):
        text_num = db.session.get(Room, room_code).text_num
        input_text = 'console.log("Jello! ");'
        output_text = '''function greet(name) {
    console.log("Hello, " + name + "!");
}'''
        with open(text_path_f(text_num) / 'input.txt', 'r') as f:
            input_text = f.read()
        with open(text_path_f(text_num) / 'output.txt', 'r') as f:
            output_text = f.read()
        return (input_text, output_text)

    # SocketIO connection events

    @socketio.on('connect') # Happens when race.html is accessed
    def connect(auth=None):
        room_code = session.get('code')
        if not room_code:
            print('connect: no room code')
            return
        join_room(room_code)
        add_this_player(room_code)

        room = db.session.get(Room, room_code)
        leader_id = db.session.scalar(select(func.min(PlayerInRoom.id)).where(PlayerInRoom.room_code == room_code))

        # Room size limit
        if len(room.plrs) >= 5:
            room.accessible = False
            db.session.commit()

        emit('players_bars', {
            'bars_data': get_bars_data(room), 
            'leader_id': leader_id,
            'game_in_progress': False
            }, to=room_code)
        
    @socketio.on('disconnect')
    def disconnect(reason=None):
        room_code = session.get('code')
        if not room_code:
            print('disconnect: no room code')
            return
        leave_room(room_code)

        room_progress = game_progress.get(room_code)
        if room_progress and request.sid in room_progress['rankings']:
            # Player is ranked. Meaning player left after completing the race. Should not delete the PlayerInRoom
            pass
        else:
            delete_this_player()

        room = db.session.get(Room, room_code)
        leader_id = None

        if not room:
            return

        # Close room
        if len(room.plrs) == 0:
            db.session.delete(room)
            db.session.commit()
            if room_progress:
                game_progress.pop(room_code) # In case last player leaves while game loop ongoing
        else:
            if not room.accessible and not room_progress: # If game is ongoing, should not reopen the room
                # Reopen the room
                room.accessible = True
                db.session.commit()
            leader_id = db.session.scalar(select(func.min(PlayerInRoom.id)).where(PlayerInRoom.room_code == room_code))

            # Alter bars_data based on whether game is in progress or not
            bars_data = get_bars_data(room)
            if room_progress is not None: # Game in progress, need to edit bars data
                for dd in bars_data: # dd is dictionary, bcuz bars_data is list of dictionaries
                    plr_progress = room_progress.get(dd['id'])
                    if plr_progress is not None:
                        dd['progress'] = plr_progress

                    if dd['socket_id'] in room_progress['rankings']:
                        i = room_progress['rankings'].index(dd['socket_id'])
                        dd['placement'] = index_to_placement[i]

            # Emit based on whether game is in progress or not
            emit('players_bars', {
                'bars_data': bars_data, 
                'leader_id': leader_id,
                'game_in_progress': room_progress is not None
                }, to=room_code)
        
    # Helper functions for SocketIO connection events
        
    def add_this_player(code):
        plr = PlayerInRoom(
            room_code=code,
            socket_id=request.sid, # For deleting the correct player
            username=current_user.username,
            car_color=session['car_color'],
            car_filter=session['car_filter']
        )
        db.session.add(plr)
        db.session.commit()

    def delete_this_player():
        plr = db.session.scalar(select(PlayerInRoom).where(PlayerInRoom.socket_id == request.sid))
        if plr:
            db.session.delete(plr)
            db.session.commit()
        
    # SocketIO game loop events

    game_progress = {}
    index_to_placement = ['1ST PLACE', '2ND PLACE', '3RD PLACE', '4TH PLACE', '5TH PLACE', '6TH PLACE']
    
    @socketio.on('start_game')
    def start_all_games():
        if game_progress.get(session['code']) is None: # Only start game if it is not alr in progress already (defensive check)
            # Lock room first
            room = db.session.get(Room, session['code'])
            room.accessible = False
            db.session.commit()

            game_progress[session['code']] = {}
            game_progress[session['code']]['rankings'] = []
            game_progress[session['code']]['start_time'] = time.perf_counter()
            emit('start_game', session['code'], to=session['code'])
            socketio.start_background_task(game_loop, session['code'], app)

    @socketio.on('update_bar')
    def update_progress(data):
        plr_id = data[0]
        progress = data[1]
        room_code = data[2]

        room_progress = game_progress.get(room_code)

        if room_progress is not None: # In case all players leave the room, then this will be None
            room_progress[plr_id] = progress
            if progress >= 100 and request.sid not in room_progress['rankings']: 
                room_progress['rankings'].append(request.sid)
                i = room_progress['rankings'].index(request.sid)
                socketio.emit('winner', 
                              {
                                'placement': i,
                                'speed': 999, # TODO: CHANGE LATER
                                'time': str(round(time.perf_counter() - room_progress['start_time'], 2)) + 's'
                              }, to=request.sid) # Emit to the winner only
                socketio.emit('placement_label', 
                              {
                                'id': db.session.scalar(select(PlayerInRoom).where(PlayerInRoom.socket_id == request.sid)).id,
                                'placement': index_to_placement[i]
                              }, to=room_code)      

    # Helper functions for SocketIO game loop events

    def game_loop(room_code, app_para): 
        # Need to get app context bcuz if not, I get error saying "Working outside application context"
        with app_para.app_context():
            while room_code in game_progress:
                socketio.emit('update_bar', game_progress.get(room_code), to=room_code)

                # Game ends when num of players in the rankings list is same as num of players in room
                # Note that when players who are ranked disconnect from the room, they are NOT removed from the db
                # But if players disconnect without being ranked, they are removed from the db
                # That's why this works
                if len(game_progress.get(room_code).get('rankings')) == len(db.session.get(Room, room_code).plrs):
                    # Close the room, break
                    room = db.session.get(Room, room_code)
                    for plr in room.plrs:
                        db.session.delete(plr)
                    db.session.delete(room)
                    db.session.commit()
                    game_progress.pop(room_code)
                    break

                socketio.sleep(0.2)

    def get_bars_data(room):
        plrs = room.plrs
        list_of_dicts = []
        for plr in plrs:
            list_of_dicts.append({
                'id': plr.id,
                'username': plr.username,
                'socket_id': plr.socket_id,
                'car_color': plr.car_color,
                'car_filter': plr.car_filter,
                'progress': 0,
                'placement': '   ' # 3 spaces so that placement can slice properly
            })
        return list_of_dicts
