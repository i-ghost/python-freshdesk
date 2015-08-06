from dateutil.parser import parser as datetime_parser

class FreshdeskModel(object):
    """Base class for Fershdesk objects.
    Maps the JSON response from the web API to instance variables
    Convenience variables and methods are defined at a higher level"""
    _keys = set()

    def __init__(self, api, **kwargs):
        self._api = api
        for k, v in kwargs.items():
            # prevent clobbering with our properties below
            if hasattr(Topic, k):
                k = '_' + k
            if hasattr(Ticket, k):
                k = '_' + k
            setattr(self, k, v)
            self._keys.add(k)
        self.created_at = self._to_timestamp(self.created_at)
        self.updated_at = self._to_timestamp(self.updated_at)

    def _to_timestamp(self, timestamp_str):
        """Converts a timestamp string as returned by the API to
        a native datetime object and return it."""
        return datetime_parser(timestamp_str)

class Post(FreshdeskModel):
    """A Post object
    Interesting things:
    .body: Non-HTML
    .body_html: Escaped HTML
    .hits: View count"""
    def __str__(self):
        return self.body

    def __repr__(self):
        return '<Post for {}>'.format(repr(self.topic))

class Topic(FreshdeskModel):
    def __str__(self):
        return self.title

    def __repr__(self):
        return '<Topic \'{}\'>'.format(self.title)

    @property
    def sticky(self):
        """Is the topic stickied?"""
        return bool(self._sticky)

    @property
    def locked(self):
        """Is the topic locked?"""
        return bool(self._locked)

    @property
    def stamp_type(self):
        """What's the status of the topic?"""
        _s = {1: 'planned', 2:'implemented', 3: 'not taken', 4: 'in progress', 5: 'deferred', 6: 'answered', 7: 'unanswered', 8: 'solved', 9: 'unsolved'}
        return _s[self._stamp_type]

    @property
    def posts(self):
        """Returns a list of Post instances"""
        return [Post(api=self._api, topic=self, **p) for p in self._posts]

    def update(self, title, body_html, sticky=None, locked=None):
        """Update the topic body"""
        url = 'discussions/topics/%d.json' % self.id
        data = self._api._create_post("topic",
                                      title=title or self.title,
                                      body_html=body_html or self.posts[0].body_html,
                                      sticky=sticky or self.sticky,
                                      locked=locked or self.locked)
        return self._api._put(url, data)

class Ticket(FreshdeskModel):
    def __str__(self):
        return self.subject

    def __repr__(self):
        return '<Ticket \'{}\'>'.format(self.subject)

    @property
    def comments(self):
        return [Comment(ticket=self, **c['note']) for c in self.notes]

    @property
    def priority(self):
        _p = {1: 'low', 2: 'medium', 3: 'high', 4: 'urgent'}
        return _p[self._priority]

    @property
    def status(self):
        _s = {2: 'open', 3: 'pending', 4: 'resolved', 5: 'closed'}
        try:
            return _s[self._status]
        except KeyError:
            return 'status_{}'.format(self._status)

    @property
    def source(self):
        _s = {1: 'email', 2: 'portal', 3: 'phone', 4: 'forum', 5: 'twitter', 6: 'facebook', 7: 'chat'}
        return _s[self._source]

class Comment(FreshdeskModel):
    def __str__(self):
        return self.body

    def __repr__(self):
        return '<Comment for {}>'.format(repr(self.ticket))

class Contact(FreshdeskModel):
    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Contact \'{}\'>'.format(self.name)
