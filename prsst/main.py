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

# https://programmingideaswithjake.wordpress.com/2016/05/07/object-literals-in-python/
class Object:
    def __init__(self, **attributes):
        self.__dict__.update(attributes)

currentURL = ''
global_queue = None

root = tkinter.Tk()
# https://stackoverflow.com/a/15463496
default_font = tkinter.font.nametofont("TkDefaultFont")
root.option_add("*Font", default_font)

labelvar = tkinter.StringVar()
label = tkinter.ttk.Label(root, textvariable=labelvar)

growright = False
config = {}

TITLE_KEY = "i'm a title"

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--feed', help="specify feed directly", \
    action='append')
parser.add_argument('-y', '--yaml', help="specify YAML file", \
    action='append')
args = parser.parse_args()

# make into a lambda
def openbrowser(event):
    webbrowser.open(currentURL)

def initialize():
    root.title('PRSST')
    labelvar.set('Initializing')

    tkinter.ttk.Style().configure("TLabel", padding=4)
    label.bind("<Button-1>", openbrowser)
    label.pack()

    menubar = tkinter.Menu(root)
    settings = tkinter.Menu(menubar, tearoff=0)
    settings.add_command(label="Font", command=setfont)
    menubar.add_cascade(label="Settings", menu=settings)
    root.config(menu=menubar)

def setdefaults():
    if 'font' in config:
        label.configure(font=config['font'])
        size = config['font'].split()
        default_font.configure(size=size[1])
    if 'feeds' not in config:
        config['feeds'] = ['http://feeds.rssboard.org/rssboard']
    if 'growright' not in config:
        config['growright'] = False
    if 'delay' not in config:
        config['delay'] = 10
    if 'reload' not in config:
        config['reload'] = 120

def readconfig():
    if args.feed:
        config['feeds'] = args.feed

    if args.yaml:
        for ayaml in args.yaml:
            with Path(ayaml).open() as afile:
                config.update(yaml.safe_load(afile))

    if args.feed is None and args.yaml is None:
        with Path(str(Path.home()) + '/.prsst.yml').open() as afile:
            config.update(yaml.safe_load(afile))

    setdefaults()
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

        default_font.configure(family=font_str.split()[0])
        default_font.configure(size=font_str.split()[1])
        default_font.configure(weight=font_str.split()[2])
        default_font.configure(slant=font_str.split()[3])

        with open('prsst.yml', 'w') as afile:
            yaml.dump(config, afile)

class FetchThread(threading.Thread):
    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
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
            global_queue.put({TITLE_KEY:afeed.feed.title})
            for entry in afeed.entries:
                global_queue.put(entry)

class Reload(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            global global_queue

            # the second and subsequent times
            if global_queue is not None:
                config['reload'] = (config['delay'] * global_queue.qsize() / 60) + 2

            with threading.Lock():
                global_queue = queue.SimpleQueue()
                for feed in config['feeds']:
                    fetch_thread = FetchThread(feed)
                    fetch_thread.daemon = True
                    fetch_thread.start()

            time.sleep(config['reload'] * 60)

# bleah
# https://stackoverflow.com/questions/26703502/threads-and-tkinter
def infinite_process():
    while True:
        with threading.Lock():
            entry = global_queue.get()
            global_queue.put(entry)

        # find a better way to do this.
        if TITLE_KEY in entry.keys():
            root.title(html.unescape(entry[TITLE_KEY]))
            root.update()
            continue

        # use dictionary syntax so error messages are easily created
        text = re.sub(r'<[^<>]+?>', r'', entry['title'])
        text = html.unescape(text)
        labelvar.set(text)

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

initialize()
readconfig()

mainThread = Reload()
mainThread.daemon = True
mainThread.start()

root.after(1, infinite_process)
root.mainloop()

# https://stackoverflow.com/questions/47127585/tkinter-grow-frame-to-fit-content
