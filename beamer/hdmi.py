from global_variables import pi
from beamer.pin_mapping import RELAIS_HDMI

class HDMI_Relay:
    
    def __init__(self) -> None:
        self.hdmi_used = self.is_enabled()

    def is_enabled(self):
        return not pi.read(RELAIS_HDMI)

    def disable(self):
        pi.write(RELAIS_HDMI, 1)

    def enable(self):
        pi.write(RELAIS_HDMI, 0)

hdmi_relay = HDMI_Relay()

