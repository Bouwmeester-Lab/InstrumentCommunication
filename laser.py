"""
This class defines a laser object defining mode hop zones to avoid.
It will also use the zurich instrument to set the voltages and do the scans.
"""
from typing import Union
import zurich.zurich as zi
import agilent.agilent as ag

class VoltageModeHopError(Exception):
    pass



class Laser:
    def __init__(self, mode_hop_ranges : list[tuple[float, float]],  zurich_instrument : zi.ZurichInstruments, channel : int, from_zero : bool = False) -> None:
        """
        Creates a laser object
        args:
            mode_hop_ranges: a list of voltage ranges where the laser has mode hops - regions to be AVOIDED
            zurich_instrument: the ZI used to control the laser voltage
            channel: the channel in the ZI used
            from_zero: how are you counting the channels? from_zero = True: 0, 1, 2, 3 ; from_zero = False: 1, 2, 3, 4
        """
        self.mode_hop_ranges = []
        for (v1, v2) in mode_hop_ranges:
            lower_bound = min(v1, v2)
            upper_bound = max(v1, v2)
            self.mode_hop_ranges.append((lower_bound, upper_bound))
        self.zurich_instrument = zurich_instrument
        self.channel = channel
        self.from_zero = from_zero
    
    def __is_mode_hop(self, voltage : float) -> tuple[bool, Union[None, tuple[float, float]]]:
        """
        Checks if the voltage is in a mode hop region.
        It returns False if it's not in a mode hop region and True if it's in a hop region and the region that it found as a match (or None if no region was matched)
        """
        
        for (lower_end, upper_end) in self.mode_hop_ranges:
            if(voltage > lower_end and voltage < upper_end): # checks if the voltage is in the hop mode range. It adds with the previous check, so that if it's in any then the hop ranges becomes true
                return (True, (lower_end, upper_end))
        return (False, None)
    
    def setVoltage(self, voltage : float):
        mode_hop, mode_hop_range = self.__is_mode_hop(voltage)
        if(mode_hop):
            raise VoltageModeHopError(f"The voltage {voltage:.2e} is in a mode hop region! Mode hop region: {mode_hop_range}")
        self.zurich_instrument.setOffsetValue(self.channel, voltage, self.from_zero)

    def getVoltage(self) -> float:
        return self.zurich_instrument.getOffsetValue(self.channel, self.from_zero)
    
    def stepVoltage(self, total_sweep : float, steps : int, forward_sweep : bool = True):
        if forward_sweep:
            new_voltage = self.getVoltage() + total_sweep / steps
        else:
            new_voltage = self.getVoltage() - total_sweep / steps
        self.setVoltage(new_voltage)

    
    def isSweepInModeHopRegion(self, total_sweep : float, steps : int, starting_voltage = None, forward_sweep : bool = True):
        """
        checks if a sweep enters a Mode Hop region.
        Args:
            - total_sweep: the total length of the sweep
            - steps: the number of steps to take
            - forward_sweep: is the sweep in the forward direction (positive steps)
        Returns:
            - bool, (lower, upper) or None : is sweep in a Mode Hop region? | the lower and upper bound of the first found conflicting region if any.
        """
        if starting_voltage is None:
            starting_voltage = self.getVoltage()
        if forward_sweep:
            voltages_in_sweep = [starting_voltage + (step+1)*total_sweep / (steps) for step in range(steps)]
        else:
            voltages_in_sweep = [starting_voltage - (step+1)*total_sweep / (steps) for step in range(steps)]
        
        for voltage in voltages_in_sweep:
            mode_hop, region = self.__is_mode_hop(voltage)
            if mode_hop:
                return mode_hop, region
        return False, None





    


