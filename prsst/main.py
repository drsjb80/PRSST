''' A simple RSS/ATOM ticker. '''
import encodings.idna
import argparse
import tkinter
import time
import webbrowser
import queue
import threading
import html
import re
from pathlib import Path
import logging
import feedparser
import yaml
import sys
from tkfontchooser import askfont

# logging.basicConfig(level=logging.DEBUG)
current_url = ''
global_queue = None
config = {}
args = None

root = tkinter.Tk()
root.overrideredirect(True)

# https://stackoverflow.com/a/15463496
root.option_add("*Font", tkinter.font.nametofont("TkDefaultFont"))

labelvar = tkinter.StringVar()
label = tkinter.ttk.Label(root, textvariable=labelvar)

title_key = "i'm a title"

# make into a lambda
def openbrowser(event):
    """ Look at global (bleah) and open browser. """
    webbrowser.open(current_url)

def initialize():
    """ Get everything the way it needs to be. Not sure how much should be
    here and how much above. """
    root.title('PRSST')
    labelvar.set('Initializing')

    tkinter.ttk.Style().configure("TLabel", padding=4)
    label.bind("<Button-1>", openbrowser)
    label.pack()

    menubar = tkinter.Menu(root)
    settings = tkinter.Menu(menubar, tearoff=0)
    settings.add_command(label="Font", command=set_font)
    menubar.add_cascade(label="Settings", menu=settings)
    root.config(menu=menubar)

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--feed', help="specify feed directly", action='append')
    parser.add_argument('-y', '--yaml', help="specify YAML file", action='append')

    global args
    args = parser.parse_args()

def set_defaults():
    """ Yeah, what it says. """

    if 'font-family' in config:
        font_str = config['font-family'] + " " \
            + str(config['font-size']) + " " \
            + config['font-weight'] + " " \
            + config['font-slant']
        label.configure(font=font_str)
        default_font.configure(family=config['font-family'])
    if 'font-size' in config:
        default_font.configure(size=config['font-size'])
    if 'font-weight' in config:
        default_font.configure(weight=config['font-weight'])
    if 'font-slant' in config:
        default_font.configure(slant=config['font-slant'])

    if 'feeds' not in config:
        config['feeds'] = ['https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss']
    if 'growright' not in config:
        config['growright'] = False
    if 'delay' not in config:
        config['delay'] = 10
    if 'reload' not in config:
        config['reload'] = 120

def read_config():
    """ Yeah, what it says. """
    if args.feed:
        config['feeds'] = args.feed

    if args.yaml:
        for ayaml in args.yaml:
            with Path(ayaml).open() as afile:
                config.update(yaml.safe_load(afile))

    if args.feed is None and args.yaml is None:
        with Path(str(Path.home()) + '/.prsst.yml').open() as afile:
            config.update(yaml.safe_load(afile))

    set_defaults()

def save_config():
    home_yml = Path(str(Path.home()) + '/.prsst.yml')
    if home_yml.exists() and home_yml.is_file():
        with open(str(home_yml), 'w') as afile:
            yaml.dump(config, afile)
    else:
        with open('prsst.yml', 'w') as afile:
            yaml.dump(config, afile)

def set_font():
    """ Called via the menu. """
    font = askfont(root)
    if font:
        font_family = font['family']
        font['family'] = font['family'].replace(' ', '\\ ')
        font_str = "%(family)s %(size)i %(weight)s %(slant)s" % font
        if font['underline']:
            font_str += ' underline'
        if font['overstrike']:
            font_str += ' overstrike'
        label.configure(font=font_str)

        # overstrike and underline?
        default_font.configure(family=font_family)
        default_font.configure(size=font['size'])
        default_font.configure(weight=font['weight'])
        default_font.configure(slant=font['slant'])

        config['font-family'] = font_family
        config['font-size'] = font['size']
        config['font-weight'] = font['weight']
        config['font-slant'] = font['slant']

        save_config()

class FetchThread(threading.Thread):
    """ A thread to fetch a URL. """
    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        """ Read the URL passed in. """
        afeed = None
        try:
            afeed = feedparser.parse(self.url)
            afeed.feed
            afeed.feed.title
        except:
            logging.error(f'error fetching feed {self.url}')
            return

        global_queue.put({title_key:afeed.feed.title})
        for entry in afeed.entries:
            global_queue.put(entry)

class Reload(threading.Thread):
    """ One thread to call a FetchThread for each URL. """
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            global global_queue

            # the second and subsequent times
            if global_queue is not None:
                config['reload'] = (config['delay'] * global_queue.qsize() / 60) + 2
                logging.debug(global_queue.qsize())
                logging.debug(config['reload'])

            global_queue = queue.SimpleQueue()
            for feed in config['feeds']:
                fetch_thread = FetchThread(feed)
                fetch_thread.daemon = True
                fetch_thread.start()

            time.sleep(config['reload'] * 60)

# bleah
# https://stackoverflow.com/questions/26703502/threads-and-tkinter
def infinite_process():
    """ Recursive to loop, but it doesn't seem to grow the stack, see tail recursion. """
    while True:
        entry = global_queue.get()
        global_queue.put(entry)

        # find a better way to do this.
        if title_key in entry.keys():
            root.title(html.unescape(entry[title_key]))
            root.update()
            continue

        # use dictionary syntax so error messages are easily created
        text = re.sub(r'<[^<>]+?>', r'', entry['title'])
        text = html.unescape(text)
        labelvar.set(text)

        global current_url
        current_url = entry['link']

# https://stackoverflow.com/questions/47127585/tkinter-grow-frame-to-fit-content
        if config['growright']:
            # not my favorite approach but i don't yet know how to grow
            # a frame to the left.
            ex = root.winfo_screenwidth() - root.winfo_width()
            why = root.winfo_screenheight() - root.winfo_height()
            # notsure = root.wm_geometry().split('+') 23 works for
            # OSX...
            root.geometry('+%d+%d' % (ex, why-23))

        root.update()
        break

    root.after(config['delay'] * 1000, infinite_process)

def popup(one):
    print(one)
    print('popup')

initialize()
read_config()

# https://stackoverflow.com/questions/16082243/how-to-bind-ctrl-in-python-tkinter
# https://www.tcl-lang.org/man/tcl8.6/TkCmd/keysyms.htm
if sys.platform == 'darwin':
    root.bind("<Control-1>", lambda one: print('popup'))

root.bind("<Button-3>", lambda one: print('popup'))
# root.bind("<Button-3>", popup)

# retrieve the initial list
mainthread = Reload()
mainthread.daemon = True
mainthread.start()

root.after(1, infinite_process)
root.mainloop()

# vim: wm=0
