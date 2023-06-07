from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Footer, Input


class InputBar(Input):
    class UserCommand(Message):
        def __init__(self, command: str) -> None:
            self.command = command
            super().__init__()

    def __init__(self,**kwargs):
        super().__init__()
        
    def on_input_submitted(self, message: Input.Submitted) -> None:
        self.post_message(self.UserCommand(self.value))
        self.value = ""

class AbacuraFooter(Footer):
    """Name of current session"""

    session: reactive[str | None] = reactive[str | None]("null")

    def render(self) -> str:
        return f"#{self.session}"    

