import hashlib
import random
import string

# Function to generate a secure password
def generate_secure_password(length=12):
    if length < 8:
        raise ValueError("Length must be at least 8 characters for better security.")
    charset = string.ascii_letters + string.digits
    return ''.join(random.choices(charset, k=length))

# Function to generate a SHA-256 hash
def generate_sha256_hash(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Function to verify the hash
def verify_hash(entered_password, saved_hash):
    computed_hash = generate_sha256_hash(entered_password)
    return computed_hash == saved_hash




if __name__ == "__main__":
    # Generate a random secure password
    new_password = generate_secure_password(length=33)
    print(f"Generated secure password: {new_password}")

    # Create initial SHA-256 hash
    generated_hash = generate_sha256_hash(new_password)
    print(f"Generated hash (SHA-256): {generated_hash}")

    # Simulate user password input
    entered_password = new_password

    # Verify entered password
    if verify_hash(entered_password, generated_hash):
        print("Password is correct.")
    else:
        print("Password is incorrect.")