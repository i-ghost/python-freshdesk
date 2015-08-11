import json
import requests
from requests.exceptions import HTTPError

from freshdesk.models import *

class SolutionAPI(object):
    """Provides an interface to solutions on a Freshdesk instance"""
    def __init__(self, api):
        self._api = api

    # Categories
    def create_category(self, name, description):
        """Create and return a solution category"""
        url = 'solution/categories.json'
        data = self._api._create_post("solution_category", name=name, description=description)
        return self._api._post(url, data=data)

    def get_category(self, category_id):
        """Return a solution category for a given id"""
        url = 'solution/categories/%d.json' % category_id
        return SolutionCategory(self._api, **self._api._get(url)['category'])

    def list_categories(self):
        """Return a list of all solution categories"""
        url = 'solution/categories.json'
        return [self.get_solution_category(c['category'] for c in self._api._get(url))]

    # Folders

    def create_folder(self, category_id, name, visibility, description, customer_folder_attributes=[]):
        """Create and return a solution folder for a given category id
        :param int category_id: Category ID of the containing category
        :param str name: The name of the new folder
        :param int visibility: 1: All, 2: Logged in users, 3: Agents only, 4: Company Specific Users
        :param str description: A description of the new folder
        :param list[int: customer_id] customer_folder_attributes: A list of companies to which this folder is visible"""
        url = 'solution/categories/%d/folders.json' % category_id
        data = self._api._create_post("solution_folder", category_id=category_id, name=name, visibility=visibility, description=description, customer_folder_attributes=customer_folder_attributes)
        return SolutionFolder(self._api, **self._api._post(url, data)['folder'])

    # Articles

    def get_article(self, category_id, folder_id, solution_id):
        """Return a solution article for the given ids"""
        url = 'solution/categories/%d/folders/%d/articles/%d.json' % (category_id, folder_id, solution_id)
        return Solution(self._api, **self._api._get(url)['article'])

    def delete_article(self, category_id, folder_id, solution_id):
        """Delete a solution article for the given ids"""
        url = 'solution/categories/%d/folders/%d/articles/%d.json'
        return self._api._delete(url)

    def create_article(self, category_id, folder_id, title, status, art_type, description, tags=[]):
        """Creates a solution article in the given category and folder"""
        # TODO: implement tags
        url = '/solution/categories/%d/folders/%d/articles.json' % (category_id, folder_id)
        data = self._api._create_post("solution_article", folder_id=folder_id, title=title, status=status, art_type=art_type, description=description)
        return Solution(self._api, **self._api._post(url, data=data)['article'])

class TopicAPI(object):
    """Provides an interface to topics on a Freshdesk instance"""
    def __init__(self, api):
        self._api = api

    def get_topic(self, topic_id):
        """Returns a Topic instance for the given topic_id"""
        url = 'discussions/topics/%d.json' % topic_id
        return Topic(self._api, **self._api._get(url)['topic'])

    def delete_topic(self, topic_id):
        """Deletes a topic with the given topic_id, returns JSON response"""
        url = 'discussions/topics/%d.json' % topic_id
        return self._api.delete(url)

    def create_topic(self, forum_id, title, body_html, sticky=False, locked=False):
        """Create a new topic and return it as a new Topic instance"""
        url = 'discussions/topics.json'
        data = self._api._create_post("topic", forum_id=forum_id, title=title, locked=locked, body_html=body_html)
        return self._api._post(url, data=data)['topic']

class TicketAPI(object):
    """Provides an interface to tickets on a Freshdesk instance"""
    def __init__(self, api):
        self._api = api

    def get_ticket(self, ticket_id):
        """Fetches the ticket for the given ticket ID"""
        url = 'helpdesk/tickets/%d.json' % ticket_id
        return Ticket(self._api, **self._api._get(url)['helpdesk_ticket'])

    def list_tickets(self, **kwargs):
        """List all tickets, optionally filtered by a view. Specify filters as
        keyword arguments, such as:

        filter_name = one of ['all_tickets', 'new_my_open', 'spam', 'deleted']
            (defaults to 'all_tickets')

        Multiple filters are AND'd together.
        """

        filter_name = 'all_tickets'
        if 'filter_name' in kwargs:
            filter_name = kwargs['filter_name']
            del kwargs['filter_name']

        url = 'helpdesk/tickets/filter/%s?format=json' % filter_name
        page = 1
        tickets = []

        # Skip pagination by looping over each page and adding tickets
        while True:
            this_page = self._api._get(url + '&page=%d' % page, kwargs)
            if len(this_page) == 0:
                break
            tickets += this_page
            page += 1

        return [self.get_ticket(t['display_id']) for t in tickets]

    def list_all_tickets(self):
        """List all tickets, closed or open."""
        return self.list_tickets(filter_name='all_tickets')

    def list_open_tickets(self):
        """List all new and open tickets."""
        return self.list_tickets(filter_name='new_my_open')

    def list_deleted_tickets(self):
        """Lists all deleted tickets."""
        return self.list_tickets(filter_name='deleted')

class ContactAPI(object):
    def __init__(self, api):
        self._api = api

    def get_contact(self, contact_id):
        """Get a contact's details by id"""
        url = 'contacts/%s.json' % contact_id
        return Contact(self._api, **self._api._get(url)['user'])

    def create_contact(self, name, email):
        url = 'contacts.json'
        return Contact(self._api._post(self._api._create_post("user", name=name, email=email))['user'])

class API(object):
    def __init__(self, domain, user=None, password=None, api_key=None):
        """Creates a wrapper to perform API actions.
        :param str domain:    the Freshdesk domain (not custom). e.g. company.freshdesk.com
        :param str user:      the username
        :param str password:  password for the username
        :param str api_key:   the API key - NOTE: username and password are ignored if specified

        Instances:
          .tickets:   the Ticket API
          .contacts:  the Contacts API
          .topics:    the Topics API
          .solutions: the Solutions API
        """

        self._api_prefix = 'http://{}/'.format(domain.rstrip('/'))
        self._session = requests.Session()
        if api_key:
            self._session.auth = (api_key, 'unused_with_api_key')
        else:
            self._session.auth = (user, password)
        self._session.headers = {'Content-Type': 'application/json'}

        self.tickets = TicketAPI(self)
        self.contacts = ContactAPI(self)
        self.topics = TopicAPI(self)
        self.solutions = SolutionAPI(self)

    def _create_post(self, post_type="", **kwargs):
        """Internal: Create a post body
        :param str post_type: The type of post to create e.g. 'topic'"""
        return json.dumps({post_type: kwargs})

    def _handle_response(self, response):
        """Internal: Handle any errors
        
        #TODO: Needs improvement"""
        response.raise_for_status()
        if 'Retry-After' in response.headers:
            raise HTTPError('403 Forbidden: API rate-limit has been reached until {}.' \
                    'See http://freshdesk.com/api#ratelimit'.format(r.headers['Retry-After']))
        try:
            j = response.json()
            if 'require_login' in j:
                raise HTTPError('403 Forbidden: API key is incorrect for this domain')
        except:
            j = "{}"
        return j

    def _get(self, url, params={}):
        """Internal: Wrapper around request.get() to use the API prefix. Returns a JSON response."""
        response = self._handle_response(self._session.get(self._api_prefix + url, params=params))
        return response

    def _put(self, url, data={}):
        """Internal: Wrapper around request.put() to use the API prefix. Returns a JSON response"""
        response = self._handle_response(self._session.put(self._api_prefix + url, data=data))
        return response

    def _post(self, url, data={}):
        """Internal: Wrapper around request.post() to use the API prefix. Returns a JSON response"""
        response = self._handle_response(self._session.post(self._api_prefix + url, data=data))
        return response

    def _delete(self, url):
        """Internal: Wrapper around request.delete() to use the API prefic. Returns a JSON response"""
        response = self._handle_response(self._session.delete(self._api_prefix + url))
        return response
