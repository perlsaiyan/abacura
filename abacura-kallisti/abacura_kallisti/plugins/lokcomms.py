"""LOK Communications plugins"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Optional

from rich.text import Text
from textual.widgets import TextLog

from abacura.mud import OutputMessage
from abacura.plugins import action, command, CommandError
from abacura.plugins.events import AbacuraMessage
from abacura_kallisti.plugins import LOKPlugin

@dataclass
class CommsMessage(AbacuraMessage):
    event_type:str = "lok.comms"
    channel: str = ""
    speaker: str = ""
    message: str = ""
    datetime: str = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

class LOKComms(LOKPlugin):
    comms_textlog: Optional[TextLog] = None

    #valid channels in LOK
    channels = [
        'gossip',
        'barter',
        'market',
        'market-info',
        'group',
        'clan',
        'gemote',
        'imm',
        'request',
        'respond',
        'world',
        'whisper',
        'say',
        'yell',
        'shout',
        'tell',
        'arena',
        'advice',
        'rude',
        'obscene',
        'music',
        'politics',
        'sports',
        'hero',
        'development',
        'roleplay',
        'pk',
        'veteran',
        'code'

    ]
    #comms toggle for comms log (not mud output window)
    comms_toggles = {}
    comms_gag_entities = []
    
    for channel in channels:
        comms_toggles[channel] = 'on'

    def comms_log(self, channel, speaker, msg):
        channel = channel.lower()
        speaker = speaker.lower()
        if channel not in self.channels:
            self.channels.append(channel)
            self.comms_toggles[channel] = 'on'
        if self.comms_toggles[channel] == 'on' and speaker not in self.comms_gag_entities:
            if self.comms_textlog is None:
                self.comms_textlog = self.session.screen.query_one("#commsTL", expect_type=TextLog)
            self.comms_textlog.write(Text.from_ansi(msg.message))

    #<Gossip: Taszlehoff (Shade)> 'morning'
    @action(r"^<(\w+): (\w+)( \(.*\))?> '(.*)'", color=False)
    def comms_common(self, channel: str, speaker: str, account: str, message: str, msg: OutputMessage):
        """Send common pattern comms to the commslog, including clan chat"""
        if account == None:
            account = 'None'
        self.comms_log(channel, speaker, msg)
    
    #<Market: the MGSE supervisor> 'Lapis Lazuli stocks went up 10.  Trading at 130 now.'
    # Market info is a different pattern and gets different channel assignment
    @action (r"^<Market: the MGSE supervisor> (.*)", color=False)
    def comms_market_info(self, msg: OutputMessage):
        channel = 'market_info'
        speaker = 'MGSE'
        if self.comms_textlog is None:
            self.comms_textlog = self.session.screen.query_one("#commsTL", expect_type=TextLog)
        self.comms_textlog.write(Text.from_ansi(msg.message))

    #**Whitechain: 'huehuehue'
    @action (r"(^\*\*(\w+): '(.*'))", color=False)
    def comms_group_other(self, speaker: str, message: str, msg: OutputMessage):
        channel = 'group'
        self.dispatch(CommsMessage(channel=channel, speaker=speaker, message=message))
        self.comms_log(channel, speaker, msg)

    #You grouptell: huehuehue
    @action (r"You grouptell: (.*)$", color=False)
    def comms_group_self(self, message: str, msg: OutputMessage):
        channel = 'group'
        speaker = 'You'
        self.comms_log(channel, speaker, msg)

    """
    This case: <Clan: Atropa> 'huehue' is caught by comms_common
    This method covers this case: You cchat, 'huehue'
    """
    @action(r"^(You) cchat, '(.*)'", color=False)
    def comms_clan_self(self, speaker: str, message: str, msg: OutputMessage):
        channel = 'clan'
        self.comms_log(channel, speaker, msg) 

    @action(r"^{RolePlay: (\w+)} '(.*)'", color=False)
    def comms_roleplay(self, speaker: str, message: str, msg: OutputMessage):
        channel = 'roleplay'
        self.comms_log(channel, speaker, msg) 

    @action(r"^<Gemote> '(.*)'", color=False)
    def comms_gemote(self, msg: OutputMessage):
        """Gemote speaker is indeterminate"""
        channel = 'gemote'
        speaker = ''
        self.comms_log(channel, speaker, msg) 
    
    #You shout, 'huehue'
    #Whitechain shouts, 'huehue'
    @action(r"^(\w+) (shout|shouts), '(.*)'", color=False)
    def comms_shout(self, speaker: str, verb: str, message: str, msg: OutputMessage):
        channel = 'shout'
        self.comms_log(channel, speaker, msg)

    #yell has a comma when others yell, not when self yells
    @action(r"^(\w+) (yell|yells,) '(.*)'", color=False)
    def comms_yell(self, speaker: str, verb: str, message: str, msg: OutputMessage):
        channel = 'yell'
        self.comms_log(channel, speaker, msg)

    """
    immchat, imms only
    [Whitechain:(Vajra)] 'blurp'
    [Vajra:] 'blurp'
    [Vajra:(?)] 'blurp'
    """
    @action(r"^\[(\w+):(\(.*\)+)?] '(.*)'", color=False)
    def comms_immchat(self, speaker: str, account: str, message: str, msg: OutputMessage):
        channel = 'imm'
        self.comms_log(channel, speaker, msg)
    
    #imms see requests this way
    #[Whitechain (Goliath) Requests:] 'huehue'
    @action(r"^\[(\w+) (\(.*\)) Requests:] ('.*)'", color=False)
    def comms_request_other(self, speaker: str, account: str, message: str, msg:OutputMessage):
        channel = 'request'
        self.comms_log(channel, speaker, msg)

    #only requesting player and imms can see
    @action(r"^(You) request, '(.*)'", color=False)
    def comms_request_self(self, speaker: str, message: str, msg: OutputMessage):
        channel = 'request'
        self.comms_log(channel, speaker, msg)

    #imm only, all imms can see and listener can see
    @action(r"^\[(\w+) responds to (\w+) \((.*)\):] '(.*)'", color=False)
    def comms_respond(self, speaker: str, listener: str, listener_acct: str, msg:OutputMessage):
        channel = 'respond'
        self.comms_log(channel, speaker, msg)

    @action(r"^The winds whisper, (.*)", color=False)
    def comms_world(self, message: str, msg: OutputMessage):
        channel = 'world'
        speaker = 'world'
        self.comms_log(channel, speaker, msg)

    """
    Whitechain says, 'huehue'
    You say, 'huehue'
    """
    @action(r"^(\w+) say[s]?, '(.*)'", color=False)
    def comms_say(self, speaker: str, message: str, msg: OutputMessage):
        channel = 'say'
        self.comms_log(channel, speaker, msg)

    #Vajra whispers to you, 'huehue'
    @action(r"(\w+) whispers to you, '(.*)'", color=False)
    def comms_whisper(self, speaker: str, message: str, msg: OutputMessage):
        channel = 'whisper'
        listener = 'You'
        self.comms_log(channel, speaker, msg) 

    """
    You tell Vajra (Anicca){Rp}, 'huehue'
    You tell Vajra{Rp}, 'huehue'
    """
    @action(r"You tell (.*), '(.*)'", color=False)
    def comms_tell_self(self, listener: str, message: str, msg: OutputMessage):
        channel = 'tell'
        speaker = 'You'
        _listener = re.sub("{Rp}", "", listener)
        _listener = listener.split()
        if len(_listener) > 1:
            acct = _listener[1]
            acct = re.sub("\(|\)", '', acct)
            listener = _listener[0]
        self.comms_log(channel, speaker, msg)  

    """
    Vajra tells you, 'huehue'
    Whitechain (Goliath) tells you, 'huehue'
    """
    @action(r"^(.*) tells you, '(.*)'", color=False)
    def comms_tell_other(self, speaker: str, message: str, msg: OutputMessage):
        channel = 'tell'
        listener = 'You'
        _speaker = speaker.split()
        if len(_speaker) > 1:
            acct  = speaker[1]
            acct = re.sub("\(|\)", '', acct)
            speaker = _speaker[0]
        self.comms_log(channel, speaker, msg)  
    
    @action (r"^The winds whisper, '(.*)'", color=False)
    def comms_world(self, message: str, msg: OutputMessage):
        channel = 'world'
        speaker = 'world'
        self.comms_log(channel, speaker, msg)

    #commsgag <channel/speaker> <arg> <on/off>
    @command(name='commstog')
    def comms_toggle(self, channel_or_speaker: str=None, name: str=None, on_off: str=""):
        """Turn a channel or speaker on/off"""

        if channel_or_speaker is None:
            raise CommandError("Must give channel or speaker.")
        
        if name is None:
            raise CommandError("Must provide a channel or speaker.")
        
        name = name.lower()
        if on_off in ["on", "off"]:
            if channel_or_speaker == "channel":
                name = name.lower()
                if name in self.channels:
                    self.comms_toggles[name] = on_off
                    self.session.output(f"Comms window output for channel: {name} is {on_off}.")
                else:
                    raise CommandError(f"'{name}' not in list of valid channels.")
            elif channel_or_speaker == "speaker":
                if name in self.comms_gag_entities and on_off == 'on':
                    self.comms_gag_entities.remove(name)
                elif name not in self.comms_gag_entities and on_off == 'off':
                    self.comms_gag_entities.append(name)

                self.session.output(f"Comms window output for speaker: {name} is {on_off}.")

            else:
                raise CommandError("Valid options are 'channel' or 'speaker'.")
        else:
            raise CommandError("Valid options are 'on' or 'off'.")
        