import sys
sys.path.insert(0, '../')
import spa_lib

aid = "1e9b8da6ca2a47de863e74dbbe8d926f"
seed = "46facea41fdd11e8acf9646e69b26c4f"
new_seed = "46facea41fdd11e8acf9646e69b26c4a"
password="jaskdaj"

spa_lib.send_spa(aid, password, seed, new_seed, spa_lib.get_public_ip(), 8888)
