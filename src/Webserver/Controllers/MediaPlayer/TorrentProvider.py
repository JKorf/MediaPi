from __future__ import unicode_literals

from functools import wraps
from lxml import html
import re
import time

from urllib.request import urlopen
from urllib.request import Request

from Shared.Util import headers

unicode = str


def self_if_parameters(func):
    """
    If any parameter is given, the method's binded object is returned after
    executing the function. Else the function's result is returned.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if args or kwargs:
            return self
        else:
            return result
    return wrapper


class List(object):
    """
    Abstract class for parsing a torrent list at some url and generate torrent
    objects to iterate over. Includes a resource path parser.
    """

    _meta = re.compile('Uploaded (.*), Size (.*), ULed by (.*)')
    base_path = ''

    def items(self):
        """
        Request URL and parse response. Yield a ``Torrent`` for every torrent
        on page.
        """

        request = Request(str(self.url), data=None, headers=headers)
        request = urlopen(request)

        document = html.parse(request)
        root = document.getroot()
        items = [self._build_torrent(row) for row in
                self._get_torrent_rows(root)]
        for item in [x for x in items if x is not None]:
            yield item

    def __iter__(self):
        return self.items()

    def _get_torrent_rows(self, page):
        """
        Returns all 'tr' tag rows as a list of tuples. Each tuple is for
        a single torrent.
        """
        content = page.find('.//div[@id="content"]')
        table = content.find('.//table[@id="searchResult"]')  # the table with all torrent listing
        if table is None:  # no table means no results:
            return []
        else:
            return table.findall('.//tr')[1:]  # get all rows but header

    def _build_torrent(self, row):
        """
        Builds and returns a Torrent object for the given parsed row.
        """
        # Scrape, strip and build!!!
        cols = row.findall('.//td') # split the row into it's columns

        # this column contains the categories
        cat = [c.text for c in cols[0].findall('.//a')]
        if len(cat) < 2:
            category = ""
            sub_category = ""
        else:
            [category, sub_category] = cat

        # this column with all important info
        links = cols[1].findall('.//a') # get 4 a tags from this columns
        title = unicode(links[0].text)
        url = self.url.build().path(links[0].get('href'))
        magnet_link = links[1].get('href') # the magnet download link
        try:
            torrent_link = links[2].get('href') # the torrent download link
            if not torrent_link.endswith('.torrent'):
                torrent_link = None
        except IndexError:
            torrent_link = None

        meta_col = cols[1].find('.//font').text_content() # don't need user
        created = None
        size = None
        user = None
        match = self._meta.match(meta_col)
        if match:
            created = match.groups()[0].replace('\xa0', ' ')
            size = match.groups()[1].replace('\xa0', ' ')
            user = match.groups()[2]  # uploaded by user

        # last 2 columns for seeders and leechers
        if cols[2].text is not None:
            seeders = int(cols[2].text)
            leechers = int(cols[3].text)
        else:
            seeders = 0
            leechers = 0

        t = Torrent(title, url, category, sub_category, magnet_link,
                    torrent_link, created, size, user, seeders, leechers)
        return t


class Paginated(List):
    """
    Abstract class on top of ``List`` for parsing a torrent list with
    pagination capabilities.
    """
    def __init__(self, *args, **kwargs):
        super(Paginated, self).__init__(*args, **kwargs)
        self._multipage = False

    def items(self):
        """
        Request URL and parse response. Yield a ``Torrent`` for every torrent
        on page. If in multipage mode, Torrents from next pages are
        automatically chained.
        """
        if self._multipage:
            while True:
                # Pool for more torrents
                items = super(Paginated, self).items()
                # Stop if no more torrents
                first = next(items, None)
                if first is None:
                    raise StopIteration()
                # Yield them if not
                else:
                    yield first
                    for item in items:
                        yield item
                # Go to the next page
                self.next()
        else:
            for item in super(Paginated, self).items():
                yield item

    def multipage(self):
        """
        Enable multipage iteration.
        """
        self._multipage = True
        return self

    @self_if_parameters
    def page(self, number=None):
        """
        If page is given, modify the URL correspondingly, return the current
        page otherwise.
        """
        if number is None:
            return int(self.url.page)
        self.url.page = str(number)

    def next(self):
        """
        Jump to the next page.
        """
        self.page(self.page() + 1)
        return self

    def previous(self):
        """
        Jump to the previous page.
        """
        self.page(self.page() - 1)
        return self


class Search(Paginated):
    """
    Paginated search featuring query, category and order management.
    """
    base_path = '/search'

    def __init__(self, base_url, query, page='0', order='7', category='0'):
        super(Search, self).__init__()
        self.url = URL(base_url, self.base_path,
                        segments=['query', 'page', 'order', 'category'],
                        defaults=[query, str(page), str(order), str(category)],
                        )

    @self_if_parameters
    def query(self, query=None):
        """
        If query is given, modify the URL correspondingly, return the current
        query otherwise.
        """
        if query is None:
            return self.url.query
        self.url.query = query

    @self_if_parameters
    def order(self, order=None):
        """
        If order is given, modify the URL correspondingly, return the current
        order otherwise.
        """
        if order is None:
            return int(self.url.order)
        self.url.order = str(order)

    @self_if_parameters
    def category(self, category=None):
        """
        If category is given, modify the URL correspondingly, return the
        current category otherwise.
        """
        if category is None:
            return int(self.url.category)
        self.url.category = str(category)


class Recent(Paginated):
    """
    Paginated most recent torrents.
    """
    base_path = '/recent'

    def __init__(self, base_url, page='0'):
        super(Recent, self).__init__()
        self.url = URL(base_url, self.base_path,
                        segments=['page'],
                        defaults=[str(page)],
                        )


class Top(List):
    """
    Top torrents featuring category management.
    """
    base_path = '/top'

    def __init__(self, base_url, category='0'):
        self.url = URL(base_url, self.base_path,
                        segments=['category'],
                        defaults=[str(category)],
                        )

    @self_if_parameters
    def category(self, category=None):
        """
        If category is given, modify the URL correspondingly, return the
        current category otherwise.
        """
        if category is None:
            return int(self.url.category)
        self.url.category = str(category)


class TPB(object):
    """
    TPB API with searching, most recent torrents and top torrents support.
    Passes on base_url to the instantiated Search, Recent and Top classes.
    """

    def __init__(self, base_url):
        self.base_url = base_url

    def search(self, query, page=0, order=7, category=0, multipage=False):
        """
        Searches TPB for query and returns a list of paginated Torrents capable
        of changing query, categories and orders.
        """
        search = Search(self.base_url, query, page, order, category)
        if multipage:
            search.multipage()
        return search

    def recent(self, page=0):
        """
        Lists most recent Torrents added to TPB.
        """
        return Recent(self.base_url, page)

    def top(self, cat=0):
        """
        Lists top Torrents on TPB optionally filtering by category.
        """
        return Top(self.base_url, cat)


class Torrent(object):
    """
    Holder of a single TPB torrent.
    """

    def __init__(self, title, url, category, sub_category, magnet_link,
                 torrent_link, created, size, user, seeders, leechers):
        self.title = title # the title of the torrent
        self.url = url # TPB url for the torrent
        self.id = self.url.path_segments()[1]
        self.category = category # the main category
        self.sub_category = sub_category # the sub category
        self.torrent_link = torrent_link # .torrent download link
        self._created = (created, time.time()) # uploaded date, current time
        self.size = size # size of torrent
        self.user = user # username of uploader
        self.seeders = seeders # number of seeders
        self.leechers = leechers # number of leechers

    def __repr__(self):
        return '{0} by {1}'.format(self.title, self.user)

    @staticmethod
    def get_magnet_uri(url):
        request = Request(str(url), data=None, headers=headers)
        request = urlopen(request)
        document = html.parse(request)
        root = document.getroot()
        return root.xpath("//div[contains(@class, 'download')]")[0][0].get("href")



from collections import OrderedDict

from purl import URL as PURL


def URL(base, path, segments=None, defaults=None):
    """
    URL segment handler capable of getting and setting segments by name. The
    URL is constructed by joining base, path and segments.
    For each segment a property capable of getting and setting that segment is
    created dynamically.
    """
    # Make a copy of the Segments class
    url_class = type(Segments.__name__, Segments.__bases__,
                     dict(Segments.__dict__))
    segments = [] if segments is None else segments
    defaults = [] if defaults is None else defaults
    # For each segment attach a property capable of getting and setting it
    for segment in segments:
        setattr(url_class, segment, url_class._segment(segment))
    # Instantiate the class with the actual parameters
    return url_class(base, path, segments, defaults)


class Segments(object):

    """
    URL segment handler, not intended for direct use. The URL is constructed by
    joining base, path and segments.
    """

    def __init__(self, base, path, segments, defaults):
        # Preserve the base URL
        self.base = PURL(base, path=path)
        # Map the segments and defaults lists to an ordered dict
        self.segments = OrderedDict(zip(segments, defaults))

    def build(self):
        # Join base segments and segments
        segments = self.base.path_segments() + tuple(self.segments.values())
        # Create a new URL with the segments replaced
        url = self.base.path_segments(segments)
        return url

    def __str__(self):
        return self.build().as_string()

    def _get_segment(self, segment):
        return self.segments[segment]

    def _set_segment(self, segment, value):
        self.segments[segment] = value

    @classmethod
    def _segment(cls, segment):
        """
        Returns a property capable of setting and getting a segment.
        """
        return property(
            fget=lambda x: cls._get_segment(x, segment),
            fset=lambda x, v: cls._set_segment(x, segment, v),
        )


class_type = type


class ConstantType(type):

    """
    Tree representation metaclass for class attributes. Metaclass is extended
    to all child classes too.
    """
    def __new__(cls, clsname, bases, dct):
        """
        Extend metaclass to all class attributes too.
        """
        attrs = {}
        for name, attr in dct.items():
            if isinstance(attr, class_type):
                # substitute attr with a new class with Constants as
                # metaclass making it possible to spread this same method
                # to all child classes
                attr = ConstantType(
                    attr.__name__, attr.__bases__, attr.__dict__)
            attrs[name] = attr
        return super(ConstantType, cls).__new__(cls, clsname, bases, attrs)

    def __repr__(cls):
        """
        Tree representation of class attributes. Child classes are also
        represented.
        """
        # dump current class name
        tree = cls.__name__ + ':\n'
        for name in dir(cls):
            if not name.startswith('_'):
                attr = getattr(cls, name)
                output = repr(attr)
                if not isinstance(attr, ConstantType):
                    output = '{}: {}'.format(name, output)
                # indent all child attrs
                tree += '\n'.join([' ' * 4 + line
                                  for line in output.splitlines()]) + '\n'
        return tree

    def __str__(cls):
        return repr(cls)


Constants = ConstantType('Constants', (object,), {})


class ORDERS(Constants):

    class NAME:
        DES = 1
        ASC = 2

    class UPLOADED:
        DES = 3
        ASC = 4

    class SIZE:
        DES = 5
        ASC = 6

    class SEEDERS:
        DES = 7
        ASC = 8

    class LEECHERS:
        DES = 9
        ASC = 10

    class UPLOADER:
        DES = 11
        ASC = 12

    class TYPE:
        DES = 13
        ASC = 14


class CATEGORIES(Constants):
    ALL = 0

    class AUDIO:
        ALL = 100
        MUSIC = 101
        AUDIO_BOOKS = 102
        SOUND_CLIPS = 103
        FLAC = 104
        OTHER = 199

    class VIDEO:
        ALL = 200
        MOVIES = 201
        MOVIES_DVDR = 202
        MUSIC_VIDEOS = 203
        MOVIE_CLIPS = 204
        TV_SHOWS = 205
        HANDHELD = 206
        HD_MOVIES = 207
        HD_TV_SHOWS = 208
        THREE_DIMENSIONS = 209
        OTHER = 299

    class APPLICATIONS:
        ALL = 300
        WINDOWS = 301
        MAC = 302
        UNIX = 303
        HANDHELD = 304
        IOS = 305
        ANDROID = 306
        OTHER = 399

    class GAMES:
        ALL = 400
        PC = 401
        MAC = 402
        PSX = 403
        XBOX360 = 404
        WII = 405
        HANDHELD = 406
        IOS = 407
        ANDROID = 408
        OTHER = 499

    class PORN:
        ALL = 500
        MOVIES = 501
        MOVIES_DVDR = 502
        PICTURES = 503
        GAMES = 504
        HD_MOVIES = 505
        MOVIE_CLIPS = 506
        OTHER = 599

    class OTHER:
        EBOOKS = 601
        COMICS = 602
        PICTURES = 603
        COVERS = 604
        PHYSIBLES = 605
        OTHER = 699