#-*- coding: utf-8 -*-
import json
from datetime import datetime
import httplib
import logging
from settings import ADDRESS, PORT, URL, KEY_DJANGO, TIMEOUT

#Log param
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename='log/django_porter.log')
log_msg = logging.getLogger('Message')
#End Log param


class Method(object):

    def __init__(self, method):
        self.method = method
        self.param = ""
        self.response = None
        self.error_code = None
        self.error_text = None
        self.ActionID = None

    def correct(self):
        #Correct Phone number
        if self.method == 'GetTestForEmployee':
            self.response['TimeStart'] = datetime.strptime(self.response['TimeStart'], "%Y-%m-%dT%H:%M:%SZ")



class Query(object):

    def __init__(self):
        self.method_list = []
        #id-ки лица, осуществляющего запрос.
        #Получаем по маске токен.
        self.body = {'Methods': [], 'Key': KEY_DJANGO}
        self.headers = {"Content-type": "application/json"}
        self.response = None

    #Добавление метода к запросу
    def add(self, method):
        self.method_list.append(method)
        #Получение ActionID
        method.ActionID = len(self.method_list)


    #Сделать запрос
    def do(self):
        #Добавляем методы в тело запроса.
        for method in self.method_list:
            self.body['Methods'].append({'Method': method.method, 'Param': method.param, 'ActionID': method.ActionID})
        conn = httplib.HTTPConnection(ADDRESS, PORT, timeout=TIMEOUT)
        self.body = json.dumps(self.body)
        try:
            conn.request("POST", URL, self.body, self.headers)
        except Exception as e:
            log_msg.error(e)
            self.response = '{"Result":"Error connect to django"}'
            return
        self.response = conn.getresponse().read()



