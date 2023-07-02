# from abacura.utils.meval import meval
from datetime import datetime
import asyncio


class ScriptRunner:
    def __init__(self, code: str, exec_globals: dict, exec_locals: dict):
        self.code = code
        self.exec_globals = exec_globals
        self.exec_locals = exec_locals
        self.output = exec_globals.get("output", lambda x: print(x))
        self.exec_globals['wait_for_condition'] = self.wait_for_condition
        self.exec_globals['asyncio'] = asyncio

    async def wait_for_condition(self, condition, seconds=30):
        self.output(f">waiting {seconds}s for {condition} [{condition()}]")
        async for _ in self.loop_for_duration(seconds):
            if condition():
                return True

        return False

    async def loop_for_duration(self, seconds, tick=0.1):
        start_time: datetime = datetime.utcnow()

        while (datetime.utcnow() - start_time).total_seconds() < seconds:
            yield (datetime.utcnow() - start_time).total_seconds()
            await asyncio.sleep(tick)

    async def run(self):
        pass
        # return await meval(self.code, self.exec_globals, self.exec_locals)
