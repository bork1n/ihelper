from fake_useragent import UserAgent
import requests
import time
import random
import pickle
import os

SESSIONS_DIR = 'sessions'
DEFAULT_COOKIES = {
    'ig_vw': '1536',
    'ig_pr': '1.25',
    'ig_vh': '772',
    'ig_or': 'landscape-primary',
}
DEFAULT_HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Content-Length': '0',
    'Host': 'www.instagram.com',
    'Origin': 'https://www.instagram.com',
    'Referer': 'https://www.instagram.com/',
    'X-Instagram-AJAX': '1',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest'
}


class InstaConnection:
    url = 'https://www.instagram.com/'
    url_login = 'https://www.instagram.com/accounts/login/ajax/'
    accept_language = 'en-US,en;q=0.5'
    login_status = False
    user_login = None
    user_password = None

    def __init__(self, accounts):
        self.user_login = accounts[0]['login']
        self.user_password = accounts[0]['password']
        self.s = requests.Session()
        self.do_login()

    def _session_file(self):
        return "{}/{}".format(SESSIONS_DIR, self.user_login)

    def check_login(self):
        r = self.s.get(self.url)
        finder = r.text.find(self.user_login)
        if finder != -1:
            self.login_status = True
        else:
            self.login_status = False
            self.logger.error(r.text)
            self.logger.error('Login error! Check your login data!')

    def _generate_ua(self):
        fake_ua = UserAgent()
        self.s.headers.update({'User-Agent': fake_ua['google chrome']})

    def do_login(self):
        self.load_session()
        if self.login_status:
            return
        self.logger.info("Logging in")
        self.login_post = {
            'username': self.user_login,
            'password': self.user_password
        }
        self._generate_ua()
        self.s.headers.update(DEFAULT_HEADERS)
        self.s.cookies.update(DEFAULT_COOKIES)

        r = self.s.get(self.url)
        self.s.headers.update({'X-CSRFToken': r.cookies['csrftoken']})
        time.sleep(5 * random.random())
        login = self.s.post(
            self.url_login, data=self.login_post, allow_redirects=True)

        if login.status_code == 200:
            self.csrftoken = login.cookies['csrftoken']
            self.s.headers.update({'X-CSRFToken': self.csrftoken})
            time.sleep(5 * random.random())
            self.check_login()
            if self.login_status:
                self.save_session()

        if not self.login_status:
            self.logger.error('Login error! Connection error!')

    def get(self, url):
        data = self.s.get(url)
        if data.status_code == 403:
            self.login_status = False
            os.remove(self._session_file())
            self.do_login()
            data = self.s.get(url)
        return data

    def post(self, url):
        pass

    def save_session(self):
        with open(self._session_file(), 'wb') as f:
            data = [
                requests.utils.dict_from_cookiejar(self.s.cookies),
                self.s.headers
            ]
            pickle.dump(data, f)

    def load_session(self):
        try:
            with open(self._session_file(), 'rb') as f:
                data = pickle.load(f)
                cookies = requests.utils.cookiejar_from_dict(data[0])
                self.csrftoken = cookies['csrftoken']
                self.s.cookies = cookies
                self.s.headers = data[1]
                self.login_status = True
                self.logger.info("Using existing cookies")

        except FileNotFoundError:
            pass
