#-*- coding: utf-8 -*-
import json
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.websocket import websocket_connect
from api_1C_server import log_msg, SimpleQuery
from time import sleep
from settings import SECRET_KEY_CLIENT, WS_ADDRESS

auth_message = json.dumps({'Type': 'Request', 'Name': 'AuthorizationService', 'Key': SECRET_KEY_CLIENT, 'Service': 'Porter_1C'})


@gen.coroutine
def main():
    server = None
    # First connect
    log_msg.info('Start 1C Server Porter')
    while server is None:
        try:
            server = yield websocket_connect(WS_ADDRESS)
            server.write_message(auth_message)
            log_msg.info(auth_message)
        except Exception as e:
            log_msg.error(e)
            sleep(1)
    # work
    while True:
        message = yield server.read_message()
        log_msg.info(message)
        if message is None:
            server.close()
            server = None
            while server is None:
                try:
                    server = yield websocket_connect(WS_ADDRESS)
                    server.write_message(auth_message)
                    log_msg.info(auth_message)
                    sleep(5)
                except Exception as e:
                    log_msg.error(e)
                    sleep(1)
        else:
            # PARSE message from tornado_server
            try:
                request_1C = SimpleQuery(message)
                request_1C.do()
                server.write_message(request_1C.response)
            except Exception as e:
                log_msg.error(e)


if __name__ == "__main__":
    IOLoop.current().run_sync(main)