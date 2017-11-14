from passlib.hash import pbkdf2_sha256

def compute_passlib_hash(password):
    """
    password(string): a password
    returns: a string from passlib that has both a unique salt and
    the hashed value of the salt+pw. It contains everything 
    passlib needs to verify a password later
    """
    passlib_hash = pbkdf2_sha256.hash(password)
    return passlib_hash


def verify_password(password, passlib_hash):
    """
    password(str): a password that you want to know if it matches 
        the hash
    passlib_hash(str): the output of compute_passlib_hash()
    returns: True if the password is the original password used
    in the call to compute_passlib_hash(password)
    """
    password_matches = pbkdf2_sha256.verify(password, passlib_hash)
    return password_matches
