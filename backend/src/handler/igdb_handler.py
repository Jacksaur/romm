import sys
import functools
from unidecode import unidecode as uc
from time import time

import requests
from config import CLIENT_ID, CLIENT_SECRET
from utils import get_file_name_with_no_tags as get_search_term
from logger.logger import log


class IGDBHandler():

    def __init__(self) -> None:
        base_url: str = 'https://api.igdb.com/v4'
        self.platform_url: str = f'{base_url}/platforms/'
        self.games_url: str = f'{base_url}/games/'
        self.covers_url: str = f'{base_url}/covers/'
        self.twitch_auth: TwitchAuth = TwitchAuth()
        self.headers = {
            'Client-ID': self.twitch_auth.client_id,
            'Authorization': f'Bearer {self.twitch_auth.get_oauth_token()}',
            'Accept': 'application/json'
        }
        

    def check_twitch_token(func) -> tuple:
        @functools.wraps(func)
        def wrapper(*args):
            args[0].headers['Authorization'] = f'Bearer {args[0].twitch_auth.get_oauth_token()}'
            return func(*args)
        return wrapper
    

    def _search_rom(self, search_term: str, p_igdb_id: str, category: int = None) -> dict:
            category_filter: str = f"& category={category}" if category else ""
            try:
                return requests.post(self.games_url, headers=self.headers,
                                     data=f"search \"{search_term}\"; \
                                            fields id, slug, name, summary; \
                                            where platforms=[{p_igdb_id}] {category_filter};").json()[0]
            except IndexError:
                return {}


    def _search_cover(self, rom_id: str) -> str:
        res: dict = requests.post(self.covers_url, headers=self.headers,
                                  data=f"fields url; where game={rom_id};").json()[0]
        return f"https:{res['url']}" if 'url' in res.keys() else ""

    
    @check_twitch_token
    def get_platform(self, slug: str) -> tuple:
        try:
            res: dict = requests.post(self.platform_url, headers=self.headers,
                                      data=f"fields id, name; where slug=\"{slug}\";").json()[0]
            igdb_id = res['id'] if 'id' in res.keys() else ""
            name = res['name'] if 'name' in res.keys() else ""
        except IndexError:
            log.warning(f"{slug} not found in IGDB")
        if not name: name = slug
        return {'igdb_id': igdb_id, 'name': name, 'slug': slug, 'logo_path': ''}


    @check_twitch_token
    def get_rom_by_id(self, r_igdb_id: str) -> dict:
        res: dict = requests.post(self.games_url, headers=self.headers,
                                  data=f"fields slug, name, summary; where id={r_igdb_id};").json()[0]
        log.debug(res)
        r_slug = res['slug'] if 'slug' in res.keys() else ""
        r_name = res['name'] if 'name' in res.keys() else ""
        summary = res['summary'] if 'summary' in res.keys() else ""
        return {'r_igdb_id': r_igdb_id, 'r_slug': r_slug, 'r_name': r_name, 'summary': summary, 'url_cover': self._search_cover(r_igdb_id)}


    @check_twitch_token
    def get_rom(self, file_name: str, p_igdb_id: int) -> dict:
        search_term: str = uc(get_search_term(file_name))
        res = (self._search_rom(search_term, p_igdb_id, 0) or
               self._search_rom(search_term, p_igdb_id, 10) or
               self._search_rom(search_term, p_igdb_id))

        r_igdb_id = res['id'] if 'id' in res.keys() else ""
        r_slug = res['slug'] if 'slug' in res.keys() else ""
        r_name = res['name'] if 'name' in res.keys() else ""
        summary = res['summary'] if 'summary' in res.keys() else ""

        if not r_name: r_name = search_term
        if not r_igdb_id: log.warning(f"{r_name} not found in IGDB")
        return {'r_igdb_id': r_igdb_id, 'r_slug': r_slug, 'r_name': r_name, 'summary': summary, 'url_cover': self._search_cover(r_igdb_id)}
    
    
    @check_twitch_token
    def get_matched_rom_by_id(self, igdb_id: str) -> list:
        matched_rom: dict = self.get_rom_by_id(igdb_id)
        matched_rom['url_cover'] = matched_rom['url_cover'].replace('t_thumb', f't_cover_big')
        return [matched_rom]
    

    @check_twitch_token
    def get_matched_roms(self, file_name: str, p_igdb_id: int, p_slug: str) -> list:
        matched_roms: list[dict] = []
        if p_igdb_id:
            matched_roms: list = requests.post(self.games_url, headers=self.headers,
                                               data=f"search \"{uc(get_search_term(file_name))}\"; \
                                                    fields name, id, slug, summary; \
                                                    where platforms=[{p_igdb_id}];").json()
            for rom in matched_roms:
                rom['url_cover'] = self._search_cover(rom['id']).replace('t_thumb', f't_cover_big')
                rom['r_igdb_id'] = rom.pop('id')
                rom['r_slug'] = rom.pop('slug')
                rom['r_name'] = rom.pop('name')
        else:
            log.warning(f"{p_slug} is not supported!")
        return matched_roms



class TwitchAuth():

    def __init__(self) -> None:
        self.base_url: str = 'https://id.twitch.tv/oauth2/token'
        self.token: str = ""
        self.token_checkout: int = int(time())
        self.SECURE_SECONDS_OFFSET: int = 10 # seconds offset to avoid invalid token 
        self.token_valid_seconds: int = 0
        self.client_id: str = CLIENT_ID
        self.client_secret: str = CLIENT_SECRET


    def _is_token_valid(self) -> str:
        return True if int(time()) + self.SECURE_SECONDS_OFFSET - self.token_checkout < self.token_valid_seconds else False


    def _update_twitch_token(self) -> str:
        res = requests.post(url=self.base_url,
                            params={
                                'client_id': self.client_id,
                                'client_secret': self.client_secret,
                                'grant_type': 'client_credentials'}
                            ).json()
        self.token_checkout = int(time())
        try:
            self.token_valid_seconds = res['expires_in']
            self.token = res['access_token']
            log.info("Twitch token fetched!")
        except KeyError:
            log.error("Could not get twitch auth token: check client_id and client_secret")
            sys.exit(2)


    def get_oauth_token(self) -> str:
        if not self._is_token_valid():
            log.warning("Twitch token invalid: fetching a new one")
            self._update_twitch_token()
        return self.token