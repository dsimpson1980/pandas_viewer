from PySide import QtGui, QtCore
import pandas as pd
import os
from functools import partial

import pickling


class PandasTreeWidgetItem(QtGui.QTreeWidgetItem):
    """Basic node of a tree widget"""

    def __init__(self, *args):
        """Initiate the leaf with the non-None keys

        Parameters
        ----------
        keys: list(str)
            The names for the

        Returns
        -------
        PandasTreeWidgetItem
        """
        super(PandasTreeWidgetItem, self).__init__([str(args[-1])])
        self.keys = args


class PandasTreeWidget(QtGui.QTreeWidget):
    """Widget used to expand the columns of the dataframe for selection

    """

    selection_made = QtCore.Signal((pd.DataFrame, ))

    def __init__(self, parent=None, obj=None):
        """Initiate the tree structure with the obj

        Parameters
        ----------
        parent: object
            The parent for the tree, should be the mainwindow for the gui
        obj: object
            The object to expand and display in the tree structure

        Returns
        -------
        PandasTreeWidget
        """
        QtGui.QTreeWidget.__init__(self, parent)
        self.setDragEnabled(True)
        self.setDragDropMode(self.DropOnly)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setColumnCount(1)
        self.setHeaderLabels(['Pandas Variables'])
        self.set_tree(obj)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

    def set_tree(self, obj):
        """Iterate through the object, obj, levels and set the nodes in the tree

        Parameters
        ----------
        obj: object, iterable
            The object to iterate through
        """
        self.clear()
        self.obj = obj
        root = self.invisibleRootItem()
        idx = obj.items()
        idx.sort()
        for key, value in idx:
            if isinstance(value, pd.Series):
                leaf = PandasTreeWidgetItem(key)
                root.addChild(leaf)
            if isinstance(value, pd.DataFrame):
                twig = PandasTreeWidgetItem(key, None)
                root.addChild(twig)
                for column in value.columns:
                    leaf = PandasTreeWidgetItem(key, column)
                    twig.addChild(leaf)
            if isinstance(value, pd.Panel):
                branch = PandasTreeWidgetItem(key, None, None)
                root.addChild(branch)
                for mj in value.major_axis:
                    twig = PandasTreeWidgetItem(key, mj, None)
                    branch.addChild(twig)
                    for mi in value.minor_axis:
                        leaf = PandasTreeWidgetItem(key, mj, mi)
                        twig.addChild(leaf)

    def selectionChanged(self, selected, deselected):
        """Construct a DataFrame from selections in the tree and pass to
        dataframe_changed to populate the table widget and pass to the plot.

        A signal is emitted to instigate dataframe_changed

        Parameters
        ----------
        selected: list(PandasTreeWidgetItem)
            List of WidgetItems selected
        deselected: list(PandasTreeWidgetItem)
            List of WidgetItems deselected
        """
        result = []
        for item in self.selectedItems():
            obj = reduce(lambda x, y: x.get(y), (self.obj,) + item.keys)
            if isinstance(obj, pd.Panel):
                for itm in obj.items:
                    df = obj.get(itm)
                    result.append(df)
            else:
                result.append(obj)
        if len(result) == 1 and isinstance(result[0], pd.DataFrame):
            result = result[0]
        else:
            result = pd.DataFrame(pd.concat(result, axis=1))
        self.selection_made.emit(result)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.reject()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                self.add_file_to_tree(filepath)
        else:
            event.ignore()

    def add_file_to_tree(self, filepath):
        filename = os.path.basename(filepath)
        obj = load_file(filepath)
        self.add_obj_to_tree({filename: obj})

    def add_obj_to_tree(self, d, root=None):
        if root is None:
            root = self.invisibleRootItem()
        for key, value in d.iteritems():
            self.obj[key] = value
            base = PandasTreeWidgetItem(key)
            root.addChild(base)
            if isinstance(value, pd.DataFrame):
                for column in value.columns:
                    leaf = PandasTreeWidgetItem(key, column)
                    base.addChild(leaf)
            if isinstance(value, pd.Panel):
                for itm in value.items:
                    twig = PandasTreeWidgetItem(key, itm)
                    base.addChild(twig)
                    for mi in value.minor_axis:
                        leaf = PandasTreeWidgetItem(key, itm, mi)
                        twig.addChild(leaf)
            if isinstance(value, dict):
                self.add_obj_to_tree(value, base)

    def mousePressEvent(self, event):
        if event.button() is QtCore.Qt.MouseButton.RightButton:
            pos = event.pos()
            self.context_menu(pos)
        else:
            super(PandasTreeWidget, self).mousePressEvent(event)

    def context_menu(self, pos):
        item = self.itemAt(pos)
        menu = QtGui.QMenu()
        remove = QtGui.QAction('Remove', menu)
        remove.triggered.connect(partial(self.remove_item, item))
        menu.addAction(remove)
        menu.exec_(self.viewport().mapToGlobal(pos))

    def remove_item(self, item):
        keys = item.keys
        parent = item.parent()
        if parent is None:
            parent = self.invisibleRootItem()
        parent.removeChild(item)
        obj = reduce(lambda x, y: x.get(y), (self.obj,) + keys[:-1])
        obj.pop(keys[-1])
        if parent.childCount() == 0 and parent is not self.invisibleRootItem():
            self.remove_item(parent)
        print 'Done'

def load_file(filepath):
    filename, ext = os.path.splitext(filepath)
    if ext == '.csv':
        obj = pd.read_csv(filepath)
    elif ext == '.pickle':
        obj = pickling.load(filepath)
    else:
        raise ValueError('file ext %s not implemented', ext)
    return obj
