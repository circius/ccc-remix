#!/usr/bin/python3
# apt-get install gphoto2 graphicsmagick-imagemagick-compat
import os
import subprocess
import json
import signal
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

def get_cameras():
    p = subprocess.Popen(['gphoto2', '--auto-detect'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    cameras = stdout.decode().split('-'*58)[-1].strip()
    if cameras:
        cameras = [c.split('usb:')[0].strip() for c in cameras.split('\n')]
    else:
        cameras = []
    return cameras

def get_titles():
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
        c1 = subprocess.Popen([
            'gphoto2', '--camera', cameras[0],
            '--force-overwrite', '--capture-image-and-download',
            '--filename', left
        ])
        c2 = subprocess.Popen([
            'gphoto2', '--camera', cameras[1],
            '--force-overwrite', '--capture-image-and-download',
            '--filename', right
        ])
        c1.wait()
        c2.wait()
        error = []
        if not os.path.exists(left):
            error += ['left missing']
        if not os.path.exists(right):
            error += ['right missing']
        if error:
            trigger_event('error', 'capture failed %s' % ', '.join(error))
            print('capture failed %s' % ', '.join(error))
            return
        for cmd in (
            ['mogrify', '-rotate', '-90', left],
            ['mogrify', '-rotate', '90', right]
        ):
            subprocess.call(cmd)
        trigger_event('page', [left, right])
    else:
        trigger_event('error', 'Cameras Missing')

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
        trigger_event('cameras', get_cameras())
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
    port = 8000
    address = '127.0.0.1'
    static_path = os.path.abspath(os.path.dirname(__name__))
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
    webbrowser.open_new_tab('http://%s:%s' % (address, port))
    try:
        main.start()
    except:
        print('shutting down...')
    shutdown()
