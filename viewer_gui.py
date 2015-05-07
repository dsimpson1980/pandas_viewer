from PySide import QtGui, QtCore
import pandas as pd
import numpy as np
import sys
import os
import h5py

import matplotlib

matplotlib.rcParams['backend.qt4'] = 'PySide'

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from simp_tools import pickling

# ToDo Add email plot icon to navigation bar
# ToDo Add email plot functionality (save png to buffer then attach to email)
# ToDo Add difference plots action
# ToDo Add difference plots functionality
# ToDo fix pyinstaller build so that menu items are shown


class DataFrameTableView(QtGui.QTableView):

    def __init__(self, df):
        """Initiate the TableView with pd.DataFrame df

        Parameters
        ----------
        df: pd.DataFrame
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

        df: pd.DataFrame
            The pd.DataFrame to set the property
        """
        table_model = DataFrameTableModel(self, df)
        self.df = df
        self.setModel(table_model)
        self.resizeColumnsToContents()


class DataFrameTableModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, df):
        """Initiate the Table Model from a parent object, that should be a
        QtGui.QTableView and an initial pd.DataFrame, df

        Parameters
        ----------
        parent: QtGui.QTableView
            The parent object for the the instance
        df: pd.DataFrame
            The pd.DataFrame used to initialise the model

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
    """QWidget to hold a matplotlib plot of the pd.DataFrame

    """
    def __init__(self, df=None):
        """Initiates the figure, canvas, toolbar and subplot necessary for
        plotting the dataframe

        Parameters
        ----------
        df: pd.DataFrame, optional
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
        """Set the pd.DataFrame for the widget and plot it on the subplot

        Parameters
        ----------
        dataframe: pd.DataFrame
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
        result = {}
        for item in self.selectedItems():
            keys_for_item = item.keys
            non_none_keys = [k for k in keys_for_item if k is not None]
            if len(keys_for_item) == 1:
                # pd.Series
                name = keys_for_item[0]
                obj = self.obj[name]
                if isinstance(obj, pd.Series):
                    result[name] = self.obj[name]
                elif isinstance(obj, pd.DataFrame):
                    for col_name, ts in obj.iteritems():
                        result['%s[%s]' % (name, col_name)] = ts
            elif len(keys_for_item) == 2:
                # pd.DataFrame
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
            elif len(keys_for_item) == 3:
                # pd.Panel selection
                pl = self.obj[keys_for_item[0]]
                pl_name, mj, mi = keys_for_item
                if mj is None:
                    # whole panel selection
                    # ToDo submit bug report for doctsring pd.Panel.iteritems()
                    for mj in pl.major_axis:
                        for mi in pl.minor_axis:
                            result['%s[:, %s, %s]' % (pl_name, mj, mi
                                )] = pl.ix[:, mj, mi]
                elif mi is None:
                    # dataframe slice of Panel
                    for mi in pl.minor_axis:
                        result['%s[:, %s, %s]' % (pl_name, mj, mi)] = pl.ix[:, mj, mi]
                else:
                    # single Series slice of Panel
                    result['%s[:, %s, %s]' % tuple(keys_for_item)] = pl.ix[:, mj, mi]
            else:
                raise ValueError('len of keys %s is not covered' % len(keys_for_item))
        result = pd.DataFrame(result)
        self.selection_made.emit(result)


class PandasViewer(QtGui.QMainWindow):
    """Main window for the GUI"""

    def __init__(self, obj):
        """

        Parameters
        ----------
        obj: pd.Series, pd.DataFrame, pd.Panel, dict
            The obj to iterate through to allow selection

        Returns
        -------
        PandasViewer

        Examples
        --------
        >>> timestamps = pd.date_range('1-Apr-14', '30-Apr-14')
        >>> dataframe = pd.DataFrame(np.random.rand(len(timestamps), 2), index=timestamps)
        >>> app = QtGui.QApplication(sys.argv)
        >>> PandasViewer(dataframe) #doctest: +ELLIPSIS
        <viewer_gui.PandasViewer object at ...>
        """
        QtGui.QMainWindow.__init__(self)
        if isinstance(obj, (pd.Series, pd.DataFrame, pd.Panel)):
            obj = {str(type(obj)): obj}
        self.freq = None
        self.agg = None
        self.filepath = None
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
        self.obj = obj
        self.tree_widget = PandasTreeWidget(self, obj=obj)
        self.tree_widget.selection_made.connect(self.dataframe_changed)
        left_layout.addWidget(self.tree_widget)
        self.df_viewer = DataFrameTableView(None)
        left_layout.addWidget(self.df_viewer)

        self.df_plot_viewer = DataFramePlotWidget()
        splitter.addWidget(self.df_plot_viewer)
        self.df = None
        self.displayed_df = None
        self.init_menu()

    def dataframe_changed(self, df):
        """Set the dataframe in the dataframe viewer to df

        Parameters
        ----------
        df: pd.DataFrame
            The dataframe to set
        """
        self.df = df
        self.displayed_df = self.df if self.freq is None else self.df.resample(
            self.freq, how=self.agg)
        self.df_viewer.set_dataframe(self.displayed_df)
        self.df_plot_viewer.set_dataframe(self.displayed_df)
        self.df_plot_viewer.draw()

    def init_menu(self):
        """Initiate the drop down menus for the window"""
        menubar = QtGui.QMenuBar(self)
        action_menu = QtGui.QMenu('Actions')
        menubar.addMenu(action_menu)
        open_action = QtGui.QAction('Open File', action_menu, shortcut=QtGui.QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        # open_action.setShortcut(['ctrl 0'])
        action_menu.addAction(open_action)
        style_menu = QtGui.QMenu('Style')
        menubar.addMenu(style_menu)
        self.freq_submenu = QtGui.QMenu('Freq')
        self.freq_mapper = QtCore.QSignalMapper(self)
        for freq in ['D', 'H', 'T']:
            action = QtGui.QAction(freq, self, checkable=True)
            self.freq_mapper.setMapping(action, freq)
            action.triggered.connect(self.freq_mapper.map)
            self.freq_submenu.addAction(action)
        self.freq_mapper.mapped['QString'].connect(self.change_freq)
        style_menu.addMenu(self.freq_submenu)
        self.agg_submenu = QtGui.QMenu('How')
        self.agg_mapper = QtCore.QSignalMapper(self)
        for how in ['mean', 'sum', 'last']:
            action = QtGui.QAction(how, self, checkable=True)
            self.agg_mapper.setMapping(action, how)
            action.triggered.connect(self.agg_mapper.map)
            self.agg_submenu.addAction(action)
        self.agg_mapper.mapped['QString'].connect(self.change_agg)
        style_menu.addMenu(self.agg_submenu)
        self.strip_zeros = QtGui.QAction(
            'Strip Zeros', style_menu, checkable=True)
        self.strip_zeros.triggered.connect(self.change_strip_zeros)
        style_menu.addAction(self.strip_zeros)
        self.legend_action = QtGui.QAction(
            'Legend', style_menu, checkable=True, checked=True)
        self.legend_action.triggered.connect(self.change_legend)
        style_menu.addAction(self.legend_action)

    def change_freq(self, freq):
        """Resample the original pd.DataFrame to frequency freq

        Parameters
        ----------
        freq: str
            The frequency to resample the dataframe to
        """
        self.freq = freq
        for action in self.freq_submenu.actions():
            action.setChecked(action.text() == freq)
        if self.df is not None:
            self.dataframe_changed(self.df)

    def change_agg(self, how):
        """Change the method of aggregation/resample

        Parameters
        ----------
        how: str
            The method to use for resample parameter how
        """
        self.agg = how
        for action in self.agg_submenu.actions():
            action.setChecked(action.text() == how)
        if self.df is not None:
            self.dataframe_changed(self.df)

    def change_legend(self):
        """Set the visibility of the subplot legend to match the checked status
        of the submenu item.  The submenu item is checkable and as such changes
        state automatically when clicked
        """
        self.df_plot_viewer.legend.set_visible(self.legend_action.isChecked())
        self.df_plot_viewer.draw()

    def change_strip_zeros(self):
        """Strip the zeros from teh displayed data"""
        df = self.df
        if self.strip_zeros.isChecked():
            for col, ts in df.iteritems():
                df.ix[ts == 0, col] = np.nan
        self.dataframe_changed(df)

    def open_file(self):
        """Open either a pickle or h5 file"""
        self.filepath, _ = QtGui.QFileDialog.getOpenFileName(
            self, 'Select pickle to load', '/Users/davidsimpson/')
        filename, ext = os.path.splitext(os.path.basename(self.filepath))
        if ext == '.pickle':
            obj = pickling.load(self.filepath)
        elif ext == '.h5':
            with h5py.File(self.filepath, 'r') as file_obj:
                keys = file_obj.keys()
            obj = {}
            for key in keys:
                obj[key] = pd.read_hdf(self.filepath, key)
                col_idx = [k for k, d in obj[key].dtypes.iteritems() if d.type == np.float64]
                if 'timestamp' in obj[key].columns:
                    obj[key].index = [pd.Timestamp(t, tz='UTC') for t in obj[key]['timestamp']]
                obj[key] = obj[key][col_idx]
        else:
            raise ValueError('File type %s not supported', ext)
        if isinstance(obj, dict):
            self.obj = obj
        elif isinstance(obj, pd.core.generic.NDFrame):
            obj_name = os.path.splitext(os.path.basename(self.filepath))[0]
            self.obj = {obj_name: obj}
        else:
            msg_box = QtGui.QMessageBox()
            msg = 'Pickle file should contain a dict of pandas objects or a '
            msg += 'pandas object\n Object in pickle is %s' % type(obj)
            msg_box.setText(msg)
            msg_box.exec_()
            return
        self.displayed_df = None
        self.tree_widget.set_tree(self.obj)


def main():
    """Main method for the app"""
    app = QtGui.QApplication(sys.argv)
    #ToDo this is just a random dataframe for testing
    timestamps = pd.date_range('1-Apr-14', '30-Apr-14', freq='H')
    ts = pd.Series(np.random.rand(len(timestamps)), timestamps)
    dataframe = pd.DataFrame(
        np.random.rand(len(timestamps), 2), index=timestamps)
    pandas_viewer = PandasViewer(dict(ts=ts, df=dataframe))
    pandas_viewer.show()
    app.exec_()

if __name__ == '__main__':
    main()