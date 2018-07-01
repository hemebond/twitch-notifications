# Twitch Watch
Watches Twitch and sends out notifications when someone begins streaming a particular game.

## Requirements

* Python 3
* xdg

### Optional

* Python-DBUS

## Configuration

The configuration file is used by `broadcasters.py` and `streams.py`.

Three locations will be checked for a `config.json` file:

1. The path specified via the `--config` parameter
2. `config.json` in `$XDG_CONFIG_HOME/twitchwatch/`, e.g., `~/.config/twitchwatch/config.json`
3. `config.json` in the program directory

The configuration file is a JSON file and is used to define and configure the broadcasters and logging. You need to have a Client-ID to use the Twitch API. You can create one by following the [instructions on the Twitch blog](https://blog.twitch.tv/client-id-required-for-kraken-api-calls-afbb8e95f843).

Here is an example of a basic `config.json` file that will only send notifications to DBus:
```
{
	"client-id": "xxxxxxxxxxxxxxxxxxxxxxx",
	"broadcasters": [
		{
			"type": "dbus"
		}
	]
}
```

## Running

Start the broadcaster with:

```
python3 broadcaster.py
```

Now check to see if anyone is streaming a particular game (substitute with the title for an actual game):
```
python3 streams.py "My Game"
```

And, assuming someone is streaming "My Game", you should see some desktop notifications. Found streams are cached so that on subsequent runs only new streams trigger notifications.

## IRC Broadcaster

Now update your `config.json` file with an IRC:
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
Be sure to change the network, room and nick. Save the file and restart `broadcaster.py`. It should now connect to the IRC server and join the channel (room) you've selected. Now when you check for streams a notification will be sent to your desktop *and* the IRC channel. Bear in mind that notifications will only be sent for *new* streams.

## Cron

To run the check as a cron job you have to export a couple of environment variables. The following example cron line will check for "My Game" streams every 15 minutes:
```
0,15,30,45 * * * * export DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000 && /usr/bin/python3 /path/to/twitchwatch/streams.py "My Game"
```
