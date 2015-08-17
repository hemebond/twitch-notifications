#!/usr/bin/python3

import argparse
import asyncore
import socket
import os
import json
import logging
import xdg.BaseDirectory
import dbus


class ListenHandler(asyncore.dispatcher):
	"""
	Incoming data via the socket is passed off to this handler
	"""
	def __init__(self, sock):
		self.logger = logging.getLogger("ListenHandler (%s)" % str(sock.getsockname()))
		asyncore.dispatcher.__init__(self, sock=sock)

	def handle_read(self):
		"""
		When a stream notification is sent to the broadcast socket file
		we read in the JSON data and pass the data onto each broadcaster
		"""
		self.logger.debug("handle_read()")

		buffer = data = self.recv(4096)

		while data:
			data = self.recv(4096)
			buffer += data

		if buffer:
			self.logger.debug(buffer)

			# Data is received as bytes, convert to string
			str_data = buffer.decode('utf-8')

			try:
				streams = json.loads(str_data)
			except Exception as e:
				self.logger.exception(e)
				self.logger.debug(str_data)
				return

			self.logger.info("Broadcasting")

			for broadcaster in self.broadcasters:
				for stream in streams:
					try:
						broadcaster.broadcast(stream)
					except Exception as e:
						self.logger.exception(e)


class ListenServer(asyncore.dispatcher):
	"""
	This is the main broadcast listener that creates a UNIX socket to listen
	for stream notifications (sent from streams.py)
	"""
	def __init__(self, socket_path, broadcasters):
		self.logger = logging.getLogger("ListenServer")
		self.logger.debug("__init__()")

		asyncore.dispatcher.__init__(self)

		# Store the list of broadcasters
		self.broadcasters = broadcasters

		self.logger.debug("boardcasters: {0}".format(broadcasters))

		# Create a new socket file
		self.logger.debug("Creating socket")
		self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)

		# Remove the socket file if it already exists
		# Failure means there is possibly another broadcaster running
		if os.path.exists(socket_path):
			os.remove(socket_path)

		# Create the socket file and start listening for connections
		self.logger.debug("Binding to socket_path {0}".format(socket_path))
		self.bind(socket_path)
		self.listen(1)

	def handle_accept(self):
		"""
		Accept connections
		"""
		self.logger.debug("handle_accept()")

		client = self.accept()

		self.logger.debug(client)

		if client is not None:
			sock, addr = client
			self.logger.info("Incoming connection from {0}".format(repr(addr)))
			lh = ListenHandler(sock)
			lh.broadcasters = self.broadcasters


class IrcBroadcaster(asyncore.dispatcher):
	def __init__(self, network, room, nick, port=6667):
		self.logger = logging.getLogger("IrcBroadcaster (%s:%s)" % (network, port))
		self.logger.debug("__init__()")

		asyncore.dispatcher.__init__(self)

		self._irc_network = network
		self._irc_port = port
		self._irc_room = room
		self._irc_nick = nick
		self._irc_registered = False

		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect((network, port))

	def handle_close(self):
		self.logger.debug("handle_close()")

		# Exit IRC
		self.send("QUIT\r\n")

		# Close the connection to the server
		self.shutdown(socket.SHUT_RDWR)
		self.close()

	def handle_read(self):
		self.logger.debug("handle_read()")

		try:
			buffer = data = self.recv(1024)
		except BlockingIOError as e:
			# logging.exception(e)
			return

		while data:
			try:
				data = self.recv(1024)
				buffer += data
			except BlockingIOError as e:
				# logging.exception(e)
				data = None

		if buffer:
			# Data is received as bytes, convert to string
			str_data = buffer.decode('UTF-8')

			# Print out the data, commas prevents newline
			self.logger.debug(str_data)

			if str_data.find("Welcome to the StarChat IRC Network!") != -1:
				self.logger.info("Responding to welcome")
				self._irc_join(self._irc_room)

			elif str_data.startswith("PING "):
				self.logger.info("Responding to PING")
				self.send('PONG %s\r\n' % str_data.split()[1])

			elif not self._irc_registered:
				self.logger.info("Sending NICK details")
				self.send("NICK {0}\r\n".format(self._irc_nick))
				self.send("USER {0} {0} {0} :Python IRC\r\n".format(self._irc_nick))
				self._irc_registered = True

	def send(self, msg):
		self.logger.debug("send()")
		msg = bytes(msg, "UTF-8")
		super().send(msg)

	def _irc_send(self, msg):
		self.logger.debug("_irc_send()")
		self.send("PRIVMSG %s : %s\r\n" % (self._irc_room, msg))

	def _irc_join(self, chan):
		self.logger.debug("_irc_join()")
		self.send("JOIN %s\r\n" % chan)

	def broadcast(self, stream):
		self.logger.debug("broadcast()")
		self._irc_send("New \"%s\" stream %s" % (stream['game'], stream['channel']['url']))


class DbusBroadcaster(object):
	def __init__(self, **kwargs):
		self.logger = logging.getLogger("DbusBroadcaster")

		self.logger.debug("__init__()")

		_bus_name = "org.freedesktop.Notifications"
		_object_path = "/org/freedesktop/Notifications"
		_interface_name = _bus_name
		session_bus = dbus.SessionBus()
		obj = session_bus.get_object(_bus_name, _object_path)
		self._interface = dbus.Interface(obj, _interface_name)

	def broadcast(self, stream):
		self.logger.debug("broadcast()")

		msg_summary = "New \"{0}\" stream".format(stream['game'])
		msg_body = "{0}".format(stream['channel']['url'])
		self._interface.Notify("TwitchWatch", 0, "", msg_summary, msg_body, [], {}, -1)


def read_config_file(path):
	logging.debug("Looking for config '{0}'".format(path))

	if os.path.exists(path):
		logging.debug("Reading config file '{0}'".format(path))

		with open(path) as f:
			try:
				return json.load(f)
			except Exception as e:
				logging.error("Could not read config file '{0}'".format(path))
				logging.exception(e)

	return {}


def get_config(args_cfg_path=None, appname="twitchwatch"):
	"""
	Reads a JSON configuration file. Searches several paths, picking the first
	file it finds.

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
		os.path.join(config_dir, cfg_file_name),
		os.path.join(os.path.dirname(os.path.realpath(__file__)), cfg_file_name)
	]

	if args_cfg_path is not None:
		new_settings = read_config_file(args_cfg_path)
		cfg.update(new_settings)
	else:
		for path in cfg_paths:
			new_settings = read_config_file(path)

			if new_settings != {}:
				cfg.update(new_settings)
				break

	logging.debug("Config file result: {0}".format(cfg))

	return cfg


def get_args():
	"""
	Returns a dict of command line arguments to override config settings
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument("--config",
	                    help="Configuration file in JSON format. Default is config.json in the current working directory.")
	parser.add_argument("--socket",
	                    help="The name of the Unix socket file to use. The default Unix socket file name is $XDG_RUNTIME_DIR/twitchwatch.sock")
	parser.add_argument("--log-level",
	                    help="Logging level, e.g., debug, info, critical. Default: critical")
	args = parser.parse_args()

	# Change from an object to a dict
	args = vars(args)

	# Rename log_level back to log-level
	args["log-level"] = args.pop("log_level")

	return args


def set_logging_level(level):
	if level in ["debug", "info", "warning", "error", "critical"]:
		logging.getLogger().setLevel(getattr(logging, level.upper()))


def main():
	logging.basicConfig(
		level=logging.DEBUG,
		format="%(name)s: %(message)s"
	)

	args = get_args()

	if args["log-level"] is not None:
		set_logging_level(args["log-level"])

	# Load the configuration files
	cfg = get_config(args_cfg_path=args["config"])

	# Override config settings with command-line arguments
	for k, v in args.items():
		if v is not None:
			cfg[k] = v

	logging.debug("Final configuration: {0}".format(cfg))

	# Set the logging level
	if args["log-level"] is None:
		if "log-level" in cfg:
			set_logging_level(cfg["log-level"])

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

	# Get the path to the UNIX socket file for the listen server
	socket_file_path = cfg['socket']

	# Create the broadcast server
	server = ListenServer(socket_file_path, broadcasters)

	try:
		asyncore.loop()
	finally:
		# Always clean up
		if os.path.exists(socket_file_path):
			os.unlink(socket_file_path)


if __name__ == "__main__":
	main()
