from peewee import *
import uuid 


SEED_SIZE = 32
PASSWORD_SIZE = 32

class spa_db():
	
	def __init__(self, host='localhost', user="root", passwd="", db="spa_db", port=3316):
		self.db = MySQLDatabase(db, host=host, user=user, passwd=passwd, port=port,\
								use_unicode=True,  charset= 'utf8')
		self.db.connect()

		self.Seed, self.Random, self.Client = self.init_models()


	# creates a new client
	def add_client(self, password, seed):
		password = password if password else ""

		if not seed or len(seed) != SEED_SIZE:
			return {'success' : False, 'aid' : None, 
			'error' : 'Seed must be ' + str(SEED_SIZE) + ' bytes'}
		if len(password) > PASSWORD_SIZE:
			return {'success' : False, 'aid' : None, 
			'error' : 'Password must be less than' + str(PASSWORD_SIZE) + ' bytes'}
				
		# create seed object first
		seed = self.Seed.create(seed=seed)
		# generate new aid for client
		aid = uuid.uuid4().hex
		client = self.Client.create(seed=seed, aid=aid, password = password)

		return {'success' : True, 'aid' : aid}

	
	# edits existing client 
	def get_client(self, aid):
		'''
			So far it just changes client's password
		'''
		Client = self.Client
		Random = self.Random
		Seed = self.Seed
		try : 
			res_client = Client.get(Client.aid == aid)
		except Exception:
			return {'success' : False, 'client' : None, 
			'error' : 'Client not found'}

		old_seed = None if not res_client.old_seed else res_client.old_seed.seed
		
		randoms = []
		try :
			randoms = Random.select().where(Random.seed == res_client.seed.id)
		except Exception:
			pass

		old_randoms = []
		if old_seed:
			try : 
				old_randoms = Random.select().where(Random.seed == res_client.old_seed.id)
			except Exception:
				pass
		
		# now parse
		client_dict = {
			'aid' : res_client.aid,
			'password' : res_client.password,
			'seed' : res_client.seed.seed,
			'old_seed' : old_seed,
			'randoms' : [x.random for x in randoms],
			'old_randoms' : [x.random for x in old_randoms],
		}

		return {'success' : True, 'client' : client_dict}

	# edits existing client 
	def edit_client(self, aid, password = None):
		'''
			So far it just changes client's password
		'''
		Client = self.Client
		try : 
			res_client = Client.get(Client.aid == aid)
		except Exception:
			return {'success' : False, 'aid' : None, 
			'error' : 'Client not found'}
		if password:
			res_client.password = password
			res_client.save()

		return {'success' : True}	

	def delete_seed_randoms(self, seed_id):
		# get all of those seeds's randoms
		Random = self.Random
		randoms = []
		try : 
			randoms = Random.select().where(Random.seed == seed_id)
		except Exception:
			pass
		for r in randoms:
			r.delete_instance()

	# remove client 
	def remove_client(self, aid):
		Client = self.Client
		Seed = self.Seed
		
		# get client
		try : 
			res_client = Client.get(Client.aid == aid)
		except Exception:
			return {'success' : False,  
			'error' : 'Could not find client'}

		# get all of Clients seeds
		seed = Seed.get(Seed.id == res_client.seed.id)

		# get old_seed as well
		old_seed = None
		if res_client.old_seed:
			old_seed = Seed.get(Seed.id == res_client.old_seed.id)
				
		self.delete_seed_randoms(seed.id)
		if old_seed:
			self.delete_seed_randoms(old_seed.id)
		# now delete client and seeds
		res_client.delete_instance()
		seed.delete_instance()
		if old_seed:
			old_seed.delete_instance()

		
		return {'success' : True}

	def set_new_seed(self, aid, seed):
		if not seed or len(seed) != SEED_SIZE:
			return {'success' : False, 'aid' : None, 
			'error' : 'Seed must be ' + str(SEED_SIZE) + ' bytes'}
		
		# first set this seed to the old seed
		Client = self.Client
		Seed = self.Seed	
		# get client
		try : 
			res_client = Client.get(Client.aid == aid)
		except Exception:
			return {'success' : False,  
			'error' : 'Could not find client'}

		# delete old seed
		if res_client.old_seed:
			self.delete_seed_randoms(res_client.old_seed.id) 
			res_client.old_seed.delete_instance()
		new_seed = Seed.create(seed=seed)
		res_client.old_seed = res_client.seed	
		res_client.seed = new_seed

		res_client.save()
		return {'success' : True}


	def use_old_seed(self, aid):
		Client = self.Client
		Seed = self.Seed
		# get client
		try : 
			res_client = Client.get(Client.aid == aid)
		except Exception:
			return {'success' : False,  
			'error' : 'Could not find client'}
		
		# get current seed 
		seed = Seed.get(Seed.id == res_client.seed.id)

		# delete new seed
		self.delete_seed_randoms(seed.id) 

		res_client.seed = res_client.old_seed;
		res_client.old_seed = None
		res_client.save()

		seed.delete_instance()

	def add_random_to_seed(self, aid, random):
		Client = self.Client
		Random = self.Random
		# get client
		try : 
			res_client = Client.get(Client.aid == aid)
		except Exception:
			return {'success' : False,  
			'error' : 'Could not find client'}
		# get all of Clients seeds
		random = Random.create(random = random, seed = res_client.seed.id)

		return {'success' : True, 'random' : random}


	def add_random_to_old_seed(self, aid, random):
		Client = self.Client
		Random = self.Random
		# get client
		try : 
			res_client = Client.get(Client.aid == aid)
		except Exception:
			return {'success' : False,  
			'error' : 'Could not find client'}

		if not res_client.old_seed:
			return {'success' : False,  
			'error' : 'Client does not have an old seed'}
				
		# get all of Clients seeds
		random = Random.create(random = random, seed = res_client.old_seed.id)

		return {'success' : True, 'random' : random}

	
	def init_models(self,):
		SPA_LIB = self
		
		class BaseModel(Model):
			class Meta:
				database = SPA_LIB.db

		class Seed(BaseModel):
			seed = CharField()

			class Meta:
				table_name = 'seeds'

		class Client(BaseModel):
			aid = CharField(index=True, null=True)
			old_seed = ForeignKeyField(column_name='old_seed', field='id', model=Seed, null=True)
			password = CharField(null=True)
			seed = ForeignKeyField(backref='seeds_seed_set', column_name='seed', field='id', model=Seed, null=True)

			class Meta:
				table_name = 'clients'

		class Random(BaseModel):
			random = FloatField(null=True)
			seed = ForeignKeyField(index=True, column_name='seed', field='id', model=Seed, null=True)

			class Meta:
				table_name = 'randoms'
	
		# create if it does not exist 
		for m in [Seed, Random, Client]:
			if not m.table_exists():
				m.create_table(True)

		return [Seed, Random, Client]		


