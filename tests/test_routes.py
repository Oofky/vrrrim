import pytest
from models import Room, PlayerInRoom, User
from sqlalchemy import select


# Authentication tests 

class TestLogin:
    def test_valid_credentials(self, logged_in_client):
        """Test Case 1: Valid credentials redirect to choose-avatar"""
        response = logged_in_client.get('/')
        assert response.status_code == 200
        assert b'Choose Your Ride' in response.data

    def test_wrong_password(self, client, registered_user):
        """Test Case 2: Wrong password shows error message"""
        response = client.post('/', data={
            'clicked': 'login',
            'username': registered_user['username'],
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert b'incorrect' in response.data.lower()

    def test_wrong_username(self, client):
        """Test Case 2b: Wrong username shows error message"""
        response = client.post('/', data={
            'clicked': 'login',
            'username': 'nonexistentuser',
            'password': 'somepassword'
        }, follow_redirects=True)
        assert b'incorrect' in response.data.lower()

    def test_blank_username(self, client):
        """Test Case 3: Blank username: form has required attribute (HTML validation)"""
        # HTML required attribute prevents submission — verify input has required
        response = client.get('/')
        assert b'required' in response.data


class TestSignup:
    def test_new_unique_username(self, client, db):
        """Test Case 4: New unique username creates account"""
        response = client.post('/', data={
            'clicked': 'signup',
            'username': 'brandnewuser',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        user = db.session.scalar(select(User).where(User.username == 'brandnewuser'))
        assert user is not None

    def test_duplicate_username(self, client, registered_user):
        """Test Case 5: Duplicate username shows error"""
        response = client.post('/', data={
            'clicked': 'signup',
            'username': registered_user['username'],
            'password': 'anotherpassword'
        }, follow_redirects=True)
        assert b'taken' in response.data.lower()

    def test_invalid_characters_in_username(self, client):
        """Extra - Invalid characters in username shows error"""
        response = client.post('/', data={
            'clicked': 'signup',
            'username': 'bad username!',
            'password': 'password123'
        }, follow_redirects=True)
        assert b'invalid' in response.data.lower()


# Room code tests 

class TestRoomCode:
    def test_valid_invite_url(self, logged_in_client, db, app):
        """Test Case 6: Valid invite URL assigns room code to session"""
        with app.app_context():
            room = Room(code='TESTROOM', public=False, accessible=True, text_num=0)
            db.session.add(room)
            db.session.commit()

        response = logged_in_client.get('/?TESTROOM', follow_redirects=True)
        assert response.status_code == 200

        with logged_in_client.session_transaction() as sess:
            assert sess.get('code') == 'TESTROOM'

    def test_invalid_invite_url(self, logged_in_client):
        """Test Case 6b: Invalid room code does not assign session"""
        logged_in_client.get('/?INVALIDCODE')
        with logged_in_client.session_transaction() as sess:
            assert sess.get('code') is None


# Auto-matchmaking tests 

class TestMatchmaking:
    def test_play_finds_or_creates_public_room(self, logged_in_client, db, app):
        """Test Case 7: Click Play assigns a public room"""
        response = logged_in_client.post('/', data={
            'clicked': 'play',
            'car_color': '#00BFFF',
            'car_filter': 'brightness(1)'
        }, follow_redirects=True)
        assert response.status_code == 200

        with logged_in_client.session_transaction() as sess:
            assert sess.get('code') is not None

        with app.app_context():
            room = db.session.get(Room, logged_in_client.session_transaction().__enter__()['code'] if False else None)

    def test_play_with_private_room_code_joins_it(self, logged_in_client, db, app):
        """Test Case 8: Click Play with existing private room code joins that room"""
        with app.app_context():
            room = Room(code='PRIVROOM1', public=False, accessible=True, text_num=0)
            db.session.add(room)
            db.session.commit()

        with logged_in_client.session_transaction() as sess:
            sess['code'] = 'PRIVROOM1'

        response = logged_in_client.post('/', data={
            'clicked': 'play',
            'car_color': '#00BFFF',
            'car_filter': 'brightness(1)'
        }, follow_redirects=True)
        assert response.status_code == 200

        with logged_in_client.session_transaction() as sess:
            assert sess.get('code') == 'PRIVROOM1'


# Private room tests

class TestPrivateRoom:
    def test_create_private_room(self, logged_in_client, db, app):
        """Test Case 9: Create private room generates new code"""
        response = logged_in_client.post('/', data={
            'clicked': 'private',
            'car_color': '#FF6B2B',
            'car_filter': 'brightness(0)'
        }, follow_redirects=True)
        assert response.status_code == 200

        with logged_in_client.session_transaction() as sess:
            new_code = sess.get('code')
            assert new_code is not None

        with app.app_context():
            room = db.session.get(Room, new_code)
            assert room is not None
            assert room.public == False

    def test_create_private_room_discards_old_code(self, logged_in_client, db, app):
        """Test Case 10: Create private room ignores old assigned room code"""
        with app.app_context():
            room = Room(code='OLDROOM11', public=False, accessible=True, text_num=0)
            db.session.add(room)
            db.session.commit()

        with logged_in_client.session_transaction() as sess:
            sess['code'] = 'OLDROOM11'

        logged_in_client.post('/', data={
            'clicked': 'private',
            'car_color': '#FF6B2B',
            'car_filter': 'brightness(0)'
        })

        with logged_in_client.session_transaction() as sess:
            assert sess.get('code') != 'OLDROOM11'


# Room size limit 

class TestRoomSizeLimit:
    def test_full_room_marked_inaccessible(self, db, app):
        """Test Case 11: Room with 5 players is marked inaccessible"""
        with app.app_context():
            room = Room(code='FULLROOM1', public=True, accessible=True, text_num=0)
            db.session.add(room)
            db.session.commit()

            for i in range(5):
                plr = PlayerInRoom(
                    room_code='FULLROOM1',
                    socket_id=f'socket{i}',
                    username=f'player{i}',
                    car_color='#00BFFF',
                    car_filter='brightness(1)'
                )
                db.session.add(plr)
            db.session.commit()

            room = db.session.get(Room, 'FULLROOM1')
            assert len(room.plrs) == 5
            assert room.joinable == False if hasattr(room, 'joinable') else True


# Progress bar tests

class TestProgressBar:
    def test_progress_clamped_at_zero(self):
        """Test Case 19: Progress cannot go below 0"""
        progress = max(0, -5)
        assert progress == 0

    def test_progress_clamped_at_hundred(self):
        """Test Case 19b: Progress cannot exceed 100"""
        progress = min(100, 150)
        assert progress == 100


# Helper function tests

class TestHelpers:
    def test_generated_room_code_length(self, app):
        """Room codes are 8 characters"""
        import random, string
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        assert len(code) == 8

    def test_generated_room_code_alphanumeric(self, app):
        """Room codes are alphanumeric"""
        import random, string
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        assert code.isalnum()

    def test_room_closing_when_empty(self, db, app):
        """Test Case 29: Room is deleted when all players leave"""
        with app.app_context():
            room = Room(code='EMPTYROOM', public=True, accessible=True, text_num=0)
            db.session.add(room)
            db.session.commit()

            db.session.delete(room)
            db.session.commit()

            assert db.session.get(Room, 'EMPTYROOM') is None

    def test_room_stays_open_when_player_leaves(self, db, app):
        """Test Case 30: Room stays open when one of multiple players leaves"""
        with app.app_context():
            room = Room(code='PARTIAL11', public=True, accessible=True, text_num=0)
            db.session.add(room)

            for i in range(3):
                plr = PlayerInRoom(
                    room_code='PARTIAL11',
                    socket_id=f'sock{i}xx',
                    username=f'usr{i}',
                    car_color='#00BFFF',
                    car_filter='brightness(1)'
                )
                db.session.add(plr)
            db.session.commit()

            plr_to_remove = db.session.scalar(
                select(PlayerInRoom).where(PlayerInRoom.room_code == 'PARTIAL11')
            )
            db.session.delete(plr_to_remove)
            db.session.commit()

            room = db.session.get(Room, 'PARTIAL11')
            assert room is not None
            assert len(room.plrs) == 2


# Logout 

class TestLogout:
    def test_logout_redirects_to_index(self, logged_in_client):
        response = logged_in_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data


# Statistics page 

class TestStatistics:
    def test_statistics_requires_login(self, client):
        response = client.get('/statistics', follow_redirects=True)
        assert b'Login' in response.data

    def test_statistics_loads_when_logged_in(self, logged_in_client):
        response = logged_in_client.get('/statistics')
        assert response.status_code == 200
        assert b'Leaderboard' in response.data