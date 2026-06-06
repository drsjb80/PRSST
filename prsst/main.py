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

CURRENT_URL = ''
GLOBAL_QUEUE = None
config = {}
ARGS = None
DEFAULT_FONT = None

root = tkinter.Tk()
root.overrideredirect(True)

root.option_add("*Font", tkinter.font.nametofont("TkDefaultFont"))

labelvar = tkinter.StringVar()
label = tkinter.ttk.Label(root, textvariable=labelvar)

TITLE_KEY = "i'm a title"


def openbrowser(_event):
    """Open the current URL in the default web browser."""
    webbrowser.open(CURRENT_URL)


def initialize():
    """Initialize the GUI window and parse command-line arguments."""
    global ARGS  # pylint: disable=global-statement
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

    ARGS = parser.parse_args()


def validate_config():
    """Validate the loaded configuration for required and valid values."""
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
    """Set default configuration values and apply font settings."""
    global DEFAULT_FONT  # pylint: disable=global-statement
    DEFAULT_FONT = tkinter.font.Font(name="TkDefaultFont", exists=True)

    if 'font-family' in config:
        font_str = config['font-family'] + " " \
            + str(config['font-size']) + " " \
            + config['font-weight'] + " " \
            + config['font-slant']
        label.configure(font=font_str)
        DEFAULT_FONT.configure(family=config['font-family'])
    if 'font-size' in config:
        DEFAULT_FONT.configure(size=config['font-size'])
    if 'font-weight' in config:
        DEFAULT_FONT.configure(weight=config['font-weight'])
    if 'font-slant' in config:
        DEFAULT_FONT.configure(slant=config['font-slant'])

    if 'feeds' not in config:
        config['feeds'] = ['https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss']
    if 'growright' not in config:
        config['growright'] = False
    if 'delay' not in config:
        config['delay'] = 10
    if 'reload' not in config:
        config['reload'] = 120


def read_config():
    """Load configuration from YAML files or command-line arguments."""
    if ARGS.feed:
        config['feeds'] = ARGS.feed

    if ARGS.yaml:
        for ayaml in ARGS.yaml:
            yaml_path = Path(ayaml)
            if not yaml_path.exists():
                logging.error("YAML file not found: %s", ayaml)
                sys.exit(1)
            try:
                with yaml_path.open(encoding='utf-8') as afile:
                    config.update(yaml.safe_load(afile))
            except yaml.YAMLError as e:
                logging.error("Invalid YAML in %s: %s", ayaml, e)
                sys.exit(1)

    if ARGS.feed is None and ARGS.yaml is None:
        home_yml = Path.home() / '.prsst.yml'
        if not home_yml.exists():
            logging.error("No configuration found. Please create %s or use -f/--feed", home_yml)
            sys.exit(1)
        try:
            with home_yml.open(encoding='utf-8') as afile:
                config.update(yaml.safe_load(afile))
        except yaml.YAMLError as e:
            logging.error("Invalid YAML in %s: %s", home_yml, e)
            sys.exit(1)

    set_defaults()

    if not validate_config():
        sys.exit(1)


def save_config():
    """Save the current configuration to a YAML file."""
    home_yml = Path.home() / '.prsst.yml'
    if home_yml.exists() and home_yml.is_file():
        with home_yml.open('w', encoding='utf-8') as afile:
            yaml.dump(config, afile)
    else:
        with Path('prsst.yml').open('w', encoding='utf-8') as afile:
            yaml.dump(config, afile)


def set_font():
    """Open font chooser dialog and update the label font."""
    font = askfont(root)
    if font:
        font_family = font['family']
        font['family'] = font['family'].replace(' ', '\\ ')
        font_str = f"{font['family']} {font['size']} {font['weight']} {font['slant']}"
        if font['underline']:
            font_str += ' underline'
        if font['overstrike']:
            font_str += ' overstrike'
        label.configure(font=font_str)

        DEFAULT_FONT.configure(family=font_family)
        DEFAULT_FONT.configure(size=font['size'])
        DEFAULT_FONT.configure(weight=font['weight'])
        DEFAULT_FONT.configure(slant=font['slant'])

        config['font-family'] = font_family
        config['font-size'] = font['size']
        config['font-weight'] = font['weight']
        config['font-slant'] = font['slant']

        save_config()


class FetchThread(threading.Thread):
    """Thread for fetching RSS/Atom feeds."""

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        """Fetch and parse the RSS/Atom feed."""
        afeed = None
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            afeed = feedparser.parse(BytesIO(response.content))
        except requests.exceptions.Timeout:
            logging.warning("Timeout fetching %s (10s)", self.url)
            time.sleep(config['reload'] * 60)
            return
        except requests.exceptions.HTTPError as e:
            logging.warning("HTTP error fetching %s: %s", self.url, e.response.status_code)
            time.sleep(config['reload'] * 60)
            return
        except requests.exceptions.RequestException as e:
            logging.warning("Network error fetching %s: %s", self.url, e)
            time.sleep(config['reload'] * 60)
            return
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Unexpected error fetching %s: %s", self.url, e)
            time.sleep(config['reload'] * 60)
            return

        try:
            feed_title = getattr(afeed.feed, 'title', 'Untitled Feed')
            GLOBAL_QUEUE.put({TITLE_KEY: feed_title})
            if not afeed.entries:
                logging.info("Feed %s has no entries", self.url)
                return
            for entry in afeed.entries:
                GLOBAL_QUEUE.put(entry)
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Error processing feed %s: %s", self.url, e)


class Reload(threading.Thread):
    """Thread for reloading feeds at regular intervals."""

    def __init__(self):
        super().__init__()

    def run(self):
        """Fetch feeds and update the queue."""
        global GLOBAL_QUEUE  # pylint: disable=global-statement

        while True:
            if GLOBAL_QUEUE is not None:
                config['reload'] = (config['delay'] * GLOBAL_QUEUE.qsize() / 60) + 2
                logging.debug(GLOBAL_QUEUE.qsize())
                logging.debug(config['reload'])

            GLOBAL_QUEUE = queue.SimpleQueue()
            for feed in config['feeds']:
                fetch_thread = FetchThread(feed)
                fetch_thread.daemon = True
                fetch_thread.start()

            time.sleep(config['reload'] * 60)


def infinite_process():
    """Process the next entry from the queue and update the display."""
    global CURRENT_URL  # pylint: disable=global-statement

    entry = GLOBAL_QUEUE.get()
    GLOBAL_QUEUE.put(entry)

    if TITLE_KEY in entry.keys():
        root.title(html.unescape(entry[TITLE_KEY]))
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

        CURRENT_URL = entry.get('link', '')

        if config['growright']:
            ex = root.winfo_screenwidth() - root.winfo_width()
            why = root.winfo_screenheight() - root.winfo_height()
            root.geometry(f'+{ex}+{why - 23}')

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
