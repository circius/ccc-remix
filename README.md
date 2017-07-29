# campcamcapture

Forked from https://r-w-x.org/campcamcapture.git

## reasons for fork

Learning project for javascript, JQuery, tornado.web and websockets.

## changes

+ Added provision of zipped copies of scan-folders.
+ Added a 'delete' interface to allow users to delete finished (exported) work.
+ Added a rudimentary guide to usage on the index.html.
+ Made some cosmetic changes to the stylesheet.
+ Corrected the overly-persistent 'cameras missing' error-message.
## Install

install dependencies:

    sudo apt-get install gphoto2 graphicsmagick-imagemagick-compat python3-tornado

checkout the latest version:

    git clone https://r-w-x.org/campcamcapture.git


run campcampcapture:

    cd campcamcapture
    ./campcamcapture.py


## Preparing Cameras

make sure camera is not mounted and shows up in gphoto2 --auto-detect
some cameras to set capture target, try running ./setupcamera.py


## Usage

to use campcamcapture, open browser at http://127.0.0.1:8008/

click "Create New Book" and enter a title, scans are stored in a folder scans inside of campcamcapture

Available Keyboard commands:

    SPACE - capture next page
    f     - flip cameras left/right
    r     - detect cameras
    arrow left / arrow right to flip through existing pages (new pages are added after current page)

