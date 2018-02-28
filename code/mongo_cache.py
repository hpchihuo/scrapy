from datetime import datetime, timedelta
from pymongo import MongoClient
import pickle
import zlib
from bson.binary import Binary

class MongoCache:
	def __init__(self, client=None, expires=timedelta(days=30)):
		#如果没有给定MongoDB客户端，则选择默认端口
		self.client = MongoClient('localhost', 27017) if client is None else client
		#创建一个集合用于储存网页缓存，该集合等同于关系型数据库中得表格
		self.db = client.cache
		#设置网页时间的过期时间索引
		self.db.webpage.create_index('timestamp', expireAfterSeconds=expires.total_seconds())

	def __contains__(self, url):
		try:
			self[url]
		except KeyError:
			return False
		else:
			return True

	def __getitem__(self, url):
		"""load value at this url
		"""
		record = self.db.websage.find_one({'_id': url})
		if record:
			return pickle.loads(zlib.decompress(record['result']))
		else:
			raise KeyError(url + ' dose not exist')

	def __setitem__(self, url, result):
		"""save value for URL
		"""
		record = ('result': Binary(zlib.compress(pickle.dumps(result))), 'timestamp':datetime.utcnow())
		self.db.websage.update({'_id':url}, {'$set': record}, upsert=True)

	def clear(self):
		self.db.webpage.drop()