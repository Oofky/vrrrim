from flask import Flask, render_template, request

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend', static_url_path='/')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/play')
def play():
    # When users are redirected here, they either have a URL parameter of the room code or not.
    # If no URL parameter: implies they are the room host (they created the room).
    # If URL parameter: implies they were sent the URL by the room host / not real room code.
    
    if len(request.args) == 0:
        #TODO: generate new room code, store it.
        return render_template('race.html')
    else:
        room_code = next(iter(request.args)) # First parameter
        print(room_code)
        #TODO: check if room_code exists. if yes, join the private room. else, join a public room.
        return render_template('race.html')

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)