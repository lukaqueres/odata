import logging

from odata.client import Client


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s : %(message)s', level=logging.DEBUG)

odata_logger = logging.getLogger("odata")


odata_logger.level = logging.DEBUG
