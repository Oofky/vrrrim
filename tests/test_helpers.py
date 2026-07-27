from app import room_exists, find_room, generate_private_room

def test_find_room_returns_8_chars():
    code = find_room()
    assert len(code) == 8

def test_generate_private_room_returns_8_chars():
    code = generate_private_room()
    assert len(code) == 8

def test_room_exists_returns_bool():
    result = room_exists('ABCD1234')
    assert isinstance(result, bool)