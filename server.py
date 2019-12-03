import asyncore
import socket
import logging
import json
import os

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

		self.logger.debug("broadcasters: {0}".format(broadcasters))

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
