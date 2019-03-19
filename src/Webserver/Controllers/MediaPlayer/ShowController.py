import json
import urllib.parse

from flask import request

from Database.Database import Database
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Util import to_JSON
from Webserver.APIController import app
from Webserver.Models import BaseMedia

class ShowController:

    shows_api_path = Settings.get_string("serie_api")
    server_uri = "http://localhost:50009/torrent"

    @staticmethod
    @app.route('/shows', methods=['GET'])
    def get_shows():
        page = int(request.args.get('page'))
        order_by = request.args.get('orderby')
        keywords = request.args.get('keywords')
        include_previous_pages = request.args.get('page') == "true"
        search_string = ""
        if keywords:
            search_string = "&keywords=" + urllib.parse.quote(keywords)

        if include_previous_pages:
            data = []
            current_page = 0
            while current_page != page:
                current_page+= 1
                data += ShowController.request_shows(
                    ShowController.shows_api_path + "shows/" + str(current_page) + "?sort=" + urllib.parse.quote(
                        order_by) + search_string)

        else:
            data = ShowController.request_shows(ShowController.shows_api_path + "shows/" + str(page) + "?sort=" + urllib.parse.quote(order_by) + search_string)

        return to_JSON(data).encode()

    @staticmethod
    def request_shows(url):
        data = RequestFactory.make_request(url)

        if data is not None:
            return ShowController.parse_show_data(data.decode('utf-8'))
        else:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get show data"])
            Logger().write(LogVerbosity.Info, "Error fetching shows")
            return []

    @staticmethod
    @app.route('/show', methods=['GET'])
    def get_by_id():
        id = request.args.get('id')
        data = ShowController.get_by_id_internal(id)
        return json.dumps(data).encode('utf-8')

    @staticmethod
    def get_by_id_internal(id):
        Logger().write(LogVerbosity.Debug, "Get show by id " + id)
        response = RequestFactory.make_request(ShowController.shows_api_path + "show/" + id)
        data = json.loads(response.decode('utf-8'))

        seen_episodes = []
        data['favorite'] = False
        if not Settings.get_bool("slave"):
            seen_episodes = Database().get_history_for_id(id)
            data['favorite'] = id in [x.id for x in Database().get_favorites()]
        for episode in data['episodes']:
            seen = [x for x in seen_episodes if episode['season'] == x.season and episode['episode'] == x.episode]
            episode['seen'] = len(seen) != 0
            if len(seen) == 0:
                continue
            seen = seen[-1]
            episode['seen'] = True
            episode['played_for'] = seen.played_for
            episode['length'] = seen.length
        return data

    @staticmethod
    @app.route('/show/favorite', methods=['POST'])
    def add_favorite():
        id = request.args.get('id')
        title = urllib.parse.unquote(request.args.get('title'))
        image = urllib.parse.unquote(request.args.get('image'))

        Logger().write(LogVerbosity.Info, "Add show favorite: " + id)
        Database().add_favorite(id, "Show", title, image)
        return "OK"

    @staticmethod
    @app.route('/show/favorite', methods=['DELETE'])
    def remove_favorite():
        id = request.args.get('id')

        Logger().write(LogVerbosity.Info, "Remove show favorite: " + id)
        Database().remove_favorite(id)
        return "OK"

    @staticmethod
    def parse_show_data(data):
        json_data = json.loads(data)
        if isinstance(json_data, list):
            return [Show(x['imdb_id'], ShowController.get_poster(x), x['title'], x['rating']['percentage']) for x in json_data]
        else:
            return Show(json_data['imdb_id'], ShowController.get_poster(json_data), json_data['title'], json_data['rating']['percentage'])

    @staticmethod
    def get_poster(show):
        poster = ""
        if 'images' in show:
            if 'poster' in show['images']:
                poster = show['images']['poster']
            elif len(show['images']) > 0:
                poster = show['images'][0]
        return poster

class Show(BaseMedia):

    def __init__(self, id, poster, title, rating):
        super().__init__(id, poster, title)
        self.rating = rating
