import uuid
import string
import random
from spa_packet import *

password = 'thisisapassword'
seed = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))
aid = uuid.uuid1().hex

spa_pack = SPAreq(aid, password, seed)
s = SPAreq(spa_pack.get_encoded_pack())
s.decrypt_packet(seed)

spa_rpack = SPAresp(SUCCESS,1989,seed)
r = SPAresp(spa_rpack.get_encoded_pack(),seed)

print "SUCCESS"