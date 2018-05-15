#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QCheckBox, QTableView, QComboBox, QFileDialog, QAction, QMainWindow, QApplication, QLabel, QLineEdit, QPushButton, QMessageBox, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QDialog, QGroupBox, QFormLayout, QGridLayout, QTabWidget, QTableWidget

from PyQt5.QtGui import QDoubleValidator, QIntValidator

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from numpy.fft import rfft
import matplotlib.pyplot as plt

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt

import wavelets_lib as wl
from helper.pandasTable import PandasModel
import random
import numpy as np
import pandas as pd

# set matplotlib settings, no fontsize effect??!
from matplotlib import rc
# rc('font', family='sans-serif', size = 10)
# rc('lines', markeredgewidth = 0)
rc('text', usetex=False) # better for the UI

tick_label_size = 10
label_size = 12
DEBUG = True

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.nViewers = 0
        self.DataViewers = {} # no Viewers yet
        self.detr = {}
        self.initUI()
    def initUI(self):
        self.setGeometry(1400,100,400,100)
        self.setWindowTitle('TFAnalyzer')

        self.quitAction = QAction("&Quit", self)
        self.quitAction.setShortcut("Ctrl+Q")
        self.quitAction.setStatusTip('Quit pyTFA')
        self.quitAction.triggered.connect(self.close_application)

        openFile = QAction("&Load data", self)
        openFile.setShortcut("Ctrl+L")
        openFile.setStatusTip('Load data')
        openFile.triggered.connect(self.load)

        detrending = QAction('&Detrend signal', self)
        detrending.setShortcut('Ctrl+T')
        detrending.setStatusTip('Detrends signal')
        detrending.triggered.connect(self.detrending)

        plotSynSig = QAction('&Plot synthetic signal',self)
        plotSynSig.setShortcut('Ctrl+P')
        plotSynSig.setStatusTip('Plot synthetic signal')
        plotSynSig.triggered.connect(self.plotSynSig)
        
        viewer = QAction('&View Data',self)
        viewer.setShortcut('Ctrl+D')
        viewer.setStatusTip('View data')
        viewer.triggered.connect(self.Viewer_Ini)

        self.statusBar()

        mainMenu = self.menuBar()
        mainMenu.setNativeMenuBar(False)
        
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(self.quitAction)
        fileMenu.addAction(openFile)
        
        analyzerMenu = mainMenu.addMenu('&Analyzer')
        analyzerMenu.addAction(plotSynSig)
        analyzerMenu.addAction(detrending)
        analyzerMenu.addAction(viewer)
        
        #self.home()

    #def home(self):

        #self.quitAction.triggered.connect(self.close_application)
        #self.toolBar = self.addToolBar("Extraction")
        #self.toolBar.addAction(self.quitAction)
        #self.toolBar.addAction(openFile)

        quitButton = QPushButton("Quit", self)
        quitButton.clicked.connect(self.close_application)
        quitButton.resize(quitButton.minimumSizeHint())
        quitButton.move(50,50)

        openFileButton = QPushButton("Load data",self)
        openFileButton.clicked.connect(self.load)
        quitButton.resize(quitButton.minimumSizeHint())
        openFileButton.move(120,50)


        self.show()
        
    def close_application(self):
        choice = QMessageBox.question(self, 'Quitting',
                                            'Do you want to exit pyTFA?',
                                            QMessageBox.Yes | QMessageBox.No)
        if choice == QMessageBox.Yes:
            print("Quitting ...")
            #sys.exit()
            appc = QApplication.instance()
            appc.closeAllWindows()
        else:
            pass
        
    def load(self):

        self.new_data = DataLoader()

        # dh data handler?!
        # self.dh.make_connection(self.new_data)
        test = self.new_data.initUI()
        if test:
            self.Viewer_Ini() # initialize data viewer
###################################
    def Viewer_Ini (self):
        print ('function Viewer_Ini called')
        self.nViewers += 1

        # make new DataViewer
        self.DataViewers[self.nViewers] = DataViewer()
        
        self.DataViewers[self.nViewers].make_connection(self.new_data)
        self.new_data.emit_values()
        print ('DataLoader transferred data to DataViewer')

        # only now call the UI
        self.DataViewers[self.nViewers].initUI()

        
    def detrending (self):
        print ('function detrending called')
        self.i +=1
        self.detr[self.i] = Detrender()
        
        self.detr[self.i].make_connection(self.dh) 
        #self.dh.data_request_connection(self.detr)
        self.dh.ini_connect_analyzer_tools() #emit ids
        self.detr[self.i].initUI()
        print ('detr and plotSynSig connected')

    def plotSynSig (self):
        pdic = {'T' : 900, 'amp' : 6, 'per' : 70, 'sigma' : 2, 'slope' : -10.}
        gen_func = synth_signal1 #TODO dropdown which synthetic signal
        default_para_dic = pdic
        self.synSig=SyntheticSignalGenerator(gen_func, default_para_dic)
        self.dh.make_connection(self.synSig)
        self.synSig.initUI()
        
class DataLoader(QWidget):

    # time signal?!
    DataTransfer = pyqtSignal('PyQt_PyObject')
    
    def __init__(self):
        super().__init__()
        self.raw_df = pd.DataFrame()
        self.signal_dic = {}
        #self.initUI()
        
    def initUI(self):
        
        if DEBUG:
            file_names = ['PSMexamples.csv']
        else:
            file_names = QFileDialog.getOpenFileName(self, 'Open File')
                        
        ###If correct file path/type is supplied data are read in and emitted
        #try:
        
        
        if DEBUG:
            print (file_names)

        try:
            file_name = file_names[0]

            file_ext = file_name.split('.')[-1]


        except IndexError:
            self.noFile = Error('No valid path or file supplied!', 'No File')
            print ('returned no values emiited')
            return False

        try:
            print('Loading',file_ext, file_name)
            # open file according to extension 
            if file_ext == 'csv':
                print("CSV")
                self.raw_df = pd.read_csv(file_name, header=0)
                
            elif file_ext == 'tsv':
                print("TSV")
                self.raw_df = pd.read_csv(file_name, header=0, sep = '\t')

            elif file_ext in ['xls','xlsx']:
                print("EXCEL")
                self.raw_df = pd.read_excel(file_name, header=0)

            # try white space separation as a fallback
            else:
                print('WHITESPACE')
                self.raw_df = pd.read_csv(file_name, delim_whitespace = True, header=1)
            print('Raw Columns:',self.raw_df.columns)
        except FileNotFoundError:
            self.raw_df = pd.DataFrame()
            self.noFile = Error('No valid path or file supplied!', 'No File')
            print ('returned no values emiited')
            return False
        
        
        ## TODO drop NaNs
        ## later TODO deal with 'holes'
        # self.emit_values()
        return True
        
    def emit_values(self):
        self.DataTransfer.emit(self.raw_df)
            
    


# class DataHandler(QWidget):
#     #Add signal, 2nd DataTransfer?!
#     signalIds = pyqtSignal('PyQt_PyObject')
    
#     def __init__(self):
#         super().__init__()
#         self.signal_ids = []
#         self.signal_dic = {}

#     def ini_connect_analyzer_tools(self):
#         print ('ini_connect_analyzer_tools called')
        
#         self.signalIds.emit([self.signal_ids, self.signal_dic])
    

#     def make_connection(self, new_data):        ###########################
#         new_data.DataTransfer.connect(self.get_signal) #######################

        

#     @pyqtSlot('PyQt_PyObject')
#     def get_signal(self, signal_dic):
#         self.signal_ids = signal_dic.keys()
#         self.signal_dic = signal_dic


    

class DataViewer(QWidget):
        
    def __init__(self):
        super().__init__()
        self.df = None # initialize empty  
        #self.signal_dic = {}
        self.anaWindows = {}
        self.w_position = 0 # analysis window position offset
        
        self.signal_id= None # no signal id initially selected
        self.raw_signal = None # no signal initial array
        self.dt = None # gets initialized from the UI -> qset_dt
        self.T_c = None # gets initialized from the UI -> qset_T_c
        self.tvec = None # gets initialized by vector_prep
        self.time_unit = None # gets initialized by qset_time_unit

        # some Qt Validators
        
        self.posfloatV = QDoubleValidator(bottom = 1e-16, top = 1e16)
        
        # gets updated with dt in -> qset_dt
        self.periodV = QDoubleValidator(bottom = 1e-16, top = 1e16)

        self.posintV = QIntValidator(bottom = 1,top = 9999999999)
    
    # to get data from DataLoader instance,
    # get_df gets called when data_loader emits
    def make_connection(self, data_loader):
        data_loader.DataTransfer.connect(self.get_df)

    # should be called by DataLoader emission before initUI 
    @pyqtSlot('PyQt_PyObject')
    def get_df(self, df):
        print ('get_df called')
        self.df = df
        
    #===============UI=======================================

    def initUI(self):
        self.plotWindow = TimeSeriesViewerCanvas()
        main_frame = QWidget()
        self.plotWindow.setParent(main_frame)
        ntb = NavigationToolbar(self.plotWindow, main_frame) # full toolbar

        # the table instance,
        # self.df created by get_df <-> DataLoader.DataTransfer signal
        DataTable = QTableView()
        model= PandasModel(self.df)
        DataTable.setModel(model)
        DataTable.setSelectionBehavior(2) # columns only
        DataTable.clicked.connect(self.Table_select) # magically transports QModelIndex
        # so that it also works for header selection
        header = DataTable.horizontalHeader() # returns QHeaderView
        header.sectionClicked.connect(self.Header_select) # magically transports QModelIndex

                

        # the signal selection box
        SignalBox = QComboBox(self)
        
        # needs to be connected befor calling initUI
        self.setWindowTitle('DataViewer')
        self.setGeometry(20,30,900,650)
        
        #Data selection box (very top)
        main_layout_v =QVBoxLayout()
        #Data selction drop-down
        dataLabel = QLabel('Select signal', self)
        
        dt_label= QLabel('Sampling intervall:')
        dt_edit = QLineEdit()
        dt_edit.setValidator(self.posfloatV)
                
        unit_label= QLabel('time unit:')
        unit_edit = QLineEdit(self)
        
        
        data_selection_layout_h =QHBoxLayout()
        data_selection_layout_h.addWidget(dataLabel)
        data_selection_layout_h.addWidget(SignalBox)
        data_selection_layout_h.addStretch(0)
        data_selection_layout_h.addWidget(dt_label)
        data_selection_layout_h.addWidget(dt_edit)
        data_selection_layout_h.addStretch(0)
        data_selection_layout_h.addWidget(unit_label)
        data_selection_layout_h.addWidget(unit_edit)
        data_selection_layout_h.addStretch(0)
        main_layout_v.addLayout(data_selection_layout_h)
        
        
        # plot options box
        plot_options_box = QGroupBox('Signal plot options')
        cb_layout= QFormLayout()
        cb_raw = QCheckBox('Raw signal', self)
        cb_trend = QCheckBox('Trend', self)
        cb_detrend = QCheckBox('Detrended Signal', self)
        plotButton = QPushButton('Refresh plot', self)
        button_layout_h = QHBoxLayout()
        plotButton.clicked.connect(self.doPlot)
        button_layout_h.addWidget(plotButton)
        button_layout_h.addStretch(0)
                
        
        ##detrending parameters
        
        T_c_edit = QLineEdit()
        T_c_edit.setValidator(self.posfloatV)

        # self.T_c.insert(str(100)) # no default value
        self.v_max = QLineEdit()
        self.v_max.insert(str(20))
        
        ## checkbox layout
        cb_layout.addRow(cb_raw)
        cb_layout.addRow(QLabel('Cut-off period for sinc:'),T_c_edit)
        cb_layout.addRow(cb_trend)
        cb_layout.addRow(cb_detrend)
        cb_layout.addRow(button_layout_h)
        
        plot_options_box.setLayout(cb_layout)
        #Fix X size of plot_options_box containing parameter boxes
        size_pol= QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        plot_options_box.setSizePolicy(size_pol)
        
        ## checkbox signal set and change
        cb_raw.toggle()
        
        cb_raw.stateChanged.connect(self.toggle_raw)
        cb_trend.stateChanged.connect(self.toggle_trend)
        cb_detrend.stateChanged.connect(self.toggle_detrended)
        
        self.plot_raw = bool(cb_raw.checkState() )
        self.plot_trend = bool(cb_trend.checkState() )
        self.plot_detrended = bool(cb_detrend.checkState() )
        
        #Plot box
        plot_box = QGroupBox('Signal and trend')
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.plotWindow)
        plot_layout.addWidget(ntb)
        plot_box.setLayout(plot_layout)
        
        
        #Analyzer box with tabs
        table_widget = QWidget()
        ana_box = QVBoxLayout()
 
        ## Initialize tab screen
        tabs = QTabWidget()
        tab1 = QWidget()
        tab2 = QWidget()

        ## Add tabs
        tabs.addTab(tab1,"Wavelet analysis")
        tabs.addTab(tab2,"Fourier transform")
 
        ## Create first tab
        tab1.ana_box = QFormLayout()
        
        ## for wavlet params, button, etc.
        self.T_min = QLineEdit()
        self.step_num = QLineEdit()
        self.step_num.insert('100')
        self.T_max = QLineEdit()
        self.v_max = QLineEdit()
        self.v_max.insert(str(20))
        
        T_min_lab = QLabel('Smallest period')
        step_lab = QLabel('Number of periods')
        T_max_lab = QLabel('Highest  period')
        v_max_lab = QLabel('Expected maximal power')
        
        T_min_lab.setWordWrap(True)
        step_lab.setWordWrap(True)
        T_max_lab.setWordWrap(True)
        v_max_lab.setWordWrap(True)
        
        
        wletButton = QPushButton('Analyze signal', self)
        wletButton.clicked.connect(self.run_wavelet_ana)
        
        ## add  button to layout
        wlet_button_layout_h = QHBoxLayout()

        wlet_button_layout_h.addStretch(0)
        wlet_button_layout_h.addWidget(wletButton)

        self.cb_use_detrended = QCheckBox('Use detrended signal', self)
        # self.cb_use_detrended.stateChanged.connect(self.toggle_use)
        self.cb_use_detrended.setChecked(True) # detrend by default
        self.use_detrended = bool(self.cb_use_detrended.checkState() )

        
        ## Add Wavelet analyzer options to tab1.ana_box layout
        
        tab1.ana_box.addRow(T_min_lab,self.T_min)
        tab1.ana_box.addRow(step_lab, self.step_num)
        tab1.ana_box.addRow(T_max_lab,self.T_max)
        tab1.ana_box.addRow(v_max_lab, self.v_max)
        tab1.ana_box.addRow(self.cb_use_detrended)
        tab1.ana_box.addRow(wlet_button_layout_h)
        
        tab1.setLayout(tab1.ana_box)

        # fourier button
        fButton = QPushButton('Analyze signal', self)
        ## add  button to layout
        f_button_layout_h = QHBoxLayout()
        fButton.clicked.connect(self.fourier_ana)
        f_button_layout_h.addStretch(0)
        f_button_layout_h.addWidget(fButton)

        # fourier detrended switch
        self.cb_use_detrended2 = QCheckBox('Use detrended signal', self)
        # self.cb_use_detrended2.stateChanged.connect(self.toggle_use)
        self.cb_use_detrended2.setChecked(True) # detrend by default
        self.use_detrended2 = bool(self.cb_use_detrended2.checkState() )

        ## Create second tab
        tab2.ana_box = QFormLayout()
        #tab2.ana_box.addRow(T_min_lab,self.T_min)
        #tab2.ana_box.addRow(T_max_lab,self.T_max)
        tab2.ana_box.addRow(self.cb_use_detrended2)
        tab2.ana_box.addRow(f_button_layout_h)
        tab2.setLayout(tab2.ana_box)
        
        
        #Add tabs to widget
        ana_box.addWidget(tabs)
        #set layout of table_widget (will be added to options layout) as ana_box (containing actual layout)
        table_widget.setLayout(ana_box)
        
        #Fix X size of table_widget containing parameter boxes
        size_pol= QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        table_widget.setSizePolicy(size_pol)
        

        #Options box (big box)
        #options_box = QGroupBox('Options')
        #options_layout=QFormLayout()
        #options_layout.addRow(plot_options_box)
        #options_layout.addRow(table_widget)
        
        #options_box.setLayout(options_layout)
        
        #Merge all layout in main layout
        horizontalGroupBox = QGroupBox('Input data')
        layout = QGridLayout()
        layout.addWidget(DataTable,0,0,3,6)
        layout.addWidget(plot_box, 4,0,4,5)
        layout.addWidget(plot_options_box, 4,5,2,1)
        layout.addWidget(table_widget, 6,5,2,1)
        # layout.addWidget(options_box, 3,4,4,2)
        horizontalGroupBox.setLayout(layout)

        main_layout_v.addWidget(horizontalGroupBox)

        # populate signal selection box
        SignalBox.addItem('') # empty initial selector

        for col in self.df.columns:
            SignalBox.addItem(col)
            
        # connect to plotting machinery
        SignalBox.activated[str].connect(self.select_signal_and_Plot)
        self.SignalBox = SignalBox # to modify current index by table selections
        
        # initialize parameter fields
        dt_edit.textChanged[str].connect(self.qset_dt)
        dt_edit.insert(str(1)) # initial sampling interval is 1

        T_c_edit.textChanged[str].connect(self.qset_T_c)

        unit_edit.textChanged[str].connect(self.qset_time_unit)
        unit_edit.insert( 'min' ) # standard time unit is minutes

        
        self.setLayout(main_layout_v)
        self.show()

        # trigger initial plot?!
        # self.select_signal_and_Plot(self.df.columns[0])

    # when clicked into the table
    def Table_select(self,qm_index):
        # recieves QModelIndex
        col_nr = qm_index.column()
        self.SignalBox.setCurrentIndex(col_nr + 1)
        if DEBUG:
            print('table column number clicked:',col_nr)
        self.signal_id = self.df.columns[col_nr] # DataFrame column name
        self.doPlot()

    # when clicked on the header
    def Header_select(self,index):
        # recieves index
        col_nr = index
        self.SignalBox.setCurrentIndex(col_nr + 1)

        if DEBUG:
            print('table column number clicked:',col_nr)
        self.signal_id = self.df.columns[col_nr] # DataFrame column name
        self.doPlot()

        
    # the signal to work on, connected to selection box
    def select_signal_and_Plot(self, text):
        self.signal_id = text
        succ =  self.vector_prep() # fix a raw_signal + time vector
        if not succ: # error handling done in data_prep
            print('Could not load', self.signal_id)
            return
        self.set_initial_periods()
        self.doPlot()


    # probably all the toggle state variables are not needed -> read out checkboxes directly
    def toggle_raw (self, state):
        if state == Qt.Checked:
            self.plot_raw = True
        else:
            self.plot_raw = False

        # signal selected?
        if self.signal_id:
            self.doPlot()

        
    def toggle_trend (self, state):
        print (self.plot_trend)
        if state == Qt.Checked:
            self.plot_trend = True
        else:
            self.plot_trend = False

        # signal selected?
        if self.signal_id:
            self.doPlot()
        
    def toggle_detrended (self, state):
        if state == Qt.Checked:
            self.plot_detrended = True
            #self.cb_use_detrended.setCheckState(Qt.Checked)
        else:
            self.plot_detrended = False
            #self.cb_use_detrended.setCheckState(Qt.Unchecked)

        # signal selected?
        if self.signal_id:
            self.doPlot()

    #connected to unit_edit
    def qset_time_unit(self,text):
        self.time_unit = text #self.unit_edit.text()
        if DEBUG:
            print('time unit changed to:',text)


    # connected to dt_edit 
    def qset_dt(self, text):
        t = text

        # checking the input is done automatically via .setValidator!
        # check,str_val,_ = self.posfloatV.validate(t,  0) # pos argument not used

        try:
            self.dt = float(t)
            self.set_initial_periods()
            # update period Validator
            self.periodV = QDoubleValidator(bottom = 2*self.dt,top = 1e16)


        # empty input
        except ValueError:
            pass
        
        if DEBUG:
            print('dt set to:',self.dt)


    # connected to T_c_edit
    def qset_T_c(self, text):
        tc = text
        # value checking done by validator

        try:
            self.T_c = float(tc)

        # empty line edit
        except ValueError:
            pass

        if DEBUG:
            print('T_c set to:',self.T_c)

        
    def set_initial_periods(self):
        
        self.T_min.clear()
        self.T_max.clear()
        self.T_min.insert(str(2*self.dt)) # Nyquist
        if np.any(self.raw_signal): # check if raw_signal already selected
            self.T_max.insert(str(self.dt*0.5*len(self.raw_signal))) # half the observation time

    # retrieve and check set wavelet paramers
    def set_wlet_pars (self):

        # period validator
        vali = self.periodV
        
        T_min = self.T_min.text()
        check,_,_ = vali.validate(T_min, 0)
        if DEBUG:
            print('Min periodValidator output:',check, 'value:',T_min)
        if check == 0:
            self.OutOfBounds = Error("Wavelet periods out of bounds!","Value Error")
            return False
        self.T_min_value = float(T_min)

        step_num = self.step_num.text()
        check,_,_ = self.posintV.validate(step_num, 0)
        if DEBUG:
            print('# Periods posintValidator:',check, 'value:', step_num)
        if check == 0:
            self.OutOfBounds = Error("Number of periods must be a positive integer!","Value Error")
            return False
        self.step_num_value = int(step_num)

        T_max = self.T_max.text()
        check,_,_ = vali.validate(T_max, 0)
        if DEBUG:
            print('Max periodValidator output:',check)
        if check == 0:
            self.OutOfBounds = Error("Wavelet periods out of bounds!","Value Error")
            return False
        self.T_max_value = float(T_max)

        v_max = self.v_max.text()
        check,_,_ = self.posfloatV.validate(v_max, 0) # checks for positive float
        if check == 0:
            self.OutOfBounds = Error("Powers are positive!", "Value Error")
            return False

        self.v_max_value = float(v_max)
        
        # success!
        return True
        
    def vector_prep(self):
        ''' prepares signal vector (NaN removal) and
        corresponding time vector '''
        
        print('trying to prepare', self.signal_id)

        # checks for empty signal_id string
        if self.signal_id:
            print('preparing signal',self.signal_id)
            self.raw_signal = self.df[self.signal_id]

            # remove NaNs
            self.raw_signal =self.raw_signal[~np.isnan(self.raw_signal)]
            self.tvec =np.arange(0,len(self.raw_signal)*self.dt,self.dt)
            return True # success
            
        else:
            self.NoSignalSelected = Error('Please select a signal!','No Signal')
            return False

        
    def doPlot(self):
        # update raw_signal and tvec
        succ = self.vector_prep() # error handling done here
        if not succ:
            return False

        print("called Plotting [raw] [trend] [derended]",self.plot_raw,self.plot_trend,self.plot_detrended)
        # no trend plotting without T_cut_off value is set by user
        if self.T_c and (self.plot_trend or self.plot_detrended):
                
            self.trend = wl.sinc_smooth(raw_signal = self.raw_signal,T_c = self.T_c, dt = self.dt)
                
        else:
            self.trend = None

        # call the plotting routine
        self.plotWindow.mpl_update(self.tvec, self.raw_signal, self.trend, plot_raw= self.plot_raw, plot_trend=self.plot_trend, plot_detrended=self.plot_detrended, time_unit = self.time_unit)


    def run_wavelet_ana(self):
        ''' run the Wavelet Analysis '''

        if not np.any(self.raw_signal):
            self.NoSignalSelected = Error('Please select a signal first!','No Signal')
            return False
        
        succ = self.set_wlet_pars() # Error handling done there
        if not succ:
            if DEBUG:
                print('Wavelet parameters could not be set!')
            return False
        
        if self.step_num_value > 1000:
            
            choice = QMessageBox.question(self, 'Too much periods?: ',
                                            'High number of periods: Do you want to continue?',
                                            QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.Yes:
                pass
            else:
                return


        if self.cb_use_detrended.isChecked() and not np.any(self.trend):
            self.NoTrend = Error('No trend calculated yet, can not use detrended signal!','No Trend')
            return

        if self.cb_use_detrended.isChecked():
            signal= self.raw_signal-self.trend
        else:
            signal= self.raw_signal
            
        self.w_position += 20
        
        self.anaWindows[self.w_position] = WaveletAnalyzer(signal=signal, dt=self.dt, T_min= self.T_min_value, T_max= self.T_max_value, position= self.w_position, signal_id =self.signal_id, step_num= self.step_num_value, v_max = self.v_max_value, time_unit= self.time_unit)

    def fourier_ana(self):

        self.w_position += 20

        if self.cb_use_detrended2.isChecked() and self.T_c.isModified():
            signal= self.raw_signal-self.trend
        else:
            signal= self.raw_signal
        
        self.anaWindows[self.w_position] = FourierAnalyzer(signal = signal, dt = self.dt, signal_id = self.signal_id, position = self.w_position, time_unit = self.time_unit)


class FourierAnalyzer(QWidget):
    def __init__(self, signal, dt, signal_id, position,time_unit, parent = None):
        super().__init__()

        self.fCanvas = FourierCanvas()
        self.fCanvas.plot_spectrum(signal,dt, time_unit)

        self.initUI(position, signal_id)

    def initUI(self, position, signal_id):

        self.setWindowTitle('Fourier spectrum ' + signal_id)
        self.setGeometry(510+position,30+position,550,600)

        main_frame = QWidget()
        self.fCanvas.setParent(main_frame)
        ntb = NavigationToolbar(self.fCanvas, main_frame)

        main_layout = QGridLayout()
        main_layout.addWidget(self.fCanvas,0,0,9,1)
        main_layout.addWidget(ntb,10,0,1,1)

        # test canvas resize
        # dummy_h = QHBoxLayout()
        # dummy_h.addStretch(0)
        # button = QPushButton('push me', self)
        # dummy_h.addWidget(button)
        # main_layout.addLayout(dummy_h,11,0)
        
        self.setLayout(main_layout)
        self.show()
        
class FourierCanvas(FigureCanvas):
    def __init__(self):
        self.fig, self.axs = plt.subplots(1,1)

        FigureCanvas.__init__(self, self.fig)

        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
    def plot_spectrum(self,signal,dt, time_unit):

        #time_label = '[min]'

        N = len(signal)
        
        df = 1./(N*dt) # frequency bins
        fft_freqs = np.arange(0,1./(2*dt)+df+df/2., step = df) # prevent rounding errors
        rf = rfft(signal) # positive frequencies
        
        print(N,dt,df)
        print(len(fft_freqs),len(rf))
        
        print('Fourier power: ', max(np.abs(rf)))
        fpower = np.abs(rf)/np.var(signal)
        print('Fourier power/var: ', max(fpower))


        # period view
        # self.axs.plot(1/fft_freqs[1:-1],fpower[1:],lw = 1.8, alpha = 0.8)
        self.axs.vlines(1/fft_freqs[1:-1],0,fpower[1:],lw = 1.8, alpha = 0.8)
        self.axs.set_xlabel('Periods ' + time_unit, fontsize = label_size)
        self.axs.set_ylabel('Fourier power', fontsize = label_size)
        self.axs.ticklabel_format(style='sci',axis='y',scilimits=(0,0))
        self.axs.tick_params(axis = 'both',labelsize = tick_label_size)


class WaveletAnalyzer(QWidget):

    def __init__(self, signal, dt, T_min, T_max, position, signal_id, step_num, v_max, time_unit):
        super().__init__()
        self.signal_id = signal_id
        self.signal = signal
        self.v_max = v_max
        self.time_unit = time_unit

        self.periods=np.linspace(T_min, T_max, step_num)
        #self.periods = periods
        
        print (self.periods[-1])
        
        # Plot input signal
        self.tvec = np.arange(0,len(signal)*dt,dt)
        #self.tvec = tvec

        # no ridge yet
        self.rdata = None
        #self._has_ridge = False # no plotted ridge

        #=============Compute Spectrum============================
        self.modulus, self.wlet = wl.compute_spectrum(self.signal, dt, self.periods)
        #========================================================
        
        
        self.initUI(position)
        
    def initUI(self, position):
        self.setWindowTitle('WaveletAnalyzer - '+str(self.signal_id))
        self.setGeometry(510+position,30+position,600,700)
        
        # Wavelet and signal plot
        self.waveletPlot = SpectrumCanvas()
        main_frame = QWidget()
        self.waveletPlot.setParent(main_frame)
        ntb = NavigationToolbar(self.waveletPlot, main_frame) # full toolbar

        #-------------plot the wavelet power spectrum---------------------------
        self.waveletPlot.plot_signal_modulus(self.tvec, self.signal,self.modulus,self.periods, self.v_max, self.time_unit)
        #-----------------------------------------------------------------------
        
        #Save output
        saveButton = QPushButton('Save', self)
        saveButton.clicked.connect(self.save_out)
        
        #Analyzer box with tabs
        table_widget = QWidget()
        ridge_opt_box = QVBoxLayout()
 
        ## Initialize tab screen
        tabs = QTabWidget()
        tab1 = QWidget()
        tab2 = QWidget()

        ## Add tabs
        tabs.addTab(tab2,'Trace maxima')
        tabs.addTab(tab1,'Simulated annealing')
 
        ## Create first tab
        tab1.ridge_opt_box = QFormLayout()

        #Start ridge detection
        ridgeButton2 = QPushButton('Detect maxRidge!', self)
        # ridgeButton2.setFixedHeight(20) # has almost no effect
        ridgeButton2.clicked.connect(self.do_maxRidge_detection)

        ridgeButton1 = QPushButton('Detect annealRidge!', self)
        ridgeButton1.clicked.connect(self.do_annealRidge_detection)
        
        #saveButton_hbox = QHBoxLayout()

        self.power_thresh = None
        self.power_thresh_tb = QLineEdit()
        self.power_thresh_tb.textChanged.connect(self.read_power_thresh)
        self.power_thresh_tb.insert('0')

        # anneal parameters
        self.per_ini = QLineEdit(str(int(np.mean(self.periods)))) # start at middle of period interval
        self.T_ini = QLineEdit('1')
        self.Nsteps = QLineEdit('5000')
        self.max_jump = QLineEdit('3')
        self.curve_pen = QLineEdit('0')
        
        power_thresh_lab = QLabel('Power threshold')
        per_ini_lab = QLabel('Initial period guess')
        T_ini_lab = QLabel('Initial temperature')
        Nsteps_lab = QLabel('Number of iterations')
        max_jump_lab = QLabel('Maximal jumping distance')
        curve_pen_lab = QLabel('Curvature cost')

        power_thresh_lab.setWordWrap(True)
        per_ini_lab.setWordWrap(True)
        T_ini_lab.setWordWrap(True) 
        Nsteps_lab.setWordWrap(True) 
        max_jump_lab.setWordWrap(True)
        curve_pen_lab.setWordWrap(True)
        
        #Copy of powerth
        power_thresh2_tb = QLineEdit()
        power_thresh2_tb.textChanged.connect(self.read_power_thresh)
        power_thresh2_tb.insert('0')
        power_thresh_lab2 = QLabel('Power threshold')

        # anneal parameters end
        
        ridgebutton2_h = QHBoxLayout()
        ridgebutton2_h.addWidget(ridgeButton2)
        #buttons_hbox.addWidget(ridgeButton2)
        #buttons_hbox.addWidget(saveButton)
        ridgebutton2_h.addStretch(0)

        ridgebutton1_h = QHBoxLayout()
        ridgebutton1_h.addWidget(ridgeButton1)
        #buttons_hbox.addWidget(saveButton)
        ridgebutton1_h.addStretch(0)
        
        
        grid_lay = QGridLayout()
        #grid_lay.addWidget(self.waveletPlot, 0,0,5,5)
        grid_lay.addWidget(power_thresh_lab, 0,0,1,1)
        grid_lay.addWidget(self.power_thresh_tb, 0,1,1,1)
        grid_lay.addWidget( per_ini_lab, 1,0,1,1)
        grid_lay.addWidget(self.per_ini, 1,1,1,1)
        grid_lay.addWidget(T_ini_lab, 2,0,1,1)
        grid_lay.addWidget(self.T_ini, 2,1,1,1)
        grid_lay.addWidget(Nsteps_lab, 0,2,1,1)
        grid_lay.addWidget(self.Nsteps, 0,3,1,1)
        grid_lay.addWidget(max_jump_lab, 1,2,1,1)
        grid_lay.addWidget(self.max_jump, 1,3,1,1)
        grid_lay.addWidget(curve_pen_lab, 2,2,1,1)
        grid_lay.addWidget(self.curve_pen, 2,3,1,1)
        
        grid = QWidget()
        grid.setLayout(grid_lay)

        tab1.ridge_opt_box.addRow(grid)
        tab1.ridge_opt_box.addRow(ridgebutton1_h)
        
        tab1.setLayout(tab1.ridge_opt_box)
        
        ## Create second tab
        tab2.ridge_opt_box = QFormLayout()
        tab2.ridge_opt_box.addRow(power_thresh_lab2,power_thresh2_tb)
        tab2.ridge_opt_box.addRow(ridgebutton2_h)
        tab2.setLayout(tab2.ridge_opt_box)
        
        #Add tabs to widget
        ridge_opt_box.addWidget(tabs)
        #set layout of table_widget (will be added to options layout) as ridge_opt_box (containing actual layout)
        table_widget.setLayout(ridge_opt_box)
        size_pol= QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        table_widget.setSizePolicy(size_pol)
        #table_widget.updateGeometry(self)
        
        #box_layout.addLayout(tab1.ridge_opt_box)
        
        #box_layout.addLayout(buttons_hbox)
        #big_box.setLayout(box_layout)
        
        savebutton_h = QHBoxLayout()
        savebutton_h.addWidget(saveButton)
        savebutton_h.addStretch(0)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.waveletPlot)
        main_layout.addWidget(ntb)
        main_layout.addWidget(table_widget)
        # main_layout.addLayout(savebutton_h)
        self.setLayout(main_layout)
        
        self.show()

    def read_power_thresh(self, text):
        
        try:
            power_thresh = float(text)
        except ValueError:
            print('except')
            self.e = Error('Enter positive number (or 0) for Wavelet power threshold!','Value Error')
            return
        
        if power_thresh < 0:
            print('<0')
            self.e = Error('Enter positive number (or 0) for Wavelet power threshold!','Value Error')
            return
        print('read power thresh', power_thresh)
        self.power_thresh = power_thresh

    def do_maxRidge_detection(self):
        #print(self.RidgeMSelection.currentText())
        #print(self.power_thresh_tb.text())
        

        ridge_y = wl.get_maxRidge(self.modulus)

        rdata = wl.mk_rdata(ridge_y,self.modulus,self.wlet,self.periods,self.tvec,Thresh = self.power_thresh, smoothing = True, win_len = 17)

        if not rdata:
            self.e = Error('No ridge found..check spectrum!','Ridge detection error')
            return
        
        self.rdata = rdata

        # plot the ridge
        ax_spec = self.waveletPlot.axs[1] # the spectrum

        # already has a plotted ridge
        if ax_spec.lines:
            ax_spec.lines.pop() # remove old one
            
        ax_spec.plot(rdata['time'],rdata['periods'],'o',color = 'crimson',alpha = 0.6,ms = 3)
        # refresh the canvas
        self.waveletPlot.draw()

    def do_annealRidge_detection(self):

        # todo add out-of-bounds parameter check
        per_ini = float(self.per_ini.text())
        T_ini = float(self.T_ini.text())
        Nsteps = int(self.Nsteps.text())
        max_jump = int(self.max_jump.text())
        curve_pen = float(self.curve_pen.text())

        # get modulus index of initial straight line ridge
        y0 = np.where(self.periods < per_ini)[0][-1]

        ridge_y, cost = wl.find_ridge_anneal(self.modulus,y0,T_ini,Nsteps,mx_jump = max_jump,curve_pen = curve_pen)

        rdata = wl.mk_rdata(ridge_y,self.modulus,self.wlet,self.periods,self.tvec,Thresh = self.power_thresh, smoothing = True, win_len = 17)

        if not rdata:
            self.e = Error('No ridge found..check spectrum!','Ridge detection error')
            return
        
        self.rdata = rdata
        
        # plot the ridge
        ax_spec = self.waveletPlot.axs[1] # the spectrum

        # already has a plotted ridge
        if ax_spec.lines:
            ax_spec.lines.pop() # remove old one

        ax_spec.plot(rdata['time'],rdata['periods'],'o',color = 'crimson',alpha = 0.6,ms = 3)
        # refresh the canvas
        self.waveletPlot.draw()
        
    def save_out (self):
        dialog = QFileDialog()
        options = QFileDialog.Options()
        #options = QFileDialog.DontUseNativeDialog
        #file_name, _ = dialog.getSaveFileName(self,"Save as","","All Files (*);;Text Files (*.txt);; Image Files (*.png)", options=options)
        file_name, _ = dialog.getSaveFileName(self,"Save as","","Text Files (*.txt);; Image Files (*.png)", options=options)

        if not self.rdata:
            print('no ridge data!')
            # no ridge detection performed -> show warning/error window
            return
        
        print('ridge data keys:', self.rdata.keys())
        df_out = pd.DataFrame()

        # add everything to data frame
        for key in self.rdata:
            df_out[key] = self.rdata[key]
            

        
        if file_name:
            print (_)
            #_.selectedNameFilter()
            print(file_name)
    
        ##save_dialog = QFileDialog()
        #file_name = QFileDialog.getOpenFileName(self, 'Open File')
        ##save_dialog.setAcceptMode(QFileDialog.AcceptSave)
        #save_dialog.setFilter(['*.png', '*.jpg'])
        #save_dialog.setOption(QFileDialog.DontConfirmOverwrite, False)
        ##file_name = save_dialog.getSaveFileName()
        ##print (file_name[0])
        ##if save_dialog.exce():
        ##    self.waveletPlot.save(file_name[0])
            t= 'test'

            # choose what to write out
            obs_list = ['time','periods','amplitudes']
            df_out[ obs_list ].to_csv(file_name, sep = '\t', index = False)
            
            # f = open( file_name, 'w' )
            # f.write( str(self.rdata['time']) + str(self.rdata['periods']) )
            # f.close()
        else: 
            self._error = Error('No valid file name!','File name error')
        
        #self.waveletPlot.save(file_name)

            
class SpectrumCanvas(FigureCanvas):
    def __init__(self, parent=None): #, width=6, height=3, dpi=100):
        self.fig, self.axs = plt.subplots(2,1,gridspec_kw = {'height_ratios':[1, 2.5]}, sharex = True)
        
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        
    def plot_signal_modulus(self,tvec, signal,modulus,periods, v_max, time_unit):
        
        # self.fig.clf() # not needed as only once initialised?!
        sig_ax = self.axs[0]
        mod_ax = self.axs[1]

        # Plot Signal

        sig_ax.plot(tvec, signal, color = 'black', lw = .75, alpha = 0.7)
        sig_ax.plot(tvec, signal, '.', color = 'black', ms = 3., alpha = 0.7)
        sig_ax.set_ylabel('signal [a.u.]', fontsize = label_size) 
        sig_ax.ticklabel_format(style='sci',axis='y',scilimits=(0,0))
        sig_ax.tick_params(axis = 'both',labelsize = tick_label_size)
        # Plot Wavelet Power Spectrum
        
        # aspect = len(tvec)/len(periods)
        im = mod_ax.imshow(modulus[::-1], cmap = 'viridis', vmax = v_max,extent = (tvec[0],tvec[-1],periods[0],periods[-1]),aspect = 'auto')
        mod_ax.set_ylim( (periods[0],periods[-1]) )
        mod_ax.set_xlim( (tvec[0],tvec[-1]) )

        min_power = modulus.min()
        cb_ticks = [np.ceil(min_power),v_max]
        cb = self.fig.colorbar(im,ax = mod_ax,orientation='horizontal',fraction = 0.08,shrink = .6, pad = 0.25, ticks = cb_ticks)
        #cb.set_label('$|\mathcal{W}_{\Psi}(t,T)|^2$',rotation = '0',labelpad = 5,fontsize = 15)
        cb.set_label('Wavelet power',rotation = '0',labelpad = -5,fontsize = 10)

        mod_ax.set_xlabel('time (' + time_unit + ')', fontsize = label_size) 
        mod_ax.set_ylabel('period (' + time_unit + ')', fontsize = label_size)
        mod_ax.tick_params(axis = 'both',labelsize = tick_label_size)
        plt.subplots_adjust(bottom = 0.11, right=0.95,left = 0.13,top = 0.95)
        self.fig.tight_layout()
        
    def save (self, signal_id):
        self.fig.savefig(signal_id)

### end from wavelet_lib


class Detrender (DataViewer):
    def __init__(self):
        super().__init__()
        self.default_para_dic = {'T' : 900, 'amp' : 6, 'per' : 70, 'sigma' : 2, 'slope' : -10.}
        self.gen_func = synth_signal1
        self.raw_data= pd.DataFrame()
        self.series_ids = []
        
        
    def data_input(self):
        print ('Detrender data_input called')
        self.table = NumericParameterDialog(self.default_para_dic) #table needs to be QWidget
        pdic = self.table.read()
        
        tvec, signal = self.gen_func( **pdic)
        self.raw_data['synthetic siganl1_{}'.format(pdic)] = signal
        #self.series_ids.append('synthetic siganl1_{}'.format(pdic))










class SyntheticSignalGenerator(QWidget):
    ''' 
    tvec: array containing the time vector
    signal: array containing the signal or 'synthetic' if synthetic signal shall be used
    default_para_dic: dictonary containing default parameters for synthetic signal creation


    '''
    # Added a signal, that emits signal name, tvec and signal values
    DataTransfer = pyqtSignal('PyQt_PyObject')  #########################

    def __init__(self,gen_func, default_para_dic): 
        super().__init__()
        self.default_para_dic = default_para_dic
        self.gen_func = gen_func

        if DEBUG:
            print ('default para{}'.format(self.default_para_dic))

        #self.initUI()
           
        
        

    def initUI(self):

        self.plotWindow = TimeSeriesCanvas('Synthetic Signal')

        self.setWindowTitle('Synthetic Signal Generator')
        self.setGeometry(300,300,450,550) #???

        main_layout_v = QVBoxLayout()
        button_layout_h = QHBoxLayout()

        # add/create dialog
        self.dialog = NumericParameterDialog(self.default_para_dic)

        main_layout_v.addWidget(self.plotWindow)
        main_layout_v.addWidget(self.dialog)

        # Create a plot button in the window                                                                     
        plotButton = QPushButton('Save / Plot signal', self)
        # connect button to function save_on_click                                                          
        plotButton.clicked.connect(self.doPlot)
        
        button_layout_h.addStretch(1)
        button_layout_h.addWidget(plotButton)
        
        main_layout_v.addLayout(button_layout_h)
        
        # TODO button to reset to default parameters        

        
        self.setLayout(main_layout_v)
        if DEBUG:
            print ('Showing Syn Plot')
        self.show()
        if DEBUG:
            print ('Closing Syn Plot')

    def doPlot(self):
        if DEBUG:
            if not self.gen_func:
                raise ValueError('No gen_func supplied')
        pdic = self.dialog.read()
        print('Plotting with {}'.format(pdic))
        tvec, signal = self.gen_func( **pdic)
        
        self.DataTransfer.emit(['synthetic signal1_{}'.format(pdic),signal])
        self.plotWindow.mpl_update(tvec, signal)

class NumericParameterDialog(QDialog):

    def __init__(self,default_para_dic):
        super().__init__()
        self.default_para_dic = default_para_dic
        self.input_fields ={} #holds para_names:textbox
        self.para_dic = self.default_para_dic.copy()

        self.createFormGroupBox()

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        
        self.setLayout(mainLayout)
        self.show()
        

    def createFormGroupBox(self):

        self.formGroupBox = QGroupBox('Parameters')
        layout = QFormLayout()
        for par_name, value in self.default_para_dic.items():
            textbox = QLineEdit()
            textbox.insert(str(value))
            layout.addRow(QLabel(par_name),textbox)
            self.input_fields[par_name] = textbox
        
        self.formGroupBox.setLayout(layout)
    
    def read(self):

        for pname in self.para_dic.keys():

            textbox = self.input_fields[pname]
            textboxString = textbox.text()

            self.para_dic[pname] = float(textboxString)

        return self.para_dic
        
        

class TimeSeriesCanvas(FigureCanvas):
    def __init__(self, parent=None, width=4, height=3, dpi=100):
        fig = Figure(figsize=(width,height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        #self.axes.set_xlabel('time')

        #if not signal:
        #    raise ValueError('No time or signal supplied') ###gen_func

        FigureCanvas.__init__(self, fig)
        #self.setParent(parent)
        
        print ('Time Series Size', FigureCanvas.sizeHint(self))
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
    def mpl_update(self, tvec, signal, clear = True):

        if DEBUG:
            print('mpl update called with {}, {}'.format(tvec[:10], signal[:10]))

        if clear:
            self.axes.cla()
        self.axes.plot(tvec, signal)
        self.draw()
        self.show()

class TimeSeriesViewerCanvas(FigureCanvas):

    # dpi != 100 looks wierd?!
    def __init__(self, parent=None, width=4, height=3, dpi=100):
        self.fig1 = Figure(figsize=(width,height), dpi=dpi)
        self.fig1.clf()
        #self.axes.set_xlabel('time')

        #if not signal:
        #    raise ValueError('No time or signal supplied') ###gen_func

        FigureCanvas.__init__(self, self.fig1)
        self.setParent(parent)
        
        # print ('Time Series Size', FigureCanvas.sizeHint(self))
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
    def mpl_update(self, tvec, signal,trend, plot_raw, plot_trend, plot_detrended,time_unit, clear = True):
        self.fig1.clf()
        ax1 = self.fig1.add_subplot(111)

        if DEBUG:
            print('mpl update called with {}, {}'.format(tvec[:10], signal[:10]))

        if clear:
            ax1.cla()
            
        if plot_raw:
            ax1.plot(tvec,signal,lw = 1.5, color = 'royalblue',alpha = 0.8)
            
        if trend is not None and plot_trend:
            ax1.plot(tvec,trend,color = 'orange',lw = 1.5)
            
        if trend is not None and plot_detrended:
            ax2 = ax1.twinx()
            ax2.plot(tvec, signal - trend,'-', color = 'k',lw = 1.5, alpha = 0.6) 
            ax2.set_ylabel('detrended', fontsize = label_size)
            ax2.ticklabel_format(style='sci',axis='y',scilimits=(0,0))
    
        ax1.set_xlabel('time (' + time_unit + ')', fontsize = label_size) 
        ax1.set_ylabel(r'signal', fontsize = label_size) 
        ax1.ticklabel_format(style='sci',axis='y',scilimits=(0,0))
        ax1.tick_params(axis = 'both',labelsize = tick_label_size)

        self.fig1.subplots_adjust(bottom = 0.15,left = 0.15, right = 0.85)

        self.draw()
        self.show()
    

        

# test case for data generating function, standard synthetic signal
def synth_signal1(T, amp, per, sigma, slope):  
    
    tvec = np.arange(T)
    trend = slope*tvec**2/tvec[-1]**2*amp
    noise = np.random.normal(0,sigma, len(tvec))
    sin = amp*np.sin(2*np.pi/per*tvec)+noise+trend

    return tvec, sin
        
    

class Error(QWidget):
    def __init__(self, message,title):
        super().__init__()
        self.message = message
        self.title = title
        self.initUI()
       
    def initUI(self):
        error = QLabel(self.message)
        self.setGeometry(300,300,220,100)
        self.setWindowTitle(self.title)
        okButton = QPushButton('OK', self)
        okButton.clicked.connect(self.close)
        main_layout_v = QVBoxLayout()
        main_layout_v.addWidget(error)
        main_layout_v.addWidget(okButton)
        self.setLayout(main_layout_v)
        self.show()

class ValidateValue(QWidget):
    ''' Error message plus Validator handling '''
            
    def __init__(self, validator, str_value, message,title = 'Value Error'):
        super().__init__()
        self.message = message
        self.title = title
            
        # check the value with the validator, pos is 0
        result, str_val, _ = validator(str_value, 0)
        self.result = result

        # show error message only when invalid
        if result == 0:
            self.initUI()

        
    def initUI(self):
        error = QLabel(self.message)
        self.setGeometry(300,300,220,100)
        self.setWindowTitle(self.title)
        okButton = QPushButton('OK', self)
        okButton.clicked.connect(self.close)
        main_layout_v = QVBoxLayout()
        main_layout_v.addWidget(error)
        main_layout_v.addWidget(okButton)
        self.setLayout(main_layout_v)
        self.show()

            
            
if __name__ == '__main__':

    app = QApplication(sys.argv)
    pdic = {'T' : 900, 'amp' : 6, 'per' : 70, 'sigma' : 2, 'slope' : -10.}



    #dt = 1
    #T_c = 100
    tvec, raw_signal = synth_signal1(**pdic)

    #pDialog = SyntheticSignalGenerator(synth_signal1, pdic)
    #pDialog2 = Detrender()
    #pDialog2.make_connection(pDialog)
    #detrDialog = InterActiveTimeSeriesPlotter(tvec, detrend, pdic)
    
    #open_file = DataLoader()
    #dh = DataHandler()
    #dh.make_connection(open_file)
    
    #testWavelet = WaveletAnalyzer()
    #test = Detrender()
    
    # raw_df = pd.read_csv('PSMexamples.csv', header=0)
    # print(raw_df.columns)

    window = MainWindow()
    window.load()
    # window.load()
    sys.exit(app.exec_())
        
