
from typing import Callable


class Signal[*T = *tuple[()]]:
	_listeners: list[Callable[[*T], None]]

	def __init__(self):
		self._listeners = []
	
	def connect(self, listener: Callable[[*T], None]) -> None:
		self._listeners.append(listener)

	def emit(self, *args: *T) -> None:
		for listener in self._listeners:
			listener(*args)
