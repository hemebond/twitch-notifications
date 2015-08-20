#!/usr/bin/python3

import argparse
import asyncore
import logging
import os

from server import ListenServer
from broadcasters import IrcBroadcaster, DbusBroadcaster
import config


def main(cfg):
	broadcasters = []

	for bc in cfg.get("broadcasters", []):
		new_broadcaster = None

		if bc['type'] == "irc":
			try:
				new_broadcaster = IrcBroadcaster(network=bc['network'],
				                                 port=bc.get('port', 6667),
				                                 room=bc['room'],
				                                 nick=bc['nick'],
				                                 games=bc.get("games", []),
				                                 blacklist=cfg.get("blacklist", []))
			except Exception as e:
				logging.error("Could not create IrcBroadcaster")
				logging.exception(e)
		elif bc['type'] == "dbus":
			try:
				new_broadcaster = DbusBroadcaster()
			except Exception as e:
				logging.error("Could not create DbusBroadcaster")
				logging.exception(e)

		if new_broadcaster:
			broadcasters.append(new_broadcaster)

	# Get the path to the UNIX socket file for the listen server
	socket_file_path = cfg['socket']

	# Create the broadcast server
	ListenServer(socket_file_path, broadcasters)

	try:
		asyncore.loop()
	finally:
		# Always clean up
		if os.path.exists(socket_file_path):
			os.unlink(socket_file_path)


if __name__ == "__main__":
	logging.basicConfig(
		level=logging.DEBUG,
		format="%(name)s: %(message)s"
	)

	parser = argparse.ArgumentParser()
	parser.add_argument("--config",
	                    help="Configuration file in JSON format. Default is config.json in the current working directory.")
	parser.add_argument("--socket",
	                    help="The name of the Unix socket file to use. The default Unix socket file name is $XDG_RUNTIME_DIR/twitchwatch.sock")
	parser.add_argument("--log-level",
	                    help="Logging level, e.g., debug, info, critical. Default: critical")
	args = parser.parse_args()

	cfg = config.get_config(args)

	main(cfg)
