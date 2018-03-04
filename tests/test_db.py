import sys
sys.path.insert(0, '../')
import client_db
import uuid

c = client_db.spa_db(passwd="")
seed = uuid.uuid1().hex
new_seed = uuid.uuid1().hex

res = c.add_client(password="dasda",seed=seed)
aid = res['aid']

c.edit_client(aid = aid, password = "jaskdaj")
c.add_random_to_new_seed(aid, 0.2342342)

c.set_new_seed(aid, new_seed)
c.add_random_to_new_seed(aid, 0.2342342)
c.add_random_to_old_seed(aid, 0.23423333)
c.use_old_seed(aid)
a = c.get_client(aid)['client']

print a
c.remove_client(aid)










