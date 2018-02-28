import urllib2
import re 
import time


ua_headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
}
url = "http://top.chinaz.com/all/index.html"
def download(url=url, uesr_agent=ua_headers):
	request = urllib2.Request(url, headers= uesr_agent)
	response = urllib2.urlopen(request).read()
	return response
def crawl_rule(html):
	links = re.findall('<span class="col-gray">(.*?)</span>', html)
	return links 


url_list = []
for i in range(2, 2000):
	url1 = 'http://top.chinaz.com/all/index'
	url1 = url1 + '_'+ str(i) + '.html'
	url_list = url_list.append(url1)



if __name__ == "__main__":
	crawl_links('http://top.chinaz.com/all/index.html')