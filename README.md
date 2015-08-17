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

To check for "My Game" streams, with debug logging and a custom configuration file:
```
python3 streams.py "My Game" --log-level debug --config myconfig.json
```

To run the stream check as a cron job you have to export several environment variables. The following example cron line will check for "My Game" streams every 15 minutes:
```
0,15,30,45 * * * * export DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000 && /usr/bin/python3 /path/to/twitchwatch/streams.py "My Game"
```
