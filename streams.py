#!/usr/bin/python

import os
import argparse
import urllib
import urllib2
import socket
import json
import logging
from xdg.BaseDirectory import xdg_cache_home


def get_streams(game):
	"""
		Fetches the current list of Twitch streams for a game
	"""
	# Create the query string with the game a limit
	# on the number of streams to return
	query = urllib.urlencode({
		"game": game,
		"limit": 5
	})
	url = "https://api.twitch.tv/kraken/streams?%s" % query

	logging.debug("Requesting: %s" % url)

	request = urllib2.Request(url)
	request.add_header("Accept", "application/vnd.twitchtv.v3+json")

	try:
		response = urllib2.urlopen(request)
	except Exception, e:
		logging.exception(e)
		return []

	# Read the data out of the response
	try:
		data = response.read()
		logging.debug(data)
	except Exception, e:
		logging.exception(e)
		return []

	# Parse the JSON into a Python dict
	try:
		return json.loads(data)['streams']
	except Exception, e:
		logging.exception(e)

	return []


def get_old_streams(streams=[]):
	"""
		Reads the locally cached list of streams from a file. If the streams parameter
		is provided,
		Replaces
		Returns an empty list if no cache exists.
	"""
	logging.debug("streams: %s" % streams)
	old_streams = []

	# Read in the previous list of streams
	cache_file = os.path.join(xdg_cache_home, "twitch_streams.json")

	if os.path.exists(cache_file):
		# Open the file for read+write
		try:
			f = open(cache_file, 'r+')
		except Exception, e:
			logging.exception(e)
			return []

		# Read the list of old streams from the file
		try:
			old_streams = json.load(f)
		except ValueError:
			logging.info("Cache file is empty")

		# Empty the file
		try:
			f.seek(0)
			f.truncate()
		except Exception, e:
			logging.exception(e)
	else:
		# The cache file doesn't already exist so
		# we need to create a new file
		try:
			f = open(cache_file, 'w')
		except Exception, e:
			logging.exception(e)
			return []

	# Save the current list of streams
	try:
		f.write(json.dumps(streams))
	except Exception, e:
		logging.exception(e)
	finally:
		f.close()

	return old_streams


def main(cfg):
	current_streams = get_streams(cfg['game'])

	# Get the old list of streams and give it to current list to save
	old_streams = get_old_streams(current_streams)

	# TODO: make saving of current streams a separate process

	if current_streams:
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		server_address = "/tmp/twitch-notifications.sock"
		try:
			sock.connect(server_address)
		except socket.error, e:
			logging.exception(e)
			exit(1)

		try:
			# A list of old stream IDs
			old_stream_ids = [s['_id'] for s in old_streams]
			logging.debug(old_stream_ids)

			# Create a list for the new streams
			new_streams = []

			# Iterate through the list of current streams
			for stream in current_streams:
				if stream['_id'] not in old_stream_ids:
					new_streams.append(stream)

			if new_streams != []:
				message = json.dumps(new_streams)
				logging.debug("Sending '%s'" % message)
				sock.sendall(message)
		except Exception, e:
			logging.exception(e)
		finally:
			sock.close()


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
	                    default="/tmp/twitch-notifications.sock",
	                    help="The name of the Unix socket file to use. The default Unix socket file name is /tmp/broadcaster.sock")
	args = parser.parse_args()

	# Initialise a variable to hold our configuration dict
	cfg = {}

	# TODO: search several paths for the config file

	# Read in the config file
	try:
		with open("config.json", "r") as f:
			cfg = json.load(f)
	except Exception, e:
		logging.info("Could not load config file")
		logging.exception(e)

	# log-level gets changed to log_level by parse_args()
	if args.log_level is not None:
		user_log_level = args.log_level
	elif "log-level" in cfg:
		user_log_level = cfg["log-level"]
	else:
		user_log_level = "critical"

	# Set the logging level
	log_level = getattr(logging, user_log_level.upper(), None)
	logging.basicConfig(level=log_level)

	main({
		"game": args.game
	})
