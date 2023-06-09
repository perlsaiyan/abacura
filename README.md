# abacura

This is a python implmentation of a MUD client, using the textual library.

## Installation

I haven't published pip packages yet, waiting on some stability.

Check out the repository and run:
```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Launch with `abacura`.  You can specify `--config /path/to/config.file`,
abacura will look in ~/.abacura by default, but a config file is not required.

If you want to build, you will also want to `pip install requirements-dev.txt`

## Usage
The app starts in the `#null` session.  You can use `connect <name> <host> <port>`
to connect to a MUD.

## Contributing

Pull requests are welcome.  For major changes, please open an issue first to
discuss what you would like to change.

Please include information about your PR.

## License

Will likely be [MIT](https://choosealicense.com/licenses/mit/)

## Sample configuration file (~/.abacura)
* named sections can be used with `connect <section>` to avoid typing host
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
* sessions via the @connect command (should rename to #session)
* `@config` command to view config, or `@config <section>` to view specific section
* Overloading the layouts
* session switching
* scrollback
* MSDP parsing (specific to Legends of Kallisti for complex values, view with `@msdp` command)
* TOML config in ~/.abacura, but defaults if it doesn't exist

todo:
* Session PluginManager - mud- or player-specific stuff goes here
* Logging
* Pre-parsing of inputs
* Commands, Triggers, Actions, Timers
* SSL support
* GCMP and other telnet sub protocols

