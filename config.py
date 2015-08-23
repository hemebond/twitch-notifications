import logging
import os
import json
import xdg.BaseDirectory


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
		args["log-level"] = args.pop("log_level")
		args["max-age"] = args.pop("max_age")
		args["cache-file"] = args.pop("cache_file")
	else:
		args = {}

	# Set the logging level
	set_logging_level(args.get("log-level"))

	config_dir = xdg.BaseDirectory.save_config_path(appname)
	cache_dir = xdg.BaseDirectory.save_cache_path(appname)
	run_dir = xdg.BaseDirectory.get_runtime_dir()
	cfg_file_name = "config.json"

	# Configuration defaults
	cfg = {
		"socket": os.path.join(run_dir, "{0}.sock".format(appname)),
		"cache-file": os.path.join(cache_dir, "streams.json"),
		"log-level": "critical",
		"max-age": "24h",
	}

	# The paths to search for the config file
	cfg_paths = [
		os.path.join(config_dir, cfg_file_name),
		os.path.join(os.path.dirname(os.path.realpath(__file__)), cfg_file_name)
	]

	if args.get("config", False):
		new_settings = read_config_file(args.get("config"))
		cfg.update(new_settings)
	else:
		for path in cfg_paths:
			new_settings = read_config_file(path)

			if new_settings != {}:
				cfg.update(new_settings)
				break

	logging.info("Configuration file: {0}".format(cfg))

	# Override config file settings with command-line settings
	for k, v in args.items():
		if v is not None:
			cfg[k] = v

	logging.info("Final configuration: {0}".format(cfg))

	return cfg
