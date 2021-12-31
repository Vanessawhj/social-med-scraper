# source /Users/huijee/Python/pyqt5_v3/bin/activate

from PyQt5 import QtWidgets
from PyQt5.QtCore import QLine
from PyQt5.QtWidgets import QApplication, QGridLayout, QMainWindow
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QStatusBar,
    QTableView, QButtonGroup, QMessageBox, QRadioButton

)
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QIcon
import pygsheets
import pandas as pd
import scraping.fb_scrape as fb
import scraping.ig_scrape as ig
import sentiment.sentiment as sent
import sentiment.create_plot as plot
import sentiment.gsheet as get_data

import datetime

import sys
from PyQt5 import QtCore, QtWidgets

from oauth2client.service_account import ServiceAccountCredentials
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import os



class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.window_width, self.window_height = 700,500
        
        self.setMinimumSize(self.window_width, self.window_height)
        self.setGeometry(200, 200, self.window_width, self.window_height)
        self.setWindowTitle('Web scraping')
        self.initUI()
        self.show()

    def initUI(self):


        container = QWidget()
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        databuttons_layout = QHBoxLayout()
        self.btn_grp = QButtonGroup()
        self.btn_grp.setExclusive(True)


        self.button_lst = [
            QPushButton(item) for item in
            ['Instagram', 'Facebook', 'Twitter']
        ]

        for i, b in enumerate(self.button_lst, start=1):
            button_layout.addWidget(b)
            self.btn_grp.addButton(b, i)

        self.btn_grp.buttonClicked[int].connect(self.slot)

        self.data_view = QTableView()
        self.data_view.setAlternatingRowColors(True)




        self.btn_export = QPushButton('Export to .csv', self)
        self.btn_loaddata = QPushButton('Predict sentiment', self)
        self.btn_plot = QPushButton('Plot graph', self)



        self.df_fb = self.df_ig = self.df = self.df_copy = self.df_ig_combined =pd.DataFrame()
        # self.df_ig = pd.DataFrame()
        # self.df = pd.DataFrame()

        self.btn_loaddata.clicked.connect(self.sentiment)
        self.btn_plot.clicked.connect(self.plot_chart)

        databuttons_layout.addWidget(self.btn_loaddata)
        databuttons_layout.addWidget(self.btn_export)
        databuttons_layout.addWidget(self.btn_plot)


        # layout
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.data_view)
        main_layout.addLayout(databuttons_layout)

        # assign QLayout to the QWidget, and set central on the QMainWindow
        container.setLayout(main_layout)
        self.setCentralWidget(container)  # to show the content


    def print_error(self, message_type, message):

        msg = QMessageBox()

        if message_type == 'Error':
            msg.setIcon(QMessageBox.Critical)

        # elif message_type == 'Success':
            # msg.setIcon(QMessageBox.Inform)

        msg.setText(message_type)
        msg.setInformativeText(message)
        msg.setWindowTitle(message_type)
        msg.exec_()


    def get_date_range(self, df):
        df['Time'] = pd.to_datetime(df["Time"], format = "%Y-%m-%d") # to be commented out


        # # df = df[df['Time'] >= '2021-09-13']
        min_day = min(df['Time'])
        # min_date = f'{min_day.day}/{min_day.month}/{min_day.year}'

        max_day = max(df['Time'])
        # max_date = f'{max_day.day}/{max_day.month}/{max_day.year}'

        # # date_range = f'{min_date.date()} till {max_date.date()}'
        date_range = f'{min_day.day}/{min_day.month}/{min_day.year} till {max_day.day}/{max_day.month}/{max_day.year}'
        return date_range




    def combine_df(self, is_existing):

        if is_existing == 'Yes':
            if not self.df_ig.empty:
                self.df_copy, _ = get_data.main(self.df, 'ig')

            elif not self.df_fb.empty:
                self.df_copy, _ = get_data.main(self.df, 'fb')

            date_range = self.get_date_range(self.df_copy)

            start_msg = f'Enter Start Date ("dd/mm/yyyy"), date range is {date_range}'
            end_msg = f'Enter End Date ("dd/mm/yyyy"), date range is {date_range}'

            #############
            isNotValidStartDate = isNotValidEndDate = True
            while isNotValidStartDate:
                startdate,done1 = QtWidgets.QInputDialog.getText(
                self, 'Input Dialog', start_msg)
                # print(done1)
                
                try:
                    day, month, year = startdate.split('/')
                    test_start = datetime.datetime(int(year), int(month), int(day))
                    isNotValidStartDate = False
                except ValueError:
                    isNotValidStartDate = True
                    self.print_error("Error", 'Not A Valid Date')


            while isNotValidEndDate:
                enddate, done1 = QtWidgets.QInputDialog.getText(
                self, 'Input Dialog', end_msg)
            
                
                try:
                    day, month, year = enddate.split('/')
                    test_end = datetime.datetime(int(year), int(month), int(day))
                    if test_end < test_start:
                        self.print_error("Error", 'End Date Should Be After Start Date!')
                    else: 
                        isNotValidEndDate = False
                except ValueError:
                    isNotValidEndDate = True
                    self.print_error("Error", 'Not A Valid Date!')


            self.df_copy = self.df_copy[(self.df_copy['Time'] >= test_start) & (self.df_copy['Time'] <= test_end)]

            date_range = f'{test_start.date()} till {test_end.date()}'

        
        else:           
            date_range = self.get_date_range(self.df)

        return date_range



    def plot_chart(self):



        if self.df_ig.empty and self.df_fb.empty:
            self.print_error("Error", 'No data to plot. Web scraping required first!')

        elif self.df.empty:
            self.print_error("Error", 'Sentiment required first!')


        else:
            is_existing =['Yes', 'No']
            is_existing, done4 = QtWidgets.QInputDialog.getItem(
            self, 'Input Dialog', 'Plot with existing data?', is_existing)

            date_range = self.combine_df(is_existing)

            
            top_n, done1 = QtWidgets.QInputDialog.getInt(
            self, 'Input Dialog', 'Enter top n:') 

            ngram, done2 = QtWidgets.QInputDialog.getInt(
            self, 'Input Dialog', 'Enter ngram words:') 


            sentiments =['Positive', 'Neutral', 'Negative']
            sent, done3 = QtWidgets.QInputDialog.getItem(
            self, 'Input Dialog', 'Enter sentiment:', sentiments)


            filter =['True', 'False']
            is_filter, done4 = QtWidgets.QInputDialog.getItem(
            self, 'Input Dialog', 'Filter sentiment?', filter)

            if is_existing == 'Yes':
                self.img = plot.main(self.df_copy,top_n, ngram,sent,False,date_range)

            else:

                self.img = plot.main(self.df,top_n, ngram,sent,False,date_range)


            if self.img is not None:
                self.img.show()
                image_name, done5 = QtWidgets.QInputDialog.getText(
                self, 'Input Dialog', 'Upload image? If yes, input the name for image file, else press cancel')

                print(f'word is {image_name}')
                if done5:
                    image_name = f'{image_name}.png'
                    self.img.savefig(f'{os.getcwd()}/sentiment/graphs/{image_name}',bbox_inches='tight')
                    print('Successfully saved image!')


                    print('Waiting to upload')
                    print(os.getcwd())
                    self.upload_file(f'sentiment/graphs/{image_name}')
                    self.print_error("Success", 'Successfully uploaded image to Google Drive!')


            else: 
                self.print_error('Error', 'No sentiment to show / No data for that period')


        
    

    def slot(self, id):

        handle_dialog = QtWidgets.QInputDialog(self)
        handle_dialog.setOkButtonText("Start scraping")
        handle_dialog.setLabelText("Enter handle:")
        handle_dialog.setTextEchoMode(QtWidgets.QLineEdit.Normal)


        if handle_dialog.exec_() == QtWidgets.QDialog.Accepted:
            handle = handle_dialog.textValue()

        if id == 1:
            isNotValidStartDate = isNotValidEndDate = True
            while isNotValidStartDate:
                startdate,done1 = QtWidgets.QInputDialog.getText(
                self, 'Input Dialog', "Enter Start Date: ('dd/mm/yyyy')")
                
                try:
                    day, month, year = startdate.split('/')
                    test_start = datetime.datetime(int(year), int(month), int(day))
                    isNotValidStartDate = False
                except ValueError:
                    isNotValidStartDate = True
                    self.print_error("Error", 'Not A Valid Date')


            while isNotValidEndDate:
                enddate, done1 = QtWidgets.QInputDialog.getText(
                self, 'Input Dialog', "Enter End Date: ('dd/mm/yyyy')")
            
                
                try:
                    day, month, year = enddate.split('/')
                    test_end = datetime.datetime(int(year), int(month), int(day))
                    if test_end < test_start:
                        self.print_error("Error", 'End Date Should Be After Start Date!')
                    else: 
                        isNotValidEndDate = False
                except ValueError:
                    isNotValidEndDate = True
                    self.print_error("Error", 'Not A Valid Date!')


            self.df_ig = ig.main(handle, startdate, enddate)
            self.model = TableModel(self.df_ig)



        elif id == 2:
            print('Facebook')
            self.df_fb = fb.main(handle)
            self.model = TableModel(self.df_fb)

        self.data_view.setModel(self.model)
        

    
    def sentiment(self):
        
        if not self.df_fb.empty:
            self.df = sent.main(self.df_fb)
            self.model = TableModel(self.df)
            self.data_view.setModel(self.model)

        elif not self.df_ig.empty:
            self.df = sent.main(self.df_ig)
            self.model = TableModel(self.df)
            self.data_view.setModel(self.model)


        else:
            print('is empty')
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText('No data to predict. Web scraping required.')
            msg.setWindowTitle("Error")
            msg.exec_()



        # # UNCOMMENT THIS
        gc = pygsheets.authorize(service_file='sentiment/creds.json')
        sh = gc.open('User Sentiment')

        if not self.df_ig.empty:
            wks = sh.worksheet('title','IG Sentiment')
        else: 
            wks = sh.worksheet('title','FB Sentiment')


        existing_df = wks.get_as_df()
        merged_df = pd.concat([existing_df, self.df])
        merged_df = merged_df.fillna(0)
        
        try:
            merged_df = merged_df.loc[merged_df.astype(str).drop_duplicates().index].sort_values(by='Time') # drop_duplcates run into error bc of list in rows
        except:
            merged_df = merged_df.loc[merged_df.astype(str).drop_duplicates().index]
            print('cannot remove duplicates')


        wks.set_dataframe(merged_df,(1,1)) 

    def upload_file(self, filename):

        gauth = GoogleAuth()
        scope = ['https://www.googleapis.com/auth/drive']

        gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secrets.json', scope)
        drive = GoogleDrive(gauth)

        upload_file_list = filename

        file1 = drive.CreateFile({'parents': [{'id': '1VtEDgkaKqshjOz77ISC5YXJ7NjWCgpmt'}]})

        file1.SetContentFile(upload_file_list)
        file1.Upload()
        print('title: %s, id: %s' % (file1['title'], file1['id']))



class TableModel(QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]

            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])



def window():
    app = QApplication(sys.argv)
    win = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    window()



