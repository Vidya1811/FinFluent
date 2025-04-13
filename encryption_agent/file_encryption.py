from cryptography.fernet import Fernet
import os

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

fldr_name = "stock_market"

print("Encrypting CSV file...")
# Generate and save a key (do this once and reuse the key later)
key = Fernet.generate_key()
with open("secret.key", "wb") as key_file:
    key_file.write(key)

# Load the key
with open("secret.key", "rb") as key_file:
    key = key_file.read()

cipher = Fernet(key)

file_path = "FinFluent\\user_data\\"  # add slash at end of file path
file_name = "5_year.csv"
user_name = "user_1"
orig_path = os.path.join(desktop_path, fldr_name, file_path, user_name, file_name)
encrypted_file_path = "FinFluent\\encrypted_files\\"  # add slash at end of file path
encryp_path = os.path.join(desktop_path, fldr_name, encrypted_file_path, user_name, file_name)

# Encrypt the CSV file
with open(orig_path, "rb") as f:
    data = f.read()

encrypted_data = cipher.encrypt(data)

with open(encryp_path, "wb") as f:
    f.write(encrypted_data)
 
decrypted_data = cipher.decrypt(encrypted_data)

decrypted_file_path = "FinFluent\\decrypted_files\\"  # add slash at end of file path
decryp_path = os.path.join(desktop_path, fldr_name, decrypted_file_path, user_name, file_name)

with open(decryp_path, "wb") as f:
    f.write(decrypted_data)