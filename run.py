""" Main entry point for ORSAT """

import argparse
import errno
import os

import environment
import gui
import toml

SETTINGS_FILE = "configuration/settings.toml"

def enter_mode(**kwargs):
    """ Runs ORSAT in the desired mode. """
    pass

def is_valid_configuration(config_id):
    """ Checks whether the provided config ID is valid,
    and if so, whether the file exists. """
    settings = toml.load(SETTINGS_FILE)
    if config_id in settings["configs"]:
        if not os.path.isfile("configuration/" + settings["configs"][config_id]["file"]):
            raise FileNotFoundError(errno.ENOENT,
                os.strerror(errno.ENOENT), settings["configs"][config_id]["file"])
    else:
        raise KeyError(f"{config_id} is not a valid key in {SETTINGS_FILE}")
    return config_id

def view(config):
    """ Initializes and runs the GUI with a single 
    instance of ORSAT """
    if config is None:
        gui.GUI().run()
        # random start
        pass
    else:
        # start with the ID'd config
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Specify an initial configuration \
        of ORSAT, where [CONFIG] is the ID of the configuration defined in \
        'settings.toml'. If not specified, then a random configuration is \
        generated.", type=is_valid_configuration, required=False) 
    args = parser.parse_args()  
    # enter_mode(**vars(args))
    vis = gui.GUI(environment.Environment(), toml.load(SETTINGS_FILE))
    vis.animate()
