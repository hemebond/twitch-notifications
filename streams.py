#!/usr/bin/env python3

import os
import argparse
import socket
import json
import logging
from datetime import datetime, timedelta
from xdg import (XDG_CACHE_HOME,
                 XDG_CONFIG_DIRS,
                 XDG_CONFIG_HOME,
                 XDG_DATA_DIRS,
                 XDG_DATA_HOME,
                 XDG_RUNTIME_DIR)

from client import get_current_streams
import config



logging.basicConfig(
	level=logging.DEBUG,
	format="%(name)s: %(message)s"
)
log = logging.getLogger(__name__)



def read_stream_cache(cache_file):
	"""
		Reads the locally cached list of streams from a file. If the streams parameter
		is provided,
		Replaces
		Returns an empty list if no cache exists.
	"""
	log.debug("get_stream_cache(cache_file='%s')" % cache_file)
	streams = {}

	if os.path.exists(cache_file):
		try:
			f = open(cache_file, 'r')
		except Exception as e:
			log.exception(e)
			return []

		# Read the list of old streams from the file
		try:
			streams = json.load(f)
		except ValueError:
			log.info("Cache file is empty")
		finally:
			f.close()

	return streams


def save_stream_cache(cache_file, stream_cache):
	log.debug("save_stream_cache('{0}', '{1}')".format(cache_file, stream_cache))

	try:
		f = open(cache_file, "w")
	except Exception as e:
		log.exception(e)
		return

	try:
		f.write(json.dumps(stream_cache))
	except Exception as e:
		log.exception(e)
	finally:
		f.close()


def main(cfg):
	game = cfg.get("game")

	old_streams = []
	old_streams_channel_ids = []

	new_streams = []

	# Stream IDs change each time the stream is started so we actually use the
	# channel ID instead as this won't change
	current_streams = get_current_streams(game)
	current_streams_channel_ids = [stream["user_id"] for stream in current_streams]
	log.debug("current_streams_channel_ids: {0}".format(current_streams_channel_ids))

	# Read in the previous list of streams
	cache_dir = os.path.join(XDG_CACHE_HOME, "twitchwatch")
	cache_file = os.path.join(cache_dir, "streams.json")

	# Get the old list of streams and give it to current list to save
	stream_cache = read_stream_cache(cache_file)

	if current_streams:
		if game in stream_cache.keys():
			old_streams = stream_cache.get(game)

			# Get the list of channel ids for old streams
			old_streams_channel_ids = [stream["user_id"] for stream in old_streams]

			log.debug("old_streams_channel_ids: {0}".format(old_streams_channel_ids))

			# Iterate through the list of current streams
			for stream in current_streams:
				channel_id = stream["user_id"]

				# We want to make sure old_stream is very old (more than max_age hours ago)
				if channel_id not in old_streams_channel_ids:
					new_streams.append(stream)
		else:
			new_streams = current_streams

		if new_streams:
			# Are configured to use a socket file for broadcasting?
			if "socket" in cfg:
				try:
					sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
					server_address = cfg["socket"]

					try:
						log.debug("Talking to socket file {0}".format(server_address))
						sock.connect(server_address)
					except Exception as e:
						log.error("Could not connect to socket file {0}".format(server_address))
						log.exception(e)
						return

					message = json.dumps(new_streams)
					message_bytes = bytes(message, "utf-8")

					# root: Sending '[{"id": "36338956736", "user_id": "25590253", "user_name": "Rainoa92", "game_id": "118212", "type": "live", "title": "playing some random games with friends :3", "viewer_count": 4, "started_at": "2019-12-03T00:03:33Z", "language": "en", "thumbnail_url": "https://static-cdn.jtvnw.net/previews-ttv/live_user_rainoa92-{width}x{height}.jpg", "tag_ids": ["6ea6bca4-4712-4ab9-a906-e3336a9d8039"]}]'
					log.debug("Sending '%s'" % message)

					sock.sendall(message_bytes)
				except Exception as e:
					log.exception(e)
				finally:
					sock.close()

	if cfg.get('no_cache', False) is False:
		if current_streams_channel_ids != old_streams_channel_ids:
			stream_cache[game] = current_streams
			save_stream_cache(cache_file, stream_cache)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("game",
	                    nargs="?",
	                    help="This is the title of the game to search for in the Twitch stream list.")
	parser.add_argument("--config",
	                    default="config.json",
	                    help="A path to a JSON configuration file. Used instead of any in $XDG_CONFIG_HOME or script directory. Default: none")
	parser.add_argument("--log-level",
	                    default="error",
	                    help="Logging level, e.g., debug, info, warning, error, critical. Default: critical")
	parser.add_argument("--socket",
	                    help="The name of the Unix socket file to use. Default: $XDG_RUNTIME_DIR/twitchwatch.sock")
	parser.add_argument("--cache-file",
	                    help="File path where streams should be cached. Use /dev/null to not cache. Default: $XDG_CACHE_HOME/twitchwatch/streams.json")
	parser.add_argument("--max-age",
	                    help="Integer. Number of hours. Any cache entry older than this number of hours wil be ignored when deciding if the stream is new. Default: 24")
	parser.add_argument("--no-cache",
	                    default=False,
	                    action="store_true",
	                    help="Do not add the streams found to the cache")

	args = parser.parse_args()

	log.setLevel({
		'debug': logging.DEBUG,
		'info': logging.INFO,
		'warning': logging.WARNING,
		'error': logging.ERROR,
		'critical': logging.CRITICAL,
	}[args.log_level])

	cfg = config.get_config(args)

	main(cfg)
