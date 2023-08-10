# make sure you run "pip install zhinst" before using this! You need the labone packages to interface with the Zurich Instruments
# see https://docs.zhinst.com/labone_programming_manual/introduction.html and https://docs.zhinst.com/labone_programming_manual/python.html
import zhinst.utils as ziutils

from typing_extensions import Self # make sure to have the typing_extensions plugin (use pip to install)

class ZurichInstruments:
    def __init__(self,
                device_serial : str,
                api_level: int,
                server_host: str = None,
                server_port: int = 8004) -> None:
        """
        Args:
            device_serial: A string specifying the device serial number. For
                example, 'uhf-dev2123' or 'dev2123'.
            api_level: The targeted API level used by the code where the returned API
                session will be used. The maximum API level you may use is defined by the
                device class. HF2 only supports API level 1 and other devices support
                API level 6. You should try to use the maximum level possible to enable
                extended API features.
            server_host: A hostname or IP address. The data server can be omitted
                if the targeted device is an MF* device or a local data server is running.
                In this case it will try to connect to the local data server or device
                internal data server (local server has priority).
            server_port: The port number of the data server. The default port is 8004.
        """
        self.device_serial = device_serial
        self.api_level = api_level
        self.server_host = server_host
        self.server_port = server_port
    
    def initialize(self) -> None:
        self.daq, self.device, _ = ziutils.create_api_session(self.device_serial, api_level=self.api_level, server_host=self.server_host, server_port=self.server_port)
    
    def connect(self) -> None:
        self.daq.connect()

    # allows you to use the "with" keyword in Python
    def __enter__(self) -> Self:
        self.initialize()
    # allows you to use the "with" keyword in Python
    def __exit__(self, type, value, traceback) -> None:
        pass


    def close(self) -> None:
        """
        No need to call it, the daq disconnects automatically on destruction
        """
        self.daq.disconnect()
    
    def getOffsetValue(self, channel : int, from_zero : bool = False) -> float:
        """
        Allows you to get the voltage on the auxiliary channels of the ZI.
        Args:
            - channel is the channel to be queried
            - from_zero is how you are counting your channels, from zero or from 1: channels 0,1,2,3 or channels 1,2,3,4
        Returns:
            A float corresponding to the voltage queried.
        """
        if not from_zero:
            channel -= 1 # this fixes the channel if the user expects to communicate from chan 1 to 4 and not 0 to 3

        path = f"{self.device_serial}/auxouts/{channel}/"

        self.daq.sync()

        return self.daq.getDouble(path)
    
    def setOffsetValue(self, channel : int, value : float, from_zero : bool = False) -> None:
        """
        Allows you to set the voltage on the auxiliary channels of the ZI.
        Args:
            - channel is the channel to be queried
            - from_zero is how you are counting your channels, from zero or from 1: channels 0,1,2,3 or channels 1,2,3,4
        Returns:
            Nothing
        """
        if not from_zero:
            channel -= 1 # this fixes the channel if the user expects to communicate from chan 1 to 4 and not 0 to 3
        
        path = f"{self.device_serial}/auxouts/{channel}/"

        self.daq.setDouble(path, value)
        self.daq.sync()

