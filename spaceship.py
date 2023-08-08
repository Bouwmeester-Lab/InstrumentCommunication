## This is a port of the spaceship matlab file "coupling0727.m"

## it makes a few improvements like using the agilent library created in the agilent folder as well as the zurich's wrapper in the zurich folder.

import agilent.agilent as ag
import zurich.zurich as zi

# def getOffResonanceVoltage()


if __name__ == "__main__": # runs only if ran directly. This is not a library

    scope_resource_name = "USB0::0x0957::0x179A::MY51250106::0::INSTR"
    zi_device_serial_name = "dev012"
    api_level = 6 # depends on the device used. HF2 only supports api level = 1, other devices support level 6.
    
    file_name = ""

    with ag.AgilentScope(scope_resource_name) as scope:
        with zi.ZurichInstruments(zi_device_serial_name, api_level) as zurich:
            pass