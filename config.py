import os
from decouple import config

from log import logger


def unpack_list(string):
    try:
        return string.replace("\"", "").replace(" ", "").split(",")
    except:
        logger.error("Failed to unpack values in config file!")


class Config:
    VERSION = config("VERSION")

    '''
        DB_PATH = "{}://{}:{}@{}:{}/{}".format(
            config("DB_ENGINE"),
            config("DB_USER"),
            config("DB_PASS"),
            config("DB_HOST"),
            config("DB_PORT"),
            config("DB_NAME")
        )
        '''
    # TODO: Use proper database ;-)
    DB_PATH = f"sqlite:///{os.path.dirname(__file__)}/db.sqlite"

    AUDIO_TYPES = unpack_list(config("AUDIO_TYPES"))
    ROOT_DIR = config("ROOT_DIR")


try:
    CONFIG = Config
except:
    logger.error("No config file found!")
