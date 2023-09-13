from abacura.plugins.task_queue import Task

class SpellTask(Task):
    insert_check=lambda: self.msdp.position in ["Standing", "Fighting", "Flying", "Mounted"]

class NCOSpellTask(Task):
    insert_check=lambda: self.msdp.position in ["Standing", "Flying", "Mounted"]
