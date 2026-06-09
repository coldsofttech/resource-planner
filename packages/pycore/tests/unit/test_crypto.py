import pytest
from cryptography.fernet import Fernet
from pycore.crypto import fernet_decrypt, fernet_encrypt, generate_key


@pytest.fixture
def key() -> str:
    return Fernet.generate_key().decode()


# ---------------------------------------------------------------------------
# fernet_encrypt
# ---------------------------------------------------------------------------


class TestFernetEncrypt:
    def test_result_starts_with_enc_prefix(self, key):
        assert fernet_encrypt("hello", key).startswith("enc:")

    def test_ciphertext_decrypts_back_to_original(self, key):
        result = fernet_encrypt("my secret", key)
        ciphertext = result[len("enc:") :]
        plaintext = Fernet(key.encode()).decrypt(ciphertext.encode()).decode()
        assert plaintext == "my secret"

    def test_same_value_produces_different_ciphertexts(self, key):
        assert fernet_encrypt("value", key) != fernet_encrypt("value", key)

    def test_encrypts_empty_string(self, key):
        assert fernet_encrypt("", key).startswith("enc:")


# ---------------------------------------------------------------------------
# fernet_decrypt
# ---------------------------------------------------------------------------


class TestFernetDecrypt:
    def test_decrypts_enc_prefixed_value(self, key):
        encrypted = fernet_encrypt("secret", key)
        assert fernet_decrypt(encrypted, key) == "secret"

    def test_passthrough_when_no_enc_prefix(self, key):
        assert fernet_decrypt("plain text", key) == "plain text"

    def test_passthrough_for_empty_string(self, key):
        assert fernet_decrypt("", key) == ""

    def test_passthrough_preserves_value_containing_colon(self, key):
        assert fernet_decrypt("not:encrypted", key) == "not:encrypted"


# ---------------------------------------------------------------------------
# generate_key
# ---------------------------------------------------------------------------


class TestGenerateKey:
    def test_returns_a_string(self):
        assert isinstance(generate_key(), str)

    def test_returned_key_is_valid_for_fernet(self):
        Fernet(generate_key().encode())  # must not raise

    def test_successive_calls_return_different_keys(self):
        assert generate_key() != generate_key()


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


class TestFernetRoundTrip:
    def test_round_trip_preserves_value(self, key):
        value = "sensitive data"
        assert fernet_decrypt(fernet_encrypt(value, key), key) == value

    def test_round_trip_with_empty_string(self, key):
        assert fernet_decrypt(fernet_encrypt("", key), key) == ""

    def test_round_trip_with_special_characters(self, key):
        value = "hello\nworld\t!@#$%^&*()"
        assert fernet_decrypt(fernet_encrypt(value, key), key) == value
