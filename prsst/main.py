''' A simple RSS/ATOM ticker. '''
import argparse
import tkinter
import time
import webbrowser
import queue
import threading
import html
import re
from pathlib import Path
import feedparser
import yaml
from tkfontchooser import askfont


CURRENT_URL = ''
GLOBAL_QUEUE = None

ROOT = tkinter.Tk()
# https://stackoverflow.com/a/15463496
DEFAULT_FONT = tkinter.font.nametofont("TkDefaultFont")
ROOT.option_add("*Font", DEFAULT_FONT)

LABELVAR = tkinter.StringVar()
LABEL = tkinter.ttk.Label(ROOT, textvariable=LABELVAR)

CONFIG = {}

TITLE_KEY = "i'm a title"

PARSER = argparse.ArgumentParser()
PARSER.add_argument('-f', '--feed', help="specify feed directly", action='append')
PARSER.add_argument('-y', '--yaml', help="specify YAML file", action='append')
ARGS = PARSER.parse_args()

# make into a lambda
def openbrowser(event):
    """ Look at global (bleah) and open browser. """
    webbrowser.open(CURRENT_URL)

def initialize():
    """ Get everything the way it needs to be. Not sure how much should be
    here and how much above. """
    ROOT.title('PRSST')
    LABELVAR.set('Initializing')

    tkinter.ttk.Style().configure("TLabel", padding=4)
    LABEL.bind("<Button-1>", openbrowser)
    LABEL.pack()

    menubar = tkinter.Menu(ROOT)
    settings = tkinter.Menu(menubar, tearoff=0)
    settings.add_command(label="Font", command=set_font)
    menubar.add_cascade(label="Settings", menu=settings)
    ROOT.config(menu=menubar)

def set_font_info(info):
    """ Yeah, what it says. """
    font_info = info.split()
    DEFAULT_FONT.configure(family=font_info[0])
    DEFAULT_FONT.configure(size=font_info[1])
    DEFAULT_FONT.configure(weight=font_info[2])
    DEFAULT_FONT.configure(slant=font_info[3])

def set_defaults():
    """ Yeah, what it says. """
    if 'font' in CONFIG:
        LABEL.configure(font=CONFIG['font'])
        set_font_info(CONFIG['font'])
    if 'feeds' not in CONFIG:
        CONFIG['feeds'] = ['https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss']
    if 'growright' not in CONFIG:
        CONFIG['growright'] = False
    if 'delay' not in CONFIG:
        CONFIG['delay'] = 10
    if 'reload' not in CONFIG:
        CONFIG['reload'] = 120

def read_config():
    """ Yeah, what it says. """
    if ARGS.feed:
        CONFIG['feeds'] = ARGS.feed

    if ARGS.yaml:
        for ayaml in ARGS.yaml:
            with Path(ayaml).open() as afile:
                CONFIG.update(yaml.safe_load(afile))

    if ARGS.feed is None and ARGS.yaml is None:
        with Path(str(Path.home()) + '/.prsst.yml').open() as afile:
            CONFIG.update(yaml.safe_load(afile))

    set_defaults()

def set_font():
    """ Called via the menu. """
    font = askfont(ROOT)
    if font:
        font['family'] = font['family'].replace(' ', '\ ')
        font_str = "%(family)s %(size)i %(weight)s %(slant)s" % font
        if font['underline']:
            font_str += ' underline'
        if font['overstrike']:
            font_str += ' overstrike'
        LABEL.configure(font=font_str)
        CONFIG['font'] = font_str
        set_font_info(font_str)

        with open('prsst.yml', 'w') as afile:
            yaml.dump(CONFIG, afile)

# https://programmingideaswithjake.wordpress.com/2016/05/07/object-literals-in-python/
class Object:
    def __init__(self, **attributes):
        self.__dict__.update(attributes)

class FetchThread(threading.Thread):
    """ A thread to fetch a URL. """
    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        """ Read the URL passed in. """
        afeed = feedparser.parse(self.url)
        try:
            afeed.feed
            afeed.feed.title
        except:
            print('error fetching feed', self.url)
            afeed.feed.title = 'Error'
            # this is a hack so i don't have to create objects
            afeed.entries = [{'title':('Unable to load %s') % self.url, \
                'link':'https://www.example.com'}]

        # get everything in safely so there's no interleaving
        with threading.Lock():
            GLOBAL_QUEUE.put({TITLE_KEY:afeed.feed.title})
            for entry in afeed.entries:
                GLOBAL_QUEUE.put(entry)

class Reload(threading.Thread):
    """ One thread to call a FetchThread for each URL. """
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            global GLOBAL_QUEUE

            # the second and subsequent times
            if GLOBAL_QUEUE is not None:
                CONFIG['reload'] = (CONFIG['delay'] * GLOBAL_QUEUE.qsize() / 60) + 2

            with threading.Lock():
                GLOBAL_QUEUE = queue.SimpleQueue()
                for feed in CONFIG['feeds']:
                    fetch_thread = FetchThread(feed)
                    fetch_thread.daemon = True
                    fetch_thread.start()

            time.sleep(CONFIG['reload'] * 60)

# bleah
# https://stackoverflow.com/questions/26703502/threads-and-tkinter
def infinite_process():
    """ Recursive to loop, but it doesn't seem to grow the stack. """
    while True:
        with threading.Lock():
            entry = GLOBAL_QUEUE.get()
            GLOBAL_QUEUE.put(entry)

        # find a better way to do this.
        if TITLE_KEY in entry.keys():
            ROOT.title(html.unescape(entry[TITLE_KEY]))
            ROOT.update()
            continue

        # use dictionary syntax so error messages are easily created
        text = re.sub(r'<[^<>]+?>', r'', entry['title'])
        text = html.unescape(text)
        LABELVAR.set(text)

        global CURRENT_URL
        CURRENT_URL = entry['link']

# https://stackoverflow.com/questions/47127585/tkinter-grow-frame-to-fit-content
        if CONFIG['growright']:
            # not my favorite approach but i don't yet know how to grow
            # a frame to the left.
            ex = ROOT.winfo_screenwidth() - ROOT.winfo_width()
            why = ROOT.winfo_screenheight() - ROOT.winfo_height()
            # notsure = ROOT.wm_geometry().split('+') 23 works for
            # OSX...
            ROOT.geometry('+%d+%d' % (ex, why-23))

        ROOT.update()

        break

    # it appears this doesn't increase the stack size...
    ROOT.after(CONFIG['delay'] * 1000, infinite_process)

initialize()
read_config()

MAINTHREAD = Reload()
MAINTHREAD.daemon = True
MAINTHREAD.start()

ROOT.after(1, infinite_process)
ROOT.mainloop()

# vim: wm=0
