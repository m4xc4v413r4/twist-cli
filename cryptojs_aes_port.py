# From https://gist.github.com/adrianlzt/d5c9657e205b57f687f528a5ac59fe0e
# Encryption with AES-CBC
# Adapted to work with CryptoJS (crypto-js@3.1.9) with default configuration
#
# pkcs7==0.1.2
# pycrypto==2.6.1
#

import base64
import binascii
import struct
import hashlib
from pkcs7 import PKCS7Encoder
from Crypto.Cipher import AES
from Crypto import Random

MODE = AES.MODE_CBC

def evpKDF(passwd, salt, key_size=8, iv_size=4, iterations=1, hash_algorithm="md5"):
    """
    https://github.com/Shani-08/ShaniXBMCWork2/blob/master/plugin.video.serialzone/jscrypto.py
    """
    target_key_size = key_size + iv_size
    derived_bytes = b""
    number_of_derived_words = 0
    block = None
    hasher = hashlib.new(hash_algorithm)
    while number_of_derived_words < target_key_size:
        if block is not None:
            hasher.update(block)

        hasher.update(passwd)
        hasher.update(salt)
        block = hasher.digest()
        hasher = hashlib.new(hash_algorithm)

        for i in range(1, iterations):
            hasher.update(block)
            block = hasher.digest()
            hasher = hashlib.new(hash_algorithm)

        derived_bytes += block[0: min(len(block), (target_key_size - number_of_derived_words) * 4)]

        number_of_derived_words += len(block)/4

    return {
        "key": derived_bytes[0: key_size * 4],
        "iv": derived_bytes[key_size * 4:]
    }


def encrypt(passphrase, plaintext):
    salt = Random.new().read(8)
    resp = evpKDF(passphrase, salt, key_size=12)
    key = resp.get("key")
    iv = key[len(key)-16:]
    key = key[:len(key)-16]

    aes = AES.new(key, MODE, iv)
    encoder = PKCS7Encoder()
    pad_text = encoder.encode(plaintext)
    encrypted_text = aes.encrypt(pad_text)
    
    concat = "Salted__"+salt+encrypted_text
    return binascii.b2a_base64(concat).rstrip()

def decrypt(passphrase, encrypted_text):
    encrypted_text_bytes = base64.b64decode(encrypted_text)

    # Remove "Salt__"
    encrypted_text_bytes = encrypted_text_bytes[8:]

    # Get and remove salt
    salt = encrypted_text_bytes[:8]
    encrypted_text_bytes = encrypted_text_bytes[8:]

    resp = evpKDF(passphrase, salt, key_size=12)
    key = resp.get("key")
    iv = key[len(key)-16:]
    key = key[:len(key)-16]

    aes = AES.new(key, MODE, iv)
    decrypted_text = aes.decrypt(encrypted_text_bytes)
    encoder = PKCS7Encoder()
    unpad_text = encoder.decode(decrypted_text)

    return unpad_text.decode("utf-8")