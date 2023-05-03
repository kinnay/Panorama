
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import html
import signals
import string


PRINTABLE = string.ascii_letters + string.digits + string.punctuation + " "

def formatChar(byte):
	"""Returns the character that is shown in the ascii view for a given byte."""
	char = chr(byte)
	if char in PRINTABLE:
		return html.escape(char)
	return "."


class TextStream:
	def __init__(self):
		self.text = ""
		self.color = None
		self.bgcolor = None
		
	def setColor(self, color):
		if color != self.color:
			if self.color or self.bgcolor:
				self.text += "</span>"
			if color or self.bgcolor:
				self.text += "<span style='color: %s; background-color: %s'>" %(color, self.bgcolor)
			self.color = color
	
	def setBackground(self, color):
		if color != self.bgcolor:
			if self.color or self.bgcolor:
				self.text += "</span>"
			if color or self.color:
				self.text += "<span style='color: %s; background-color: %s'>" %(self.color, color)
			self.bgcolor = color
	
	def write(self, text):
		self.text += text.replace("\n", "<br>").replace(" ", "&nbsp;")
		
	def get(self):
		if self.color or self.bgcolor:
			self.text += "</span>"
			self.color = None
			self.bgcolor = None
		return self.text


class BinaryView(QTextEdit):
	def __init__(self, data):
		super().__init__()
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.verticalScrollBar().valueChanged.connect(self.resetScroll)

		self.viewChanged = signals.Signal()
		self.wheel = signals.Signal()
		self.scroll = signals.Signal()

		self.data = data

		self.base = 0
		self.end = 0

		self.cursorAddr = 0
		self.cursorOffset = 0
		self.cursorAscii = False

		self.selectionAnchor = 0
		self.selectionStart = 0
		self.selectionEnd = 0
		self.selectionAscii = False

		self.mousePos = 0

		self.timer = QTimer()
		self.timer.timeout.connect(self.updateScroll)
		self.timer.setInterval(50)
		self.timer.start()

	def resizeEvent(self, e):
		super().resizeEvent(e)
		self.viewChanged.emit()

	def resetScroll(self):
		self.verticalScrollBar().setValue(0)

	def updateScroll(self):
		if self.mousePos < 0:
			self.scroll.emit(self.mousePos // 10)
		elif self.mousePos > self.height():
			self.scroll.emit((self.mousePos - self.height()) // 10)

	def wheelEvent(self, e):
		self.wheel.emit(e)

	def contextMenuEvent(self, e):
		pass

	def keyPressEvent(self, e):
		self.handleKeyPress(e)
		self.updateText()

	def handleKeyPress(self, e):
		if e.key() == Qt.Key_Left:
			if self.cursorOffset != 0:
				self.cursorOffset = 0
			elif self.cursorAddr > 0:
				self.cursorAddr -= 1
			self.clearSelection()
		
		elif e.key() == Qt.Key_Right:
			self.cursorOffset = 0
			if self.cursorAddr < len(self.data):
				self.cursorAddr += 1
			self.clearSelection()
		
		elif e.key() == Qt.Key_Up:
			if self.cursorAddr >= 16:
				self.cursorAddr -= 16
			self.clearSelection()
		
		elif e.key() == Qt.Key_Down:
			if self.cursorAddr <= len(self.data) - 16:
				self.cursorAddr += 16
			self.clearSelection()
		
		elif e.key() == Qt.Key_Home:
			self.cursorAddr &= ~15
			self.cursorOffset = 0
			self.clearSelection()
			
		elif e.key() == Qt.Key_End:
			self.cursorAddr = ((self.cursorAddr + 16) & ~15)
			if self.cursorAddr > len(self.data):
				self.cursorAddr = len(self.data)
			
			self.cursorOffset = 0
			if self.cursorAddr % 16 == 0 and self.cursorAddr != 0:
				self.cursorAddr -= 1
				self.cursorOffset = 2 - self.cursorView
			
			self.clearSelection()

	def clearSelection(self):
		addr = self.selectionAddr(self.cursorAddr, self.cursorOffset, self.cursorView)
		self.selectionAnchor = addr
		self.selectionStart = addr
		self.selectionEnd = addr

	def mouseDoubleClickEvent(self, e):
		self.mousePressEvent(e)

	def mousePressEvent(self, e):
		if e.button() == Qt.LeftButton:
			cursor = self.cursorForPosition(e.pos())
			self.cursorAddr, self.cursorOffset, self.cursorView = \
				self.getCursorInfo(cursor.position())
			
			self.clampCursor()
			
			self.selectionAnchor = self.selectionAddr(
				self.cursorAddr, self.cursorOffset, self.cursorView
			)
			self.selectionStart = self.selectionAnchor
			self.selectionEnd = self.selectionAnchor
			self.selectionView = self.cursorView
			
			self.updateText()

	def mouseMoveEvent(self, e):
		if e.buttons() & Qt.LeftButton:
			self.mousePos = e.y()
			
			cursor = self.cursorForPosition(e.pos())
			self.cursorAddr, self.cursorOffset, self.cursorView = \
				self.getCursorInfo(cursor.position(), self.cursorView)
			
			self.clampCursor()
			
			selectionPos = self.selectionAddr(
				self.cursorAddr, self.cursorOffset, self.cursorView
			)
			
			if selectionPos < self.selectionAnchor:
				self.selectionStart = selectionPos
				self.selectionEnd = self.selectionAnchor
			else:
				self.selectionStart = self.selectionAnchor
				self.selectionEnd = selectionPos
			
			self.updateText()

	def mouseReleaseEvent(self, e):
		if e.button() == Qt.LeftButton:
			self.mousePos = 0

	def selectionAddr(self, pos, offset, view):
		if pos % 16 == 15:
			if view and offset:
				return pos + 1
			return pos + (offset == 2)
		return pos

	def clampCursor(self):
		if self.cursorAddr > len(self.data):
			self.cursorAddr = len(self.data)
		
		if self.cursorAddr == len(self.data):
			self.cursorOffset = 0
			if self.cursorAddr % 16 == 0 and self.cursorAddr != 0:
				self.cursorAddr -= 1
				if self.cursorView:
					self.cursorOffset = 1
				else:
					self.cursorOffset = 2

	def getCursorInfo(self, pos, view=None):
		row = max(pos // 76, 2)
		col = max(pos % 76, 10)
		
		if view is not None:
			if view:
				col = max(col, 59)
			else:
				col = min(col, 57)
		
		base = self.base + (row - 2) * 16
		if col < 57:
			return base + (col - 9) // 3, col % 3 == 2, False
		if col == 57:
			return base + 15, 2, False
		if col == 58:
			return base, 0, True
		if col < 75:
			return base + col - 59, 0, True
		return base + 15, 1, True

	def getCursorPos(self, addr, offset, ascii):
		row = 76 * ((addr - self.base) // 16 + 2)
		if ascii:
			return row + 59 + addr % 16 + offset
		return row + 10 + 3 * (addr % 16) + offset

	def updateCursor(self):
		if self.cursorAddr >= self.base and self.cursorAddr < self.end:
			pos = self.getCursorPos(self.cursorAddr, self.cursorOffset, self.cursorAscii)
			
			cursor = QTextCursor(self.document())
			cursor.setPosition(pos)
			self.setTextCursor(cursor)
		else:
			self.setTextCursor(QTextCursor())

	def updateColor(self, stream, addr, ascii):
		if not ascii and addr % 2:
			stream.setColor("gray")
		else:
			stream.setColor(None)
		
		if self.selectionStart <= addr < self.selectionEnd:
			if ascii == self.selectionAscii:
				stream.setBackground("blue")
			else:
				stream.setBackground("lightblue")
			stream.setColor("white")
		else:
			stream.setBackground(None)

	def updateText(self):
		stream = TextStream()
		stream.setColor("blue")
		stream.write("Binary    ")
		stream.write("00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F")
		stream.write("  ")
		stream.write("0123456789ABCDEF\n")
		stream.write(" " * 75 + "\n")
		
		addr = self.base
		data = self.data[self.base : self.end]
		while data:
			stream.setColor("blue")
			stream.write("%08X " %addr)
			
			for i in range(min(len(data), 16)):
				stream.write(" ")
				self.updateColor(stream, addr + i, False)
				stream.write("%02X" %data[i])
			
			stream.setColor(None)
			stream.setBackground(None)
			stream.write(" " * (2 + (15 - i) * 3))
			
			for i, byte in enumerate(data[:16]):
				self.updateColor(stream, addr + i, True)
				stream.write(formatChar(byte))
			
			stream.setColor(None)
			stream.setBackground(None)
			stream.write("\n")
			
			data = data[16:]
			addr += 16
		
		if not self.data:
			stream.setColor("blue")
			stream.write("00000000 " + " " * 50)
		
		self.setText(stream.get())
		
		self.updateCursor()
	
	def setRange(self, offset, rows):
		self.base = offset
		self.end = min(offset + rows * 16, len(self.data) + 1)
		self.updateText()


class BinaryWidget(QWidget):
	def __init__(self, data):
		super().__init__()
		self.data = data
			
		self.scrollBar = QScrollBar()
		self.scrollBar.setRange(0, len(data) // 16)
		self.scrollBar.valueChanged.connect(self.updateView)

		self.font = QFont("Monospace")
		self.font.setPixelSize(14)
		self.setFont(self.font)

		self.metrics = QFontMetrics(self.font)

		width = self.metrics.boundingRect("_" * 75).width() + 10

		self.view = BinaryView(data)
		self.view.setMinimumWidth(width)
		self.view.viewChanged.connect(self.updateView)
		self.view.wheel.connect(self.scrollBar.wheelEvent)
		self.view.scroll.connect(self.moveScroll)

		self.layout = QHBoxLayout(self)
		self.layout.addWidget(self.view)
		self.layout.addWidget(self.scrollBar)

		self.updateView()
	
	def moveScroll(self, offset):
		self.scrollBar.setValue(self.scrollBar.value() + offset)

	def updateView(self):
		offset = self.scrollBar.value() * 16
		rows = int((self.view.height() - 10) / (self.metrics.lineSpacing() + 1)) - 2

		self.view.setRange(offset, rows)

		scroll = max((len(self.data) + 15) // 16 - rows, 0)
		self.scrollBar.setVisible(scroll != 0)
		self.scrollBar.setRange(0, scroll)
