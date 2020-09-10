from tkinter import ttk
import tkinter
import webbrowser
import queue
import threading
import feedparser
# import pprint
import yaml
from tkfontchooser import askfont

# https://programmingideaswithjake.wordpress.com/2016/05/07/object-literals-in-python/
class Object:
   def __init__(self, **attributes):
      self.__dict__.update(attributes)

delay = 10000
growright = False
currentURL = ''
q = queue.SimpleQueue()

feeds = ['noworky', 'https://portswigger.net/daily-swig/rss', \
    'http://feeds.denverpost.com/dp-news-breaking', \
    'https://www.nws.noaa.gov/data/current_obs/KDEN.rss', \
    'http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/world/rss.xml', \
    'http://rss.cnn.com/rss/cnn_topstories.rss', \
    'http://www.us-cert.gov/channels/cas.rdf']

config = {'feeds': feeds}

def openbrowser(event):
    webbrowser.open(currentURL)

root = tkinter.Tk()
# root.title('DRSST')
labelvar = tkinter.StringVar()
# labelvar.set('Initializing')

label = ttk.Label(root, textvariable=labelvar)
ttk.Style().configure("TLabel", padding=4)
label.bind("<Button-1>", openbrowser)
label.pack()
# pprint.pprint(label.config())

# import urllib.request
# import base64
# url = 'https://portswigger.net/daily-swig/rss/icon'
# raw_data = urllib.request.urlopen(url).read()
# im = Image.open(io.BytesIO(raw_data))
# img = ImageTk.PhotoImage(im)
# label = ttk.Label(root, image=img, textvariable=labelvar)

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

menubar = tkinter.Menu(root)
settings = tkinter.Menu(menubar, tearoff=0)
settings.add_command(label="Font", command=setfont)
menubar.add_cascade(label="Settings", menu=settings)
root.config(menu=menubar)

class FetchThread(threading.Thread):
    def __init__(self, URL):
        super().__init__()
        self.URL = URL

    def run(self):
        f = feedparser.parse(self.URL)
        if not f.feed:
            f.feed.title = 'Error'
            # this is a hack so i don't have to create objects
            f.entries = [{'title':('Unable to load %s') % self.URL, \
                'link':'http://www.example.com'}]

        # get everything in safely so there's no interleaving
        with threading.Lock():
            q.put({"i'm a title":f.feed.title})
            for entry in f.entries:
                q.put(entry)

def reload():
    global q
    with threading.Lock():
        q = queue.SimpleQueue()
        # for feed in feeds:
        for feed in config['feeds']:
            FetchThread(feed).start()

    t = threading.Timer(30 * 60, reload)
    t.daemon = True
    t.start()

# bleah
# https://stackoverflow.com/questions/26703502/threads-and-tkinter
def infinite_process():
    global currentURL
    global q

    while True:
        with threading.Lock():
            entry = q.get()
            q.put(entry)

        # find a better way to do this.
        if "i'm a title" in entry.keys():
            root.title(entry["i'm a title"])
            root.update()
            continue

        # use dictionary syntax so error messages are easily created
        labelvar.set(entry['title'])
        # apparently need this if window moved.
        root.update()
        currentURL = entry['link']
        root.update()
        if growright:
            # not my favorite approach but i don't yet know how to grow
            # a frame to the left.
            ex = root.winfo_screenwidth() - root.winfo_width()
            why = root.winfo_screenheight() - root.winfo_height()
            # notsure = root.wm_geometry().split('+') 23 works for
            # OSX...
            root.geometry('+%d+%d' % (ex, why-23))

        break

    # it appears this doesn't increase the stack size...
    root.after(delay, infinite_process)

reload()
root.after(1, infinite_process)
root.mainloop()

# https://stackoverflow.com/questions/47127585/tkinter-grow-frame-to-fit-content

# 4360 rewrite
# FCAR decision/rewrite
# agenda and decisions made documents
