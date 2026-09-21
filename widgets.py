
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


class ScaledTreeWidget(QTreeWidget):
	"""Tree widget that supports fixed scaling ratios for each column."""

	def __init__(self):
		super().__init__()

		font = QFont("Monospace")
		font.setPixelSize(14)
		self.setFont(font)
	
	def setRatios(self, ratios: list[float]) -> None:
		width = self.width()
		total = sum(ratios)
		for i, ratio in enumerate(ratios):
			self.setColumnWidth(i, int(width * ratio / total))
