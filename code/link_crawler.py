import re
import urlparse
import urllib2
import time
import datetime
import robotparser
import random
from datetime import datetime, timedelta
import socket
import os
import shutil
import zlib
import json
import string
from PySide.QtGui import *
from PySide.QtCore import *
from PySide.QtWebKit import *
import lxml
import os
import glob
import cookielib

def load_ff_session(session_filename):
    cj = cookielib.CookieJar()
    if os.path.exists(session_filename):
        json_data = json.loads(open(session_filename,'rb').read())
        for window in json_data.get('windows', []):
            for cookiein window.get('cookies', []):
                c = cookielib.Cookie(0,
                    cookie.get('name', ''),
                    cookie.get('value', ''), None, False,
                    cookie.get('host', ''),
                    cookie.get('host', '').startswith('.'),
                    cookie.get('host', '').startswith('.'),
                    cookie.get('path', ''), False, False,
                    str(int(time.time()) + 3600*24*7),
                    False, None, None, ())
                cj.set_cookie(c)
    else:
        print("Session filename dose not exist: ", session_filename)
    return cj


def find_ff_session():
    paths = [
        '~/.mozilla/firefox/*.default',
        '~/Library/Appliction Support/Firefox/Profiles/*.default/sessionstore.js',
        '%APPDATA%/Roaming/Mozilla/Firefox/Profile/*.default'
        ]
    for path in paths:
        filename = os.path.join(path, 'sessionstore.js')
        matches = glob.glob(os.path.expanduser(filename))
        if matches:
            return matches[0]


class BrowserRender(QWebView):
    def __init__(self, show=True):
        self.app = QApplication(sys.argv)
        QWebView.__init__(self)
        if show:
            self.show()

        def downloader(self, url, timeout=60):
            loop = QEventLoop()
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(loop.quit)
            time.loadFinished.connect(loop.quit)
            self.load(QUrl(url))
            timer.start(timeout * 1000)

            loop.exec_()
            if timer.isActive():
                timer.stop()
                return self.html()

            else:
                print("Request timed out: "+ url)

        def html(self):
            return self.page().mainFrame().toHtml()

        def find(self, pattern):
            return self.page().mainFrame().findAllElements(pattern)

        def attr(self, pattern, name, value):
            for e in self.find(pattren):
                e.setAttribute(name, value)

        def text(self, pattern, value):
            for e in self.find(pattren):
                e.setPlainText(value)

        def click(self, patern):
            for e in self.find(pattern):
                e.evalueteJavaScript("this.click()")

        def wait_load(self, pattern, timeout=60):
            deadline = time.time() + timeout
            while time.time() < deadline:
                self.app.processEvents()
                matches = self.find(pattern)
                if matches:
                    return matches

            print("wait load timed out")

try:
    import cPickle as pickle
except ImportError:
    import pickle
from pymongo import MongoClient
from bson.binary import Binary


class MongoCache:
    """
    Wrapper around MongoDB to cache downloads

    >>> cache = MongoCache()
    >>> cache.clear()
    >>> url = 'http://example.webscraping.com'
    >>> result = {'html': '...'}
    >>> cache[url] = result
    >>> cache[url]['html'] == result['html']
    True
    >>> cache = MongoCache(expires=timedelta())
    >>> cache[url] = result
    >>> # every 60 seconds is purged http://docs.mongodb.org/manual/core/index-ttl/
    >>> import time; time.sleep(60)
    >>> cache[url] 
    Traceback (most recent call last):
     ...
    KeyError: 'http://example.webscraping.com does not exist'
    """
    def __init__(self, client=None, expires=timedelta(days=30)):
        """
        client: mongo database client
        expires: timedelta of amount of time before a cache entry is considered expired
        """
        # if a client object is not passed 
        # then try connecting to mongodb at the default localhost port 
        self.client = MongoClient('localhost', 27017) if client is None else client
        #create collection to store cached webpages,
        # which is the equivalent of a table in a relational database
        self.db = self.client.cache
        self.db.webpage.create_index('timestamp', expireAfterSeconds=expires.total_seconds())

    def __contains__(self, url):
        try:
            self[url]
        except KeyError:
            return False
        else:
            return True
    
    def __getitem__(self, url):
        """Load value at this URL
        """
        record = self.db.webpage.find_one({'_id': url})
        if record:
            #return record['result']
            return pickle.loads(zlib.decompress(record['result']))
        else:
            raise KeyError(url + ' does not exist')


    def __setitem__(self, url, result):
        """Save value for this URL
        """
        #record = {'result': result, 'timestamp': datetime.utcnow()}
        record = {'result': Binary(zlib.compress(pickle.dumps(result))), 'timestamp': datetime.utcnow()}
        self.db.webpage.update({'_id': url}, {'$set': record}, upsert=True)


    def clear(self):
        self.db.webpage.drop()


class DiskCache:
    """
    Dictionary interface that stores cached 
    values in the file system rather than in memory.
    The file path is formed from an md5 hash of the key.

    >>> cache = DiskCache()
    >>> url = 'http://example.webscraping.com'
    >>> result = {'html': '...'}
    >>> cache[url] = result
    >>> cache[url]['html'] == result['html']
    True
    >>> cache = DiskCache(expires=timedelta())
    >>> cache[url] = result
    >>> cache[url]
    Traceback (most recent call last):
     ...
    KeyError: 'http://example.webscraping.com has expired'
    >>> cache.clear()
    """

    def __init__(self, cache_dir='cache', expires=timedelta(days=30), compress=True):
        """
        cache_dir: the root level folder for the cache
        expires: timedelta of amount of time before a cache entry is considered expired
        compress: whether to compress data in the cache
        """
        self.cache_dir = cache_dir
        self.expires = expires
        self.compress = compress

    
    def __getitem__(self, url):
        """Load data from disk for this URL
        """
        path = self.url_to_path(url)
        if os.path.exists(path):
            with open(path, 'rb') as fp:
                data = fp.read()
                if self.compress:
                    data = zlib.decompress(data)
                result, timestamp = pickle.loads(data)
                if self.has_expired(timestamp):
                    raise KeyError(url + ' has expired')
                return result
        else:
            # URL has not yet been cached
            raise KeyError(url + ' does not exist')


    def __setitem__(self, url, result):
        """Save data to disk for this url
        """
        path = self.url_to_path(url)
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)

        data = pickle.dumps((result, datetime.utcnow()))
        if self.compress:
            data = zlib.compress(data)
        with open(path, 'wb') as fp:
            fp.write(data)


    def __delitem__(self, url):
        """Remove the value at this key and any empty parent sub-directories
        """
        path = self._key_path(url)
        try:
            os.remove(path)
            os.removedirs(os.path.dirname(path))
        except OSError:
            pass


    def url_to_path(self, url):
        """Create file system path for this URL
        """
        components = urlparse.urlsplit(url)
        # when empty path set to /index.html
        path = components.path
        if not path:
            path = '/index.html'
        elif path.endswith('/'):
            path += 'index.html'
        filename = components.netloc + path + components.query
        # replace invalid characters
        filename = re.sub('[^/0-9a-zA-Z\-.,;_ ]', '_', filename)
        # restrict maximum number of characters
        filename = '/'.join(segment[:255] for segment in filename.split('/'))
        return os.path.join(self.cache_dir, filename)


    def has_expired(self, timestamp):
        """Return whether this timestamp has expired
        """
        return datetime.utcnow() > timestamp + self.expires


    def clear(self):
        """Remove all the cached values
        """
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)




DEFAULT_AGENT = 'wswp'
DEFAULT_DELAY = 5
DEFAULT_RETRIES = 1
DEFAULT_TIMEOUT = 60

class Downloader:
    def __init__(self, delay=DEFAULT_DELAY, user_agent=DEFAULT_AGENT, proxies=None, num_retries=DEFAULT_RETRIES, timeout=DEFAULT_TIMEOUT, opener=None, cache=None):
        socket.setdefaulttimeout(timeout)
        self.throttle = Throttle(delay)
        self.user_agent = user_agent
        self.proxies = proxies
        self.num_retries = num_retries
        self.opener = opener
        self.cache = cache


    def __call__(self, url):
        result = None
        if self.cache:
            try:
                result = self.cache[url]
            except KeyError:
                # url is not available in cache 
                pass
            else:
                if self.num_retries > 0 and 500 <= result['code'] < 600:
                    # server error so ignore result from cache and re-download
                    result = None
        if result is None:
            # result was not loaded from cache so still need to download
            self.throttle.wait(url)
            proxy = random.choice(self.proxies) if self.proxies else None
            headers = {'User-agent': self.user_agent}
            result = self.download(url, headers, proxy=proxy, num_retries=self.num_retries)
            if self.cache:
                # save result to cache
                self.cache[url] = result
        return result['html']


    def download(self, url, headers, proxy, num_retries, data=None):
        print 'Downloading:', url
        request = urllib2.Request(url, data, headers or {})
        opener = self.opener or urllib2.build_opener()
        if proxy:
            proxy_params = {urlparse.urlparse(url).scheme: proxy}
            opener.add_handler(urllib2.ProxyHandler(proxy_params))
        try:
            response = opener.open(request)
            html = response.read()
            code = response.code
        except Exception as e:
            print 'Download error:', str(e)
            html = ''
            if hasattr(e, 'code'):
                code = e.code
                if num_retries > 0 and 500 <= code < 600:
                    # retry 5XX HTTP errors
                    return self._get(url, headers, proxy, num_retries-1, data)
            else:
                code = None
        return {'html': html, 'code': code}


class Throttle:
    """Throttle downloading by sleeping between requests to same domain
    """
    def __init__(self, delay):
        # amount of delay between downloads for each domain
        self.delay = delay
        # timestamp of when a domain was last accessed
        self.domains = {}
        
    def wait(self, url):
        """Delay if have accessed this domain recently
        """
        domain = urlparse.urlsplit(url).netloc
        last_accessed = self.domains.get(domain)
        if self.delay > 0 and last_accessed is not None:
            sleep_secs = self.delay - (datetime.now() - last_accessed).seconds
            if sleep_secs > 0:
                time.sleep(sleep_secs)
        self.domains[domain] = datetime.now()


def link_crawler(seed_url, link_regex=None, delay=5, max_depth=-1, max_urls=-1, user_agent='wswp', proxies=None, num_retries=1, scrape_callback=None, cache=None):
    """Crawl from the given seed URL following links matched by link_regex
    """
    # the queue of URL's that still need to be crawled
    crawl_queue = [seed_url]
    # the URL's that have been seen and at what depth
    seen = {seed_url: 0}
    # track how many URL's have been downloaded
    num_urls = 0
    #rp = get_robots(seed_url)
    D = Downloader(delay=delay, user_agent=user_agent, proxies=proxies, num_retries=num_retries, cache=cache)

    while crawl_queue:
        url = crawl_queue.pop()
        depth = seen[url]
        # check url passes robots.txt restrictions
        #if rp.can_fetch(user_agent, url):
        html = D(url)
        links = []
        if scrape_callback:
            links.extend(scrape_callback(url, html) or [])

        if depth != max_depth:
                # can still crawl further
           
                    # filter for links matching our regular expression
            links.extend(link for link in get_links(html))

            for link in links:
                link = normalize(seed_url, link)
                    # check whether already crawled this link
                if link not in seen:
                    seen[link] = depth + 1
                        # check link is within same domain
                    if same_domain(seed_url, link):
                            # success! add this new link to queue
                        crawl_queue.append(link)

            # check whether have reached downloaded maximum
        num_urls += 1
        if num_urls == max_urls:
                break


def normalize(seed_url, link):
    """Normalize this URL by removing hash and adding domain
    """
    link, _ = urlparse.urldefrag(link) # remove hash to avoid duplicates
    return urlparse.urljoin(seed_url, link)


def same_domain(url1, url2):
    """Return True if both URL's belong to same domain
    """
    return urlparse.urlparse(url1).netloc == urlparse.urlparse(url2).netloc


def get_robots(url):
    """Initialize robots parser for this domain
    """
    rp = robotparser.RobotFileParser()
    rp.set_url(urlparse.urljoin(url, '/robots.txt'))
    rp.read()
    return rp
        

def get_links(html):
    """Return a list of links from html 
    """
    # a regular expression to extract all links from the webpage
    webpage_regex = re.compile('<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
    # list of all links from the webpage
    return webpage_regex.findall(html)


if __name__ == '__main__':
    url = 'http://example.webscraping.com/search'
    session_filename = session_filename = 'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\jd1aw476.default\sessionstore.js'
    cj = load_ff_session(session_filename)
    processor  = urllib2.HTTPCookieProcessor(cj)
    opener = urllib2.build_opener(processor)
    url = 'http://example.webscraping.com'
    html = opener.open(url).read()
    