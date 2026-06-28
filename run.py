from app import create_app

flask_app = create_app()

if __name__ == '__main__':
    flask_app.run(host='localhost', port=5500, debug=True)