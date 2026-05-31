import hashlib

from otpcore import generate_otp, hash_otp


class TestGenerateOtp:
    def test_default_six_digits(self):
        code, code_hash = generate_otp()
        assert len(code) == 6
        assert code.isdigit()

    def test_custom_digits(self):
        code, _ = generate_otp(digits=8)
        assert len(code) == 8

    def test_hash_matches_code(self):
        code, code_hash = generate_otp()
        assert code_hash == hashlib.sha256(code.encode()).hexdigest()

    def test_codes_are_unique(self):
        codes = {generate_otp()[0] for _ in range(50)}
        assert len(codes) > 1

    def test_leading_zeros_preserved(self):
        for _ in range(100):
            code, _ = generate_otp()
            assert len(code) == 6


class TestHashOtp:
    def test_deterministic(self):
        assert hash_otp("123456") == hash_otp("123456")

    def test_different_codes_differ(self):
        assert hash_otp("123456") != hash_otp("654321")

    def test_matches_sha256(self):
        code = "000000"
        assert hash_otp(code) == hashlib.sha256(code.encode()).hexdigest()
