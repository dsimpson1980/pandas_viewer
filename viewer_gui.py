from PySide import QtGui, QtCore
import pandas
import numpy
import sys

import matplotlib

matplotlib.rcParams['backend.qt4'] = 'PySide'

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure


class DataFrameTableView(QtGui.QTableView):

    def __init__(self, df):
        """Initiate the TableView with pandas.DataFrame df

        Parameters
        ----------
        df: pandas.DataFrame
            The DataFrame to display in the TableView

        Returns
        -------
        DataFrameTableView
        """
        QtGui.QTableView.__init__(self)
        self.resize(500, 500)
        if df is not None:
            self.set_dataframe(df)

    def set_dataframe(self, df):
        """Setter for the dataframe property

        Parameters
        ----------

        df: pandas.DataFrame
            The pandas.DataFrame to set the property
        """
        table_model = DataFrameTableModel(self, df)
        self.df = df
        self.setModel(table_model)
        self.resizeColumnsToContents()


class DataFrameTableModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, df):
        """Initiate the Table Model from a parent object, that should be a
        QtGui.QTableView and an initial pandas.DataFrame, df

        Parameters
        ----------
        parent: QtGui.QTableView
            The parent object for the the instance
        df: pandas.DataFrame
            The pandas.DataFrame used to initialise the model

        Returns
        -------
        DataFrameTableModel
        """
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.df = df

    def rowCount(self, parent):
        """Returns the length of the DataFrame property of the parent object

        Parameters
        ----------
        parent: The parent object used to extract the DataFrame to measure

        Returns
        -------
        int
        """
        return len(self.df)

    def columnCount(self, parent):
        """Returns the number of columns in the DataFrame with a plus one for
        the index column

        Parameters
        ----------
        parent: The parent object used to extract the DataFrame to measure

        Returns
        -------
        int
        """
        return len(self.df.columns) + 1

    def data(self, index, role):
        """Used to extract the data from the DataFrame for the row and column
        specified in the index

        Parameters
        ----------
        index: QtCore.QModelIndex
            The index object to use to lookup data in the DataFrame
        role: int

        Returns
        -------
        str
        """
        if not index.isValid() or role != QtCore.Qt.DisplayRole:
            value = None
        else:
            col, row = index.column(), index.row()
            if col == 0:
                value = self.df.index[row].strftime('%d-%b-%y %H:%M')
            else:
                value = str(self.df.iloc[row, col-1])
        return value

    def headerData(self, idx, orientation, role):
        """Returns the column name of the dataframe at idx or 'Timestamp' if the
         idx = 0

        idx: int
            The integer index of the column header, 0 indicates the index
        orientation: QtCore.Qt.Orientation
            Indicates the orientation of the object, either QtCore.Qt.Horizontal
            or QtCore.Qt.Vertical
        role: int

        Returns
        -------
        str
        """
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            value = 'Timestamp' if idx == 0 else self.df.columns[idx-1]
        else:
            value = None
        return value


class DataFramePlotWidget(QtGui.QWidget):
    """QWidget to hold a matplotlib plot of the pandas.DataFrame

    """
    def __init__(self, df=None):
        """Initiates the figure, canvas, toolbar and subplot necessary for
        plotting the dataframe

        Parameters
        ----------
        df: pandas.DataFrame, optional
            The dataframe used to initialise the plot, defaults to None

        Returns
        -------
        DataFramePlotWidget
        """
        QtGui.QWidget.__init__(self)
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addWidget(self.toolbar)
        self.vbox.addWidget(self.canvas)

        self.setLayout(self.vbox)
        self.subplot = self.fig.add_subplot(111)
        self.legend = self.subplot.legend([])
        self.set_dataframe(df)

    def set_dataframe(self, dataframe):
        """Set the pandas.DataFrame for the widget and plot it on the subplot

        Parameters
        ----------
        dataframe: pandas.DataFrame
            The dataframe to plot
        """
        self.dataframe = dataframe
        if dataframe is not None:
            self.subplot.clear()
            self.subplot.plot_date(dataframe.index, dataframe.values, '-')
            legend = self.subplot.legend(self.dataframe.columns)
            legend.set_visible(self.legend.get_visible())
            self.legend = legend

    def draw(self):
        """Draw the Canvas for the plot Figure"""
        self.canvas.draw()


class PandasTreeWidgetItem(QtGui.QTreeWidgetItem):
    """Basic node of a tree widget"""

    def __init__(self, keys):
        """Initiate the leaf with the non-None keys

        Parameters
        ----------
        keys: list(str)
            The names for the

        Returns
        -------
        PandasTreeWidgetItem
        """
        self.keys = [k for k in keys if k is not None]
        QtGui.QTreeWidgetItem.__init__(self, [str(self.keys[-1])])


class PandasTreeWidget(QtGui.QTreeWidget):
    """Widget used to expand the columns of the dataframe for selection

    """

    selection_made = QtCore.Signal((pandas.DataFrame, ))

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
        for key, value in obj.items():
            leaf = PandasTreeWidgetItem((key, None))
            root.addChild(leaf)
            if isinstance(value, pandas.DataFrame):
                root.addChild(leaf)
                for column in value.columns:
                    sub_node = PandasTreeWidgetItem([key, column])
                    leaf.addChild(sub_node)
        self.expandToDepth(3)

    def selectionChanged(self, selected, deselected):

        result = {}
        for item in self.selectedItems():
            keys_for_item = item.keys
            non_none_keys = [k for k in keys_for_item if k is not None]
            if len(keys_for_item) == 1:
                # pandas.Series
                name = keys_for_item[0]
                obj = self.obj[name]
                if isinstance(obj, pandas.Series):
                    result[name] = self.obj[name]
                elif isinstance(obj, pandas.DataFrame):
                    for col_name, ts in obj.iteritems():
                        result['%s[%s]' % (name, col_name)] = ts
            elif len(keys_for_item) == 2:
                # pandas.DataFrame
                df_name = keys_for_item[0]
                df = self.obj[df_name]
                if len(non_none_keys) == 2:
                    col_name = keys_for_item[1]
                    result['%s[%s]' % (df_name, col_name)] = df[col_name]
                elif len(non_none_keys) == 1:
                    for col_name, value in df.iteritems():
                        result['%s[%s]' % (df_name, col_name)] = df[col_name]
                else:
                    raise ValueError('len of non_keys %s not covered' % len(non_none_keys))
            else:
                raise ValueError('len of keys %s is not covered' % len(keys_for_item))
        result = pandas.DataFrame(result)
        self.selection_made.emit(result)


class PandasViewer(QtGui.QMainWindow):
    """Main window for the GUI"""

    def __init__(self, obj):
        """

        Parameters
        ----------
        obj: pandas.Series, pandas.DataFrame, pandas.Panel, dict
            The obj to iterate through to allow selection

        Returns
        -------
        PandasViewer

        Examples
        --------
        >>> timestamps = pandas.date_range('1-Apr-14', '30-Apr-14')
        >>> dataframe = pandas.DataFrame(numpy.random.rand(len(timestamps), 2), index=timestamps)
        >>> app = QtGui.QApplication(sys.argv)
        >>> PandasViewer(dataframe) #doctest: +ELLIPSIS
        <viewer_gui.PandasViewer object at ...>
        """
        QtGui.QMainWindow.__init__(self)
        if isinstance(obj, (pandas.Series, pandas.DataFrame, pandas.Panel)):
            obj = {str(type(obj)): obj}
        window = QtGui.QWidget()
        self.setCentralWidget(window)
        main_layout = QtGui.QVBoxLayout()
        window.setLayout(main_layout)
        splitter = QtGui.QSplitter(QtCore.Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = QtGui.QWidget()
        left_layout = QtGui.QVBoxLayout()
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        self.tree_widget = PandasTreeWidget(self, obj=obj)
        self.tree_widget.selection_made.connect(self.dataframe_changed)
        left_layout.addWidget(self.tree_widget)
        self.df_viewer = DataFrameTableView(None)
        left_layout.addWidget(self.df_viewer)

        self.df_plot_viewer = DataFramePlotWidget()
        splitter.addWidget(self.df_plot_viewer)

        self.dataframe = obj[obj.keys()[0]]
        self.dataframe_changed(self.dataframe)
        self.init_menu()

    def dataframe_changed(self, df):
        """Set the dataframe in the dataframe viewer to df

        Parameters
        ----------
        df: pandas.DataFrame
            The dataframe to set
        """
        self.df_viewer.set_dataframe(df)
        self.df_plot_viewer.set_dataframe(df)
        self.df_plot_viewer.draw()

    def init_menu(self):
        """Initiate the drop down menus for the window

        Parameters
        ----------
        window: QtGui.QMainWindow
            The window to add the menubar to
        """
        menubar = QtGui.QMenuBar(self)
        action_menu = QtGui.QMenu('Actions')
        menubar.addMenu(action_menu)
        action_menu.addAction('Open File')
        style_menu = QtGui.QMenu('Style')
        menubar.addMenu(style_menu)
        self.freq_submenu = QtGui.QMenu('Freq')
        self.mapper = QtCore.QSignalMapper(self)
        for freq in ['D', 'H', 'T']:
            action = QtGui.QAction(freq, self, checkable=True)
            self.mapper.setMapping(action, freq)
            action.triggered.connect(self.mapper.map)
            self.freq_submenu.addAction(action)
        self.mapper.mapped['QString'].connect(self.change_freq)
        style_menu.addMenu(self.freq_submenu)
        self.legend_action = QtGui.QAction(
            'Legend', style_menu, checkable=True, checked=True)
        self.legend_action.triggered.connect(self.change_legend)
        style_menu.addAction(self.legend_action)

    def change_freq(self, freq):
        """Resample the original pandas.DataFrame to frequency freq

        Parameters
        ----------
        freq: str
            The frequency to resample the dataframe to
        """
        for action in self.freq_submenu.actions():
            action.setChecked(action.text() == freq)
        self.dataframe_changed(self.dataframe.resample(freq))

    def change_legend(self):
        """Set the visibility of the subplot legend to match the checked status
        of the submenu item.  The submenu item is checkable and as such changes
        state automatically when clicked
        """
        self.df_plot_viewer.legend.set_visible(self.legend_action.isChecked())
        self.df_plot_viewer.draw()


def main():
    """Main method for the app"""
    app = QtGui.QApplication(sys.argv)
    #ToDo this is just a random dataframe for testing
    timestamps = pandas.date_range('1-Apr-14', '30-Apr-14', freq='H')
    dataframe = pandas.DataFrame(
        numpy.random.rand(len(timestamps), 2), index=timestamps)
    pandas_viewer = PandasViewer(dataframe)
    pandas_viewer.show()
    app.exec_()

if __name__ == '__main__':
    main()