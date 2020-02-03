import argparse
import errno
import os

import pandas as pd

import environment as env
import gui
import toml

SETTINGS_FILE = "configuration/settings.toml"

def enter_mode(config, train):
    """ Runs ORSAT in the desired mode. """
    if config is not None:
        vis = gui.GUI(env.Environment(config[0], config[1]), toml.load(SETTINGS_FILE))
        vis.animate()
    return

def is_valid_configuration(config_id):
    """ Checks whether the provided config ID is valid,
    and if so, whether the file exists and if so,
    load the csv file. """
    settings = toml.load(SETTINGS_FILE)
    if config_id in settings["configs"]:
        if not os.path.isfile("configuration/" + settings["configs"][config_id]["file"]):
            raise FileNotFoundError(errno.ENOENT,
                os.strerror(errno.ENOENT), settings["configs"][config_id]["file"])
    else:
        raise KeyError(f"{config_id} is not a valid key in {SETTINGS_FILE}")
    config = pd.read_csv("configuration/" + settings["configs"][config_id]["file"])
    return config, config_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", 
        help="Specify an initial configuration \
        of ORSAT, where [CONFIG] is the ID of the configuration defined in \
        'settings.toml'. If not specified, then a random configuration is \
        generated.", 
        type=is_valid_configuration, 
        required=False
    ) 
    parser.add_argument("--train", 
        help="Runs ORSAT in a headless mode for training machine learning algorithms.",
        action='store_true'
    )
    args = parser.parse_args()  
    enter_mode(**vars(args))
