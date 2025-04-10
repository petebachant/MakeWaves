"""I/O operations."""

from PyQt5.QtCore import *
from PyQt5.QtGui import *

from .wavetsgen import Wave, ramp_ts
import time
import daqmx
import numpy as np


class WaveGen(QThread):
    def __init__(self, wavetype, ao_physical_channel="Dev1/ao0"):
        QThread.__init__(self)
        self.wavetype = wavetype
        self.wave = Wave(self.wavetype)
        self.enable = True
        self.ao_physical_channel = ao_physical_channel

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
        print(
            "Computed wave with min/max (V): "
            f"{min(self.dataw):.2f}, {max(self.dataw):.2f}"
        )

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
        daqmx.CreateAOVoltageChan(
            self.AOtaskHandle,
            self.ao_physical_channel,
            "",
            -10.0,
            10.0,
            daqmx.Val_Volts,
            None,
        )
        daqmx.CfgSampClkTiming(
            self.AOtaskHandle,
            "",
            self.sr,
            daqmx.Val_Rising,
            daqmx.Val_ContSamps,
            self.buffsize,
        )
        daqmx.SetWriteRegenMode(self.AOtaskHandle, daqmx.Val_DoNotAllowRegen)
        print("Writing the rampup time series")
        # Output the rampup time series
        daqmx.WriteAnalogF64(
            self.AOtaskHandle,
            self.buffsize,
            False,
            10.0,
            daqmx.Val_GroupByChannel,
            rampup_ts,
        )
        daqmx.StartTask(self.AOtaskHandle)
        self.t_start = time.time()
        self.n_iterations = 0
        self.sleep()

        # Main running loop that writes data to DAQmx buffer
        while self.enable:
            t0 = time.time()
            print(
                "Writing main wave time series data iteration",
                self.n_iterations,
            )
            write_space_avail = daqmx.GetWriteSpaceAvail(self.AOtaskHandle)
            print("Write space available:", write_space_avail)
            if self.wavetype != "Regular":
                if self.n_iterations >= 120:
                    self.dataw = tsparts[self.n_iterations % 120, :]
                else:
                    self.dataw = tsparts[self.n_iterations, :]
            daqmx.WriteAnalogF64(
                self.AOtaskHandle,
                self.buffsize,
                False,
                10.0,
                daqmx.Val_GroupByChannel,
                self.dataw,
            )
            self.n_iterations += 1
            self.sleep()

        print("Output disabled; ramping down")
        # After disabled, initiate rampdown time series
        if self.wavetype != "Regular":
            if self.n_iterations >= 120:
                self.rampdown_ts = ramp_ts(
                    tsparts[self.n_iterations % 120, :], "down"
                )
            else:
                self.rampdown_ts = ramp_ts(
                    tsparts[self.n_iterations, :], "down"
                )
        else:
            self.rampdown_ts = ramp_ts(self.dataw, "down")
        print(f"Writing rampdown time series (len: {len(self.rampdown_ts)})")
        daqmx.WriteAnalogF64(
            self.AOtaskHandle,
            self.buffsize,
            False,
            10.0,
            daqmx.Val_GroupByChannel,
            self.rampdown_ts,
        )
        self.n_iterations += 1.5
        self.sleep()
        # Write zeros to the buffer
        print("Writing a buffer of zeros")
        daqmx.WriteAnalogF64(
            self.AOtaskHandle,
            self.buffsize,
            False,
            10.0,
            daqmx.Val_GroupByChannel,
            np.zeros(self.buffsize),
        )
        self.n_iterations += 1.5
        self.sleep()
        daqmx.StopTask(self.AOtaskHandle)
        daqmx.WaitUntilTaskDone(self.AOtaskHandle, timeout=10.0)
        print("Done ramping down")
        daqmx.ClearTask(self.AOtaskHandle)
        self.rampeddown = True

    def sleep(self):
        """Sleep between iterations.

        Our goal is to always stay ahead of the FIFO buffer being empty.
        """
        # Based on how long we've been running and how many iterations we've
        # done, compute a time to sleep
        t_total = time.time() - self.t_start
        print("t_total:", t_total)
        iteration_period = self.period if self.wavetype == "Regular" else 1.0
        t_expected = iteration_period * self.n_iterations
        print("t_expected:", t_expected)
        sleeptime = t_expected - t_total - 0.2
        if sleeptime > 0:
            print("Sleeping", sleeptime, "seconds")
            time.sleep(sleeptime)

    def stop(self):
        self.stopgen = WaveStop(self)
        self.stopgen.start()


class WaveStop(QThread):
    def __init__(self, wavegen):
        QThread.__init__(self)
        self.wavegen = wavegen

    def run(self):
        self.wavegen.enable = False

        while not self.wavegen.rampeddown:
            time.sleep(0.2)

        self.wavegen.cleared = True
