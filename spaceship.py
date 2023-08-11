## This is a port of the spaceship matlab file "coupling0727.m"

## it makes a few improvements like using the agilent library created in the agilent folder as well as the zurich's wrapper in the zurich folder.

import agilent.agilent as ag
import zurich.zurich as zi

from twisted.internet import task, reactor

from laser import Laser
from laser_manager import LaserManager

from time import sleep




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
          period_in_seconds : int = 120,
          max_resonance_search_steps : int = 10,
          sweeping_period : int = 10,
          sweeping_total_range : float = 0.6,
          sweeping_steps : int = 25) -> None:
    # ask the scheduler
    with ag.AgilentScope(scope_resource_name) as scope:
        with zi.ZurichInstruments(zi_device_serial_name, api_level) as zurich:
            laser = Laser(mode_hop_zones, zurich, laser_channel_zi)
            laser_manager = LaserManager(zurich, scope, scope_channel, laser, 
                                         peak_threshold=peak_threshold,
                                         min_coupling=min_coupling,
                                         max_search_steps=max_resonance_search_steps,
                                         sweep_iteration_period=sweeping_period,
                                         sweep_total_range= sweeping_total_range,
                                         sweep_steps=sweeping_steps)

            loop = task.LoopingCall(laser_manager.manage_loop, filename)
            loop.start(period_in_seconds)
            reactor.run()


    


if __name__ == "__main__": # runs only if ran directly. This is not a library

    period_in_seconds = 20 # how often do you want to run the measurement code?
    scope_resource_name = "USB0::0x0957::0x179A::MY51450715::0::INSTR" # the scope VISA resource name.
    zi_device_serial_name = "dev812" # the name of the zurich instruments
    api_level = 1 # depends on the device used. HF2 only supports api level = 1, other devices support level 6.
    
    file_name_path = "data/data" #this the prefix of all data files generated

    peak_threshold = 0.15 # the minimum height of a peak to be considered a resonance
    min_coupling = 0.5 # min coupling for considering a resonance as found
    max_resonance_search_steps = 10 # how many search steps occur before giving up!
    sweeping_period = 30 # changes how often a sweep occurs
    sweeping_total_range = 0.6 # the total range of the sweep
    sweeping_steps = 25 # total number of steps in the sweep

    mode_hop_zones = [(float("-inf"), 1.4), (5.4, float("inf"))] # there's a mode hop between the smallest voltage to 1.4V and another between 5.4V and the largest voltage.



    main(scope_resource_name,
        zi_device_serial_name, 
        api_level, file_name_path,
        period_in_seconds = period_in_seconds,
        mode_hop_zones=mode_hop_zones,
        laser_channel_zi= 2,
        scope_channel=1,
        peak_threshold=peak_threshold,
        min_coupling=min_coupling,
        sweeping_period=sweeping_period,
        sweeping_total_range=sweeping_total_range,
        sweeping_steps = sweeping_steps)