#!/usr/bin/python3
# apt-get install gphoto2
import subprocess

p = subprocess.Popen(['gphoto2', '--auto-detect'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = p.communicate()
cameras = stdout.decode().split('-'*58)[-1].strip()
if cameras:
    cameras = [[p.strip() for p in c.split('usb:')] for c in cameras.split('\n')]
    for c in cameras:
        c[1] = 'usb:' + c[1]
    print("CAMERAS: {}".format(cameras))
else:
    cameras = []

for name, port in cameras:
    cmd = [
        'gphoto2',
        '--port', port,
        '--set-config /main/settings/capturetarget=0',
    ]
    subprocess.call(cmd)
