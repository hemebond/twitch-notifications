# Twitch Watch
Watches Twitch and sends out notifications when someone begins streaming a particular game.

## Requirements

* Python 3
* xdg
* Python-DBUS

## Configuration

The configuration file is used by `broadcasters.py` and `streams.py`.

Three locations will be checked for a `config.json` file:

1. The path specified via the `--config` parameter
2. `$XDG_CONFIG_HOME/twitchwatch/`, e.g., `~/.config/twitchwatch/config.json`
3. The program directory

The configuration file is a JSON file and is used to define and configure the broadcasters and logging.

## Example

Start the broadcaster with:

```
python3 broadcaster.py
```

Now check to see if anyone is streaming a particular game (substitute with the title for an actual game):
```
python3 streams.py "My Game"
```

And, assuming someone is streaming "My Game", you should see some desktop notifications. Now create a new configuration in `~/.config/twitchwatch/config.json` with something like:

```
{
  "broadcasters": [
    {
      "type": "irc",
      "network": "irc.freenode.net",
      "room": "##myroom",
      "nick": "twitchbot"
    },
    {
      "type": "dbus"
    }
  ]
}
```
Be sure to change the network, room and nick. Save the file and restart `broadcaster.py`. It should now connect to the IRC server and join the channel (room) you've selected. Now when you check for streams a notification will be sent to your desktop *and* the IRC channel. Bear in mind that notifications will only be sent for *new* streams. The streams.py file caches the streams found on previous checks.

To run the check as a cron job you have to export a couple of environment variables. The following example cron line will check for "My Game" streams every 15 minutes:
```
0,15,30,45 * * * * export DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000 && /usr/bin/python3 /path/to/twitchwatch/streams.py "My Game"
```
