import logging
import os
import json
from xdg import (XDG_CACHE_HOME, XDG_CONFIG_DIRS, XDG_CONFIG_HOME, XDG_DATA_DIRS, XDG_DATA_HOME, XDG_RUNTIME_DIR)


def set_logging_level(level):
	if level in ["debug", "info", "warning", "error", "critical"]:
		logging.getLogger().setLevel(getattr(logging, level.upper()))


def read_config_file(path):
	"""
	Takes a path to a JSON file, reads and parses it, returns as dict
	"""
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


def get_config(args=None, appname="twitchwatch"):
	"""
	Reads a JSON configuration file. Searches several paths, picking the first
	file it finds.

	:param appname: The name of the application. Used for config and runtime directory names.
	:return: Dict with the merged set of configuration options
	"""
	if args:
		# Change from an object to a dict
		args = vars(args)

		# Rename log_level back to log-level
		args["cache-file"] = args.pop("cache_file", None)
		args["log-level"] = args.pop("log_level", None)
		args["max-age"] = args.pop("max_age", None)
	else:
		args = {}

	# Set the logging level
	set_logging_level(args.get("log-level"))

	config_dir = os.path.join(XDG_CONFIG_HOME, appname)
	cache_dir = os.path.join(XDG_CACHE_HOME, appname)
	run_dir = XDG_RUNTIME_DIR
	cfg_file_name = "config.json"

	# Configuration defaults
	cfg = {
		"socket": os.path.join(run_dir, "{0}.sock".format(appname)),
		"cache-file": os.path.join(cache_dir, "streams.json"),
		"log-level": "critical",
		"max-age": "24",
	}

	# The paths to search for the config file
	if args.get("config", False):
		cfg_paths = [args.get("config")]
	else:
		cfg_paths = [
			os.path.join(config_dir, cfg_file_name),
			os.path.join(os.path.dirname(os.path.realpath(__file__)), cfg_file_name)
		]

	for path in cfg_paths:
		settings_from_file = read_config_file(path)
		logging.debug(settings_from_file)

		if settings_from_file != {}:
			cfg.update(settings_from_file)
			break

	logging.info("Configuration file: {0}".format(cfg))

	# Override config file settings with command-line settings
	for k, v in args.items():
		if v is not None:
			cfg[k] = v

	logging.info("Final configuration: {0}".format(cfg))

	return cfg
