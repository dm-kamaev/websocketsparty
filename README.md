## python(tornado) websocket

Start
``
sudo supervisorctl status

sudo supervisorctl restart tornado_server

``

Or call
``
/p/env/websockets/bin/python tornado_server.py
``

supervisor config
``
cat /etc/supervisor/conf.d/tornado_server.conf
``

Logs
``
tail -f /p/log/websockets/tornado_server.log
``


