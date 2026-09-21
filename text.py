
"""Provides a widget that displays raw text using a monospace font."""


from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


class TextWidget(QTextEdit):
	def __init__(self, text: str):
		super().__init__()
		font = QFont("Monospace")
		font.setPixelSize(14)
		self.setFont(font)

		self.setText(text)
		self.setTextInteractionFlags(
			Qt.TextInteractionFlag.TextSelectableByMouse | \
			Qt.TextInteractionFlag.TextSelectableByKeyboard
		)

		tabsize = QFontMetricsF(font).horizontalAdvance(" ") * 4
		self.setTabStopDistance(tabsize)

		self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
