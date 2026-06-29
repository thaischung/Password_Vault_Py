# Multi Factor Authentication (MFA)
# Two main types TOTP (Time-Sensitive One Time Password) and HOTP (HMAC One Time Password)
# TOTP is most common and HOTP is common in hardware key fobs
# HMAC - Hash-based Message Authentication Code
    # it is a way to produce a fixed-size "fingerprint" of some data using a secret key + hash function
# in TOTP the hash function is SHA1 
# process overview: decode the Base32-encoded secret --> get the raw key bytes --> use the HMAC (SHA1 function) --> to get the 20 byte hash --> truncate the last 4 bytes starting at an offset determined by the last nibble (4 bits) --> mod it by 1 Million --> 6 digit code
# Base32-encoded uses A-Z 2-7, decoding it acts as the HMAC key

import hashlib
import hmac
import time

class MFA:

    @staticmethod
    def _decode(Base32_encoded_secret):
        # decode the Base32-encoded secret and return the raw bytes
        base32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

        stored_bit_cout = 0
        bit_buffer = 0
        raw_bytes = []
        
        # set all chracters to upper casae and strip any padding
        secret = Base32_encoded_secret.upper().rstrip("=")

        # loop through the secret 
        for char in secret:
            # verify that the character is a valid base32 character
            value = base32.find(char) 
            if value == -1:
                print("Invalid Base32 Character")
                return
            
            # set the buffer for the next chracter (shift bits to the left by 5 bits allowing space for the next 5 bit char)
            # BitWise OR the new value into the 5 open spots 
            # increment the count
            bit_buffer = (bit_buffer << 5) | value
            stored_bit_cout += 5

            """
                bitbuffer --> 10101
                shift left by 5 bits -- > 101010000
                BitWise OR the new value ( 0 | 1 = 1, 0 | 0 = 0) (value = 01010) --> 1010101010

                if count 8 or more

                byte --> 1010101010 shift right by the remaining bit count --> 10101010 lose top 2 bits (10)
                BitWise AND the the 8 bits with 0xFF (11111111) --> preserves the 8 bits
            """
                
            if stored_bit_cout >= 8:
                byte = (bit_buffer >> (stored_bit_cout - 8)) & 0xFF
                stored_bit_cout -= 8
                raw_bytes.append(byte)

        return bytes(raw_bytes)

    # HMAC produces a fingerprint of some message with a key
    # without a changing message all codes would be the same forever
    # message = timer counter = (unix_time // 30) --> every 30 seconds produce a different output
    @staticmethod
    def _HMAC_SHA1(key, message):
        hash = hmac.new(key, message, hashlib.sha1).digest()
        # bitwise AND preserves the lower 4 bits turn the byte to 0-15
        offset = hash[19] & 0x0F

        # get the 4 bytes to truncate from the starting offset + 4 bytes
        four_bytes = hash[offset:offset+4]

        # turn the 4 bytes into one single integer
        # use big-endian form making the first byte the most significant (standard network byte order)
        # mask off the left most bit and preserve the rest of the bits 
        # we want to mask the left most bit because if it is a 1 python could interpret it as a negative number (signed number)
        code = int.from_bytes(four_bytes, 'big') &0x7FFFFFFF

        six_digit_code = code % 1000000

        return six_digit_code

    @staticmethod
    def _get_message():
        
        timer_counter = int(time.time()) // 30

        message = timer_counter.to_bytes(8, 'big')
    
        return message
    
    @staticmethod
    def time_remaining():
        return 30 - (time.time() % 30)

    @staticmethod
    def get_code(secret):
        key = MFA._decode(secret)
        message = MFA._get_message()
        return MFA._HMAC_SHA1(key, message)


