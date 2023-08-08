import agilent.agilent as ag

with ag.AgilentScope("USB0::0x0957::0x179A::MY52491615::0::INSTR") as scope:
    print(scope.get_scope_waveform())