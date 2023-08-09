## This is a port of the spaceship matlab file "coupling0727.m"

## it makes a few improvements like using the agilent library created in the agilent folder as well as the zurich's wrapper in the zurich folder.

import agilent.agilent as ag
import zurich.zurich as zi
from twisted.internet import task, reactor
import numpy as np
from scipy.signal import find_peaks, peak_widths

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

    return resonance_voltage, off_resonance_voltage





def getVoltages(scope : ag.AgilentScope, zurich : zi.ZurichInstruments) -> tuple[float, float]:
    pass

def main(scope_resource_name : str, zi_device_serial_name : str, api_level : int, filename : str) -> None:
    # ask the scheduler
    with ag.AgilentScope(scope_resource_name) as scope:
        with zi.ZurichInstruments(zi_device_serial_name, api_level) as zurich:
            

    


if __name__ == "__main__": # runs only if ran directly. This is not a library
    period_in_seconds = 60
    scope_resource_name = "USB0::0x0957::0x179A::MY51250106::0::INSTR"
    zi_device_serial_name = "dev012"
    api_level = 6 # depends on the device used. HF2 only supports api level = 1, other devices support level 6.
    
    file_name = ""

    loop = task.LoopingCall(main, (scope_resource_name, zi_device_serial_name, api_level, file_name))
    loop.start(period_in_seconds)

    reactor.run()
            