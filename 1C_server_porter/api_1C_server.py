#-*- coding: utf-8 -*-
import json
from datetime import datetime
import httplib
import base64
import logging
from settings import ADDRESS_LIST, URL, URL_TELEPHONY


logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename='log/1C_porter.log')
log_msg = logging.getLogger('Message')


class SimpleQuery():
    def __init__(self, message):
        # Статические параметры подключения и запроса
        username = 'site'
        password = 'asASDFdfs23'
        auth = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        self.headers = {"Content-type": "application/json", "Authorization": "Basic %s" % auth}
        self.response = None

        message = json.loads(message)

        self.ADDRESS = ADDRESS_LIST[message['Param']['Key']]['ip']
        self.PORT = ADDRESS_LIST[message['Param']['Key']]['port']
        del message['Param']['Key']
        self.body = json.dumps(message)

    def do(self):
        conn = httplib.HTTPConnection(self.ADDRESS, self.PORT, timeout=20)
        log_msg.info('Send simple query to 1C server %s' % self.body)
        try:
            conn.request("POST", URL, self.body, self.headers)
        except:
            raise
        self.response = conn.getresponse().read().decode("utf-8-sig")
        log_msg.info('Response from 1C %s ' % self.response)
        conn.close()
