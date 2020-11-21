import logging
import urllib.request
import urllib.parse
import json
from twitchAPI.twitch import Twitch

import config


log = logging.getLogger(__name__)


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


def get_game_id(twitch_client, game):
	'''
	Returns the game_id for a game

	Docs: https://dev.twitch.tv/docs/api/reference#get-games
	'''

	cfg = config.get_config()

	twitch = Twitch(cfg['client-id'], cfg['client-secret'])

	# First need to fetch the game_id
	query = urllib.parse.urlencode({
		"name": game,
	})
	url = "https://api.twitch.tv/helix/games?%s" % query

	log.debug("Requesting: %s" % url)

	request = urllib.request.Request(url)
	request.add_header("Accept", "application/vnd.twitchtv.v3+json")
	request.add_header("Client-Id", cfg['client-id'])

	response = urllib.request.urlopen(request)

	# Read the data out of the response
	data = response.read().decode("utf-8")
	log.debug(data)

	return json.loads(data)['data'][0]['id']



def get_current_streams(game, limit=5, blacklist=[]):
	"""
		Fetches the current list of Twitch streams for a game

		e.g., https://api.twitch.tv/helix/streams?game_id=12345&limit=5

		Docs: https://dev.twitch.tv/docs/api/reference#get-streams
	"""
	cfg = config.get_config()

	twitch = Twitch(cfg['client-id'], cfg['client-secret'])
	twitch.authenticate_app([])

	try:
		response = twitch.get_games(names=[game])
	except Exception as e:
		log.exception(e)
		return None

	log.debug(response)

	game_id = [game['id'] for game in response['data']]

	try:
		response = twitch.get_streams(game_id=game_id)
		log.debug(response)
	except Exception as e:
		log.exception(e)
		return None

	return response['data']



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
