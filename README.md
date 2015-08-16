# Twitch Watch
Watches Twitch and sends out notifications when someone begins streaming a particular game.

## Requirements

* Python 3.4
* PyXDG
* Python-DBUS

## Configuration

The configuration file is used by `broadcasters.py` and `streams.py`.

Three locations will be checked for a `config.json` file:

1. The path specified via the `--config` parameter
2. `$XDG_CONFIG_HOME/twitchwatch/`, e.g., `~/.config/twitchwatch/config.json`
3. The program directory

The configuration file is a JSON file and is used to define and configure the broadcasters and logging.

## Example

To check for "System Shock 2" streams, with debug logging and a custom configuration file:
```
python3 streams.py "System Shock 2" --log-level debug --config myconfig.json
```
