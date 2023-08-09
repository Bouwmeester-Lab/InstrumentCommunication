"""
This class defines a laser object defining mode hop zones to avoid.
It will also use the zurich instrument to set the voltages and do the scans.
"""
from typing import Union
import zurich.zurich as zi

class VoltageModeHopError(Exception):
    pass



class Laser:
    def __init__(self, mode_hop_ranges : list[tuple[float, float]],  zurich_instrument : zi.ZurichInstruments, channel : int, from_zero : bool = False) -> None:
        """
        Creates a laser object
        args:
            mode_hop_free_ranges: a list of voltage ranges where the laser has mode hops
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
        Checks if the voltage is in a hop region.
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
    
    # def sweepVoltage(self, total_sweep : float, steps : int, forward_sweep : bool = True):
    #     """
    #     Sweeps a voltage range in the 
    #     """
    #     def stepVoltage():
    #         if forward_sweep:
    #             new_voltage = self.getVoltage() + total_sweep / steps
    #         else:
    #             new_voltage = self.getVoltage() - total_sweep / steps
    #         self.setVoltage(new_voltage)


    


