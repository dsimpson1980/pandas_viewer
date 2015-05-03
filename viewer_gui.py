from PySide import QtGui, QtCore
import pandas
import numpy
import sys


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


class PandasViewer(QtGui.QMainWindow):
    """Main window for the GUI

    """
    def __init__(self, dataframe):
        """

        Parameters
        ----------
        dataframe: pandas.DataFrame
            The dataframe to display

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
        window = QtGui.QWidget()
        main_layout = QtGui.QVBoxLayout()
        window.setLayout(main_layout)
        self.setCentralWidget(window)
        self.df_viewer = DataFrameTableView(None)
        self.dataframe_changed(dataframe)
        main_layout.addWidget(self.df_viewer)
        self.resize(500, 450)

    def dataframe_changed(self, df):
        """Set the dataframe in the dataframe viewer to df

        Parameters
        ----------
        df: pandas.DataFrame
            The dataframe to set
        """
        self.df_viewer.set_dataframe(df)


def main():
    """Main method for the app"""
    app = QtGui.QApplication(sys.argv)
    #ToDo this is just a random dataframe for testing
    timestamps = pandas.date_range('1-Apr-14', '30-Apr-14')
    dataframe = pandas.DataFrame(
        numpy.random.rand(len(timestamps), 2), index=timestamps)
    pandas_viewer = PandasViewer(dataframe)
    pandas_viewer.show()
    app.exec_()

if __name__ == '__main__':
    main()