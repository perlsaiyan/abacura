# abacura

This is a python implmentation of a MUD client, using the textual library.

## Background
I love automating my character.  I love progress bars and other cool UI elements.
I want to use a terminal UI to MUD.

I've used tintin++ since 1993, but I've gotten to the point where things I want to do are either
too complex, or too cumbersome to maintain in tintin.  I wrote
[tintin-helper](https://github.com/perlsaiyan/tintin-helper) which scratched the itch for
a while, but I want to do more, and I want to enable you to as well.

This project is named after Farancia abacura, the Mud snake.

## Installation

I haven't published pip packages yet, waiting on some stability.

Check out the repository and run:
```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
Note: If you intend on using the dev tools, use `requirements-dev.txt` instead.

Launch with `abacura`.  You can specify `--config /path/to/config.file`,
abacura will look in ~/.abacura by default, but a config file is not required.

## Usage
The app starts in the `#null` session.  You can use `@connect <name> <host> <port>`
to connect to a MUD, or you can define a session in ~/.abacura and use `@connect <name>`.
  For Legends of Kallisti, there is an add-on module on github
at [abacura-kallisti](https://github.com/perlsaiyan/abacura-kallisti) which contains
more advanced features that are specific to that MUD.

## Documentation
I'll be working on a user manual when i get close to a beta-quality release.

## Contributing

Pull requests are welcome.  For major changes, please open an issue first to
discuss what you would like to change.

Please include information about your PR.

## License

Will likely be [MIT](https://choosealicense.com/licenses/mit/)

## Sample configuration file (~/.abacura)
* named sections can be used with `@connect <section>` to avoid typing host
* `css_path` can be used to replace the default Textual CSS configuration
* `screen_class` can be used to replace the default screen layout

```toml
[global]
module_paths = ["/path/to/additional/python_packages"]
#css_path = "/path/to/custom.css"

[kensho]
#screen_class = "abacura_kallisti.screens.UpsideDownScreen"
host = "kallistimud.com"
port = 4000
```

## State of things
Working:
* Custom per-session screen layouts
* sessions via the `@connect` command (should rename to #session)
* `@config` command to view config, or `@config <section>` to view specific section
* scrollback
* MSDP parsing (specific to Legends of Kallisti for complex values, view with `@msdp` command)
* TOML config in ~/.abacura, but defaults if it doesn't exist
* Commands, Triggers, Actions, Timers
* Session PluginManager - mud- or player-specific stuff goes here

todo:
* Per Player/Session variables
* Persistent per-session in-game configuration and preferences
* Many stock widgets, modal dialogs, etc
* Trigger matching on ansi-color or plaintext
* Websocket/REST API support
* Logging
* SSL support
* GCMP and other telnet sub protocols
* Features comparable to my other project [tintin-helper](https://github.com/perlsaiyan/tintin-helper)
