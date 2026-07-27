def test_index_get(client):
    response = client.get('/')
    assert response.status_code == 200

def test_login_redirects_to_avatar(client):
    response = client.post('/', data={
        'clicked': 'login',
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 302
    assert '/choose-avatar' in response.headers['Location']

def test_race_requires_login(client):
    response = client.get('/race')
    assert response.status_code == 302
    assert '/' in response.headers['Location']

def test_choose_avatar_requires_login(client):
    response = client.get('/choose-avatar')
    assert response.status_code == 302

def test_play_creates_room(client):
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    response = client.post('/choose-avatar', data={
        'clicked': 'play',
        'car_color': '#00BFFF',
        'car_filter': 'brightness(0) saturate(100%)'
    })
    assert response.status_code == 302
    assert '/race' in response.headers['Location']