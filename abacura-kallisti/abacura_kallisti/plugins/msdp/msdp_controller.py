"""LOK MSDP plugin"""
from __future__ import annotations

from dataclasses import asdict, fields

from rich.panel import Panel
from rich.pretty import Pretty

from abacura_kallisti.mud.affect import Affect
from abacura_kallisti.plugins import LOKPlugin

from abacura.mud.options.msdp import MSDPMessage
from abacura.plugins import command, CommandError
from abacura.plugins.events import event


# TODO: disable the abacura @msdp command and let's implement it here
class LOKMSDPController(LOKPlugin):
    """Converts core MSDP into typed LOK MSDP variables"""
    def __init__(self):
        super().__init__()
        self.msdp_types = {f.name: f.type for f in fields(self.msdp)}
        print(self.msdp_types)

    @command(name="msdp", override=True)
    def lok_msdp_command(self, variable: str = '', reportable: bool = False, core: bool = False) -> None:
        """
        Show MSDP values using typed LOK structure

        :param variable: Name of msdp variable to view.  Blank to view all
        :param reportable: Show reportable_variables (long list, off by default)
        :param core: Show the abacura core value instead of the typed LOK value
        """

        if not self.msdp.reportable_variables:
            raise CommandError("MSDP not loaded")

        msdp_values = self.core_msdp.values.copy() if core else asdict(self.msdp)

        if not reportable:
            msdp_values.pop("reportable_variables", None)
            msdp_values.pop("REPORTABLE_VARIABLES", None)

        if not variable:
            panel = Panel(Pretty(msdp_values), highlight=True)
        else:
            value = msdp_values.get(variable, None)
            panel = Panel(Pretty(value), highlight=True)

        self.session.output(panel, highlight=True, actionable=False)

    @event("core.msdp", priority=1)
    def update_lok_msdp(self, message: MSDPMessage):
        # self.msdp.values[message.type] = message.value
        attr_name = message.subtype.lower()

        if attr_name == 'area_maxlevel':
            if message.value == '100':
                message.value = "110"

        renames = {'class': 'cls', 'str': 'str_', 'int': 'int_'}
        attr_name = renames.get(attr_name, attr_name)

        if attr_name == 'ranged':
            pass

        # if not hasattr(self.msdp, attr_name):
        #     self.output(f"[red]Missing msdp attribute {attr_name} {message.type}", markup=True)
        #     return

        value = message.value
        if self.msdp_types[attr_name] == int:
            value = 0 if len(message.value) == 0 else int(message.value)
        elif self.msdp_types[attr_name] == str:
            value = str(message.value)

        if attr_name == 'group':
            self.msdp.group.update_members_from_msdp(value)
            self.msdp.group.update_members_from_msdp(value)
        elif attr_name == 'affects' and type(value) is dict:
            self.msdp.affects = sorted([Affect(name, int(hrs)) for name, hrs in value.items()], key=lambda a: a.name)
        else:
            setattr(self.msdp, attr_name, value)

        # if name == 'MSDP_CHARACTER_NAME':
        #     self.dispatch.dispatch(event.Event(event.NEW_CHARACTER, value))
