#!/usr/bin/python3

import argparse
import asyncore
import socket
import os
import json
import logging
import xdg
from xdg.BaseDirectory import xdg_cache_home


# When a stream notification is sent to the broadcast socket file
# we read in the JSON data and pass the data onto each broadcaster
class ListenHandler(asyncore.dispatcher_with_send):
	def handle_read(self):
		global broadcasters

		data = self.recv(8192)

		if data:
			try:
				streams = json.loads(data)
			except:
				logging.debug(data)
				return

			logging.info("Broadcasting")
			for broadcaster in broadcasters:
				for stream in streams:
					broadcaster.broadcast(stream)


# This is the main broadcast listener that creates a UNIX socket to listen
# for stream notifications (sent from streams.py)
class ListenServer(asyncore.dispatcher):
	def __init__(self, path):
		asyncore.dispatcher.__init__(self)

		# Create a new socket file
		self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)

		# Remove the socket file if it already exists
		# Failure means there is possibly another broadcaster running
		if os.path.exists(path):
			os.remove(path)

		# Create the socket file and start listening for connections
		self.bind(path)
		self.listen(5)

	def handle_accept(self):
		"""
		Accept connections
		"""
		client = self.accept()

		if client is not None:
			sock, addr = client
			logging.info("Incoming connection from {0}".format(addr))
			handler = ListenHandler(sock)


class IrcBroadcaster(asyncore.dispatcher):
	def __init__(self, **kwargs):
		asyncore.dispatcher.__init__(self)

		self._irc_network = kwargs.get("network", "irc.starchat.net")
		self._irc_port = kwargs.get("port", 6667)
		self._irc_room = kwargs.get("room", "#hemebot")
		self._irc_nick = kwargs.get("nick", "hemebot")
		self._irc_registered = False

		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect((self._irc_network, self._irc_port))

	def handle_close(self):
		# Exit IRC
		self.send("QUIT\r\n")

		# Close the connection to the server
		self.shutdown(socket.SHUT_RDWR)
		self.close()

	def handle_read(self):
		data = self.recv(4096)

		if data:
			# Print out the data, commas prevents newline
			logging.debug(data)

			if data.find("Welcome to the StarChat IRC Network!") != -1:
				logging.info("Responding to welcome")
				self._irc_join(self._irc_room)

			elif data.startswith("PING "):
				logging.info("Responding to PING")
				self.send('PONG %s\r\n' % data.split()[1])

			elif not self._irc_registered:
				logging.info("Sending NICK details")
				self.send("NICK {0}\r\n".format(self._irc_nick))
				self.send("USER {0} {0} {0} :Python IRC\r\n".format(self._irc_nick))
				self._irc_registered = True

			# else:
			# # ":hemebond!james@121.98.129.463 PRIVMSG #systemshock :hemebot: !streams"


	def _irc_send(self, msg):
		logging.debug("IrcBroadcaster._irc_send()")
		self.send('PRIVMSG %s : %s\r\n' % (self._irc_room, msg))

	def _irc_join(self, chan):
		logging.debug("IrcBroadcaster._irc_join()")
		self.send('JOIN %s\r\n' % chan)

	def broadcast(self, stream):
		logging.debug("IrcBroadcaster.broadcast()")
		self._irc_send("New \"%s\" stream %s" % (stream['game'], stream['channel']['url']))


class DbusBroadcaster(object):
	def __init__(self, **kwargs):
		import dbus

		_bus_name = "org.freedesktop.Notifications"
		_object_path = "/org/freedesktop/Notifications"
		_interface_name = _bus_name
		session_bus = dbus.SessionBus()
		obj = session_bus.get_object(_bus_name, _object_path)
		self._interface = dbus.Interface(obj, _interface_name)

	def broadcast(self, stream):
		logging.debug("DBUS Broadcast")

		msg_summary = "New \"{0}\" stream".format(stream['game'])
		msg_body = "{0}".format(stream['channel']['url'])
		self._interface.Notify("", 0, "", msg_summary, msg_body, [], [], -1)


def read_config_file(path):
	logging.debug("Looking for config '{0}'".format(path))

	if os.path.exists(path):
		logging.debug("Trying config file '{0}'".format(path))

		with open(path) as f:
			try:
				return json.load(f)
			except Exception as e:
				logging.exception(e)

	return {}


def get_config(appname="twitchwatch"):
	"""
	Checks list of path strings for a config file, reading in each as it goes

	:param appname: The name of the application. Used for config and runtime directory names.
	:return: Dict with the merged set of configuration options
	"""

	config_dir = xdg.BaseDirectory.save_config_path(appname)
	cache_dir = xdg.BaseDirectory.save_cache_path(appname)
	run_dir = xdg.BaseDirectory.get_runtime_dir()
	cfg_file_name = "config.json"

	# Configuration defaults
	cfg = {
		"socket": os.path.join(run_dir, "{0}.sock".format(appname)),
		"cache_file": os.path.join(cache_dir, "streams.json")
	}

	# The paths to search for the config file
	cfg_paths = [
		os.path.join(os.path.dirname(os.path.realpath(__file__)), cfg_file_name),
		os.path.join(config_dir, cfg_file_name)
	]

	for path in cfg_paths:
		new_settings = read_config_file(path)
		cfg.update(new_settings)

	logging.debug("Final configuration: {0}".format(cfg))

	return cfg


def main(log_level=None):
	global broadcasters

	# Load the configuration files
	cfg = get_config()

	# log-level gets changed to log_level by parse_args()
	if log_level is None and "log-level" in cfg:
		logging.getLogger().setLevel(getattr(logging, cfg["log-level"].upper()))

	exit(0)

	# Get the path for the UNIX socket file
	socket_file_path = cfg["socket"] if "socket" in cfg else "/tmp/twitch-notifications.sock"

	# Create the broadcast server
	ListenServer(socket_file_path)

	broadcasters = []
	if "broadcasters" in cfg:
		for bc in cfg['broadcasters']:
			if bc['type'] == "irc":
				broadcasters.append(
					IrcBroadcaster(
						network=bc['network'],
						port=bc.get('port', 6667),
						room=bc['room'],
						nick=bc['nick']
					)
				)
			elif bc['type'] == "dbus":
				broadcasters.append(
					DbusBroadcaster()
				)

	try:
		asyncore.loop()
	finally:
		if os.path.exists(socket_file_path):
			os.unlink(socket_file_path)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--log-level",
						help="Logging level, e.g., debug, info, critical. Default: critical")
	args = parser.parse_args()

	# Set the logging level
	if args.log_level is not None:
		log_level = getattr(logging, args.log_level.upper(), None)
		logging.basicConfig(level=log_level)

	main(args.log_level)
