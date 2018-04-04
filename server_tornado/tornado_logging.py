#-*- coding: utf-8 -*-
import logging


FILENAME = 'log/ws.log'

# set up logging to file - see previous section for more details
# logging.basicConfig(level=logging.DEBUG,
#                     datefmt='%m-%d %H:%M:%S',
#                     )

handler = logging.handlers.RotatingFileHandler(
              FILENAME, maxBytes=100*1024*1024, backupCount=5)

handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s'))

log_msg = logging.getLogger('Message')
log_msg.setLevel(logging.DEBUG)
log_event = logging.getLogger('Event')
log_event.setLevel(logging.DEBUG)
log_msg.addHandler(handler)
log_event.addHandler(handler)
