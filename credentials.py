
import pickle
import win32crypt
from pathlib import Path
from credential_prompt import prompt_for_credentials

CRED_FILE = Path(__file__).parent / "creds.pkl"


def encrypt_password(password):
    return win32crypt.CryptProtectData(password.encode(), None, None, None, None, 0)


def decrypt_password(blob):
    return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1].decode()


def load_credentials():
    if CRED_FILE.exists():
        with open(CRED_FILE, "rb") as f:
            data = pickle.load(f)
        return data["USER_EMAIL"], data["USER_ID"], decrypt_password(data["PASSWORD"])
    return None


def save_credentials(email, user_id, password):
    with open(CRED_FILE, "wb") as f:
        pickle.dump({
            "USER_EMAIL": email,
            "USER_ID": user_id,
            "PASSWORD": encrypt_password(password)
        }, f)


def get_credentials():
    creds = load_credentials()
    if creds:
        print("✅ Loaded stored credentials")
        return creds

    email, user_id, password = prompt_for_credentials()
    save_credentials(email, user_id, password)
    return email, user_id, password
