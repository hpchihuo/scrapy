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

