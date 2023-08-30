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
          search_step_size : float = 0.009,
          period_in_seconds : int = 120,
          max_resonance_search_steps : int = 10,
          sweeping_period : int = 10,
          sweeping_total_range : float = 0.6,
          sweeping_steps : int = 25,
          recentering_voltage_step : float = 0.002) -> None:
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
                                         sweep_steps=sweeping_steps,
                                         search_step_size=search_step_size,
                                         recentering_voltage_step=recentering_voltage_step)

            loop = task.LoopingCall(laser_manager.manage_loop, filename)
            loop.start(period_in_seconds)
            reactor.run()


    


if __name__ == "__main__": # runs only if ran directly. This is not a library

    period_in_seconds = 10 # how often do you want to run the measurement code?
    scope_resource_name = "USB0::0x0957::0x179A::MY51450715::0::INSTR" # the scope VISA resource name.
    zi_device_serial_name = "dev812" # the name of the zurich instruments
    api_level = 1 # depends on the device used. HF2 only supports api level = 1, other devices support level 6.
    
    file_name_path = "data/data" #this the prefix of all data files generated

    peak_threshold = 0.1 # the minimum height of a peak to be considered a resonance
    min_coupling = 0.4 # min coupling for considering a resonance as found, the minimum coupling efficiency needed to consider the resonance found.
    # for example if the coupling efficiency is below this number, the resonance will not be considered as found.
    # it can help to detect the right mode (fundamental) for example, because another mode could have a lower coupling efficiency below this threshold,
    # and like this be rejected even though the peak is seen.

    max_resonance_search_steps = 300 # how many search steps occur before giving up!
    search_step_size = 0.009 # the search step size when trying to find a resonance

    sweeping_period = 30 # changes how often a sweep occurs
    sweeping_total_range = 0.6 # the total range of the sweep
    sweeping_steps = 25 # total number of steps in the sweep
    recentering_voltage_step = 0.004
    


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
        sweeping_steps = sweeping_steps,
        search_step_size=search_step_size,
        max_resonance_search_steps=max_resonance_search_steps,
        recentering_voltage_step=recentering_voltage_step
        )