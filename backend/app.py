from flask import Flask, render_template, request, session
import random, string

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend', static_url_path='/')
app.secret_key = 'temporary' #TODO: Change to be secure

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if 'username' in session:
            return render_template('choose_avatar.html')
        return render_template('index.html')

    else:
        clicked = request.form.get('clicked')

        if clicked == 'login':
            username = request.form.get('username')
            # TODO: validate credentials against database
            session['username'] = username
            return render_template('choose_avatar.html')

        elif clicked == 'signup':
            username = request.form.get('username')
            # TODO: create user in database
            session['username'] = username
            return render_template('choose_avatar.html')

        return render_template('index.html')

    
@app.route('/choose_avatar', methods=['GET', 'POST'])
def choose_avatar():
    if request.method == 'GET':
        if len(request.args) > 0: # Joining private room / Invalid room code
            room_code = next(iter(request.args)) # Get first parameter
            if room_exists(room_code): 
                session['code'] = room_code
        return render_template('choose_avatar.html')
    
    else: # Player clicked 'Choose Avatar' or invalid POST request
        clicked = request.form.get('clicked')

        if clicked == 'play':
            room_code = session.get('code')
            car_color = request.form.get('car_color')
            car_filter = request.form.get('car_filter')
            if not room_code: # Join a public room
                room_code = find_room()
                session['code'] = room_code
            return render_template('race.html', code=session['code'], car_color=car_color, car_filter=car_filter)

        elif clicked == 'private':
            session['code'] = generate_private_room()
            car_color = request.form.get('car_color')
            car_filter = request.form.get('car_filter')
            return render_template('race.html', code=session['code'], car_color=car_color, car_filter=car_filter)
                
        # Else if invalid POST request, return index page
        session.pop('code', None)
        return render_template('choose_avatar.html')

def room_exists(code):
    #TODO: Check if room code exists in database AND is open. Retuns True if it exists and is open.
    return True

def find_room():
    #TODO: Find a public AND open room code in database. If none available, generate new code and add to db as public room.
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def generate_private_room():
    #TODO: Generate new code and add to database as private room.
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

if __name__ == '__main__':
    app.run(host='localhost', port=5500, debug=True)