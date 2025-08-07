from __future__ import annotations

from typing import TYPE_CHECKING, Callable
from rich.table import Table
from rich.markup import escape

from abacura.plugins import Plugin, command, CommandError
from abacura.utils.renderables import tabulate, AbacuraPanel
from abacura.utils import ansi_escape

if TYPE_CHECKING:
    pass


class ActionCommand(Plugin):
    """Provides action-related commands and debugging tools"""
    def show_actions(self):
        rows = []
        for action in self.director.action_manager.actions.queue:
            callback_name = getattr(action.callback, "__qualname__", str(action.callback))
            source = action.source.__class__.__name__ if action.source else ""

            rows.append((repr(action.pattern), callback_name, action.priority, action.flags))

        tbl = tabulate(rows, headers=["Pattern", "Callback", "Priority", "Flags"],
                       caption=f" {len(rows)} actions registered")
        self.output(AbacuraPanel(tbl, title="Registered Actions"))

    @command
    def action(self):
        """
        View actions

        """
        self.show_actions()

    @command()
    def action_timing_stats(self):
        """Show action processing timing and performance statistics"""
        from abacura.utils.timer import Timer
        
        stats = []
        total_time = 0
        
        # Get key metrics
        lines_processed = Timer.timers.get("lines_processed", 0)
        action_total = Timer.timers.get("action_processing_total", 0)
        prep_time = Timer.timers.get("action_preparation", 0)
        # No longer measuring regex/callback time individually to reduce overhead
        total_checks = Timer.timers.get("total_action_checks", 0)
        total_quick_checks = Timer.timers.get("total_quick_checks", 0)
        total_regex_checks = Timer.timers.get("total_regex_checks", 0)
        total_matches = Timer.timers.get("total_matches", 0)
        
        # Raw times
        for name, time_value in Timer.timers.items():
            if not name.startswith("total_") and name != "lines_processed":
                stats.append(f"{name}: {time_value:.6f}s")
                total_time += time_value
        
        stats.append(f"\nTotal measured time: {total_time:.6f}s")
        
        # Performance metrics
        if lines_processed > 0:
            stats.append(f"\n--- PERFORMANCE METRICS ---")
            stats.append(f"Lines processed: {lines_processed}")
            stats.append(f"Total action checks: {total_checks}")
            stats.append(f"Quick checks performed: {total_quick_checks}")
            stats.append(f"Regex checks performed: {total_regex_checks}")
            stats.append(f"Total matches: {total_matches}")
            stats.append(f"Actions per line: {total_checks/lines_processed:.1f}")
            
            if total_checks > 0:
                regex_reduction = (1 - total_regex_checks/total_checks) * 100
                stats.append(f"Regex operations avoided: {regex_reduction:.1f}%")
                stats.append(f"Match rate: {(total_matches/total_regex_checks*100):.1f}%")
            
            stats.append(f"\n--- TIME PER LINE ---")
            stats.append(f"Action processing per line: {(action_total/lines_processed*1000):.3f}ms")
            stats.append(f"Action preparation per line: {(prep_time/lines_processed*1000):.3f}ms")
            
            # Calculate the actual processing work time (preparation + estimated regex/callback)
            work_time = prep_time
            overhead_time = action_total - work_time
            stats.append(f"Hot loop time per line: {(overhead_time/lines_processed*1000):.3f}ms")
            stats.append(f"Hot loop percentage: {(overhead_time/action_total*100):.1f}%")
            
            # Efficiency metrics
            if total_regex_checks > 0:
                stats.append(f"\n--- EFFICIENCY METRICS ---")
                stats.append(f"Time per regex operation: {(overhead_time/total_regex_checks*1000000):.1f}μs")
                stats.append(f"Operations per millisecond: {(total_regex_checks/(overhead_time*1000)):.0f}")
        
        # Show some quick check examples for debugging
        stats.append(f"\n--- QUICK CHECK EXAMPLES ---")
        try:
            action_list = list(self.director.action_manager.actions.queue)[:10]
            for i, action in enumerate(action_list):
                pattern_short = action.pattern[:50] if len(action.pattern) > 50 else action.pattern
                stats.append(f"{pattern_short:<50} → '{action.quick_check}'")
            
            # Show stats about quick check effectiveness
            with_checks = sum(1 for a in self.director.action_manager.actions.queue if a.quick_check)
            total_actions = len(list(self.director.action_manager.actions.queue))
            stats.append(f"\nActions with quick checks: {with_checks}/{total_actions} ({with_checks/total_actions*100:.1f}%)")
        except Exception as e:
            stats.append(f"DEBUG ERROR: {e}")
        
        self.output("\n".join(stats))

    @command()
    def action_timing_reset(self):
        """Reset action processing timing statistics"""
        from abacura.utils.timer import Timer
        Timer.timers.clear()
        self.output("Action timing statistics reset.")
