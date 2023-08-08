from typing_extensions import Self # make sure to have the typing_extensions plugin (use pip to install)
from enum import Enum
import numpy

import pyvisa

class AgilentPointsMode(str, Enum):
    normal = "NORM"
    maximum = "MAX"
    raw = "raw"

class AgilentTimebaseMode(str, Enum):
    window = "WIND"
    main = "MAIN"
    xy = "XY"
    roll = "ROLL"

class AgilentAcquisitionType(str, Enum):
    normal = "NORM"
    average = "AVER"
    high_resolution = "HRES"
    peak = "PEAK"

class WaveformFormat(str, Enum):
    ascii = "ASCii" # data is formatted as ASCII -> integers are converted to floats sent in scientific notation
    word = "WORD" # data is sent ad 16 bit data, i.e. 2 bytes. The :Waveform:byteorder command sets which byte is sent first. If no command sent the upper byte is first
    byte = "BYTE" # data is sent as 8 bit data.

class ByteOrder(str, Enum):
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
    
    def __enter__(self) -> Self:
        self.open()
        return self

    def __exit__(self, type, value, traceback) -> None:
        self.close()

    def configure_acquisition(self, channel : int, 
                              timebase_mode : AgilentTimebaseMode = AgilentTimebaseMode.main,
                              acquire_type : AgilentAcquisitionType = AgilentAcquisitionType.normal,
                              average_count : int = 3
                              ) -> None:
        # seyt oscilloscope to single acquisition
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
            self.visa_resource.write(AgilentScopeCommands.digitize_channel)
    
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
        data = self.visa_resource.read_raw().decode("utf-8")
        data = data.split(", ")
        data[0] = data[0].split(" ")[-1]

        return numpy.array(data, dtype=float)
    
    def get_scope_waveform(self, channel : int = 1, configure_acquisition = True, configure_data_transfer = True):
        if configure_acquisition:
            self.configure_acquisition(channel)
        
        self.digitize(channel, force_trigger=True)

        if configure_data_transfer:
            self.configure_data_transfer(1)
            
        return self.read_data()
        


        


