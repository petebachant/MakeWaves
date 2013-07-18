# -*- coding: utf-8 -*-
"""
Created on Sun Jun 02 08:53:07 2013

@author: Pete
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui
from mainwindow import *
import PyQt4.Qwt5 as Qwt
import sys
import wavemakerlimits as wml
import numpy as np
import daqmx
import time
from wavetsgen import Wave, ramp_ts


# Spectral parameters for random waves
bret_params = [("Significant Wave Height", 0.1),
               ("Significant Wave Period", 1.0),
               ("Scale Ratio", 1.0)]
               
jonswap_params = [("Significant Wave Height", 0.1),
                  ("Significant Wave Period", 1.0),
                  ("Scale Ratio", 1.0),
                  ("Gamma", 3.3),
                  ("Sigma A", 0.07),
                  ("Sigma B", 0.09)]
                  
nhextreme_params = [("Significant Wave Height", 6.58),
                    ("Significant Wave Period", 10.5),
                    ("Scale Ratio", 15.2),
                    ("Gamma", 3.95),
                    ("Sigma A", 0.45),
                    ("Sigma B", 0.15),
                    ("P", 4.85)]
                    
nhtypical_params = [("Significant Wave Height", 1.21),
                    ("Significant Wave Period 1", 10.0),
                    ("Significant Wave Period 2", 5.34),
                    ("Scale Ratio", 15.2),
                    ("Gamma 1", 6.75),
                    ("Gamma 2", 0.5),
                    ("P", 4.34)]
                    
pm_params = [("Wind Speed", 2.0),
             ("Scale Ratio", 1.0)]
             
rw_params = {"Bretschneider" : bret_params,
             "JONSWAP" : jonswap_params,
             "NH Extreme" : nhextreme_params,
             "NH Typical" : nhtypical_params,
             "Pierson Moscowitz" : pm_params}
                  
             
# Some universal constants
physchan = "Dev1/ao0"
samprate = 200.0
stroke_cal = 7.8564 # Volts per meter stroke or wave height?
paddle_height = 1.0
water_depth = 2.44
minperiod = 0.5
maxperiod = 5.0
max_halfstroke = 0.16
max_H_L = 0.1
max_H_D = 0.65

periods = np.round(np.load("periods.npy"), decimals=3)
maxH = np.load("maxH.npy")
minL = 2*np.pi/wml.dispsolver(2*np.pi/0.65, water_depth, decimals=2)
maxL = 2*np.pi/wml.dispsolver(2*np.pi/4.50, water_depth, decimals=2)

# Constants specific to rand waves
buffsize_rand = 65536
sub_buffsize = 128
minperiod_rand = 0.90
maxperiod_rand = 3.5
cutoff_freq = 2.0
max_H_L_rand = 0.07
max_H_d_rand = 0.50
                                      

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.wavegen = None
        
        # Add a label to the status bar
        self.slabel = QLabel()
        self.ui.statusbar.addWidget(self.slabel)
        self.slabel.setText("Stopped ")
        
        # Set up a timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        
        # Set up a control variable for parameters
        self.parameters = "HT"
        
        # Set default tab to regular waves
        self.ui.tabwidget.setCurrentIndex(0)
        
        # Initialize slider values
        self.ui.slider_height.setRange(0.0, 0.4, 0.001, 10)
        self.ui.slider_height.setValue(self.ui.spinbox_wave_height.value())
        self.ui.slider_height.setScaleMaxMajor(12)
        
        self.ui.slider_horiz.setRange(0.5, 5, 0.001, 10)
        self.ui.slider_horiz.setScaleMaxMajor(12)
        self.ui.slider_horiz.setValue(self.ui.spinbox_wave_period.value())
        
        # Initialize wavelength value
        wl = 2*np.pi/wml.dispsolver(2*np.pi/1.0, water_depth, decimals=2)
        self.ui.spinbox_wavelength.setValue(wl)
        
        # Connect signals and slots using function defined below
        self.connectslots()
        
        # Initialize plot settings
        self.initialize_plots()
        
        # Add dock widgets to right dock widget area and tabify them
        self.tabifyDockWidget(self.ui.dock_time_series,
                              self.ui.dock_spectrum)
               
    
    def initialize_plots(self):
        # Create time series plot
        self.plot_ts = self.ui.plot_ts
        self.plot_ts.setCanvasBackground(Qt.white)
        self.grid = Qwt.QwtPlotGrid()
        self.grid.attach(self.plot_ts)
        self.grid.setPen(QPen(Qt.black, 0, Qt.DotLine))
        self.curve_ts = Qwt.QwtPlotCurve('')
        self.curve_ts.setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
        self.pen = QPen(QColor('black'))
        self.pen.setWidth(0)
        self.curve_ts.setPen(self.pen)
        self.curve_ts.attach(self.plot_ts)
        
        # Create output spectrum plot
        self.plot_spec = self.ui.plot_spec
        self.plot_spec.setCanvasBackground(Qt.white)
        self.grid = Qwt.QwtPlotGrid()
        self.grid.attach(self.plot_spec)
        self.grid.setPen(QPen(Qt.black, 0, Qt.DotLine))
        self.curve_spec = Qwt.QwtPlotCurve('')
        self.curve_spec.setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
        self.pen = QPen(QColor('black'))
        self.pen.setWidth(0)
        self.curve_spec.setPen(self.pen)
        self.curve_spec.attach(self.plot_spec)

        
    def connectslots(self):
        self.ui.spinbox_wave_height.valueChanged.connect(self.on_wh_changed)
        self.ui.spinbox_wave_period.valueChanged.connect(self.on_wp_changed)
        self.ui.spinbox_wavelength.valueChanged.connect(self.on_wl_changed)
        self.ui.action_about.triggered.connect(self.on_about)
        self.ui.combobox_randwavetype.currentIndexChanged.connect(self.on_rw_changed)
        self.ui.action_start.triggered.connect(self.on_start)
        self.ui.combobox_regparams.currentIndexChanged.connect(self.on_regpars)
        self.ui.action_wiki.triggered.connect(self.on_wiki)
        self.ui.slider_height.sliderMoved.connect(self.on_slider_height)
        self.ui.slider_horiz.sliderMoved.connect(self.on_slider_horiz)
    
        
    def on_timer(self):
        self.update_plot()
        
        
    def update_plot(self):
        # Plot output time series
        if self.wavegen.making:
            ydata = self.wavegen.ts_plot
            xdata = np.asarray(np.arange(len(ydata))/self.wavegen.sr)
            self.plot_ts.setAxisScale(Qwt.QwtPlot.xBottom, 0, xdata[-1])
            self.curve_ts.setData(xdata, ydata)
            self.plot_ts.replot()
            
        if self.wavegen.making:
            ydata = self.wavegen.outspec
            xdata = self.wavegen.outf
            self.plot_spec.setAxisScale(Qwt.QwtPlot.xBottom, 0, 5)
            self.curve_spec.setData(xdata, ydata)
            self.plot_spec.replot()
        
        
    def on_wh_changed(self):
        # Need some way to let user continue typing before changing slider
        self.ui.slider_height.setValue(self.ui.spinbox_wave_height.value())
        
        
    def on_wp_changed(self):
        wp = self.ui.spinbox_wave_period.value()
        if self.parameters == "HT":
            hmax = maxH[np.where(periods==np.round(wp, decimals=2))[0]]
            self.ui.spinbox_wave_height.setMaximum(np.mean(hmax))
            self.ui.slider_height.setRange(0, np.mean(hmax), 0.001, 10)
            wl = 2*np.pi/wml.dispsolver(2*np.pi/wp, water_depth, decimals=1)
            self.ui.spinbox_wavelength.setValue(wl)
            self.ui.slider_horiz.setValue(wp)

        
    def on_wl_changed(self):
        if self.parameters == "HL":
            wl = self.ui.spinbox_wavelength.value()
            wp = 2*np.pi/wml.revdispsolver(2*np.pi/wl, water_depth, decimals=1)
            self.ui.spinbox_wave_period.setValue(wp)
            hmax = maxH[np.where(periods==np.round(wp, decimals=2))[0]]
            self.ui.spinbox_wave_height.setMaximum(np.mean(hmax))
            self.ui.slider_height.setRange(0, np.mean(hmax), 0.001, 10)
            self.ui.slider_horiz.setValue(wl)            
        
        
    def on_slider_height(self):
        self.ui.spinbox_wave_height.setValue(self.ui.slider_height.value())
        
        
    def on_slider_horiz(self):
        if self.parameters == "HT":
            self.ui.spinbox_wave_period.setValue(self.ui.slider_horiz.value())
        elif self.parameters == "HL":
            self.ui.spinbox_wavelength.setValue(self.ui.slider_horiz.value())
        
        
    def on_regpars(self):
        """Decides which two parameters to use for regular waves"""
        if self.ui.combobox_regparams.currentIndex() == 0:
            self.parameters = "HT"
            
            wl = self.ui.spinbox_wavelength.value()
            wp = 2*np.pi/wml.revdispsolver(2*np.pi/wl, water_depth, decimals=1)
            
            self.ui.spinbox_wave_period.setEnabled(True)
            self.ui.spinbox_wavelength.setDisabled(True)
            
            self.ui.slider_horiz.setRange(0.5, 5.0, 0.001, 10)
            self.ui.slider_horiz.setValue(wp)
            
            self.ui.spinbox_wavelength.setMinimum(0)
            self.ui.spinbox_wavelength.setMaximum(30)
            self.ui.spinbox_wave_period.setMaximum(5)
            self.ui.spinbox_wave_period.setMinimum(0.5)
            
        elif self.ui.combobox_regparams.currentIndex() == 1:
            self.parameters = "HL"
            
            wp = self.ui.spinbox_wave_period.value()
            wl = 2*np.pi/wml.dispsolver(2*np.pi/wp, water_depth, decimals=1)
            
            self.ui.spinbox_wave_period.setEnabled(False)
            self.ui.spinbox_wavelength.setDisabled(False)
            
            self.ui.slider_horiz.setRange(minL, maxL, 0.001, 10)
            self.ui.slider_horiz.setValue(wl)
            
            self.ui.spinbox_wavelength.setMaximum(maxL)
            self.ui.spinbox_wavelength.setMinimum(minL)
            
        
    def on_rw_changed(self):
        self.rw_type = str(self.ui.combobox_randwavetype.currentText())
        self.rw_params = rw_params[self.rw_type]
        self.ui.table_rwaves.setRowCount(len(self.rw_params))
        row = 0
        
        for parameter, value in self.rw_params:
            self.ui.table_rwaves.setItem(row, 0, QTableWidgetItem(parameter))
            self.ui.table_rwaves.setItem(row, 1, QTableWidgetItem(str(value)))
            row += 1

        
    def on_start(self):
        if self.ui.action_start.isChecked() == True:
            """Make waves"""
            self.ui.action_start.setText("Stop ")
            self.ui.action_start.setToolTip("Stop Generating Waves")
            self.ui.action_start.setIcon(QIcon(":icons/agt_stop.png"))
            self.ui.tabwidget.setEnabled(False)
            
            wavetype = self.ui.tabwidget.currentIndex()
            
            if wavetype == 0:
                """Create regular waves"""
                self.slabel.setText("Generating regular waves... ")
                self.period = self.ui.spinbox_wave_period.value()
                self.height = self.ui.spinbox_wave_height.value()
                
                self.wavegen = self.WaveGen("Regular")
                self.wavegen.wave.period = self.period
                self.wavegen.wave.height = self.height
                self.wavegen.start()
                
                
            elif wavetype == 1:
                """Create random waves."""
                rspec = self.ui.combobox_randwavetype.currentText()
                self.slabel.setText("Generating " + rspec + " waves... ")
                self.wavegen = self.WaveGen(rspec)
                self.wavegen.start()
                
            self.timer.start(500)              
                
            
        elif self.ui.action_start.isChecked() == False:
            """Stop making waves"""
            self.slabel.setText("Stopping... ")
            self.wavestop = self.WaveStop(self.wavegen)
            self.wavestop.finished.connect(self.on_wave_finished)
            self.wavestop.start()
            self.ui.action_start.setEnabled(False)

            
    def on_wave_finished(self):
        self.timer.stop()
        self.update_plot()
        self.slabel.setText("Stopped ")
        self.ui.action_start.setText("Start")
        self.ui.action_start.setToolTip("Start Generating Waves")
        self.ui.action_start.setIcon(QIcon(":icons/play.png"))
        self.ui.action_start.setEnabled(True)
        self.ui.tabwidget.setEnabled(True)
        self.wavegen.clear()
        
        
    def on_about(self):
        about_text = QString("<b>MakeWaves 0.0.1</b><br>")
        about_text.append("A wave making app for the UNH tow/wave tank<br><br>")
        about_text.append("Built 6.2013 by Pete Bachant<br>")
        about_text.append("petebachant@gmail.com")
        QMessageBox.about(self, "About MakeWaves", about_text)
        
    def on_wiki(self):
        url = QUrl("http://unhtowtank.wikispaces.com/Making+Waves")
        QDesktopServices.openUrl(url)
        
    def closeEvent(self, event):
        if self.wavegen != None:
            if self.wavegen.isRunning() and not self.wavegen.cleared:
                self.wavestop = self.WaveStop(self.wavegen)
                self.wavestop.finished.connect(self.on_wave_finished)
                self.wavestop.start()
                
                
    class WaveGen(QtCore.QThread):
        def __init__(self, wavetype):
            QtCore.QThread.__init__(self)
            self.wavetype = wavetype
            self.wave = Wave(self.wavetype)
            self.enable = True
            
        def run(self):
            self.rampeddown = False
            self.cleared = False
            self.making = False
            
            # Compute the voltage time series associated with the wave
            self.wave.gen_ts_volts()
            
            # Get parameters from the wave object
            self.period = self.wave.period
            self.height = self.wave.height
            self.buffsize = self.wave.sbuffsize
            self.sr = self.wave.sr
            
            # Get data to write from the wave object
            self.ts_plot = self.wave.ts
            self.dataw = self.wave.ts_volts
            
            # If random waves, divide up time series into 64 parts
            if self.wavetype != "Regular":
                tsparts = np.zeros((64, 1024))
                for n in range(64):
                    tsparts[n, :] = self.dataw[n*1024:(n+1)*1024]
                    
                self.dataw = tsparts[0, :]
            
            # Compute spectrum for plot
            self.outf, self.outspec = self.wave.comp_spec()
            
            # Ramp time series
            rampup_ts = ramp_ts(self.dataw, "up")
            
            # Set making variable true
            self.making = True
            
            self.AOtaskHandle = daqmx.TaskHandle()
            daqmx.CreateTask("", self.AOtaskHandle)
            daqmx.CreateAOVoltageChan(self.AOtaskHandle, "Dev1/ao0", "", 
                                      -1.0, 1.0, daqmx.Val_Volts, None)
            daqmx.CfgSampClkTiming(self.AOtaskHandle, "", self.sr, 
                                   daqmx.Val_Rising, daqmx.Val_ContSamps, 
                                   self.buffsize)
                                   
            daqmx.SetWriteRegenMode(self.AOtaskHandle, 
                                    daqmx.Val_DoNotAllowRegen)
                                    
            
            def DoneCallback_py(taskHandle, status, callbackData_ptr):
                self.rampeddown = True
                print "Done"
                return 0
                
            DoneCallback = daqmx.DoneEventCallbackPtr(DoneCallback_py)
            daqmx.RegisterDoneEvent(self.AOtaskHandle, 0, DoneCallback, None)                        
            
            daqmx.WriteAnalogF64(self.AOtaskHandle, self.buffsize, False, 10.0, 
                                 daqmx.Val_GroupByChannel, rampup_ts)
                                           
            daqmx.StartTask(self.AOtaskHandle)
            
            time.sleep(self.period*0.9)

            i = 1
            
            while self.enable:
                writeSpaceAvail = daqmx.GetWriteSpaceAvail(self.AOtaskHandle)
                print "Available:", writeSpaceAvail
                
                if writeSpaceAvail >= self.buffsize:
                    
                    if self.wavetype != "Regular":
                        if i >= 64:
                            self.dataw = tsparts[i % 64, :]
                        else: 
                            self.dataw = tsparts[i, :]
                    
                    w = daqmx.WriteAnalogF64(self.AOtaskHandle, self.buffsize, False, 10.0, 
                                             daqmx.Val_GroupByChannel, self.dataw)
                    print "Wrote", w
                    print "Iteration:", i
                    i += 1
                    
                time.sleep(self.period)
            
            if self.wavetype != "Regular":
                if i >= 64:
                    self.rampdown_ts = ramp_ts(tsparts[i % 64, :], "down")
                else:
                    self.rampdown_ts = ramp_ts(tsparts[i, :], "down")
            else:
                self.rampdown_ts = ramp_ts(self.dataw, "down")
                
            daqmx.WriteAnalogF64(self.AOtaskHandle, self.buffsize, False, 10.0, 
                                     daqmx.Val_GroupByChannel, self.rampdown_ts)
            
            while True:
                pass
            
            
        def clear(self):
#            daqmx.StopTask(self.AOtaskHandle)
            daqmx.ClearTask(self.AOtaskHandle)   
            self.cleared = True
            print "Task cleared"


    class WaveStop(QtCore.QThread):
        def __init__(self, wavegen):
            QtCore.QThread.__init__(self)
            self.wavegen = wavegen
            
        def run(self):
            self.wavegen.enable = False
            print "Waiting to ramp down"
            
            while not self.wavegen.rampeddown:
                time.sleep(0.2)
               
    

def main():
    
    app = QtGui.QApplication(sys.argv)

    w = MainWindow()
    w.show()
    
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()


