from ctypes import *
import struct
import random
import hashlib
import md5
from aes_enc import *
import re
import socket

# SIZES
AID_S  = 32
PWD_S  = 32
RND_S  = 4
IP_S   = 4
UPL_S  = AID_S + PWD_S + RND_S + IP_S

SEED_S = 32
MD5_S  = 16
HASH_S = UPL_S + MD5_S
ENC_S  = 152

# distinct type of initialization
create_new_req  = lambda x : True if len(x) == 6 and\
isinstance(x[0], str) and len(x[0]) == AID_S and\
isinstance(x[1], str) and len(x[1]) <= PWD_S and\
isinstance(x[2], str) and len(x[2]) == SEED_S and\
isinstance(x[4], str) and\
isinstance(x[5], int)\
else False

parse_spa_req   = lambda x : True if len(x) == 1 and \
isinstance(x[0], str) else False

# Format of payload to be hashed
U_PAYLOAD_FORM = "!%ds%dsf%ds%dsi"    % (AID_S, PWD_S, SEED_S, IP_S)
# Format to use in AES encryption
F_PAYLOAD_FORM = "!%dsf%ds%dsi"    % (PWD_S, SEED_S,IP_S)
# For discovering SPA packets
SPA_FORMAT  = "(\S{%d}):(\S{%d}):(\S{%d})" % (AID_S, ENC_S, MD5_S)

# error for SPA packets
class InvalidSPA(Exception):
	pass

class SPAreq():
	"""
		An SPA packet based on RFC 4226 and fwknop Version.
	"""

	def __init__(self, *args):
		"""
			Creates a new SPA request packet : SPA(AID, password, seed)
			or unpacks an existing one : SPA(hash, seed)
		"""
		self.password = ""
		self.random = None
		self.new_seed = None
		self.ip = None
		self.port = None
		
		if create_new_req(args):
			self.aid = args[0]
			self.password = args[1]
			self.seed = args[2]
			self.new_seed = args[3]
			try:
				self.ip = socket.inet_aton(args[4])
			except Exception:
				raise ValueError("Incorrect IP address")
			self.port = args[5]
			
			# add padding to password string
			self.password = self.password.ljust(PWD_S, '\0')

			# create 32bit random number
			try :
				# priority is to create a strong random number
				self.random = c_double(random.SystemRandom().random()).value
			except NotImplementedError :
				self.random = c_double(random.WichmannHill().random()).value

			# create binary from payload
			self.p_str = struct.pack(U_PAYLOAD_FORM, self.aid, self.password,\
				self.random, self.new_seed, self.ip, self.port)

			#create md5 hash from payload string
			self.md5_h = md5.new(self.p_str).digest()

			# pack them together
			tmp = struct.pack(F_PAYLOAD_FORM, self.password, self.random, \
				self.new_seed, self.ip, self.port)
			# encrypt packet using AES algorithm
			aes_obj = AESCipher(self.seed)
			enc = aes_obj.encrypt(tmp)
			self.e_packet = "%s:%s:%s" % (self.aid, enc, self.md5_h)
		elif parse_spa_req(args):
			try :
				# parse spa
				match = re.search(SPA_FORMAT,args[0])
				self.aid = match.group(1)
				self.e_packet = match.group(2)
				self.md5_h = match.group(3)
			except Exception as err:
				raise ValueError("Invalid arguments for SPAreq creation")
		else :
			raise ValueError("Invalid arguments for SPAreq creation")

	def get_aid(self):
		return self.aid

	def get_encoded_pack(self):
		return self.e_packet

	def get_seed(self):
		return self.seed

	def set_seed(self, seed):
		self.seed = seed

	def get_new_seed(self,):
		return self.new_seed

	def get_ip(self,):
		return self.ip

	def get_port(self,):
		return self.port	

	def decrypt_packet(self, seed):
		# decrypt using AES algorithm
		self.seed = seed
		aes_obj = AESCipher(seed)
		tmp = aes_obj.decrypt(self.e_packet)
		# unpack
		try :
			self.password, self.random, self.new_seed, self.ip, self.port =\
				struct.unpack(F_PAYLOAD_FORM, tmp)
			self.ip = socket.inet_ntoa(self.ip)
		except Exception as err:
			raise InvalidSPA("Wrong Seed")
		
		#create p_str
		self.p_str = struct.pack(U_PAYLOAD_FORM, self.aid, self.password, self.random,\
			self.new_seed, socket.inet_aton(self.ip), self.port)
		# compare md5_hash(uPayload) with md5_hash-check for modification
		if self.md5_h != md5.new(self.p_str).digest() :
			raise InvalidSPA("MD5 Hashes do not match!")
		self.password = self.password.rstrip('\0')

	def is_authenticated(self, pwd):
		return pwd == self.password

	def get_random(self):
		if self.random:
			return self.random
		return None

	# TODO write a proper str function!!!
	def __str__(self):
		return """
aid : %s
password : %s
new_seed : %s
ip : %s
port : %d
		""" % (self.aid, self.password, self.new_seed, self.ip, self.port)
