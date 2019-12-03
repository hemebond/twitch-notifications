import logging
import urllib.request
import urllib.parse
import json

import config


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


def get_game_id(game):
	'''
	Returns the game_id for a game

	Docs: https://dev.twitch.tv/docs/api/reference#get-games
	'''

	cfg = config.get_config()

	# First need to fetch the game_id
	query = urllib.parse.urlencode({
		"name": game,
	})
	url = "https://api.twitch.tv/helix/games?%s" % query

	logging.debug("Requesting: %s" % url)

	request = urllib.request.Request(url)
	request.add_header("Accept", "application/vnd.twitchtv.v3+json")
	request.add_header("Client-ID", cfg['client-id'])

	response = urllib.request.urlopen(request)

	# Read the data out of the response
	data = response.read().decode("utf-8")
	logging.debug(data)

	return json.loads(data)['data'][0]['id']


def get_current_streams(game, limit=5, blacklist=[]):
	"""
		Fetches the current list of Twitch streams for a game

		e.g., https://api.twitch.tv/helix/streams?game_id=12345&limit=5

		Docs: https://dev.twitch.tv/docs/api/reference#get-streams
	"""
	cfg = config.get_config()

	try:
		game_id = get_game_id(game)
	except:
		return None

	# Create the query string with the game a limit
	# on the number of streams to return
	query = urllib.parse.urlencode({
		"game_id": game_id,
		"limit": limit
	})
	url = "https://api.twitch.tv/helix/streams?%s" % query

	logging.debug("Requesting: %s" % url)

	request = urllib.request.Request(url)
	request.add_header("Accept", "application/vnd.twitchtv.v3+json")
	request.add_header("Client-ID", cfg['client-id'])

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
		return json.loads(data)['data']
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
