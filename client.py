import logging
import urllib.request
import urllib.parse
import json


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


def get_current_streams(game, limit=5):
	"""
		Fetches the current list of Twitch streams for a game
	"""
	# Create the query string with the game a limit
	# on the number of streams to return
	query = urllib.parse.urlencode({
		"game": game,
		"limit": limit
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


class StreamCache(object):
	"""
	Does caching stuff for a particular game.
	"""

	def __init__(self, game):
		pass

	def write():
		pass

	def read():
		pass
