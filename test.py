# import agilent.agilent as ag

# with ag.AgilentScope("USB0::0x0957::0x179A::MY52491615::0::INSTR") as scope:
#     print(scope.get_scope_waveform(

from datetime import datetime
import csv
from typing import Union

def append_data(filename : str, data : Union[list[float], float], datetime : Union[datetime, None] = None, data_format = ".3e"):
    """
    Saves data to a CSV file by appending to it.
    It can add the datetime as the first column to the data.
    You can specify the format to use to display the saved data in the CSV file for the Data. Usually uses 3 decimal values scientific notation (Small e).
    """
    with open(filename, 'a') as f:
        writer = csv.writer(f)
        try:
            values = map(lambda voltage : f"{voltage:^{data_format}}", data)
        except TypeError:
            values = [f"{data:^{data_format}}",]
        if datetime is not None:
            writer.writerow([f"{datetime.timestamp()}", *values])
        else:
            writer.writerow(values)

append_data("test_date.csv", data=[1,2,3,4], datetime=datetime.utcnow())
append_data("test_no_date.csv", data=[1,2,3,4,5], datetime=None)
append_data("test_single_value.csv", data=2, datetime=datetime.utcnow())