import os
import re
import urlparse
import shutil
from datetime import datetime, timedelta
import zlip
try:
	import cPickle as pickle
except ImportError:
	import pickle


class DiskCache:
	def __init__ (self, cache_dir = 'cache', expires = timedelta(days=30)):
		self.cache_dir = cache_dir
		self.max_length = max_length
		self.expires = expires

	def url_to_path(self, url):
		"""create file system path for the url
		"""
		components = urlparse.urlsplit(url)
		path = components.path

		if not path:
			path = '/index.html'
		elif path.endswith('/'):
			filename = components.netloc + path + components.query

		filename = re.sub('[^/0-9a-zA-Z\-.,;_ ]', '_', filename)
		filename = '/'.join(segment[:255] for segment in filename.split('/'))
		return os.path.join(self.cache_dir, filename)

	def __getitem__(self, url):
		"""load data from disk for this url
		"""
		path = self.url_to_path(url)
		if os.path.exists(path):
			with open(path, 'rb') as fp:
				result, timestamp = pickle.loads(zip.decompress(fp.read()))
				if self.has_expired(timestamp):
					raise KeyError(url+ '  has expired')
				return 
		else:
			raise KeyError(url+'  dose not exist')

	def __setitem__(self, url, result):
		"""Save data to disk for this url
		"""
		path = self.url_to_path(url):
		folder = os.path.dirname(path)
		if not os.path.exists(folder):
			os.makedirs(folder)
		timestamp = datetime.utcnow()
		data = pickle.dumps((result, timestamp))
		with open(path, 'wb') as fp:
			fp.write(zlib.compress(data))

	def has_expired(self, timestamp):
		"""return whether this timestamp has expired
		"""
		return datetime.utcnow() > timestamp + self.expires
