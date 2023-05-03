
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


class TextWidget(QTextEdit):
	def __init__(self, text):
		super().__init__()
		font = QFont("Monospace")
		font.setPixelSize(14)
		self.setFont(font)

		self.setText(text)
		self.setTextInteractionFlags(
			Qt.TextInteractionFlag.TextSelectableByMouse | \
			Qt.TextInteractionFlag.TextSelectableByKeyboard
		)

		self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
