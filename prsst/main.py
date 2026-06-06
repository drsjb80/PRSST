''' A simple RSS/ATOM ticker. '''
import argparse
import html
import logging
import queue
import re
import sys
import threading
import time
import tkinter
import webbrowser
from io import BytesIO
from pathlib import Path

import feedparser
import requests
import yaml
from tkfontchooser import askfont

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

current_url = ''
global_queue = None
config = {}
args = None
default_font = None

root = tkinter.Tk()
root.overrideredirect(True)

root.option_add("*Font", tkinter.font.nametofont("TkDefaultFont"))

labelvar = tkinter.StringVar()
label = tkinter.ttk.Label(root, textvariable=labelvar)

title_key = "i'm a title"


def openbrowser(event):
    webbrowser.open(current_url)


def initialize():
    root.title('PRSST')
    labelvar.set('Initializing')

    tkinter.ttk.Style().configure("TLabel", padding=4)
    label.bind("<Button-1>", openbrowser)
    label.pack()

    menubar = tkinter.Menu(root)
    settings = tkinter.Menu(menubar, tearoff=0)
    settings.add_command(label="Font", command=set_font)
    menubar.add_cascade(label="Settings", menu=settings)

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--feed', help="specify feed directly", action='append')
    parser.add_argument('-y', '--yaml', help="specify YAML file", action='append')

    global args
    args = parser.parse_args()


def validate_config():
    if 'feeds' not in config or not config['feeds']:
        logging.error("No feeds specified in configuration")
        return False
    if not isinstance(config['feeds'], list):
        logging.error("'feeds' must be a list")
        return False

    if 'delay' in config and (not isinstance(config['delay'], int) or config['delay'] <= 0):
        logging.error("'delay' must be a positive integer (milliseconds)")
        return False

    if 'reload' in config and (not isinstance(config['reload'], int) or config['reload'] <= 0):
        logging.error("'reload' must be a positive integer (seconds)")
        return False

    if 'growright' in config and not isinstance(config['growright'], bool):
        logging.error("'growright' must be a boolean (true/false)")
        return False

    return True


def set_defaults():
    global default_font
    default_font = tkinter.font.Font(name="TkDefaultFont", exists=True)

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
    if args.feed:
        config['feeds'] = args.feed

    if args.yaml:
        for ayaml in args.yaml:
            yaml_path = Path(ayaml)
            if not yaml_path.exists():
                logging.error(f"YAML file not found: {ayaml}")
                sys.exit(1)
            try:
                with yaml_path.open() as afile:
                    config.update(yaml.safe_load(afile))
            except yaml.YAMLError as e:
                logging.error(f"Invalid YAML in {ayaml}: {e}")
                sys.exit(1)

    if args.feed is None and args.yaml is None:
        home_yml = Path.home() / '.prsst.yml'
        if not home_yml.exists():
            logging.error(f"No configuration found. Please create {home_yml} or use -f/--feed")
            sys.exit(1)
        try:
            with home_yml.open() as afile:
                config.update(yaml.safe_load(afile))
        except yaml.YAMLError as e:
            logging.error(f"Invalid YAML in {home_yml}: {e}")
            sys.exit(1)

    set_defaults()

    if not validate_config():
        sys.exit(1)


def save_config():
    home_yml = Path.home() / '.prsst.yml'
    if home_yml.exists() and home_yml.is_file():
        with home_yml.open('w') as afile:
            yaml.dump(config, afile)
    else:
        with Path('prsst.yml').open('w') as afile:
            yaml.dump(config, afile)


def set_font():
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
    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        afeed = None
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            afeed = feedparser.parse(BytesIO(response.content))
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout fetching {self.url} (10s)")
            time.sleep(config['reload'] * 60)
            return
        except requests.exceptions.HTTPError as e:
            logging.warning(f"HTTP error fetching {self.url}: {e.response.status_code}")
            time.sleep(config['reload'] * 60)
            return
        except requests.exceptions.RequestException as e:
            logging.warning(f"Network error fetching {self.url}: {e}")
            time.sleep(config['reload'] * 60)
            return
        except Exception as e:
            logging.error(f"Unexpected error fetching {self.url}: {e}")
            time.sleep(config['reload'] * 60)
            return

        try:
            feed_title = getattr(afeed.feed, 'title', 'Untitled Feed')
            global_queue.put({title_key: feed_title})
            if not afeed.entries:
                logging.info(f"Feed {self.url} has no entries")
                return
            for entry in afeed.entries:
                global_queue.put(entry)
        except Exception as e:
            logging.error(f"Error processing feed {self.url}: {e}")


class Reload(threading.Thread):
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


def infinite_process():
    entry = global_queue.get()
    global_queue.put(entry)

    if title_key in entry.keys():
        root.title(html.unescape(entry[title_key]))
        root.update()
    else:
        text = None
        if 'title' in entry and entry['title']:
            text = re.sub(r'<[^<>]+?>', r'', entry['title'])
        elif 'description' in entry and entry['description']:
            text = entry['description']
            if len(text) > 60:
                text = text[:60] + '...'
        else:
            text = "(No title or description)"

        text = html.unescape(text)
        labelvar.set(text)

        global current_url
        current_url = entry.get('link', '')

        if config['growright']:
            ex = root.winfo_screenwidth() - root.winfo_width()
            why = root.winfo_screenheight() - root.winfo_height()
            root.geometry('+%d+%d' % (ex, why - 23))

        root.update()

    root.after(config['delay'] * 1000, infinite_process)


if '__main__' == __name__:
    initialize()
    read_config()

    mainthread = Reload()
    mainthread.daemon = True
    mainthread.start()

    root.after(1, infinite_process)
    root.mainloop()
