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

	def click(self,patern):
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


