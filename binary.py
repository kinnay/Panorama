
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import html
import signals
import string


PRINTABLE = string.ascii_letters + string.digits + string.punctuation + " "

def formatChar(byte: int) -> str:
	"""
	Returns the character that is shown in the ascii view for a given byte.
	"""
	char = chr(byte)
	if char in PRINTABLE:
		return html.escape(char)
	return "."


class TextStream:
	_text: str
	_color: str | None
	_bgcolor: str | None

	def __init__(self):
		self._text = ""
		self._color = None
		self._bgcolor = None
		
	def setColor(self, color: str | None) -> None:
		if color != self._color:
			if self._color or self._bgcolor:
				self._text += "</span>"
			if color or self._bgcolor:
				self._text += f"<span style='color: {color}; " \
					f"background-color: {self._bgcolor}'>"
			self._color = color
	
	def setBackground(self, color: str | None) -> None:
		if color != self._bgcolor:
			if self._color or self._bgcolor:
				self._text += "</span>"
			if color or self._color:
				self._text += f"<span style='color: {self._color}; " \
					f"background-color: {color}'>"
			self._bgcolor = color
	
	def write(self, text: str) -> None:
		self._text += text.replace("\n", "<br>").replace(" ", "&nbsp;")
		
	def get(self) -> str:
		if self._color or self._bgcolor:
			self._text += "</span>"
			self._color = None
			self._bgcolor = None
		return self._text


class BinaryView(QTextEdit):
	viewChanged: signals.Signal
	"""Emitted when the size of the view changes."""

	wheel: signals.Signal[QWheelEvent]
	"""Emitted when a scroll wheel event occurs on the view."""

	scrollRequest: signals.Signal[int]
	"""
	Emitted when the view should scroll by the given number of rows, either due
	to mouse of keyboard events.
	"""

	jump: signals.Signal[int]
	"""Emitted when the view should jump to the given offset in the file."""

	_data: bytes
	"""Content of the file that is shown in the binary view."""

	_base: int
	"""Current base address of the view."""

	_rows: int
	"""Number of rows that are currently displayed."""

	_end: int
	"""End address of the range that is currently displayed."""

	_cursorAddr: int
	"""Address of the cursor."""

	_cursorOffset: int
	"""Position of the cursor in the current byte."""

	_cursorAscii: bool
	"""Whether the cursor is active in the hex or ascii view."""

	_selectionAnchor: int
	"""The address at which the user began making a selection."""

	_selectionStart: int
	"""The lowest address of the selection."""

	_selectionEnd: int
	"""The highest address of the selection."""

	_selectionAscii: bool
	"""Whether the user is making a selection in the hex or ascii view."""

	_mousePos: int
	"""
	Current position of the mouse relative to the top of the view, while the
	user is dragging a selection. This is used to determine how fast the view
	should scroll when the user moves the mouse outside of the view.
	"""

	_timer: QTimer
	"""
	Timer that periodically scrolls the view while the user drags a selection
	outside of the view.
	"""

	def __init__(self, data: bytes):
		super().__init__()
		self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.verticalScrollBar().valueChanged.connect(self._resetScroll)

		self._data = data

		self.viewChanged = signals.Signal()
		self.wheel = signals.Signal()
		self.scrollRequest = signals.Signal()
		self.jump = signals.Signal()

		self._base = 0
		self._rows = 0
		self._end = 0

		self._cursorAddr = 0
		self._cursorOffset = 0
		self._cursorAscii = False

		self._selectionAnchor = 0
		self._selectionStart = 0
		self._selectionEnd = 0
		self._selectionAscii = False

		self._mousePos = 0

		self._timer = QTimer()
		self._timer.timeout.connect(self._updateScroll)
		self._timer.setInterval(50)
		self._timer.start()
	
	def setRange(self, offset: int, rows: int) -> None:
		self._base = offset
		self._rows = rows
		self._end = min(offset + rows * 16, len(self._data) + 1)
		self._updateText()

	def resizeEvent(self, e: QResizeEvent) -> None:
		super().resizeEvent(e)
		self.viewChanged.emit()

	def wheelEvent(self, e: QWheelEvent) -> None:
		self.wheel.emit(e)

	def contextMenuEvent(self, e: QContextMenuEvent) -> None:
		"""
		Disables the context menu. We might implement a custom context menu
		later.
		"""

	def keyPressEvent(self, e: QKeyEvent) -> None:
		self._handleKeyPress(e)
		self._updateText()
	
	def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
		self.mousePressEvent(e)

	def mousePressEvent(self, e: QMouseEvent) -> None:
		if e.button() == Qt.MouseButton.LeftButton:
			cursor = self.cursorForPosition(e.pos())
			self._cursorAddr, self._cursorOffset, self._cursorAscii = \
				self._getCursorInfo(cursor.position())
			
			self._clampCursor()
			
			self._selectionAnchor = self._selectionAddr(
				self._cursorAddr, self._cursorOffset, self._cursorAscii
			)
			self._selectionStart = self._selectionAnchor
			self._selectionEnd = self._selectionAnchor
			self._selectionAscii = self._cursorAscii
			
			self._updateText()

	def mouseMoveEvent(self, e):
		if e.buttons() & Qt.MouseButton.LeftButton:
			self._mousePos = e.y()
			
			cursor = self.cursorForPosition(e.pos())
			self._cursorAddr, self._cursorOffset, self._cursorAscii = \
				self._getCursorInfo(cursor.position(), self._cursorAscii)
			
			self._clampCursor()
			
			selectionPos = self._selectionAddr(
				self._cursorAddr, self._cursorOffset, self._cursorAscii
			)
			self._moveSelectionTo(selectionPos)
			
			self._updateText()

	def mouseReleaseEvent(self, e):
		if e.button() == Qt.MouseButton.LeftButton:
			self._mousePos = 0
	
	def _resetScroll(self) -> None:
		"""Disables functionality of the scroll bar."""
		self.verticalScrollBar().setValue(0)

	def _updateScroll(self) -> None:
		"""
		Called every 50 milliseconds. This scrolls the view while the user drags
		a selection outside of the view.
		"""

		if self._mousePos < 0:
			self.scrollRequest.emit(self._mousePos // 10)
		elif self._mousePos > self.height():
			self.scrollRequest.emit((self._mousePos - self.height()) // 10)

	def _handleKeyPress(self, e: QKeyEvent) -> None:
		key = e.key()

		if key == Qt.Key.Key_Left:
			if self._cursorOffset != 0:
				self._cursorOffset = 0
			elif self._cursorAddr > 0:
				self._cursorAddr -= 1
		
		elif key == Qt.Key.Key_Right:
			self._cursorOffset = 0
			if self._cursorAddr < len(self._data):
				self._cursorAddr += 1
		
		elif key == Qt.Key.Key_Up:
			if self._cursorAddr >= 16:
				self._cursorAddr -= 16
		
		elif key == Qt.Key.Key_Down:
			if self._cursorAddr <= len(self._data) - 16:
				self._cursorAddr += 16
		
		elif key == Qt.Key.Key_PageUp:
			maxRows = self._cursorAddr // 16
			self._cursorAddr -= min(maxRows, self._rows) * 16
			self.scrollRequest.emit(-self._rows)
		
		elif key == Qt.Key.Key_PageDown:
			maxRows = (len(self._data) - self._cursorAddr) // 16
			self._cursorAddr += min(maxRows, self._rows) * 16
			self.scrollRequest.emit(self._rows)
		
		elif key == Qt.Key.Key_Home:
			self._cursorAddr &= ~15
			self._cursorOffset = 0
			
		elif key == Qt.Key.Key_End:
			self._cursorAddr = ((self._cursorAddr + 16) & ~15)
			if self._cursorAddr > len(self._data):
				self._cursorAddr = len(self._data)
			
			self._cursorOffset = 0
			if self._cursorAddr % 16 == 0 and self._cursorAddr != 0:
				self._cursorAddr -= 1
				self._cursorOffset = 2 - self._cursorAscii
		
		if key in [
			Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down,
			Qt.Key.Key_PageUp, Qt.Key.Key_PageDown, Qt.Key.Key_Home, Qt.Key.Key_End
		]:
			modifiers = e.modifiers()
			shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

			if shift:
				self._moveSelectionTo(self._cursorAddr)
			else:
				self._clearSelection()
		
		if self._cursorAddr < self._base:
			self.jump.emit(self._cursorAddr & ~0xF)
		elif self._cursorAddr >= self._end:
			addr = (self._cursorAddr & ~0xF) - (self._rows - 1) * 16
			self.jump.emit(addr)

	def _clearSelection(self) -> None:
		"""
		Clears the selection, e.g. when the user presses an arrow key without
		holding shift.
		"""
		addr = self._selectionAddr(
			self._cursorAddr, self._cursorOffset, self._cursorAscii
		)
		self._selectionAnchor = addr
		self._selectionStart = addr
		self._selectionEnd = addr
	
	def _moveSelectionTo(self, addr):
		if addr < self._selectionAnchor:
			self._selectionStart = addr
			self._selectionEnd = self._selectionAnchor
		else:
			self._selectionStart = self._selectionAnchor
			self._selectionEnd = addr

	def _selectionAddr(self, pos, offset, view):
		if pos % 16 == 15:
			if view and offset:
				return pos + 1
			return pos + (offset == 2)
		return pos

	def _clampCursor(self):
		if self._cursorAddr > len(self._data):
			self._cursorAddr = len(self._data)
		
		if self._cursorAddr == len(self._data):
			self._cursorOffset = 0
			if self._cursorAddr % 16 == 0 and self._cursorAddr != 0:
				self._cursorAddr -= 1
				if self._cursorAscii:
					self._cursorOffset = 1
				else:
					self._cursorOffset = 2

	def _getCursorInfo(
		self, pos: int, ascii: bool | None = None
	) -> tuple[int, int, bool]:
		"""
		From the given cursor position in the text, computes the address of the
		byte under the cursor, the location of the cursor within that byte, and
		whether the cursor is in the hex or ascii view.

		If the ascii parameter is provided and not None, it forces the cursor to
		be either in the hex or ascii view.
		"""
		
		row = max(pos // 76, 2)
		col = max(pos % 76, 10)
		
		if ascii is not None:
			if ascii:
				col = max(col, 59)
			else:
				col = min(col, 57)
		
		base = self._base + (row - 2) * 16
		if col < 57:
			return base + (col - 9) // 3, col % 3 == 2, False
		if col == 57:
			return base + 15, 2, False
		if col == 58:
			return base, 0, True
		if col < 75:
			return base + col - 59, 0, True
		return base + 15, 1, True

	def _getCursorPos(self, addr: int, offset: int, ascii: bool) -> int:
		"""
		Computes the position for a cursor in the text that corresponds to the
		given byte address, cursor offset within that byte, and view.
		"""
		row = 76 * ((addr - self._base) // 16 + 2)
		if ascii:
			return row + 59 + addr % 16 + offset
		return row + 10 + 3 * (addr % 16) + offset

	def _updateCursor(self) -> None:
		if self._cursorAddr >= self._base and self._cursorAddr < self._end:
			pos = self._getCursorPos(self._cursorAddr, self._cursorOffset, self._cursorAscii)
			
			cursor = QTextCursor(self.document())
			cursor.setPosition(pos)
			self.setTextCursor(cursor)
		else:
			self.setTextCursor(QTextCursor())

	def _updateColor(self, stream: TextStream, addr: int, ascii: bool) -> None:
		if not ascii and addr % 2:
			stream.setColor("gray")
		else:
			stream.setColor(None)
		
		if self._selectionStart <= addr < self._selectionEnd:
			if ascii == self._selectionAscii:
				stream.setBackground("blue")
			else:
				stream.setBackground("lightblue")
			stream.setColor("white")
		else:
			stream.setBackground(None)

	def _updateText(self) -> None:
		stream = TextStream()
		stream.setColor("blue")
		stream.write("Binary    ")
		stream.write("00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F")
		stream.write("  ")
		stream.write("0123456789ABCDEF\n")
		stream.write(" " * 75 + "\n")
		
		addr = self._base
		data = self._data[self._base : self._end]
		while data:
			stream.setColor("blue")
			stream.write(f"{addr:08X} ")
			
			for i in range(min(len(data), 16)):
				stream.write(" ")
				self._updateColor(stream, addr + i, False)
				stream.write(f"{data[i]:02X}")
			
			stream.setColor(None)
			stream.setBackground(None)
			stream.write(" " * (2 + (15 - i) * 3))
			
			for i, byte in enumerate(data[:16]):
				self._updateColor(stream, addr + i, True)
				stream.write(formatChar(byte))
			
			stream.setColor(None)
			stream.setBackground(None)
			stream.write("\n")
			
			data = data[16:]
			addr += 16
		
		if not self._data:
			stream.setColor("blue")
			stream.write("00000000 " + " " * 50)
		
		self.setText(stream.get())
		
		self._updateCursor()


class BinaryWidget(QWidget):
	_scrollBar: QScrollBar
	_font: QFont
	_metrics: QFontMetrics
	_view: BinaryView
	_layout: QHBoxLayout

	def __init__(self, data):
		super().__init__()
		self._data = data
			
		self._scrollBar = QScrollBar()
		self._scrollBar.setRange(0, len(data) // 16)
		self._scrollBar.valueChanged.connect(self._updateView)

		self._font = QFont("Monospace")
		self._font.setPixelSize(14)
		self.setFont(self._font)

		self._metrics = QFontMetrics(self._font)

		width = self._metrics.boundingRect("_" * 75).width() + 10

		self._view = BinaryView(data)
		self._view.setMinimumWidth(width)
		self._view.viewChanged.connect(self._updateView)
		self._view.wheel.connect(self._scrollBar.wheelEvent)
		self._view.scrollRequest.connect(self._moveScroll)
		self._view.jump.connect(self._handleJump)

		self._layout = QHBoxLayout(self)
		self._layout.addWidget(self._view)
		self._layout.addWidget(self._scrollBar)

		self._updateView()
	
	def _moveScroll(self, offset: int) -> None:
		self._scrollBar.setValue(self._scrollBar.value() + offset)
		self._updateView()

	def _handleJump(self, address: int) -> None:
		rows = int(
			(self._view.height() - 10) / (self._metrics.lineSpacing() + 1)
		)
		rows -= 2

		self._view.setRange(address, rows)

		scroll = max((len(self._data) + 15) // 16 - rows, 0)
		self._scrollBar.setVisible(scroll != 0)
		self._scrollBar.setRange(0, scroll)

	def _updateView(self) -> None:
		offset = self._scrollBar.value() * 16
		self._handleJump(offset)
