
class Signal:
	def __init__(self):
		self.listeners = []
	
	def connect(self, listener):
		self.listeners.append(listener)

	def emit(self, *args, **kwargs):
		for listener in self.listeners:
			listener(*args, **kwargs)
