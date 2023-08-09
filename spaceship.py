## This is a port of the spaceship matlab file "coupling0727.m"

## it makes a few improvements like using the agilent library created in the agilent folder as well as the zurich's wrapper in the zurich folder.

from time import sleep
import agilent.agilent as ag
import zurich.zurich as zi
from twisted.internet import task, reactor
import numpy as np
from scipy.signal import find_peaks, peak_widths
from laser import Laser, VoltageModeHopError
from twisted.internet.task import LoopingCall
import csv
from datetime import datetime



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

def append_data(filename : str, datetime : datetime, voltage : float):
    with open(filename, 'a') as f:
        writer = csv.writer(f)
        writer.writerow([f"{datetime.timestamp()}", f"{voltage:.3e}"])

class LaserManager:
    def __init__(self, zurich : zi.ZurichInstruments, scope : ag.AgilentScope, scope_channel : int,
                 laser : Laser,
                 search_step_size : float = 0.009,
                 peak_threshold : float = 1,
                 min_coupling : float = 0.8,
                 no_light_threshold : float = 0.01,
                 max_search_steps : int = 5) -> None:
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
                append_data(filename=f"{filename}_off_resonance.csv", datetime=now, voltage=off_resonance_voltage)
                append_data(filename=f"{filename}_resonance.csv", datetime=now, voltage=resonance_voltage)

                if cuadrant == 0:
                    self.laser.setVoltage(self.laser.getVoltage() + 0.002)
                elif cuadrant == 3:
                    self.laser.setVoltage(self.laser.getVoltage() - 0.002)
        except NoLightError:
            pass
        except VoltageModeHopError:
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
          no_light_threshold : float = 0.01) -> None:
    # ask the scheduler
    with ag.AgilentScope(scope_resource_name) as scope:
        with zi.ZurichInstruments(zi_device_serial_name, api_level) as zurich:
            laser = Laser(mode_hop_zones, zurich, laser_channel_zi)
            laser_manager = LaserManager(zurich, scope, scope_channel, laser)

            laser_manager.manage_loop(file_name_path)
            


    


if __name__ == "__main__": # runs only if ran directly. This is not a library
    period_in_seconds = 120
    scope_resource_name = "USB0::0x0957::0x179A::MY51250106::0::INSTR"
    zi_device_serial_name = "dev012"
    api_level = 6 # depends on the device used. HF2 only supports api level = 1, other devices support level 6.
    
    file_name_path = ""

    loop = task.LoopingCall(main, (scope_resource_name, zi_device_serial_name, api_level, file_name_path))
    loop.start(period_in_seconds)

    reactor.run()
            