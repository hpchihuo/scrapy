from io import BytesIO
import lxml.html
from PIL import Image
import pytesseract
import string

REGIESTER_URL = 'http://http://example.webscraping.com/places/default/user/register'

def get_captcha(html):
	tree = lxml.html.fromstring(html)
	img_data = tree.cssselect('div#recaptcha img')[0].get('src')
	img_data = img_data.partition(',')[-1]
	binary_img_data = img_data.decode('base64')
	file_like = BytesIO(binary_img_data)
	img = Image.open(file_like)
	return img


def register(first_name, last_name, email, password):
	cj= cookielib.CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	html = opener.open(REGIESTER_URL)
	form = parse_form(html)
	form['first_name'] = first_name
	form['last_name'] = last_name
	form['email'] = email
	form['password'] = form['password_two'] = password
	img = extract_image(html)
	captcha = ocr(img)
	form['recaptcha_response_field'] = captcha
	encoded_data = urllib.urlencode(form)
	request = urllib2.Request(REGIESTER_URL, encoded_data)
	response = opener.open(request)
	success = '/user/register' not in response.geturl()
	return success

def ocr(img):
	gray = img.convert('L')
	bw = gray.point(lambda x: 0 if x < 1 else 255, '1')
	word =pytesseract.image_to_string(bw)
	ascii_word = ''.join(c for c in word if c in string.letters).lower()
	return ascii_word

def parse_form(html):
	tree = lxml.html.fromstring(html)
	data = {}
	for e in tree.cssselect('form input'):
		if e.get('name'):
			data[e.get('name')] = e.get('value')
	return data

register("he", "pan", "hepan@chinatian.com", 'hepandefeng')