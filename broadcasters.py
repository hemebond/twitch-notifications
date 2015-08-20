import logging
import asyncore
import socket
import dbus

class IrcBroadcaster(asyncore.dispatcher):
	def __init__(self, network, room, nick, games=[], port=6667):
		self.logger = logging.getLogger("IrcBroadcaster (%s:%s)" % (network, port))
		self.logger.debug("__init__()")

		asyncore.dispatcher.__init__(self)

		self._irc_network = network
		self._irc_port = port
		self._irc_room = room
		self._irc_nick = nick
		self._games = games
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

		# Only send the notification if the game list is empty
		# or if the game is in the list
		if self._games == [] or stream["game"] in self._games:
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
