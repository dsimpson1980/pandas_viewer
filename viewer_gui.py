import sys
import os
import functools

from PySide import QtGui, QtCore
import pandas as pd
import numpy as np
import h5py
import matplotlib

matplotlib.rcParams['backend.qt4'] = 'PySide'

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from pandas_viewer import pickling, trees


# ToDo Add email plot icon to navigation bar
# ToDo Add email plot functionality (save png to buffer then attach to email)
# ToDo Add difference plots action
# ToDo Add difference plots functionality
# ToDo fix pyinstaller build so that menu items are shown
# ToDo Add Status in window showing freq, agg, and zeros_stripped
# ToDo fix bug where plot is not being cleared on loading new file


def update_dataframe(obj):
    @functools.wraps(obj)
    def func(*args, **kwargs):
        self = args[0]
        result = obj(*args, **kwargs)
        self.dataframe_changed(self.df)
        return result
    return func


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
        self.chart_type = 'line'
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
        values = dataframe.cumsum(
            axis=1).values if self.chart_type == 'stack' else dataframe.values
        if not dataframe.empty:
            self.subplot.clear()
            self.subplot.plot_date(dataframe.index, values, '-')
            legend = self.subplot.legend(self.dataframe.columns)
            legend.set_visible(self.legend.get_visible())
            self.legend = legend

    def draw(self):
        """Draw the Canvas for the plot Figure"""
        self.canvas.draw()


class PandasViewer(QtGui.QMainWindow):
    """Main window for the GUI"""

    def __init__(self, obj=None):
        """Initiate pandas viewer

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
        self.version = 0.1
        self.settings = QtCore.QSettings('pandas_viewer_{}'.format(self.version))
        if not obj:
            obj = {}
        QtGui.QMainWindow.__init__(self)
        if isinstance(obj, (pd.Series, pd.DataFrame, pd.Panel)):
            obj = {str(type(obj)): obj}
        self.freq = None
        self.agg = None
        self.filepath = None
        self.df = pd.DataFrame()
        self.displayed_df = pd.DataFrame()
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
        self.tree_widget = trees.PandasTreeWidget(self, obj=obj)
        self.tree_widget.selection_made.connect(self.dataframe_changed)
        left_layout.addWidget(self.tree_widget)
        self.df_viewer = DataFrameTableView(None)
        left_layout.addWidget(self.df_viewer)

        self.df_plot_viewer = DataFramePlotWidget(self.df)
        splitter.addWidget(self.df_plot_viewer)
        self.init_menu()

    def init_action_menu(self):
        self.action_menu = QtGui.QMenu('Actions')
        self.menubar.addMenu(self.action_menu)
        self._create_action(self.action_menu, 'open', 'Open',
                           QtGui.QKeySequence.Open, self.open_file)
        if os.path.exists('/md'):
            self._create_action(self.action_menu, 'open_archive', 'Open Archive',
                                'Ctrl+A', lambda: self.open_file('/md'))
        self._create_action(self.action_menu, 'collapse_action', 'Collapse All',
                            'Ctrl+Shift+C', self.tree_widget.collapseAll)
        self._create_action(self.action_menu, 'expand_all', 'Expand All',
                            'Ctrl+Shift+E', self.tree_widget.expandAll)

    def init_data_menu(self):
        data_menu = QtGui.QMenu('Data')
        self.menubar.addMenu(data_menu)
        self._create_action(data_menu, 'save_to_csv', 'Save to csv',
                           QtGui.QKeySequence.Save, self.save_to_csv)

    def init_style_menu(self):
        self.style_menu = QtGui.QMenu('Style')
        self.menubar.addMenu(self.style_menu)
        self._create_submenu(
            self.style_menu, 'freq', dict(T='30T', H='H', F='4H', D='D', M='M'),
            self.change_freq)
        self._create_submenu(
            self.style_menu, 'how', dict(W='mean', S='sum', L='last'),
            self.change_agg)
        self._create_submenu(
            self.style_menu, 'chart_type', dict(L='line', R='stack'),
            self.change_chart)
        self._create_action(self.style_menu, 'strip_zeros', 'Strip Zeros',
                            'Ctrl+0', self.change_strip_zeros, checkable=True)
        self._create_action(self.style_menu, 'legend_action', 'Legend',
                            'Ctrl+L', self.change_legend, checkable=True)

    def init_menu(self):
        """Initiate the drop down menus for the window"""
        self.menubar = QtGui.QMenuBar(self)
        self.init_action_menu()
        self.init_data_menu()
        self.init_style_menu()

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
        if self.strip_zeros.isChecked():
            for col, ts in self.displayed_df.iteritems():
                self.displayed_df.ix[ts == 0, col] = np.nan
        self.df_viewer.set_dataframe(self.displayed_df)
        self.df_plot_viewer.set_dataframe(self.displayed_df)
        self.df_plot_viewer.draw()

    def save_to_csv(self):
        """Save the contents of the currently selected DataFrame to a csv file
        """
        filepath, _ = QtGui.QFileDialog.getSaveFileName(self, 'Enter filename')
        self.df_plot_viewer.dataframe.to_csv(filepath)

    @staticmethod
    def action(*args, **kwargs):
        action = QtGui.QAction(*args, **kwargs)
        event = kwargs.pop('triggered', None)
        if event is not None:
            action.triggered.connect(event)
        return action

    @update_dataframe
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

    @update_dataframe
    def change_agg(self, how):
        """Change the method of aggregation/resample

        Parameters
        ----------
        how: str
            The method to use for resample parameter how
        """
        self.agg = how
        for action in self.how_submenu.actions():
            action.setChecked(action.text() == how)

    @update_dataframe
    def change_chart(self, chart_type):
        self.df_plot_viewer.chart_type = chart_type
        for action in self.chart_type_submenu.actions():
            action.setChecked(action.text() == chart_type)

    def change_legend(self):
        """Set the visibility of the subplot legend to match the checked status
        of the submenu item.  The submenu item is checkable and as such changes
        state automatically when clicked
        """
        self.df_plot_viewer.legend.set_visible(self.legend_action.isChecked())
        self.df_plot_viewer.draw()

    @update_dataframe
    def change_strip_zeros(self):
        pass

    @update_dataframe
    def open_file(self):
        open_dirpath = self.settings.value('open_dirpath')
        if open_dirpath is None:
            open_dirpath = os.path.expanduser('~')
        filepath, _ = QtGui.QFileDialog.getOpenFileName(
            self, 'Select pickle to load', open_dirpath)
        self.settings.setValue('open_dirpath', os.path.dirname(filepath))
        self.tree_widget.add_file_to_tree(filepath)

    def reset_all(self):
        [action.setChecked(False) for action in self.freq_submenu.actions()]
        [action.setChecked(False) for action in self.how_submenu.actions()]
        self.legend_action.setChecked(True)
        self.freq = None
        self.agg = None
        self.df = pd.DataFrame()
        self.displayed_df = pd.DataFrame()

    def _create_submenu(self, parent_menu, name, menu_items, func):
        name = name.lower()
        submenu = QtGui.QMenu(name)
        self.__setattr__('{}_submenu'.format(name), submenu)
        submapper = QtCore.QSignalMapper(self)
        self.__setattr__('{}_mapper'.format(name), submapper)
        for key, arg in menu_items.iteritems():
            action = QtGui.QAction(
                arg, self, checkable=True,
                shortcut=QtGui.QKeySequence('Ctrl+Shift+{}'.format(key)))
            submapper.setMapping(action, arg)
            action.triggered.connect(submapper.map)
            submenu.addAction(action)
        submapper.mapped['QString'].connect(func)
        parent_menu.addMenu(submenu)

    def _create_action(self, parent_menu, name, display_name, shortcut, func,
                      checkable=False):
        if isinstance(shortcut, str):
            shortcut = QtGui.QKeySequence(shortcut)
        action = QtGui.QAction(display_name, parent_menu, checkable=checkable,
                               shortcut=shortcut)
        action.triggered.connect(func)
        parent_menu.addAction(action)
        self.__setattr__(name, action)


def main():
    """Main method for the app"""
    app = QtGui.QApplication(sys.argv)
    pandas_viewer = PandasViewer()
    pandas_viewer.show()
    app.exec_()

if __name__ == '__main__':
    main()
