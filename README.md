# abacura

This is a python implmentation of a MUD client, using the textual library.

There's not much here yet, but it does actually work.

Working:
    * sessions via the #connect command (should rename to #session)
    * session switching
    * scrollback
    * PluginManager loading at global level
    * Basic MSDP parsing
    * TOML config in ~/.abacura, but defaults if it doesn't exist

todo:
    * Session PluginManager - mud- or player-specific stuff goes here
    * Logging
    * Pre-parsing of inputs
    * Commands, Triggers, Actions, Timers
    * serum injection in session contexts


