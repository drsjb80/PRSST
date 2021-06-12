import argparse
import tkinter
import time
import webbrowser
import queue
import threading
import feedparser
import yaml
import html
import re
from os import path
from tkfontchooser import askfont
from pathlib import Path


# https://programmingideaswithjake.wordpress.com/2016/05/07/object-literals-in-python/
class Object:
    def __init__(self, **attributes):
        self.__dict__.update(attributes)

currentURL = ''
q = None
root = tkinter.Tk()
labelvar = tkinter.StringVar()
label = tkinter.ttk.Label(root, textvariable=labelvar)
growright = False

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--feed', help="specify feed directly", \
    action='append')
parser.add_argument('-y', '--yaml', help="specify YAML file", \
    action='append')
args = parser.parse_args()

# make into a lambda
def openbrowser(event):
    global currentURL
    webbrowser.open(currentURL)

def initialize(root, label, labelvar):
    root.title('DRSST')
    labelvar.set('Initializing')

    tkinter.ttk.Style().configure("TLabel", padding=4)
    label.bind("<Button-1>", openbrowser)
    label.pack()

    menubar = tkinter.Menu(root)
    settings = tkinter.Menu(menubar, tearoff=0)
    settings.add_command(label="Font", command=setfont)
    menubar.add_cascade(label="Settings", menu=settings)
    root.config(menu=menubar)

def setdefaults(config, label):
    if 'font' in config:
        label.configure(font=config['font'])
    if 'feeds' not in config:
        config['feeds'] = ['http://feeds.rssboard.org/rssboard']
    if 'growright' not in config:
        config['growright'] = False
    if 'delay' not in config:
        config['delay'] = 10
    if 'reload' not in config:
        config['reload'] = 120

def readconfig(label):
    config = {}
    if args.feed:
        config['feeds'] = args.feed

    if args.yaml:
        for y in args.yaml:
            with Path(y).open() as f:
                config.update(yaml.safe_load(f))

    if args.feed is None and args.yaml is None:
        with Path(str(Path.home()) + '/.prsst.yml').open() as f:
            config.update(yaml.safe_load(f))

    setdefaults(config, label)
    return config

def setfont():
    font = askfont(root)
    if font:
        font['family'] = font['family'].replace(' ', '\ ')
        font_str = "%(family)s %(size)i %(weight)s %(slant)s" % font
        if font['underline']:
            font_str += ' underline'
        if font['overstrike']:
            font_str += ' overstrike'
        label.configure(font=font_str)
        config['font'] = font_str

        with open('prsst.yml', 'w') as f:
            yaml.dump(config, f)


# import urllib.request
# import base64
# url = 'https://portswigger.net/daily-swig/rss/icon'
# raw_data = urllib.request.urlopen(url).read()
# im = Image.open(io.BytesIO(raw_data))
# img = ImageTk.PhotoImage(im)
# label = ttk.Label(root, image=img, textvariable=labelvar)

class FetchThread(threading.Thread):
    def __init__(self, URL):
        super().__init__()
        self.URL = URL

    def run(self):
        f = feedparser.parse(self.URL)
        try:
            f.feed
            f.feed.title
        except:
            print('error fetching feed', self.URL)
            f.feed.title = 'Error'
            # this is a hack so i don't have to create objects
            f.entries = [{'title':('Unable to load %s') % self.URL, \
                'link':'http://www.example.com'}]

        # get everything in safely so there's no interleaving
        with threading.Lock():
            q.put({"i'm a title":f.feed.title})
            for entry in f.entries:
                q.put(entry)

class Reload(threading.Thread):
    def __init__(self):
        super().__init__()
        
    def run(self):
        global q
        while True:
            # the second and subsequent times
            if q != None:
                config['reload'] = (config['delay'] * q.qsize() / 60) + 2

            with threading.Lock():
                q = queue.SimpleQueue()
                for feed in config['feeds']:
                    t = FetchThread(feed)
                    t.daemon = True
                    t.start()

            time.sleep(config['reload'] * 60)

# bleah
# https://stackoverflow.com/questions/26703502/threads-and-tkinter
def infinite_process():
    while True:
        with threading.Lock():
            entry = q.get()
            q.put(entry)

        # find a better way to do this.
        if "i'm a title" in entry.keys():
            root.title(html.unescape(entry["i'm a title"]))
            root.update()
            continue

        # use dictionary syntax so error messages are easily created
        labelvar.set(re.sub('<[^<>]+?>', '', entry['title']))

        global currentURL
        currentURL = entry['link']

        if growright:
            # not my favorite approach but i don't yet know how to grow
            # a frame to the left.
            ex = root.winfo_screenwidth() - root.winfo_width()
            why = root.winfo_screenheight() - root.winfo_height()
            # notsure = root.wm_geometry().split('+') 23 works for
            # OSX...
            root.geometry('+%d+%d' % (ex, why-23))

        root.update()

        break

    # it appears this doesn't increase the stack size...
    root.after(config['delay'] * 1000, infinite_process)

initialize(root, label, labelvar)
config = readconfig(label)

t = Reload()
t.daemon = True
t.start()

root.after(1, infinite_process)
root.mainloop()

# https://stackoverflow.com/questions/47127585/tkinter-grow-frame-to-fit-content

# 4360 rewrite
# FCAR decision/rewrite
# agenda and decisions made documents
