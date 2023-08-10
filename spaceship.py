## This is a port of the spaceship matlab file "coupling0727.m"

## it makes a few improvements like using the agilent library created in the agilent folder as well as the zurich's wrapper in the zurich folder.

from time import sleep
from typing import Union
import agilent.agilent as ag
import zurich.zurich as zi
from twisted.internet import task, reactor
import numpy as np
from scipy.signal import find_peaks, peak_widths
from laser import Laser, VoltageModeHopError
from twisted.internet.task import LoopingCall
import csv
from datetime import datetime
from time import sleep



class LoopingCallWithCounter:
    def __init__(self, count, f, *a, **kw) -> None:
        self.i = 0
        def wrapper():
            if self.i >= count:
                self.lc.stop()
            else:
                f(*a, **kw)
                self.i += 1
        self.lc = LoopingCall(wrapper)

class NoLightError(Exception):
    pass

class SearchStepsExhausted(Exception):
    pass

class NoSweepDirectionFound(Exception):
    pass

def calculateOffResonanceVoltage(voltages : np.array, height : float, find_minima : bool = True):
    """
    Calculates the off resonance voltage from the voltages taken from the oscilloscope.
    args:
        - voltages is the Y axis of the oscilloscope
        - height is the minimum height of each peak
        - find_minima are we looking for minima or maxima?
    """
    if find_minima:
        voltages *= -1 # our find peaks finds maximas
        height *= -1
    peaks, _ = find_peaks(voltages, height=height)
    widths, _, intersections = peak_widths(voltages, peaks, rel_height=0.95)

    resonance_voltage = np.mean(voltages[peaks])
    
    ind = np.ones_like(voltages, bool)
    ind[np.r_[intersections]] = False

    off_resonance_voltage = np.mean(voltages[ind]) # https://stackoverflow.com/questions/32723993/how-to-exclude-few-ranges-from-numpy-array-at-once
    
    if peaks[0] < len(voltages)/4:
        cuadrant = 0
    elif peaks[0] < len(voltages)/2:
        cuadrant = 1
    elif peaks[0] < len(voltages)*0.75:
        cuadrant = 2
    else:
        cuadrant = 3

    return cuadrant, resonance_voltage, off_resonance_voltage





def getVoltages(scope : ag.AgilentScope, scope_channel : int, threshold : float) -> tuple[int, float, float]:
    """
    Returns the cuadrant (from 0 to 3) of the resonance voltage, the resonance voltage and off resonance voltage - calculated -
    """
    voltages = scope.get_scope_waveform(scope_channel)
    return calculateOffResonanceVoltage(voltages, threshold)

def calculateRatioInterference(off_resonance_voltages : np.array):
    """
    off_resonance_voltages of shape (x, 2) where the first column is the timestamp, and the second column the off resonance voltage

    Returns:
        - ratio of (max - min) /  max
        - min / max
    Note:
        calling the variables below with a _ is important since max, min are functions in python.
    """
    _max = np.max(off_resonance_voltages[:,1])
    _min = np.min(off_resonance_voltages[:, 1])
    return (_max - _min) / _max, _min / _max


def append_data(filename : str, data : Union[list[float], float], datetime : Union[datetime, None] = None, data_format = ".3e"):
    """
    Saves data to a CSV file by appending to it.
    It can add the datetime as the first column to the data.
    You can specify the format to use to display the saved data in the CSV file for the Data. Usually uses 3 decimal values scientific notation (Small e).
    """
    with open(filename, 'a') as f:
        writer = csv.writer(f)
        
        try:
            values = map(lambda voltage : f"{voltage:^{data_format}}", data)
        except TypeError: # this is the fallback case when the data is a single datapoint vs a list or iterable item.
            values = [f"{data:^{data_format}}",]

        if datetime is not None:
            writer.writerow([f"{datetime.timestamp()}", *values])
        else:
            writer.writerow(values)

class LaserManager:
    def __init__(self, zurich : zi.ZurichInstruments, scope : ag.AgilentScope, scope_channel : int,
                 laser : Laser,
                 search_step_size : float = 0.009,
                 peak_threshold : float = 1,
                 min_coupling : float = 0.8,
                 no_light_threshold : float = 0.01,
                 max_search_steps : int = 5,
                 sweep_total_range : float = 0.6,
                 sweep_iteration_period : int = 100,
                 sweep_steps : int = 25) -> None:
        self.zurich = zurich
        self.scope = scope
        self.scope_channel = scope_channel
        self.laser = laser

        self.search_direction = -1
        self.search_step = 0
        self.search_step_size = search_step_size

        self.peak_threshold = peak_threshold
        self.min_coupling = min_coupling
        self.no_light_threshold = no_light_threshold

        self.max_search_steps = max_search_steps

        self.sweep_forward = True
        self.sweep_total_range = sweep_total_range
        self.sweep_iteration_period = sweep_iteration_period
        self.sweep_steps = sweep_steps

        self.loop_number = 0

        
        pass
    def search_resonance(self, resonance_voltage, off_resonance_voltage):
        print("Searching resonance...")
        
        for i in range(self.max_search_steps):
            if self.is_resonance_found(resonance_voltage, off_resonance_voltage):
                print("Found resonance after searching")
                return # return, end the search
            
            self.search_step += self.search_step_size
            self.search_direction *= -1 # flip the search direction on each step
            self.laser.setVoltage(self.laser.getVoltage() + self.search_direction*self.search_step)

            # get the resonance voltage from the scope again after a small pause
            sleep(3)

            _, resonance_voltage, off_resonance_voltage = getVoltages(self.scope, self.scope_channel, self.peak_threshold)
            self.assert_enough_light(off_resonance_voltage) # check that there's still light
        raise SearchStepsExhausted(f"Couldn't find the resonance after {self.max_search_steps}")


    def is_resonance_found(self, resonance_voltage, off_resonance_voltage):
        coupling_efficiency = (off_resonance_voltage - resonance_voltage) / off_resonance_voltage
        return coupling_efficiency > self.min_coupling
    
    def assert_enough_light(self, off_resonance_voltage):
        """
        Checks that there's enough light.
        If not it raises an error NoLightError
        """
        if(off_resonance_voltage < self.no_light_threshold):
                raise NoLightError("There's no light visible!")
        
    def sweep(self, filename : str):
        off_resonance_voltages_during_sweep = np.zeros((self.sweep_steps, 2))
        original_voltage = self.laser.getVoltage()


        self.sweep_forward = True
        mode_hop, region = self.laser.isSweepInModeHopRegion(self.sweep_total_range, self.sweep_steps, original_voltage, self.sweep_forward)

        if mode_hop:
            lower, upper = region
            if original_voltage < lower:
                # let's sweep in the opposite direction
                self.sweep_forward = False
            
            # let's make sure that there's still no mode hop
            mode_hop, new_region = self.laser.isSweepInModeHopRegion(self.sweep_total_range, self.sweep_steps, original_voltage, self.sweep_forward)
            if mode_hop:
                raise NoSweepDirectionFound(f"Couldn't find an appropiate direction for the sweep! Sweeping forward would clash with {region}, and sweeping backwards would clash wih {new_region}.")

        # sweep
        for i in range(self.sweep_steps):
            now = datetime.utcnow() # get the time now for later timestamping
            self.laser.stepVoltage(self.sweep_total_range, self.sweep_steps, self.sweep_forward) # does one step in the direction according to sweep forward

            _, _, off_resonance_voltage = getVoltages(self.scope, self.scope_channel, self.peak_threshold)

            off_resonance_voltages_during_sweep[i] = [now.timestamp(), off_resonance_voltage]
            sleep(0.1)
        
        ratio, difference = calculateRatioInterference(off_resonance_voltages_during_sweep)

        append_data(filename=f"{filename}_minmax_sweep_{now.timestamp()}.csv", datetime=now, data = [ratio, difference])

        # reset the voltage to the original value
        self.laser.setVoltage(original_voltage)


        pass
    
    def manage_loop(self, filename : str):
        try:
            cuadrant, resonance_voltage, off_resonance_voltage = getVoltages(self.scope, self.scope_channel, self.peak_threshold)
            
            self.assert_enough_light(off_resonance_voltage)

            if not self.is_resonance_found(resonance_voltage, off_resonance_voltage):
                # we haven't found the resonance. Time to search for it
                self.search_resonance()
                pass
            else:
                # we have found the resonance.
                now = datetime.utcnow() # use utc time to avoid time zone issues
                # save the data
                append_data(filename=f"{filename}_off_resonance.csv", datetime=now, data=off_resonance_voltage)
                append_data(filename=f"{filename}_resonance.csv", datetime=now, data=resonance_voltage)

                if cuadrant == 0:
                    self.laser.setVoltage(self.laser.getVoltage() + 0.002)
                elif cuadrant == 3:
                    self.laser.setVoltage(self.laser.getVoltage() - 0.002)
                    
            if not (self.loop_number % self.sweep_iteration_period):
                self.sweep()
            self.loop_number += 1
        except NoLightError:
            pass
        except VoltageModeHopError:
            pass
        except NoSweepDirectionFound:
            pass
        except:
            pass



def main(scope_resource_name : str,
          zi_device_serial_name : str,
          api_level : int,
          filename : str,
          mode_hop_zones : list[tuple[float, float]],
          laser_channel_zi : int,
          scope_channel : int,
          peak_threshold : float = 1,
          min_coupling : float = 0.8,
          no_light_threshold : float = 0.01,
          period_in_seconds : int = 120) -> None:
    # ask the scheduler
    with ag.AgilentScope(scope_resource_name) as scope:
        with zi.ZurichInstruments(zi_device_serial_name, api_level) as zurich:
            laser = Laser(mode_hop_zones, zurich, laser_channel_zi)
            laser_manager = LaserManager(zurich, scope, scope_channel, laser)

            loop = task.LoopingCall(laser_manager.manage_loop, filename)
            loop.start(period_in_seconds)
            reactor.run()


    


if __name__ == "__main__": # runs only if ran directly. This is not a library
    period_in_seconds = 120
    scope_resource_name = "USB0::0x0957::0x179A::MY51250106::0::INSTR"
    zi_device_serial_name = "dev012"
    api_level = 6 # depends on the device used. HF2 only supports api level = 1, other devices support level 6.
    
    file_name_path = ""

    main(scope_resource_name, zi_device_serial_name, api_level, file_name_path, period_in_seconds = period_in_seconds)