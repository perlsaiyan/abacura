"""
Handle MSP
"""
from playsound import playsound

from abacura.mud import OutputMessage
from abacura.plugins import Plugin, action

class SoundPlugin(Plugin):
    """Handle MSP sound"""
    @action(r'^!!SOUND\((.*)\)')
    def msp(self, wav: str, msg: OutputMessage):
        msg.gag = True
        if not self.config.get_specific_option(self.session.name, 'sound_dir', None):
            return
        try:
            playsound(f"{self.config.get_specific_option(self.session.name, 'sound_dir')}/{wav}", block=False)
        except Exception as exc:
            self.session.show_exception(msg=f"Failure to play sound {wav}: {repr(exc)}",exc=exc, show_tb=False)
        
        return msg
