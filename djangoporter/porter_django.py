import json
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.websocket import websocket_connect
from api_django import Query, Method, log_msg
from time import sleep
from settings import WS_ADDRESS, SECRET_KEY_CLIENT


auth_message = json.dumps({'Type': 'Request', 'Name': 'AuthorizationService', 'Key': SECRET_KEY_CLIENT, 'Service': 'Porter_Django'})


@gen.coroutine
def main():
    server = None
    # First connect
    log_msg.info('Start porter django')
    while server is None:
        try:
            server = yield websocket_connect(WS_ADDRESS)
            server.write_message(auth_message)
            log_msg.info(auth_message)
        except Exception as e:
            log_msg.error(e)
            sleep(5)
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
                    sleep(5)
        else:
            #Request to django
            RequestToDjango = Query()
            Auth = Method('Auth')
            Auth.param = message
            RequestToDjango.add(Auth)
            RequestToDjango.do()
            #Send respons to Tornado server
            server.write_message(RequestToDjango.response)
            log_msg.info(RequestToDjango.response)


if __name__ == "__main__":
    IOLoop.current().run_sync(main)