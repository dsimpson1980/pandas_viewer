from PySide import QtGui, QtCore
import pandas
import numpy
import sys


class DataFrameTableView(QtGui.QTableView):

    def __init__(self, df):
        QtGui.QTableView.__init__(self)
        if df is not None:
            self.set_dataframe(df)

    def set_dataframe(self, df):
        table_model = DataFrameTableModel(self, df)
        self.df = df
        self.setModel(table_model)
        self.resizeColumnsToContents()


class DataFrameTableModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, df):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.df = df

    def rowCount(self, parent):
        return len(self.df)

    def columnCount(self, parent):
        return len(self.df.columns) + 1

    def data(self, index, role):
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
    def __init__(self, dataframe):
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
        self.df_viewer.set_dataframe(df)


def main():
    app = QtGui.QApplication(sys.argv)
    timestamps = pandas.date_range('1-Apr-14', '30-Apr-14')
    dataframe = pandas.DataFrame(
        numpy.random.rand(len(timestamps), 2), index=timestamps)
    pandas_viewer = PandasViewer(dataframe)
    pandas_viewer.show()
    app.exec_()

if __name__ == '__main__':
    main()