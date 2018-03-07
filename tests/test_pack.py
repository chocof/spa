import uuid
import string
import random
import sys
sys.path.insert(0, '../')
from spa_packet import *

password = 'thisisapassword'
seed = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))
aid = uuid.uuid4().hex
ip = "127.0.0.1"
port = 342
new_seed = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))

spa_pack = SPAreq(aid, password, seed, new_seed, ip, port)
s = SPAreq(spa_pack.get_encoded_pack())
s.decrypt_packet(seed)

print s
