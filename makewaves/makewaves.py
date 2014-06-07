# -*- coding: utf-8 -*-
"""
Created on Sun Jun 02 08:53:07 2013

@author: Pete

"""
from __future__ import division, print_function
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui
from mainwindow import *
import PyQt4.Qwt5 as Qwt
import sys
import os
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
             "Pierson-Moskowitz" : pm_params}
                  
             
# Some universal constants
paddle_height = 1.0
water_depth = 2.44
minperiod = 0.5
maxperiod = 5.0

# See if limits data exist and generate is need be
if not os.path.isfile("settings.periods.npy") or not os.path.isfile("settings.periods.npy"):
    wml.findlimits()

periods = np.round(np.load("settings/periods.npy"), decimals=4)
maxH = np.load("settings/maxH.npy")
minL = 2*np.pi/wml.dispsolver(2*np.pi/0.65, water_depth, decimals=2)
maxL = 2*np.pi/wml.dispsolver(2*np.pi/4.50, water_depth, decimals=2)

# Constants specific to rand waves
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
        hmax = maxH[np.where(periods==np.round(1, decimals=2))[0]]
        self.ui.slider_height.setRange(0.0, hmax, 0.001, 10)
        self.ui.spinbox_wave_height.setMaximum(hmax)
        self.ui.slider_height.setValue(self.ui.spinbox_wave_height.value())
        self.ui.slider_height.setScaleMaxMajor(12)
        
        self.ui.slider_horiz.setRange(0.5, 5, 0.001, 10)
        self.ui.slider_horiz.setScaleMaxMajor(12)
        self.ui.slider_horiz.setValue(self.ui.spinbox_wave_period.value())
        
        # Initialize wavelength value
        wl = 2*np.pi/wml.dispsolver(2*np.pi/1.0, water_depth, decimals=2)
        self.ui.spinbox_wavelength.setValue(wl)
        
        # Initialize plot settings
        self.initialize_plots()
        self.connectslots()        
        # Add dock widgets to right dock widget area and tabify them
        self.tabifyDockWidget(self.ui.dock_time_series,
                              self.ui.dock_spectrum)                              
        self.on_rw_changed()
        
    def setup_spinboxes(self, nboxes):  
        """Add double spin boxes to the random waves table widget"""
        self.spinboxes_rw = []
        for n in range(nboxes):
            self.spinboxes_rw.append(QDoubleSpinBox())
            self.ui.table_rwaves.setCellWidget(n, 1, self.spinboxes_rw[n])
    
    def initialize_plots(self):
        # Create time series plot
        self.plot_ts = self.ui.plot_ts
        self.plot_ts.setCanvasBackground(Qt.white)
        font = QtGui.QFont("default", pointSize=10)
        label = Qwt.QwtText("Elevation (m)")
        label.setFont(font)
        self.plot_ts.setAxisTitle(0, label)
        label.setText("Time (s)")
        self.plot_ts.setAxisTitle(2, label)
        self.grid = Qwt.QwtPlotGrid()
        self.grid.attach(self.plot_ts)
        self.grid.setPen(QPen(Qt.black, 0, Qt.DotLine))
        self.curve_ts = Qwt.QwtPlotCurve('')
        self.curve_ts.setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
        self.pen = QPen(QColor('black'))
        self.pen.setWidth(1.5)
        self.curve_ts.setPen(self.pen)
        self.curve_ts.attach(self.plot_ts)
        
        # Create output spectrum plot
        self.plot_spec = self.ui.plot_spec
        self.plot_spec.setCanvasBackground(Qt.white)
        label.setText("Spectral density")
        self.plot_spec.setAxisTitle(0, label)
        label.setText("Frequency (Hz)")
        self.plot_spec.setAxisTitle(2, label)
        self.grid = Qwt.QwtPlotGrid()
        self.grid.attach(self.plot_spec)
        self.grid.setPen(QPen(Qt.black, 0, Qt.DotLine))
        self.curve_spec = Qwt.QwtPlotCurve('')
        self.curve_spec.setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
        self.pen = QPen(QColor('black'))
        self.pen.setWidth(1.5)
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
        self.ui.action_view_ts.triggered.connect(self.ui.dock_time_series.setVisible)
        self.ui.dock_spectrum.visibilityChanged.connect(self.ui.action_view_spec.setChecked)
        self.ui.action_view_spec.triggered.connect(self.ui.dock_spectrum.setVisible)
        self.ui.dock_time_series.visibilityChanged.connect(self.on_dock_ts)
        
    def on_dock_ts(self):
        if self.ui.dock_time_series.isHidden():
            self.ui.action_view_ts.setChecked(False)
    
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
            hmax = maxH[np.where(periods==np.round(wp, decimals=2))[0][0]]
            self.ui.spinbox_wave_height.setMaximum(hmax)
            self.ui.slider_height.setRange(0, hmax, 0.001, 10)
            wl = 2*np.pi/wml.dispsolver(2*np.pi/wp, water_depth, decimals=1)
            self.ui.spinbox_wavelength.setValue(wl)
            self.ui.slider_horiz.setValue(wp)

    def on_wl_changed(self):
        if self.parameters == "HL":
            wl = self.ui.spinbox_wavelength.value()
            wp = 2*np.pi/wml.revdispsolver(2*np.pi/wl, water_depth, decimals=2)
            self.ui.spinbox_wave_period.setValue(wp)
            hmax = maxH[np.where(periods==np.round(wp, decimals=2))[0][0]]
            self.ui.spinbox_wave_height.setMaximum(hmax)
            self.ui.slider_height.setRange(0, hmax, 0.001, 10)
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
        self.setup_spinboxes(len(self.rw_params))
        row = 0
        for parameter, value in self.rw_params:
            self.ui.table_rwaves.setItem(row, 0, QTableWidgetItem(parameter))
            self.spinboxes_rw[row].setValue(value)
            self.spinboxes_rw[row].setSingleStep(0.01)
            self.spinboxes_rw[row].setAccelerated(True)
            if "Height" in parameter:
                self.spinboxes_rw[row].setMaximum(0.4)
            if "Period" in parameter:
                self.spinboxes_rw[row].setMaximum(4)
                self.spinboxes_rw[row].setMinimum(1)
            if "Scale Ratio" in parameter:
                self.spinboxes_rw[row].setDisabled(True)
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
                self.wavegen = WaveGen("Regular")
                self.wavegen.wave.period = self.period
                self.wavegen.wave.height = self.height
                self.wavegen.start()
                
            elif wavetype == 1:
                """Create random waves."""
                rspec = self.ui.combobox_randwavetype.currentText()
                self.slabel.setText("Generating " + rspec + " waves... ")
                self.wavegen = WaveGen(rspec)
                if rspec == "Bretschneider" or rspec == "JONSWAP":
                    self.wavegen.wave.sig_height = self.spinboxes_rw[0].value()
                    self.wavegen.wave.sig_period = self.spinboxes_rw[1].value()
                    self.wavegen.wave.scale_ratio = self.spinboxes_rw[2].value()
                elif rspec == "Pierson-Moskowitz":
                    self.wavegen.wave.windspeed = self.spinboxes_rw[0].value()
                    self.wavegen.wave.scale_ratio = self.spinboxes_rw[1].value()
                self.wavegen.start()
            self.timer.start(500)              
                
        elif self.ui.action_start.isChecked() == False:
            """Stop making waves"""
            self.slabel.setText("Stopping... ")
            self.wavegen.stop()
            self.wavegen.stopgen.finished.connect(self.on_wave_finished)
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
        
    def on_about(self):
        about_text = QString("<b>MakeWaves 0.0.1</b><br>")
        about_text.append("A wavemaking app for the UNH tow/wave tank<br><br>")
        about_text.append("Created by Pete Bachant (petebachant@gmail.com)<br>")
        about_text.append("with contributions by Toby Dewhurst and Matt Rowell.")
        QMessageBox.about(self, "About MakeWaves", about_text)
        
    def on_wiki(self):
        url = QUrl("http://marine.unh.edu/oelab/wiki/doku.php?id=tow_tank:operation:wavemaker")
        QDesktopServices.openUrl(url)
        
    def closeEvent(self, event):
        if self.wavegen != None:
            if self.wavegen.isRunning() and not self.wavegen.cleared:
                self.wavegen.stop()
                dialog = QtGui.QDialog()
                pbar = QtGui.QProgressBar()
                pbar.setFixedWidth(300)
                layout = QtGui.QGridLayout()
                layout.addWidget(pbar, 0, 0)
                dialog.setLayout(layout)
                dialog.setWindowTitle("Ramping down...")
                dialog.setWindowIcon(QtGui.QIcon("icons/makewaves_icon.svg"))
                dialog.show()
                progress = 0
                while not self.wavegen.cleared:
                    # The progress here is fake, just calibrated to be close
                    time.sleep(0.1)
                    progress += int(60*0.1/self.wavegen.period)
                    pbar.setValue(progress)
                dialog.close()
     
           
class WaveGen(QThread):
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
        self.ts_plot = self.wave.ts_elev
        self.dataw = self.wave.ts_volts
        
        # If random waves, divide up time series into 120 256 sample parts
        if self.wavetype != "Regular":
            tsparts = np.reshape(self.dataw, (120, 256))
            self.dataw = tsparts[0, :]
        
        # Compute spectrum for plot
        if self.wavetype == "Regular":
            self.outf, self.outspec = self.wave.comp_spec()
        else:
            self.outf, self.outspec = self.wave.f, self.wave.spec
        
        # Ramp time series
        rampup_ts = ramp_ts(self.dataw, "up")
        
        # Set making variable true
        self.making = True
        
        self.AOtaskHandle = daqmx.TaskHandle()
        daqmx.CreateTask("", self.AOtaskHandle)
        daqmx.CreateAOVoltageChan(self.AOtaskHandle, "Dev1/ao0", "", 
                                  -10.0, 10.0, daqmx.Val_Volts, None)
        daqmx.CfgSampClkTiming(self.AOtaskHandle, "", self.sr, 
                               daqmx.Val_Rising, daqmx.Val_ContSamps, 
                               self.buffsize)
        daqmx.SetWriteRegenMode(self.AOtaskHandle, 
                                daqmx.Val_DoNotAllowRegen)
                                
        # Setup a callback function to run once the DAQmx driver finishes
        def DoneCallback_py(taskHandle, status, callbackData_ptr):
            self.rampeddown = True
            return 0
            
        DoneCallback = daqmx.DoneEventCallbackPtr(DoneCallback_py)
        daqmx.RegisterDoneEvent(self.AOtaskHandle, 0, DoneCallback, None)                        
        
        # Output the rampup time series
        daqmx.WriteAnalogF64(self.AOtaskHandle, self.buffsize, False, 10.0, 
                             daqmx.Val_GroupByChannel, rampup_ts)
                                       
        daqmx.StartTask(self.AOtaskHandle)
        
        # Wait a second to allow the DAQmx buffer to empty
        if self.wavetype == "Regular":
            time.sleep(self.period*0.99) # was self.period*0.4
        else:
            time.sleep(0.99)

        # Set iteration variable to keep track of how many chunks of data
        # have been written
        i = 1
        
        # Main running loop that writes data to DAQmx buffer
        while self.enable:
            writeSpaceAvail = daqmx.GetWriteSpaceAvail(self.AOtaskHandle)
            if writeSpaceAvail >= self.buffsize:
                if self.wavetype != "Regular":
                    if i >= 120:
                        self.dataw = tsparts[i % 120, :]
                    else: 
                        self.dataw = tsparts[i, :]
                daqmx.WriteAnalogF64(self.AOtaskHandle, self.buffsize, False, 
                        10.0, daqmx.Val_GroupByChannel, self.dataw)
                i += 1
            if self.wavetype == "Regular":
                time.sleep(0.99*self.period)
            else:
                time.sleep(0.99) # Was self.period
        
        # After disabled, initiate rampdown time series
        if self.wavetype != "Regular":
            if i >= 120:
                self.rampdown_ts = ramp_ts(tsparts[i % 120, :], "down")
            else:
                self.rampdown_ts = ramp_ts(tsparts[i, :], "down")
        else:
            self.rampdown_ts = ramp_ts(self.dataw, "down")
        # Write rampdown time series
        daqmx.WriteAnalogF64(self.AOtaskHandle, self.buffsize, False, 10.0, 
                                 daqmx.Val_GroupByChannel, self.rampdown_ts)
        # Keep running, part of PyDAQmx callback syntax
        while True:
            pass
        
    def stop(self):
        self.stopgen = WaveStop(self)
        self.stopgen.start()
        

class WaveStop(QThread):
    def __init__(self, wavegen):
        QtCore.QThread.__init__(self)
        self.wavegen = wavegen
        
    def run(self):
        self.wavegen.enable = False
        
        while not self.wavegen.rampeddown:
            time.sleep(0.2)
        
        daqmx.ClearTask(self.wavegen.AOtaskHandle)
        self.wavegen.cleared = True
               
    
# Boilerplate code to run a Qt application
def main():
    
    app = QtGui.QApplication(sys.argv)

    w = MainWindow()
    w.setWindowIcon(QtGui.QIcon("icons/makewaves_icon.svg"))
    w.show()
    
    sys.exit(app.exec_())
    
# Boilerplate code to run the Python application
if __name__ == '__main__':
    main()


