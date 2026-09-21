
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import widgets


type PropertyDict = dict[str, PropertyValue]
type PropertyList = list[PropertyValue]
type PropertyValue = PropertyList | PropertyDict | object
type ParentItem = QTreeWidget | QTreeWidgetItem


class PropertyView(widgets.ScaledTreeWidget):
	"""This widget provides a simple way to display a tree of properties."""
	
	def __init__(self, props: PropertyList | PropertyDict | None = None):
		super().__init__()
		self.setHeaderLabels(["Field", "Value"])
		self.setAlternatingRowColors(True)

		self.setRatios([.5, .5])

		if props is not None:
			self.setProperties(props)

	def setProperties(self, props: PropertyList | PropertyDict) -> None:
		self.clear()
		if isinstance(props, list):
			self._addList(props, self)
		else:
			self._addDict(props, self)
	
	def _addList(self, props: PropertyList, parent: ParentItem) -> None:
		for i, value in enumerate(props):
			self._addProperty(parent, str(i), value)
	
	def _addDict(self, props: PropertyDict, parent: ParentItem) -> None:
		for key, value in props.items():
			self._addProperty(parent, key, value)
	
	def _addProperty(
		self, parent: ParentItem, key: str, value: PropertyValue
	) -> None:
		if isinstance(value, list):
			item = QTreeWidgetItem(parent, [key, f"# {len(value)}"])
			self._addList(value, item)
		elif isinstance(value, dict):
			item = QTreeWidgetItem(parent, [key])
			self._addDict(value, item)
		else:
			QTreeWidgetItem(parent, [key, str(value)])
