# -*- coding: utf-8 -*-
from tornado_logging import log_event, log_msg
import json
import uuid
from datetime import datetime



log_event.info('Start Server')
CHECK_PERMISSIONS = True


# Name service
Porter_1C = 'Porter_1C'
Check_Ping = 'Check_Ping'
Porter_Django = 'Porter_Django'
Porter_Asterisk = 'Porter_Asterisk'


# 'k2LXeQAXGJ': {'ip': '192.168.2.4', 'port': 80},  # 1C Prod
# '9vd6p0kUeo': {'ip': '192.168.1.230', 'port': 1080},  # 1C Pavel
# 'zFToQNsJJ1': {'ip': '192.168.1.240', 'port': 1080},  # 1C Damir
auth_servers = {'k2LXeQAXGJ': Porter_1C, '9vd6p0kUeo': Porter_1C, 'zFToQNsJJ1': Porter_1C, 'fadsfhHIOR': Porter_1C}

SPECIAL_CLIENT_KEY = {'asdjf27FASdh27daq3k1': 'AstDom', 'asdfashdfu134h23uih': 'TestAstDom'}


class AppError(Exception):
    def __init__(self, code='', *args):
        self.code = code
        self.args = [arg for arg in args]
        self.log()

    def log(self):
        log_event.error('App Error: %s' % self.code)


class SecretKey(AppError):
    def log(self):
        log_event.error('SecretKey error: %s' % self.code)



class ServiceIsNotConnected(AppError):
    def __str__(self):
        return 'Service is not connected error: %s' % self.code


class AuthorizationClientFailed(AppError):
    def __str__(self):
        return 'Authorization client failed error: %s' % self.code


class Connections(object):
    """
    #No Auth Client
    self.no_auth_clients[Validation RequestID] = { 'Object': object client, 'RequestID': Auth RequestID, 'ClientData': client data }
    client.id - ID client
    client.is_client = True
    client.is_auth = False
    client.val_req_id = Validation RequestID

    #Client
    self.clients[ID-client] = {'Object': object client, 'Params': set(params), 'ClientData': 'client data'}
    client.id - ID client
    client.is_client = True
    client.is_auth = True

    #Service
    self.service = { 'Name service': object service, 'Name service': object service}
    service.is_client = False
    service.is_auth = True

    #Group
    self.group = { 'Phone111': [client0, client1, client2, client3, ... ], 'phone222': [...] }
    """

    def __init__(self):
        self.clients = {}
        self.no_auth_clients = {}
        self.service = {Porter_1C: None, Check_Ping: None, Porter_Django: None, Porter_Asterisk: None}
        self.group = {}

        self.monitor_ast = {}

    def is_service(self, client):
        return client.id in self.service

    def response_client(self, name, data, client, request_id):
        message = {
            "Type": "Response",
            "Name": name,
            "Data": data,
            "RequestID": request_id,
        }
        self.write_client(client, message)

    def response_client_http(self, name, data, client, request_id):
        message = {
            "Type": "Response",
            "Name": name,
            "Data": data,
            "RequestID": request_id,
        }
        self.write_client_http(client, message)
        
    def event_client(self, recipients, msg, type_msg, sender=None):
        message = {
            "Type": "Event",
            "Name": "NewMessage",
            "Data": {
                "Type": type_msg,
                "Message": msg,
            }
        }
        if sender:
            message['Data']['Sender'] = sender
        message = json.dumps(message)
        for recipient in recipients:
            self.write_client(recipient, message)

    # Сообщение группе клиентов
    def write_clients_group(self, param, message):
        group_clients = self.group[param]
        for client in group_clients:
            self.write_client(client, message)

    # Сообщение конкретному клиенту
    def write_client(self, client, message):
        try:
            client.write_message(message)
        except Exception as e:
            log_event.error('Error %s sending message %s to client %s' % (e, message, client))

    def write_client_http(self, client, message):
        try:
            client.write(message)
        except Exception as e:
            log_event.error('Error %s sending message %s to client %s' % (e, message, client.id))


    def write_service(self, service_name, message):
        try:
            self.service[service_name].write_message(message)
        except Exception as e:
            log_event.error('Error sending message %s to service %s' % (message, service_name))
            if self.service[service_name] is None:
                log_event.error('Service %s is None' % service_name)
                return None
            log_event.error(e)

    # Маршрутизация сообщения
    def routing_message(self, client, message):
        log_msg.info(message + ' IP %s' % client.request.remote_ip)
        message = json.loads(message)
        # Определение типа запроса
        if message['Type'] == 'Request':
            if message['Name'] == 'Authorization':
                self.auth_client(client, message)
            elif message['Name'] == 'SendMessage':
                self.send_message(client, message)
            elif message['Name'] == 'AuthorizationService':
                self.add_service(client, message)
            elif message['Name'] == 'Monitor':
                self.monitor_ast = message['Message']
            elif message['Name'] == 'SpecialClient':
                self.auth_special_client(client, message)
            elif message['Name'] == 'PingAllClient':
                self.ping_all_client(client)
        elif message['Type'] == 'Response':
            if message['Name'] == 'Validation':
                self.auth_client_success(client, message)
        elif message['Method'] == 'AddService':
            self.add_service(client, message)

    def send_message(self, client, message, from_http=False):
        clients = self.intersection_flags(message["Param"]["FlagsRecipients"])
        if from_http:
            self.event_client(clients, message['Param']['Message'], message['Param']['Type'], client.id)
            self.response_client_http('SendMessage', True, client, message.get('RequestID', ''))
        else:
            self.response_client('SendMessage', True, client, message.get('RequestID', ''))
            self.event_client(clients, message['Param']['Message'], message['Param']['Type'], client.id)

    def intersection_flags(self, flags):
        if flags:
            first_flag = flags.pop(0)
            recipient_ids = set(self.group.get(first_flag, []))
            for flag in flags:
                recipient_ids.intersection_update(set(self.group.get(flag, [])))
            recipients = []
            for recipient_id in recipient_ids:
                recipients.append(self.clients[recipient_id]['Object'])
            return recipients
        else:
            return []

    # Авторизация клиента
    def auth_client(self, client, message):
        try:
            auth_server = auth_servers[message['Param']['Key']]
        except KeyError, e:
            raise SecretKey(e.message)
        message['Name'] = 'Validation'
        client.id = str(uuid.uuid4())
        client.is_client = True
        client.is_auth = False
        request_id = str(uuid.uuid4())
        message['RequestID'] = request_id
        self.no_auth_clients[request_id] = {'Object': client, 'RequestID': message['RequestID'], 'ClientData': message['Param']['ClientData']}
        client.val_req_id = request_id
        log_event.info('Send auth request client %s IP %s' % (client.id, client.request.remote_ip))
        self.write_service(auth_server, message)

    # Завершение авторизации
    def auth_client_success(self, auth_server, message):
        if not self.is_service(auth_server):
            log_event.error('No permissions run fun auth_client_success() client %s', auth_server.request.remote_ip)
            self.del_ws(auth_server)
            return
        # Авторизация прошла успешно
        no_auth_client = self.no_auth_clients.pop(message['RequestID'], None)
        # Клиент не найден
        if no_auth_client is None:
            log_event.error('RequestID %s is wrong', message['RequestID'])
            return
        client = no_auth_client['Object']
        old_request_id = no_auth_client['RequestID']
        client_data = no_auth_client['ClientData']
        if not message['Data']['Result']:
            client.on_close()
            return
        client.is_auth = True
        del client.val_req_id
        self.clients[client.id] = {'Object': client, 'Params': set(), 'ClientData': client_data}
        if not message['Data']['Flags']:
            message['Data']['Flags'] = []
        message['Data']['Flags'].append(client.id)
        self.update_param({'Add': message['Data']['Flags']}, client)
        self.response_client('Authorization', True, client, old_request_id)

    def auth_special_client(self, client, message):
        if message['Key'] in SPECIAL_CLIENT_KEY:
            client.id = SPECIAL_CLIENT_KEY[message['Key']]
            if self.clients.get(client.id):
                self.del_client(self.clients[client.id])
            self.clients[client.id] = {'Object': client, 'Params': set(), 'ClientData': 'Connected %s' % datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            self.update_param({'Add': [SPECIAL_CLIENT_KEY[message['Key']],]}, client)
            client.is_auth = True
            client.is_client = True
        else:
            client.on_close()
            return

    # Обновление параметров объекта
    def update_param(self, params, client):
        params['Add'] = params.get('Add')
        params['Delete'] = params.get('Delete')
        params['ClientData'] = params.get('ClientData')
        if params['Add']:
            self.clients[client.id]['Params'].update(params['Add'])
            for param in params['Add']:
                try:
                    self.group[param].append(client.id)
                except KeyError:
                    self.group[param] = []
                    self.group[param].append(client.id)
        if params['Delete']:
            self.clients[client.id]['Params'].difference_update(params['Delete'])
            for param in params['Delete']:
                try:
                    self.group[param].remove(param)
                except ValueError:
                    pass
        if not params['ClientData'] is None:
            self.clients[client.id]['ClientData'] = params['ClientData']
        log_event.info('Update client - %s | add - %s | del - %s' % (client.id, params['Add'], params['Delete']))

    # Добавление сервиса
    def add_service(self, client, params):
        # Авторизация сервиса
        if params['Key'] == 'asdjf27FASdh27daq3k' and params['Service'] == Porter_1C:
            self.service[Porter_1C] = client
        elif params['Key'] == 'asdfasdfqweq2341das' and params['Service'] == Check_Ping:
            self.service[Check_Ping] = client
        elif params['Key'] == 'fasdfasjdfoasidfjoasdf' and params['Service'] == Porter_Django:
            self.service[Porter_Django] = client
        else:
            client.on_close()
            return
        client.is_client = False
        client.id = params['Service']
        log_event.info('Run service %s IP %s' % (params['Service'], client.request.remote_ip))

    def del_ws(self, connection_ws):
        if hasattr(connection_ws, 'is_client'):
            if connection_ws.is_client:
                self.del_client(connection_ws)
            elif not connection_ws.is_client:
                self.del_service(connection_ws.id)
        del connection_ws

    # Удаление клиента
    def del_client(self, client):
        if client.is_auth:
            for param in self.clients[client.id]['Params']:
                self.group[param].remove(client.id)
                if not self.group[param]:
                    del self.group[param]
            del self.clients[client.id]
            log_event.info('Delete auth client %s' % client.id)
        else:
            del self.no_auth_clients[client.val_req_id]
            log_event.info('Delete no auth client %s' % client.id)

    # Удаление сервиса
    def del_service(self, service_id):
        self.service[service_id] = None
        log_event.info('Delete service %s' % service_id)

    # Проверка всех клиентов
    def ping_all_client(self, client):
        # check
        if CHECK_PERMISSIONS:
            if client is self.service[Check_Ping]:
                pass
            else:
                log_event.error('No permissions run fun ping_all_client() client %s', client.request.remote_ip)
                self.del_ws(client)
                return
        dead_clients = []
        log_event.info('Start checking for connect client')
        for client_id in self.clients:
            if self.ping_client(self.clients[client_id]['Object']):
                dead_clients.append(client_id)
        for client_id in dead_clients:
            self.del_client(client_id)
        dead_service = []
        log_event.info('Start checking for connect service')
        # Ping all Service
        for name in self.service:
            if self.ping_service(name):
                dead_service.append(name)
        for service in dead_service:
            self.del_service(service)
        self.service[Check_Ping].write_message('OK')

    def ping_client(self, client):
        try:
            client.ping('check')
        except:
            log_event.error('Client %s connection lost' % client.id)
            return True

    def ping_service(self, name):
        try:
            if self.service[name]:
                self.service[name].ping('check')
        except:
            log_event.error('Service %s connection lost' % name)
            return True
