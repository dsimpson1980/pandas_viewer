from PySide import QtGui, QtCore
import pandas as pd
import os

import random


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
        self.keys = args
        non_none_keys = [k for k in args if k is not None]
        QtGui.QTreeWidgetItem.__init__(self, [str(non_none_keys[-1])])


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

        self.expandToDepth(3)

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
            if isinstance(result, pd.Panel):
                # add iterations to append each slice of dataframe in turn
                pass
            else:
                result.append(obj)
        if len(result) == 1 and isinstance(result[0], pd.DataFrame):
            result = result[0]
        else:
            result = pd.DataFrame(pd.concat(result))
        #     non_none_keys = [k for k in keys_for_item if k is not None]
        #     if len(keys_for_item) == 1:
        #         # pd.Series
        #         name = keys_for_item[0]
        #         obj = self.obj[name]
        #         if isinstance(obj, pd.Series):
        #             result[name] = self.obj[name]
        #         elif isinstance(obj, pd.DataFrame):
        #             for col_name, ts in obj.iteritems():
        #                 result['%s[%s]' % (name, col_name)] = ts
        #     elif len(keys_for_item) == 2:
        #         # pd.DataFrame
        #         df_name = keys_for_item[0]
        #         df = self.obj[df_name]
        #         if len(non_none_keys) == 2:
        #             col_name = keys_for_item[1]
        #             result['%s[%s]' % (df_name, col_name)] = df[col_name]
        #         elif len(non_none_keys) == 1:
        #             for col_name, value in df.iteritems():
        #                 result['%s[%s]' % (df_name, col_name)] = df[col_name]
        #         else:
        #             raise ValueError('len of non_keys %s not covered' % len(non_none_keys))
        #     elif len(keys_for_item) == 3:
        #         # pd.Panel selection
        #         pl = self.obj[keys_for_item[0]]
        #         pl_name, mj, mi = keys_for_item
        #         if mj is None:
        #             # whole panel selection
        #             # ToDo submit bug report for doctstring pd.Panel.iteritems()
        #             for mj in pl.major_axis:
        #                 for mi in pl.minor_axis:
        #                     result['%s[:, %s, %s]' % (pl_name, mj, mi
        #                         )] = pl.ix[:, mj, mi]
        #         elif mi is None:
        #             # dataframe slice of Panel
        #             for mi in pl.minor_axis:
        #                 result['%s[:, %s, %s]' % (pl_name, mj, mi)] = pl.ix[:, mj, mi]
        #         else:
        #             # single Series slice of Panel
        #             result['%s[:, %s, %s]' % tuple(keys_for_item)] = pl.ix[:, mj, mi]
        #     else:
        #         raise ValueError('len of keys %s is not covered' % len(keys_for_item))
        # result = pd.DataFrame(result)
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

    def add_obj_to_tree(self, d):
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
                for mj in value.major_axis:
                    twig = PandasTreeWidgetItem(key, mj)
                    base.addChild(twig)
                    for mi in value.minor_axis:
                        leaf = PandasTreeWidgetItem(key, mj, mi)
                        twig.addChild(leaf)


def load_file(filepath):
    return random.RandomDataFrame()