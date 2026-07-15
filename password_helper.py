from Crypto.Cipher import AES
import os
import hmac
import hashlib
import random
import string

# utility functions for managing the passwords 
# using symmetric encryption since it is one person, one device, and the data being protected is at rest
class PasswordHelper:

    iter = 200000

    # PKCS#7 - cryptographic method to extend plaintext to an exact multiple of the block size needed by block ciphers (AES Multiple of 16)
    @staticmethod
    def _pkcs7_pad(plaintext):
        # get the remainder of bytes after dividing by 16 for AES, then subtract that from 16 to get the length of padding
        pad_len = 16 - (len(plaintext) % 16)
        # each byte value equals the number of bytes we need to add, know how many to remove when decrypting 
        padded_password = plaintext + bytes([pad_len] * pad_len)

        return padded_password
    
    # unpad
    @staticmethod
    def _pkcs7_unpad(padded_plaintext):
        # the last byte indicates the number of bytes padded that needs to be removed
        num_bytes = padded_plaintext[len(padded_plaintext)-1]

        # we only want the portion of the string before the padding starts
        size = len(padded_plaintext) - num_bytes

        # since bytes are immutable slice it to get the portion before the padding starts
        unpadded = padded_plaintext[:size]

        # return the unpadded portion
        return unpadded

    # encrypt passwords 
    @staticmethod
    def encrypt(password, key):
        # if the password is an instance of a string type
        if isinstance(password, str):
            # ensure that password is in bytes before being padded in pkcs7 to return bytes for aes
            password = password.encode()

        # pad our password to a multiple of 16 for AES
        padded_password = PasswordHelper._pkcs7_pad(password)

        # generate a 16 byte initalization vector to ensure that the cipher text is unique each encryption
        iv = os.urandom(16)

        # use aes built into ucryptolib pass the derived key, mode 2 (CBC), and the IV
        # CBC mode each block is XOR'd with the previous cipher text eliminating the pattern of password
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_password = cipher.encrypt(padded_password)

        # return a tuple including the encrypted password and the same iv used to encrypt
        # note to self: tuples = immutable, lists = mutable
        return (encrypted_password, iv)
    
    # decrypt passwords
    @staticmethod
    def decrypt(encrypted_password, key, iv):

        # use the derived key and iv to decrypt the encrypted password using the built in decrypt function in ucryptolib
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_password = cipher.decrypt(encrypted_password)
        
        # return the decrypted unpadded password
        return PasswordHelper._pkcs7_unpad(decrypted_password)
    
    # derive key
    @staticmethod
    def derive_key(password, salt):
        # reutrn the derived key 
        return PasswordHelper.pbkdf2(password, salt, PasswordHelper.iter)

    @staticmethod
    def pbkdf2(password, salt, iterations):
        # get the result of the password + salt hashed
        result = hmac.new(password, salt, hashlib.sha256).digest()
        
        # iterate through the number of iterations specified
        # more iterations more times the hashing process is repeated = more expensive for attackers
        for i in range(iterations):
            # empty list to hold the new result after each iteration
            # needs to be cleared every iteration or we will keep appending 32 byte blocks 
            new_result = []

            # make a new hash block of password + result hash
            block = hmac.new(password, result, hashlib.sha256).digest()
            
            # zip takes two lists and pairs them up side by side 
            # zip([1, 2, 3], [4, 5, 6]) -->
            # gives you: (1,4), (2,5), (3,6)
            # result and block are 32 bytes and zip pairs the related bytes up with eachother to be able to XOR each pair
            for a, b in zip(result, block):
                
                # XOR of two 32-byte blocks always outputs a 32 byte block since you are operating on each pair of bytes individually
                # the original hash is baked into every XOR, mixes all iterations into the final result not just the last iteration matters
                new_result.append(a ^ b)
            
            # set result equal to the new result list 
            result = bytes(new_result)

        # return the final result = derived key
        return result

    # hashing utility 00
    @staticmethod
    def sha256_hash_util(value, salt):
        # check if the value is an instance of a string
        if isinstance(value, str):
            value = value.encode()

        # return the sha256 hash using our salt and the value passed
        return hashlib.sha256(salt + value).digest()

    @staticmethod
    def generate_password(length=18):
        
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        numbers = string.digits
        symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        all_chars = lowercase + uppercase + numbers + symbols
        
        password = []
        password.append(random.choice(lowercase))
        password.append(random.choice(uppercase))
        password.append(random.choice(numbers))
        password.append(random.choice(symbols))
        
        for i in range(length - 4):
            password.append(random.choice(all_chars))
        
        random.shuffle(password)
        return ''.join(password)

    @staticmethod
    def password_strength(password):
        score = 0
        
        has_lower = False
        has_upper = False
        has_digit = False
        has_symbol = False
        symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        
        for c in password:
            if c.islower():
                has_lower = True
            if c.isupper():
                has_upper = True
            if c.isdigit():
                has_digit = True
            if c in symbols:
                has_symbol = True
        
        if has_lower:
            score += 1
        if has_upper:
            score += 1
        if has_digit:
            score += 1
        if has_symbol:
            score += 1
        if len(password) >= 8:
            score += 1
        if len(password) >= 16:
            score += 1
        
        return score


            



        