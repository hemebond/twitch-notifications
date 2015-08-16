#!/usr/bin/python

import os
import argparse
import urllib.request
import urllib.parse
import socket
import json
import logging
import xdg.BaseDirectory
from broadcaster import get_config, set_logging_level


class StreamCache(object):
	def write():
		pass

	def read():
		pass

	def get_game():
		pass

	def set_game():
		pass


def make_safe_name(string):
	"""
	Takes a string (game name) and returns a string that should be safe
	as a filename.
	"""
	s = string.lower()
	new_string = ""

	for c in s:
		if c.isalnum():
			new_string += c
		else:
			new_string += "_"

	return new_string


def get_current_streams(game):
	"""
		Fetches the current list of Twitch streams for a game
	"""
	# Create the query string with the game a limit
	# on the number of streams to return
	query = urllib.parse.urlencode({
		"game": game,
		"limit": 5
	})
	url = "https://api.twitch.tv/kraken/streams?%s" % query

	logging.debug("Requesting: %s" % url)

	request = urllib.request.Request(url)
	request.add_header("Accept", "application/vnd.twitchtv.v3+json")

	try:
		response = urllib.request.urlopen(request)
	except Exception as e:
		logging.exception(e)
		return None

	# Read the data out of the response
	try:
		data = response.read().decode("utf-8")
		logging.debug(data)
	except Exception as e:
		logging.exception(e)
		return None

	# Parse the JSON into a Python dict
	try:
		return json.loads(data)['streams']
	except Exception as e:
		logging.exception(e)
		return None


def read_stream_cache(cache_file):
	"""
		Reads the locally cached list of streams from a file. If the streams parameter
		is provided,
		Replaces
		Returns an empty list if no cache exists.
	"""
	logging.debug("get_stream_cache(cache_file='%s')" % cache_file)
	old_streams = {}

	if os.path.exists(cache_file):
		# Open the file for read+write
		try:
			f = open(cache_file, 'r+')
		except Exception as e:
			logging.exception(e)
			return []

		# Read the list of old streams from the file
		try:
			old_streams = json.load(f)
		except ValueError:
			logging.info("Cache file is empty")

	return old_streams


def save_stream_cache(cache_file, stream_cache):
	logging.debug("save_stream_cache('{0}', '{1}')".format(cache_file, stream_cache))

	if os.path.exists(cache_file):
		try:
			f = open(cache_file, "w")
		except Exception as e:
			logging.exception(e)
			return

		try:
			f.write(json.dumps(stream_cache))
		except Exception as e:
			logging.exception(e)
		finally:
			f.close()


def main(cfg):
	game = cfg["game"]

	old_streams = []
	old_streams_ids = []

	new_streams = []

	current_streams = get_current_streams(game)
	current_streams_ids = [stream["_id"] for stream in current_streams]
	logging.debug("current_streams_ids: {0}".format(current_streams_ids))

	# Read in the previous list of streams
	cache_dir = xdg.BaseDirectory.save_cache_path("twitchwatch")
	cache_file = os.path.join(cache_dir, "streams.json")

	# Get the old list of streams and give it to current list to save
	stream_cache = read_stream_cache(cache_file)

	if current_streams:
		# A list of old stream IDs
		if game in stream_cache.keys():
			old_streams = stream_cache[game]
			old_streams_ids = [stream["_id"] for stream in old_streams]

			logging.debug("old_streams_ids: {0}".format(old_streams_ids))

			# Iterate through the list of current streams
			for stream in current_streams:
				if stream["_id"] not in old_streams_ids:
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
						logging.debug("Talking to socket file {0}".format(server_address))
						sock.connect(server_address)
					except Exception as e:
						logging.error("Could not connect to socket file {0}".format(server_address))
						logging.exception(e)
						return

					message = json.dumps(new_streams)
					message_bytes = bytes(message, "utf-8")

					logging.debug("Sending '%s'" % message)

					sock.sendall(message_bytes)
				except Exception as e:
					logging.exception(e)
				finally:
					sock.close()

	if current_streams_ids != old_streams_ids:
		stream_cache[game] = current_streams
		save_stream_cache(cache_file, stream_cache)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("game",
	                    nargs="?",
	                    default="System Shock 2",
	                    help="This is the title of the game to search for in the Twitch stream list.")
	parser.add_argument("--config",
	                    default="config.json",
	                    help="Configuration file in JSON format. Default is config.json in the current working directory.")
	parser.add_argument("--log-level",
	                    help="Logging level, e.g., debug, info, critical. Default: critical")
	parser.add_argument("--socket",
	                    help="The name of the Unix socket file to use. The default Unix socket file name is $XDG_RUNTIME_DIR/twitchwatch.sock")
	parser.add_argument("--nocache",
	                    action="store_true",
	                    help="Ignore the cached list of previous streams.")
	args = vars(parser.parse_args())

	# Rename log_level back to log-level
	args["log-level"] = args.pop("log_level")

	# Initialise a variable to hold our configuration dict
	cfg = get_config()

	for k, v in args.items():
		if v is not None:
			cfg[k] = v

	cfg.update({
		"game": args["game"]
	})

	# log-level gets changed to log_level by parse_args()
	if args["log-level"] is not None:
		user_log_level = args["log-level"]
	elif "log-level" in cfg:
		user_log_level = cfg["log-level"]
	else:
		user_log_level = "debug"

	# Set the logging level
	set_logging_level(user_log_level)

	logging.info("Final configuration: {0}".format(cfg))

	main(cfg)
