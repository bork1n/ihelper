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
    BANTIME = 1800

    def __init__(self, accounts, logger, sessions_dir=SESSIONS_DIR):
        self.accounts = accounts
        self.logger = logger
        self.sessions_dir = sessions_dir
        self._load_bans()
        self._change_account()

    def _load_bans(self):
        loaded_bans = {}
        try:
            with open(self._banned_file(), 'rb') as f:
                loaded_bans = pickle.load(f)
                self.logger.info("loaded bans: %s", {
                                 x: loaded_bans[x] for x in loaded_bans if loaded_bans[x]})
        except FileNotFoundError:
            pass

        self.banned = {x['login']: loaded_bans.get(
            x['login'], 0) for x in self.accounts}

    def _save_bans(self):
        with open(self._banned_file(), 'wb') as f:
            loaded_bans = pickle.dump(self.banned, f)

    def _change_account(self):
        avail_accounts = None
        while not avail_accounts:
            if avail_accounts == None:
                pass
            else:
                self.logger.error("no accounts alive, sleeping")
                time.sleep(60)
            avail_accounts = list(filter(
                lambda acc: self.banned.get(acc['login'], 0) < time.time() - self.BANTIME, self.accounts))

        self.account = random.choice(avail_accounts)
        self.logger.info("Changing account to %s, all avail: %s",
                         self.account['login'],
                         " ".join(map(lambda a: a['login'], avail_accounts)))
        self.login_status = False
        self.s = requests.Session()
        self.do_login()

    def _session_file(self):
        return "{}/{}".format(self.sessions_dir, self.account['login'])

    def _banned_file(self):
        return "{}/{}".format(self.sessions_dir, 'banned')

    def check_login(self):
        r = self.s.get(self.url)
        finder = r.text.find(self.account['login'])
        if finder != -1:
            self.login_status = True
        else:
            self.login_status = False
            self.logger.error(r.text)
            self.logger.error('Login error! Check your login data!')

    def _generate_ua(self):
        ua = self.account['user-agent'] or UserAgent().fake_ua['google chrome']
        self.s.headers.update({'User-Agent': ua})

    def do_login(self):
        self.load_session()
        if self.login_status:
            return
        self.logger.info("Logging in")
        self.login_post = {
            'username': self.account['login'],
            'password': self.account['password']
        }
        self._generate_ua()
        self.s.headers.update(DEFAULT_HEADERS)
        self.s.cookies.update(DEFAULT_COOKIES)
        if self.account['cookies']:
            self.logger.info("Cookies provided, checking...")
            self.s.cookies.update(self.account['cookies'])
            self.check_login()
            if self.login_status:
                self.logger.info("worked!")
                self.save_session()
                return
            self.logger.info("cookies were not enough, trying to login")
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
        """ rate limit """
        if data.status_code == 429:
            self.banned[self.account['login']] = int(time.time())
            self._save_bans()
            self._change_account()
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
            self.login_status = False
            pass
