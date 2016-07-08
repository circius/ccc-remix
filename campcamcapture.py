#!/usr/bin/python3
# apt-get install gphoto2 graphicsmagick-imagemagick-compat python3-tornado
import json
import os
import re
import signal
import subprocess
import sys
from queue import Queue
from threading import Thread
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import StaticFileHandler, Application
from tornado.websocket import WebSocketHandler
import webbrowser

import logging
logger = logging.getLogger(__name__)

is_running = True
sockets = []
settings = {
    'cameras': [],
    'title': 'Untitled'
}
base = 'scan'

def get_usbport(device):
    device = device.split(',')[-1].lstrip('0')
    p = subprocess.Popen(['lsusb', '-t'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    cameras = [
        re.compile('Port (\d+): Dev (\d+),').findall(c)[0]
        for c in stdout.decode().split('\n') if 'Port' in c
    ]
    port = [p[0] for p in cameras if p[1] == device]
    if port:
        port = port[0]
    else:
        port = None
    return port

def get_cameras():
    p = subprocess.Popen(['gphoto2', '--auto-detect'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    cameras = stdout.decode().split('-'*58)[-1].strip()
    if cameras:
        cameras = [[p.strip() for p in c.split('usb:')] for c in cameras.split('\n')]
        for c in cameras:
            c[1] = 'usb:' + c[1]
            c.append(get_usbport(c[1]))
        print("CAMERAS: {}".format(cameras))

    else:
        cameras = []
    return cameras

def get_titles():
    if not os.path.exists(base):
        os.makedirs(base)
    titles = [title for title in os.listdir(base) if os.path.isdir(os.path.join(base, title))]
    titles.sort()
    return titles

def update_title(title):
    settings['title'] = title
    path = os.path.join(base, settings['title'].replace('/', '_'))
    if os.path.exists(path):
        pages = sorted([os.path.join(path, image) for image in os.listdir(path)])
        trigger_event('pages', pages)

def capture_page(page):
    print('capture page', page)
    if settings['title']:
        prefix = os.path.join(base, settings['title'].replace('/', '_'))
    else:
        prefix = base
    left = os.path.join(prefix, '%06d_left.jpg' % page)
    page += 1
    right = os.path.join(prefix, '%06d_right.jpg' % page)
    cameras = settings['cameras']
    if cameras:
        print(cameras)
        cam, port, usbport = cameras[0]
        cmd = [
            'gphoto2',
            '--port', port,
            '--force-overwrite',
            '--capture-image-and-download',
            '--filename', left
        ]
        print(" ".join(cmd))
        c1 = subprocess.Popen(cmd)

        cam, port, usbport = cameras[1]
        cmd = [
            'gphoto2',
            '--port', port,
            '--force-overwrite',
            '--capture-image-and-download',
            '--filename', right
        ]
        print(" ".join(cmd))
        c2 = subprocess.Popen(cmd)
        c1.wait()
        c2.wait()
        error = []
        if not os.path.exists(left):
            error += ['left missing']
        if not os.path.exists(right):
            error += ['right missing']
        if error:
            trigger_event('error', 'capture failed %s<br>(Reconnect cameras and press R)' % ', '.join(error))
            print('capture failed %s' % ', '.join(error))
            return
        for cmd in (
            ['mogrify', '-rotate', '-90', left],
            ['mogrify', '-rotate', '90', right]
        ):
            subprocess.call(cmd)
        trigger_event('page', [left, right])
    else:
        trigger_event('error', 'Cameras Missing<br>(Reconnect cameras and press R)')

class Tasks(Thread):
    def __init__(self):
        self.q = Queue()
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        while is_running:
            m = self.q.get()
            if is_running and m:
                try:
                    action, data = m
                    if action == 'capture':
                        capture_page(data)
                    elif action == 'cameras':
                        settings['cameras'] = data
                        trigger_event('cameras', data)
                    elif action == 'detectcameras':
                        settings['cameras'] = get_cameras()
                        trigger_event('cameras', settings['cameras'])
                    elif action == 'title':
                        update_title(data)
                except:
                    logger.debug('fail', exc_info=True)
                    pass
            self.q.task_done()

    def join(self):
        self.q.put(None)
        return Thread.join(self)

    def queue(self, action, data=None):
        if is_running:
            self.q.put((action, data))

class WSHandler(WebSocketHandler):

    def open(self):
        if self not in sockets:
            sockets.append(self)
        settings['cameras'] = get_cameras()
        trigger_event('cameras', settings['cameras'])
        trigger_event('titles', get_titles())

    def on_message(self, message):
        tasks.queue(*json.loads(message))

    def on_close(self):
        if self in sockets:
            sockets.remove(self)

    def post(self, event, data):
        message = json.dumps([event, data])
        main = IOLoop.instance()
        if self.ws_connection is None:
            self.on_close()
        else:
            main.add_callback(lambda: self.write_message(message))

def trigger_event(event, data):
    if len(sockets):
        logger.debug('trigger event %s %s %s', event, data, len(sockets))
    for ws in sockets:
        try:
            ws.post(event, data)
        except:
            logger.debug('failed to send to ws %s %s %s', ws, event, data, exc_info=True)

if __name__ == '__main__':
    port = 8008
    if len(sys.argv) == 1:
        address = '127.0.0.1'
    else:
        address = '0.0.0.0'
        port = int(sys.argv[1])
    static_path = os.path.abspath(os.path.dirname(__file__))
    handlers = [
        (r'/ws', WSHandler),
        (r'/(.*)', StaticFileHandler, {'path': static_path, 'default_filename': 'index.html'}),
    ]
    options = {
        'debug': False,
        'gzip': True
    }
    http_server = HTTPServer(Application(handlers, **options))
    http_server.listen(port, address)
    logging.basicConfig(level=logging.DEBUG)

    settings['cameras'] = get_cameras()
    tasks = Tasks()
    main = IOLoop.instance()

    def shutdown():
        global is_running
        is_running = False
        tasks.join()
    signal.signal(signal.SIGTERM, shutdown)
    if address == '127.0.0.1':
        webbrowser.open_new_tab('http://%s:%s' % (address, port))
    try:
        main.start()
    except:
        print('shutting down...')
    shutdown()
