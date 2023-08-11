pythonversion = 3.11

from typing_extensions import Self # make sure to have the typing_extensions plugin (use pip to install)

if pythonversion == 3.11:
    from enum import Enum, StrEnum #StrEnum is available in Python 3.11, see https://stackoverflow.com/a/69439703
else:
    from strenum import StrEnum # for version before this install pip install StrEnum and use 

import numpy

import pyvisa

class AgilentPointsMode(StrEnum):
    normal = "NORM"
    maximum = "MAX"
    raw = "RAW"

class AgilentTimebaseMode(StrEnum):
    window = "WIND"
    main = "MAIN"
    xy = "XY"
    roll = "ROLL"

class AgilentAcquisitionType(StrEnum):
    normal = "NORM"
    average = "AVER"
    high_resolution = "HRES"
    peak = "PEAK"

class WaveformFormat(StrEnum):
    ascii = "ASCII" # data is formatted as ASCII -> integers are converted to floats sent in scientific notation
    word = "WORD" # data is sent ad 16 bit data, i.e. 2 bytes. The :Waveform:byteorder command sets which byte is sent first. If no command sent the upper byte is first
    byte = "BYTE" # data is sent as 8 bit data.

class ByteOrder(StrEnum):
    lsbfirst = "LSBFIRST"
    msbfirst = "MSBFIRST"

class AgilentScopeCommands:
    class Trigger:
        force = ":TRIGGER:FORCE"

    single = ":SINGLE"
    source_channel = ":WAVEFORM:SOURCE CHAN{channel}"
    time_base_mode = ":TIMEBASE:MODE {mode}"
    acquire_type = ":ACQUIRE:TYPE {type}"
    acquire_count = ":ACQUIRE:COUNT {count}" # sets the number of values to average. Only works in average mode
    points_mode = ":WAVEFORM:POINTS:MODE {mode}"
    points = ":WAVEFORM:POINTS {points}"
    digitize_channel = ":DIGITIZE CHAN{channel}"
    digitize = ":DIG"
    waveform_format = ":WAV:FORM {format}"
    waveform_byte_order = ":WAV:BYT {byte_order}"
    data_read = ":WAV:DATA?"
    
    

class AgilentScope:
    def __init__(self, resource_name : str, name : str = None) -> None:
        self.resource_name = resource_name
        self.name = name
        pass

    def open(self) -> None:
        self.visa_rm = pyvisa.ResourceManager()
        self.visa_resource = self.visa_rm.open_resource(self.resource_name)
    
    def close(self) -> None:
        self.visa_resource.close()
        self.visa_rm.close()
    
    # allows you to use the "with" keyword in Python
    def __enter__(self) -> Self:
        self.open()
        return self
    
    # allows you to use the "with" keyword in Python
    def __exit__(self, type, value, traceback) -> None:
        self.close()

    def configure_acquisition(self, channel : int, 
                              timebase_mode : AgilentTimebaseMode = AgilentTimebaseMode.main,
                              acquire_type : AgilentAcquisitionType = AgilentAcquisitionType.normal,
                              average_count : int = 3
                              ) -> None:
        """
        Configures the acquisition of data in the oscilloscope.
        """
        # set oscilloscope to single acquisition (maybe let's not hard code this in here in the future)
        self.visa_resource.write(AgilentScopeCommands.single)
        
        # set time base to main (default oscilloscope mode)
        self.visa_resource.write(AgilentScopeCommands.time_base_mode.format(mode = timebase_mode))
        # set the oscilloscope to normal mode for the acquisition
        self.visa_resource.write(AgilentScopeCommands.acquire_type.format(type = acquire_type))
        # set the number of averages if the oscilloscope is averaged
        if acquire_type == AgilentAcquisitionType.average:
            self.visa_resource.write(AgilentScopeCommands.acquire_count.format(count = average_count))

    def configure_data_transfer(self, channel : int, points_mode : AgilentPointsMode = AgilentPointsMode.normal,
                                points : int = 1000,
                                waveform_format : WaveformFormat = WaveformFormat.ascii,
                                byte_order : ByteOrder = ByteOrder.msbfirst,
                                timeout : int = 5000) -> None:
        """
        Configures the data transfer from the oscilloscope to the PC.
        timeout in milliseconds
        """
        # set oscilloscope to channel
        self.visa_resource.write(AgilentScopeCommands.source_channel.format(channel = channel))
        self.visa_resource.write(AgilentScopeCommands.points_mode.format(mode = points_mode))
        self.visa_resource.write(AgilentScopeCommands.points.format(points = points))
        self.visa_resource.write(AgilentScopeCommands.waveform_format.format(format = waveform_format))

        self.visa_resource.timeout = timeout

        self.waveform_format = waveform_format

        if(waveform_format == WaveformFormat.word):
            self.byte_order = byte_order
            self.visa_resource.write(AgilentScopeCommands.waveform_byte_order.format(byte_order = byte_order))
        


    def digitize(self, channel : int = None, force_trigger : bool = False):
        if force_trigger:
            self.visa_resource.write(AgilentScopeCommands.Trigger.force)
        if channel is None:
            self.visa_resource.write(AgilentScopeCommands.digitize)
        else:
            self.visa_resource.write(AgilentScopeCommands.digitize_channel.format(channel=channel))
    
    def read_data(self):
        if(self.waveform_format == WaveformFormat.ascii):
            data = self.__read_ascii()
        elif self.waveform_format == WaveformFormat.byte:
            data = self.visa_resource.write_binary_values(AgilentScopeCommands.data_read, container=numpy.array, is_big_endian = True)
        elif self.waveform_format == WaveformFormat.word:
            data = self.visa_resource.write_binary_values(AgilentScopeCommands.data_read, container=numpy.array, is_big_endian = True if self.byte_order == ByteOrder.msbfirst else False)
        
        return data

    def __read_ascii(self) -> numpy.array:
        self.visa_resource.write(AgilentScopeCommands.data_read)
        data = self.visa_resource.read_raw().decode("ascii")
        data = data.split(",") # separating the data points spaced and separated by a comma
        data[0] = data[0].split(" ")[-1] # removal of the header of the data: first data point: "#80001335 2.5e6"

        data = list(map(lambda x: x.strip(), data))

        return numpy.array(data, dtype=float)
    
    def get_scope_waveform(self, channel : int = 1, configure_acquisition = True, configure_data_transfer = True, force_trigger = False):
        if configure_acquisition:
            self.configure_acquisition(channel)
        
        self.digitize(channel, force_trigger=force_trigger)

        if configure_data_transfer:
            self.configure_data_transfer(channel)
            
        return self.read_data()
        


        


