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

        # Wait a second to allow the DAQmx buffer to empty
        if self.wavetype == "Regular":
            time.sleep(self.period * 0.99)  # was self.period*0.4
        else:
            time.sleep(0.99)

        # Set iteration variable to keep track of how many chunks of data
        # have been written
        i = 1

        # Main running loop that writes data to DAQmx buffer
        while self.enable:
            print("Writing main wave time series data iteration", i)
            writeSpaceAvail = daqmx.GetWriteSpaceAvail(self.AOtaskHandle)
            if writeSpaceAvail >= self.buffsize:
                if self.wavetype != "Regular":
                    if i >= 120:
                        self.dataw = tsparts[i % 120, :]
                    else:
                        self.dataw = tsparts[i, :]
                daqmx.WriteAnalogF64(
                    self.AOtaskHandle,
                    self.buffsize,
                    False,
                    10.0,
                    daqmx.Val_GroupByChannel,
                    self.dataw,
                )
                i += 1
            self.sleep()

        print("Output disabled; ramping down")
        # After disabled, initiate rampdown time series
        if self.wavetype != "Regular":
            if i >= 120:
                self.rampdown_ts = ramp_ts(tsparts[i % 120, :], "down")
            else:
                self.rampdown_ts = ramp_ts(tsparts[i, :], "down")
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
        # Keep running, part of PyDAQmx callback syntax
        print("Waiting to ramp down")
        self.sleep()
        daqmx.StopTask(self.AOtaskHandle)
        daqmx.WaitUntilTaskDone(self.AOtaskHandle, timeout=10.0)
        print("Done ramping down")
        daqmx.ClearTask(self.AOtaskHandle)
        self.rampeddown = True

    def sleep(self):
        """Sleep between iterations."""
        if self.wavetype == "Regular":
            time.sleep(0.99 * self.period)
        else:
            time.sleep(0.99)  # Was self.period

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

        daqmx.ClearTask(self.wavegen.AOtaskHandle)
        self.wavegen.cleared = True
