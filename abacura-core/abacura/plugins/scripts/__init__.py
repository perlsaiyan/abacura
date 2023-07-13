from __future__ import annotations

import inspect
from typing import Dict, TYPE_CHECKING, Callable, Optional, List

from serum import inject

if TYPE_CHECKING:
    from abacura.mud.session import Session

from dataclasses import dataclass


@dataclass
class ScriptResult:
    success: bool
    result: object
    error: Optional[Exception] = None


class Script:
    def __init__(self, source: object, name: str, script_fn: Callable, session: Session):
        self.source: object = source
        self.name: str = name
        self.script_fn: Callable = script_fn
        self.session = session

    def __call__(self, callback_fn: Callable, *args, **kwargs):
        try:
            self.script_fn(callback_fn, *args, **kwargs)
        except Exception as e:
            self.session.show_exception(str(e), e)


@inject
class ScriptManager:
    session: Session

    def __init__(self):
        self.scripts: Dict[str, Script] = {}

    def register_object(self, obj: object):
        # self.unregister_object(obj)  # prevent duplicates
        for name, member in inspect.getmembers(obj, callable):
            if hasattr(member, "script_name"):
                s = Script(source=obj, script_fn=member, name=getattr(member, "script_name"), session=self.session)
                self.add(s)

    def unregister_object(self, obj: object):
        self.scripts = {s.name: s for s in self.scripts.values() if s.source != obj}

    def add(self, script: Script):
        self.scripts[script.name] = script

    def remove(self, name: str):
        self.scripts = {s.name: s for s in self.scripts.values() if name == '' or s.name != name}


class ScriptProvider:
    def __init__(self, script_manager: ScriptManager):
        self.script_manager = script_manager

    def __getattr__(self, attr) -> Script:
        return self.script_manager.scripts.get(attr, None)

    def __getitem__(self, item) -> Script:
        return self.script_manager.scripts.get(item, None)

    def get_scripts(self) -> List[Script]:
        return sorted(self.script_manager.scripts.values(), key=lambda x: x.name)
