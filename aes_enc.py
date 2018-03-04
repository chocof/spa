"""
    This code was taken from mnothic's answer to 
    http://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256
"""

import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES

AES_BLOCK_SIZE = 32
class AESCipher(object):

    def __init__(self, key): 
        self.bs = AES_BLOCK_SIZE
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:]))

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]
