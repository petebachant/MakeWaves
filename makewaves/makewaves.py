"""MakeWaves main application."""

from __future__ import division, print_function, absolute_import
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui
from .mainwindow import *
import PyQt4.Qwt5 as Qwt
import sys
import os
import platform
from . import wavemakerlimits as wml
import numpy as np
import time
import json
from .waveio import WaveGen
from .wavetsgen import Wave

_thisdir = os.path.dirname(os.path.abspath(__file__))
settings_dir = os.path.join(_thisdir, "settings")

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
periods_fpath = os.path.join(settings_dir, "periods.npy")
maxh_fpath = os.path.join(settings_dir, "maxH.npy")
if not os.path.isfile(periods_fpath) or not os.path.isfile(maxh_fpath):
    print("No wavemaker limit settings found")
    wml.findlimits()

periods = np.round(np.load(periods_fpath), decimals=4)
maxH = np.load(maxh_fpath)
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
        self.calcthread = None

        # Load settings is they exist
        self.load_settings()

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

    def load_settings(self):
        """Loads settings"""
        self.pcid = platform.node()
        try:
            with open(os.path.join(settings_dir, "app.json"), "r") as fn:
                self.settings = json.load(fn)
        except IOError:
            self.settings = {}
        if "Last PC name" in self.settings:
            if self.settings["Last PC name"] == self.pcid:
                if "Last window location" in self.settings:
                    self.move(
                        QtCore.QPoint(self.settings["Last window location"][0],
                                      self.settings["Last window location"][1])
                        )

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
        self.ui.combobox_randwavetype.currentIndexChanged.connect(
            self.on_rw_changed
        )
        self.ui.action_start.triggered.connect(self.on_start)
        self.ui.combobox_regparams.currentIndexChanged.connect(self.on_regpars)
        self.ui.action_wiki.triggered.connect(self.on_wiki)
        self.ui.slider_height.sliderMoved.connect(self.on_slider_height)
        self.ui.slider_horiz.sliderMoved.connect(self.on_slider_horiz)
        self.ui.action_view_ts.triggered.connect(
            self.ui.dock_time_series.setVisible
        )
        self.ui.dock_spectrum.visibilityChanged.connect(
            self.ui.action_view_spec.setChecked
        )
        self.ui.action_view_spec.triggered.connect(
            self.ui.dock_spectrum.setVisible
        )
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
        for sb in self.spinboxes_rw:
            sb.valueChanged.connect(self.on_rw_param_changed)

    def on_rw_param_changed(self):
        """If a random wave parameter is changed, start a thread to check
            if the parameters don't over-extend the piston."""
        rwtype = self.ui.combobox_randwavetype.currentText()
        wave = Wave(rwtype)
        if rwtype == "Bretschneider" or rwtype == "JONSWAP":
            wave.sig_height = self.spinboxes_rw[0].value()
            wave.sig_period = self.spinboxes_rw[1].value()
            wave.scale_ratio = self.spinboxes_rw[2].value()
        elif rwtype == "Pierson-Moskowitz":
            wave.windspeed = self.spinboxes_rw[0].value()
            wave.scale_ratio = self.spinboxes_rw[1].value()
        if not self.calcthread or not self.calcthread.isRunning():
            self.calcthread = CalcThread(self, wave)
            self.calcthread.start()

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
        about_text = "<b>MakeWaves 0.0.1</b><br>"
        about_text += "A wavemaking app for the UNH tow/wave tank<br><br>"
        about_text += "Created by Pete Bachant (petebachant@gmail.com)<br>"
        about_text + "with contributions by Toby Dewhurst and Matt Rowell."
        QMessageBox.about(self, "About MakeWaves", about_text)

    def on_wiki(self):
        url = QUrl("https://github.com/petebachant/MakeWaves/wiki")
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
                dialog.setWindowIcon(
                    QtGui.QIcon(
                        os.path.join(_thisdir, "icons", "makewaves_icon.svg")
                    )
                )
                dialog.show()
                progress = 0
                while not self.wavegen.cleared:
                    # The progress here is fake, just calibrated to be close
                    time.sleep(0.1)
                    progress += int(60*0.1/self.wavegen.period)
                    pbar.setValue(progress)
                dialog.close()
        self.settings["Last window location"] = [self.pos().x(),
                                                 self.pos().y()]
        self.settings["Last PC name"] = self.pcid
        with open(os.path.join(settings_dir, "app.json"), "w") as fn:
            json.dump(self.settings, fn, indent=4)


class CalcThread(QThread):
    def __init__(self, main_window, wave):
        QtCore.QThread.__init__(self)
        self.mw = main_window
        self.wave = wave

    def run(self):
        self.wave.gen_ts_stroke()
        if self.wave.ts_stroke.max() > wml.max_halfstroke:
            self.mw.ui.action_start.setDisabled(True)
        else:
            self.mw.ui.action_start.setEnabled(True)


# Boilerplate code to run a Qt application
def main():
    app = QtGui.QApplication(sys.argv)
    w = MainWindow()
    w.setWindowIcon(
        QtGui.QIcon(os.path.join(_thisdir, "icons", "makewaves_icon.svg"))
    )
    w.show()
    sys.exit(app.exec_())


# Boilerplate code to run the Python application
if __name__ == '__main__':
    main()
