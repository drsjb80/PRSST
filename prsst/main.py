from tkinter import ttk
import tkinter
import webbrowser
import queue
import threading
import feedparser

delay = 10000
growright = False
currentURL = ''
q = queue.SimpleQueue()

root = tkinter.Tk()
root.title('DRSST')
labelvar = tkinter.StringVar()
labelvar.set('Initializing')

# import urllib.request
# import base64
# url = 'https://portswigger.net/daily-swig/rss/icon'
# raw_data = urllib.request.urlopen(url).read()
# im = Image.open(io.BytesIO(raw_data))
# img = ImageTk.PhotoImage(im)
# label = ttk.Label(root, image=img, textvariable=labelvar)

def openbrowser(event):
    webbrowser.open(currentURL)

label = ttk.Label(root, textvariable=labelvar)
label.bind("<Button-1>", openbrowser)
label.pack()

class FetchThread(threading.Thread):
    def __init__(self, URL):
        super().__init__()
        self.URL = URL

    def run(self):
        print('fetching', self.URL)
        f = feedparser.parse(self.URL)
        print('done fetching', self.URL)

        # get everything in safely
        with threading.Lock():
            print("i'm a title", f.feed.title)
            q.put({"i'm a title":f.feed.title})
            for entry in f.entries:
                q.put(entry)

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

        labelvar.set(entry.title)
        currentURL = entry.link
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

feeds = ['https://portswigger.net/daily-swig/rss', \
    'http://feeds.denverpost.com/dp-news-breaking', \
    'https://www.nws.noaa.gov/data/current_obs/KDEN.rss', \
    'http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/world/rss.xml', \
    'http://rss.cnn.com/rss/cnn_topstories.rss', \
    'http://www.us-cert.gov/channels/cas.rdf']

for feed in feeds:
    FetchThread(feed).start()

root.after(1, infinite_process)
root.mainloop()

# https://stackoverflow.com/questions/47127585/tkinter-grow-frame-to-fit-content