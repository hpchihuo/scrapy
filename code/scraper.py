# _*_ coding:utf-8 _*_
import urllib2
import re 
import urlparse
import robotparser
import time
import Queue
from datetime import datetime
from bs4 import BeautifulSoup
import lxml.html
import csv
import socket

DEFAULT_AGENT = 'wswp'
DEFAULT_DELAY = 5
DEFAULT_RETRIES = 1
DEFAULT_TIMEOUT = 60

FIELDS = ('area', 'population', 'iso', 'counrtry', 'capital', 'continent', 'tld', 'currency_code', 'currency_name',
			'phone', 'postal_code_format', 'postal_code_regex', 'languages')

#设置下载间隔
class Throttle:
	def __init__(self, delay):
		self.delay = delay
		self.domains = {}

	def wait(self, url):
		domain = urlparse.urlparse(url).netloc
		#获取上一次爬取时间
		last_accessed = self.domains.get(domain)

		if self.delay > 0 and last_accessed is not None:
			sleep_secs = self.delay - (datetime.datetime.now() - last_accessed).seconds
			if sleep_secs > 0:
				time.sleep(sleep_secs)
		#记录当前爬取时间
		self.domains[domain] = datetime.now()

#抓取单个网页函数
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
		#在缓存中URL不存在，则下载
		if self.cache:
			try:
				result = self.cache[url]
			#url没有下载过，则需进行下载
			except KeyError:
				pass
			#没有下载成功，且为服务器原因，则重新下载
			else:
				if self.num_retries > 0 and results['code'] >= 500 and result['code'] < 600:
					result = None
		if result is None:
			self.throttle.wait(url)
			proxy = random.choice(self.proxies) if self.proxies else None
			headers = {'User-agent': self.user_agent}
			result = self.download(url, headers, proxy=proxy,num_retries=self.num_retries)
			if self.cache:
				self.cache[url] = result
		return result['html']
	def download(self, url, headers, proxy, num_retries, data=None):
		print("Downloading: ", url)
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
			print("Downloading error", str(e))
			html = ''
			if hasattr(e, 'code'):
				code = e.code
				if num_retries > 0 and code >= 500 and code < 600:
					return self._get(url, headers, proxy, num_retries-1, data)
				else:
					code = None
		return {'html': html, 'code':code}



def crawl_sitemap(url):
	sitemap = download(url)

	links = re.findall('<loc>(.*)</loc>', sitemap)
	for link in links:
		html = download(link)
		print(link)

def link_crawler(seed_url, link_regex=None, delay=5, max_depth=-1, max_urls=-1, user_agent='wswp', proxies=None, num_retries=1, scrape_callback=None, cache=None):
	crawl_queue = [seed_url]
	#记录爬取过的网页，避免重复或循环爬取，同时设置爬取深度，
	seen = {seed_url: 0}
	num_urls = 0
	rp = get_robots(seed_url)
	D = Downloader(delay = delay, user_agent=user_agent, proxies=proxies, num_retries=num_retries,cache=cache)

	while crawl_queue:
		url = crawl_queue.pop()
		depth = seen[url]
		#检查网页是否由robots协议禁止爬取
		if rp.can_fetch(user_agent, url):
			html =D(url)
			html = download(url,headers)
			links = []

			if scrape_callback:
				links.extend(scrape_callback(url, html) or [])

			depth = seen[url]
			if depth != max_depth:
				#获取网页中链接
				if link_regex:
					links.extend(link for link in get_links(html) if re.match(link_regex,link))

				for link in links:
					#将相对链接装换为绝对链接
					link = normalize(seed_url, link)
					#检查网页是否已被添加到爬取队列中
					if link not in seen:
						seen[link] = depth+1
						if same_domain(seed_url, link):
							crawl_queue.append(link)
		num_urls += 1
		if num_urls == max_urls:
			break
		else:
			print("Blocked by robots.txt:", url)

#提取网页中的相对链接
def get_links(html):
	webpage_regex = re.compile('<a[^>]+href=["\'](.*?)["\'])',re.IGNORECASE)
	return webpage_regex.findall(html)

def normalize(seed_url, link):
	link, _ = urlparse.urldefrag(link)
	return urlparse.urljoin(seed_url, link)

#转化相对链接为绝对链接
def same_domain(url1, url2):
	return urlparse.urlparse(url1).netloc == urlparse.urlparse(url2).netloc

#获取robots协议，得到robots协议中禁止爬取的网页
def get_robots(url):
	rp = robotparser.RobotFileParser()
	rp.set_url(urlparse.urljoin(url, '/robots.txt'))
	rp.read()
	return rp



# def re_scraper(html):
# 	results = {}
# 	for field in FIELDS:
# 		results[field] = re.search('<tr id="place_%s__row">.*?<td class="w2p_fw">(.*?)</td>'% field, html).groups()[0]
# 	return results

# def bs_scraper(html):
# 	soup = BeautifulSoup(html, 'html.parser')
# 	results = {}
# 	for field in FIELDS:
# 		results[field] = soup.find('table').find('tr', id='place_%s__row' % field).find('td', class='w2p_fw').text
# 	return results

# def lxml_scraper(html):
# 	tree = lxml.html.fromstring(html)
# 	results = {}
# 	for field in FIELDS:
# 		results[field] = tree.cssslect('table > tr#place_%s__row > td.w2p_fw'% field)[0].text_content()
# 	return results

# NUM_ITERATIONS = 1000
# html = download('http://example.webscraping.com/places/view/United_Kingdom-239')
# for name, scraper in [('Regular expressions', re_scraper), ('BeautifulSoup', bs_scraper), ('Lxml', lxml_scraper)]:
# 	start = time.time()
# 	for i in range(NUM_ITERATIONS):
# 		if scraper == re_scraper:
# 			re.purge()
# 		result = scraper(html)
# 		assert(result['area'] = '244820 square kilometers')
# 	end = time.time()
# 	print("%s: %.2f seconds"%(name, end-start))
def scrape_callback(url, html):
	if re.search('/view/', url):
		tree = lxml.html.fromstring(html)
		row = [tree.cssselect('table > tr#places_%s__row > td.w2p_fw' % field)[0].content() for field in FIELDS]
		print url, row

#将抓取的网页进行处理，并保存
class ScrapeCallback:
	def __init__(self):
		self.writer = csv.writer(open('countires.csv', 'w'))
		self.fields = FIELDS
		self.writer.writerow(self.fields)

	def __call__(self, url, html):
		if re.search('/view/', url):
			tree = lxml.html.fromstring(html)
			row = []
			for field in self.fields:
				row.append(tree.cssselect('table > tr#places_{}__row > td.w2p_fw'.format(field))[0].text_content())
				self.writer.writerow(row)

link_crawler('http://example.webscraping.com/', '/(index|view)', max_depth=-1, scrape_callback = ScrapeCallback())