#!/usr/bin/env python3

import argparse
import asyncore
import logging
from logging.handlers import WatchedFileHandler
import os

from server import ListenServer
from broadcasters import IrcBroadcaster, DbusBroadcaster, DiscordWebhookBroadcaster
import config


LOG_FORMAT = "%(asctime)s — %(name)s — %(levelname)s — %(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
log = logging.getLogger()



if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--config",
	                    help="Configuration file in JSON format. Default is config.json in the current working directory.")
	parser.add_argument("--socket",
	                    help="The name of the Unix socket file to use. The default Unix socket file name is $XDG_RUNTIME_DIR/twitchwatch.sock")
	parser.add_argument("--log-level",
	                    default="error",
	                    help="Logging level, e.g., debug, info, warning, error, critical. Default: critical")
	parser.add_argument("--log-file",
	                    default=None,
	                    help="File to send logging output")
	args = parser.parse_args()

	log.setLevel({
		'debug': logging.DEBUG,
		'info': logging.INFO,
		'warning': logging.WARNING,
		'error': logging.ERROR,
		'critical': logging.CRITICAL,
	}[args.log_level])

	if "log_file" in args and args.log_file is not None:
		log_handler = logging.FileHandler(args.log_file)
		log_handler.setFormatter(logging.Formatter(LOG_FORMAT))
		log.addHandler(log_handler)

	cfg = config.get_config(args)

	broadcasters = []

	for bc in cfg.get("broadcasters", []):
		new_broadcaster = None

		if bc['type'] == "irc":
			try:
				new_broadcaster = IrcBroadcaster(network=bc["network"],
				                                 port=bc.get("port", 6667),
				                                 room=bc["room"],
				                                 nick=bc["nick"],
				                                 games=bc.get("games", []),
				                                 blacklist=cfg.get("blacklist", []))
			except Exception as e:
				log.error("Could not create IrcBroadcaster")
				log.exception(e)
		elif bc['type'] == "dbus":
			try:
				new_broadcaster = DbusBroadcaster()
			except Exception as e:
				log.error("Could not create DbusBroadcaster")
				log.exception(e)
		elif bc['type'] == "discord":
			try:
				new_broadcaster = DiscordWebhookBroadcaster(webhook_url=bc['webhook-url'])
			except Exception as e:
				log.error("Could not create DiscordWebhookBroadcaster")
				log.exception(e)

		if new_broadcaster:
			broadcasters.append(new_broadcaster)

	# Get the path to the UNIX socket file for the listen server
	socket_file_path = cfg['socket']

	# Create the broadcast server
	ListenServer(socket_file_path, broadcasters)

	try:
		asyncore.loop()
	except KeyboardInterrupt:
		pass
	finally:
		# Always clean up
		if os.path.exists(socket_file_path):
			os.unlink(socket_file_path)
