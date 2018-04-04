#-*- coding: utf-8 -*-
import json
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.websocket import websocket_connect
from time import sleep
from settings import SECRET_KEY_CLIENT, PERIODICITY, RECONNECT, WS_ADDRESS

EXAMPLE_REQUEST = {'Type': 'Request', 'Name': 'PingAllClient'}
EXAMPLE_REQUEST = json.dumps(EXAMPLE_REQUEST)

auth_message = json.dumps({'Type': 'Request', 'Name': 'AuthorizationService', 'Key': SECRET_KEY_CLIENT, 'Service': 'Check_Ping'})

@gen.coroutine
def main():
    server = None
    #first connect
    while server is None:
        try:
            server = yield websocket_connect(WS_ADDRESS)
            server.write_message(auth_message)
        except Exception as e:
            print e
            sleep(RECONNECT)
    #Work
    while True:
        try:
            server.write_message(EXAMPLE_REQUEST)
            connect = yield server.read_message()
            if connect is None:
                server.close()
                server = None
                while server is None:
                    try:
                        server = yield websocket_connect(WS_ADDRESS)
                        server.write_message(auth_message)
                        server.write_message(EXAMPLE_REQUEST)
                    except Exception as e:
                        print e
                        sleep(RECONNECT)
            sleep(PERIODICITY)
        except Exception as e:
            print e


if __name__ == "__main__":
    IOLoop.current().run_sync(main)
