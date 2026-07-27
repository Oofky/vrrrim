import re
import random
import string


class TestProgressCalculation:
    def test_progress_zero_when_unchanged(self):
        max_dist = 10
        dist = 10
        progress = max(0, (max_dist - dist) * 100 // max_dist)
        assert progress == 0

    def test_progress_hundred_when_complete(self):
        max_dist = 10
        dist = 0
        progress = max(0, (max_dist - dist) * 100 // max_dist)
        assert progress == 100

    def test_progress_clamped_below_zero(self):
        max_dist = 10
        dist = 15
        progress = max(0, (max_dist - dist) * 100 // max_dist)
        assert progress == 0

    def test_car_position_matches_progress(self):
        progress = 75
        position = f'{progress}%'
        assert position == '75%'


class TestRoomCodeGeneration:
    def test_code_is_8_chars(self):
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        assert len(code) == 8

    def test_code_is_alphanumeric(self):
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        assert all(c.isalnum() for c in code)

    def test_codes_are_unique(self):
        codes = set(
            ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            for _ in range(100)
        )
        assert len(codes) > 90


class TestUsernameValidation:
    pattern = re.compile(r'^\w{4,20}$')

    def test_valid_username(self):
        assert self.pattern.match('validuser123')

    def test_too_short(self):
        assert not self.pattern.match('ab')

    def test_too_long(self):
        assert not self.pattern.match('a' * 21)

    def test_special_chars_rejected(self):
        assert not self.pattern.match('bad username!')

    def test_underscore_allowed(self):
        assert self.pattern.match('valid_user')