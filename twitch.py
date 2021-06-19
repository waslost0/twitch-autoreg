import requests
import random
import time
import json
import datetime
import os
from PyQt5 import QtWidgets
import sys
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from requests import RequestException
from fake_useragent import UserAgent
from python_rucaptcha import FunCaptcha
from python_rucaptcha.RuCaptchaControl import RuCaptchaControl
from string import Formatter, Template
from generate_username import generate_username
import threading
from gui import Ui_MainWindow
from random import sample
from lxml import html

requests.adapters.DEFAULT_RETRIES = 10

global path
sbf = datetime.datetime.now()
path = str(sbf.day) + '_' + str(sbf.month) + '_' + str(sbf.year) + '/' + str(sbf.hour) + '_' + str(
    sbf.minute) + '_' + str(sbf.second)

RETRIES = 10

ALPHNUM = (
        'qgftmrnzclwukphoydixavsbej' +
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ' +
        '1234567890'
)

if not os.path.isfile('all_tokens.txt'):
    with open('all_tokens.txt', 'w') as f:
        f.write('')


def generate_password(count=1, length=12, chars=ALPHNUM):
    return ''.join(sample(chars, length))


def get_username():
    return generate_username()[0]


def get_password():
    return generate_password()


def request_proxies(proxy_url):
    response = requests.get(proxy_url).content
    proxies = html.fromstring(response).xpath("//html/body/p/text()")
    proxies = proxies[0].split('\n')
    return proxies


class LogValues:
    def __init__(self):
        self.errors = 0
        self.accounts = 0
        self.proxy_error = 0
        self.threads_amount = 0
        self.thread_flag = False
        self.registered_accounts = 0
        self.active_threads_count = 0


class Proxies:
    def __init__(self):
        self.proxies_list = []
        self.proxy_type = ''
        self.proxy_path = ''
        self.proxy_url = ''


Logger = LogValues()
Proxies = Proxies()


def get_current_time():
    return ':'.join(datetime.datetime.now().strftime("%H:%M:%S").split(':'))


class Registration:
    def __init__(self, thread):
        self.rucaptcha_key, self.proxy_url = [item for item in load_data_from_file().values()]
        self.session = requests.session()
        self.ua = UserAgent()
        self.session.headers.update({'user-agent': self.ua.random})
        self.proxy = ''
        self.proxies = {}
        self.check_proxy()
        temp = self.get_proxy(self.proxy_url)
        self.set_proxy(temp)
        while not self.check_proxy():
            temp = self.get_proxy(self.proxy_url)
            self.set_proxy(temp)
        self.username = get_username()
        self.password = get_password()
        self.caps_token = "E5554D43-23CC-1982-971D-6A2262A2CA24"
        self.thread = thread

        self.received_captcha_id = None

        self.email = self.username + random.choice(["@gmail.com", "@mail.ru"])

    def check_proxy(self):
        try:
            self.session.get('https://www.twitch.tv', timeout=10)
        except (RequestException, ConnectionError):
            return False
        return True

    def get_proxy(self, url=''):
        if len(Proxies.proxies_list) == 0:
            if url == '':
                Proxies.proxies_list = open(Proxies.proxy_path, "r").read().split('\n')
            else:
                Proxies.proxies_list = request_proxies(url)

        self.proxy = Proxies.proxies_list.pop(0)
        return self.proxy

    def set_proxy(self, proxy):
        if 'http' in Proxies.proxy_type:
            Proxies.proxy_type = 'http'
        self.proxies = {
            'http': f"{Proxies.proxy_type}://{proxy}",
            'https': f"{Proxies.proxy_type}://{proxy}",
        }
        self.session.proxies.update(self.proxies)

    def validate_username(self):
        data = {
            "operationName": "UsernameValidator_User",
            "extensions": {
                "persistedQuery": {
                    "sha256Hash": "fd1085cf8350e309b725cf8ca91cd90cac03909a3edeeedbd0872ac912f3d660",
                    "version": 1
                }
            },
            "variables": {
                "username": self.username
            }
        }
        headers = {"Client-Id": "kimne78kx3ncx6brgo4mv6wki5h1ko"}

        try:
            response = requests.post(
                "https://gql.twitch.tv/gql",
                data=json.dumps(data),
                headers=headers,
                timeout=15
            ).json()

            if response['data']['isUsernameAvailable'] is True:
                return True
            else:
                return False
        except Exception as e:
            return False

    def register(self):
        headers = {
            'origin': 'https://www.twitch.tv', 'referer': 'https://www.twitch.tv/', 'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors', 'sec-fetch-site': 'cross-site'
        }

        print(f"[{self.thread}] [{get_current_time()}] Good thread running.")
        print(f"[{self.thread}] {self.proxies}")

        while not self.validate_username():
            self.username = get_username()

        # ark_token = self.Solve_Captcha()
        ark_token = self.solve_captcha()
        if not ark_token:
            return

        data = {
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "birthday": {
                "day": random.randint(1, 28),
                "month": random.randint(1, 12),
                "year": random.randint(1980, 2000)
            },
            "client_id": "kimne78kx3ncx6brgo4mv6wki5h1ko",
            "include_verification_code": bool('true'),
            "arkose": {
                "token": str(ark_token)
            }
        }
        session_result = None
        for i in range(RETRIES):
            time.sleep(0.5)
            try:
                session_result = self.session.post(
                    "https://passport.twitch.tv/register",
                    data=json.dumps(data),
                    headers=headers,
                    timeout=20)
                break
            except Exception as e:
                if i == RETRIES:
                    raise e

        if session_result is None:
            return

        print(f'[{self.thread}] {session_result.text}')

        if 'ip associated with signup throttled' in session_result.text:
            print(f'[{self.thread}] IP-Blocked')
            return

        if 'error_code' in session_result.text:
            open(path + "/errors.txt", 'a').write(
                f'{self.email}:{self.username}:{self.password}:{session_result.text}\n')

        if 'error' in session_result.json():
            if 'CAPTCHA' in session_result.json()['error']:
                Logger.errors += 1
                answer = RuCaptchaControl(rucaptcha_key=self.rucaptcha_key,
                                          service_type='rucaptcha').additional_methods(
                    action="reportbad", id=self.received_captcha_id
                )
                if not answer["error"]:
                    print(f'[{self.thread}] [ReportBad] Success.')
                elif answer["error"]:
                    print(answer["errorBody"])
                return False
        else:
            answer = RuCaptchaControl(rucaptcha_key=self.rucaptcha_key, service_type='rucaptcha').additional_methods(
                action="reportgood", id=self.received_captcha_id
            )

            if not answer["error"]:
                print(f'[{self.thread}] [ReportGood]  Success.')
            elif answer["error"]:
                print(answer["errorBody"])

            with open("all_tokens.txt", 'a') as all_tokens:
                all_tokens.write(f'{self.username}:{self.password}{session_result.json()['access_token']}\n')

            with open(path + "/log_pass.txt", 'a') as log_pass, open(path + "/tokens.txt", 'a') as tokens:
                log_pass.write(self.username + ":" + self.password + '\n')
                tokens.write(session_result.json()['access_token'] + '\n')

                if session_result.json()['access_token']:
                    Logger.accounts -= 1
                    Logger.registered_accounts += 1
            return True

    def solve_captcha(self):
        i = 0
        while True:
            try:
                send_captcha = requests.get(
                    "https://rucaptcha.com/in.php?key=" + self.rucaptcha_key + "&method=funcaptcha&publickey=" + self.caps_token + "&surl=https://client-api.arkoselabs.com&pageurl=https://www.twitch.tv/signup?no-mobile-redirect=true&json=1",
                    proxies=self.proxies, timeout=20)
                break
            except (RequestException, ConnectionError):
                if i > RETRIES:
                    return None
                i += 1
        self.received_captcha_id = send_captcha.json()['request']
        if 'ERROR_NO_SLOT_AVAILABLE' in self.received_captcha_id:
            return None

        retries = 0
        while True:
            if retries > 20:
                return None
            time.sleep(10)
            try:
                received_captcha = requests.get(
                    "https://rucaptcha.com/res.php?key=" + self.rucaptcha_key + "&action=get&id=" + self.received_captcha_id + "&json=1",
                    timeout=20)
                print(f'[{self.thread}] {received_captcha.json()}')
            except (RequestException, ConnectionError):
                retries += 1
                print(f'[{self.thread}] Retries: {retries}')
                continue
            if received_captcha.json()["request"] == "ERROR_CAPTCHA_UNSOLVABLE":
                return None

            if received_captcha.json()['status'] == 1:
                return received_captcha.json()['request']


def thread_starter(val):
    if Logger.thread_flag:
        return False
    reg1 = Registration(val)
    reg1.register()
    Logger.active_threads_count -= 1
    return True


def start_threads(threads):
    threads_list = []
    print(Proxies.proxies_list)
    while Logger.accounts > 0:
        for i in range(0, threads):
            if not Logger.thread_flag:
                Logger.active_threads_count += 1
                my_thread = threading.Thread(target=thread_starter, args=(i,))
                my_thread.setDaemon(True)
                threads_list.append(my_thread)
                my_thread.start()

            if Logger.active_threads_count < 1:
                print('We are done')
                return

            time.sleep(1)
            while Logger.active_threads_count + 1 > threads:
                time.sleep(5)
                if Logger.accounts == 0:
                    return
                if Logger.registered_accounts % 10 == 0 and Logger.registered_accounts != 0:
                    if Proxies.proxy_url:
                        Proxies.proxies_list = request_proxies(Proxies.proxy_url)


class DeltaTemplate(Template):
    delimiter = '%'


def strfdelta(tdelta, fmt):
    d = {"D": tdelta.days}
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    d["H"] = '{:02d}'.format(hours)
    d["M"] = '{:02d}'.format(minutes)
    d["S"] = '{:02d}'.format(seconds)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):

        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.get_proxy_path)
        self.pushButton_2.clicked.connect(self.get_proxy_url)

        self.pushButtonStart.clicked.connect(self.start_program)
        self.pushButtonStopThreads.clicked.connect(self.disable_thread_start)
        _rucap_key, _proxy_url = [item for item in load_data_from_file().values()]
        if _rucap_key != '':
            self.lineEdit.setText(_rucap_key)
        if _proxy_url != '':
            self.proxy_url_lineEdit.setText(_proxy_url)

        self.time_start = None

        self.stat_updater_timer = QTimer()
        self.stat_updater_timer.setInterval(1000)
        self.stat_updater_timer.timeout.connect(self.stat_updater)
        self.stat_updater_timer.start()

    def title_timer(self):
        # self.setWindowTitle(str(datetime.datetime.now().strftime("%H:%M:%S")))
        delta = datetime.datetime.now() - self.time_start
        self.setWindowTitle(str(strfdelta(delta, "%H:%M:%S")))

    def get_proxy_url(self):
        try:
            Proxies.proxies_list = request_proxies(self.proxy_url_lineEdit.text())
            Proxies.proxy_url = self.proxy_url_lineEdit.text()
            print(Proxies.proxies_list)
            self.label_3.setText("Proxies:" + str(len(Proxies.proxies_list)))
        except Exception:
            self.show_msg_box("Proxies load error")

    def get_proxy_path(self):
        try:
            Proxies.proxy_path = QFileDialog.getOpenFileName(self, "Choose proxy file")[0]
            with open(Proxies.proxy_path, "r") as f:
                Proxies.proxies_list = f.read().splitlines()

            print(Proxies.proxies_list)
            self.label_3.setText("Proxies:" + str(len(Proxies.proxies_list)))
        except Exception:
            self.show_msg_box("Proxies load error")

    @staticmethod
    def show_msg_box(message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle('Error')
        msg_box.setStyleSheet('''
            QMessageBox {
                background-color: #1b1b2f;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QPushButton {
                border: 2px solid rgb(52, 59, 72);
                border-radius: 5px;	
                width: 60px;
                height: 25px;
                color: #ffffff;
                background-color: #1b1b2f;
            }
            QPushButton:hover {
                background-color: rgb(57, 65, 80);
                border: 2px solid rgb(61, 70, 86);
            }
            QPushButton:pressed {	
                background-color: rgb(35, 40, 49);
                border: 2px solid rgb(43, 50, 61);
            }'''
                              )
        msg_box.setText(message)
        msg_box.exec()

    def start_program(self):
        global path
        Logger.thread_flag = False
        try:
            Logger.accounts = int(self.accounts_input.text())
            Logger.threads_amount = int(self.threads_input.text())
        except Exception:
            self.show_msg_box(
                "Incorrect numbers of threads and accounts")
            return

        if Logger.threads_amount > Logger.accounts:
            self.show_msg_box(
                "Incorrect numbers of threads and accounts")
            return

        Proxies.proxy_type = self.comboBox.currentText()
        rucaptcha_key = self.lineEdit.text()
        save_data_to_file(RuCaptchaKey=rucaptcha_key, proxies_url=self.proxy_url_lineEdit.text())

        print("Accounts:" + str(Logger.accounts) + "\nThreads:" + str(
            Logger.threads_amount) + "\nRucaptcha key:" + rucaptcha_key)
        sbf = datetime.datetime.now()
        path = str(sbf.day) + '_' + str(sbf.month) + '_' + str(sbf.year) + '/' + str(sbf.hour) + '_' + str(
            sbf.minute) + '_' + str(sbf.second)
        try:
            os.makedirs(path)
        except Exception:
            pass

        my_thread = threading.Thread(target=start_threads, args={Logger.threads_amount})
        my_thread.setDaemon(True)
        my_thread.start()
        self.pushButtonStart.setDisabled(True)
        self.time_start = datetime.datetime.now()
        self.update_title_timer = QTimer()
        self.update_title_timer.setInterval(1000)
        self.update_title_timer.timeout.connect(self.title_timer)
        self.update_title_timer.start()

    def disable_thread_start(self):
        if self.update_title_timer:
            self.update_title_timer.stop()
        Logger.thread_flag = True
        self.pushButtonStart.setEnabled(True)

    def stat_updater(self):
        self.label_2.setText("Errors:" + str(Logger.errors))
        self.label.setText("Accounts:" + str(Logger.registered_accounts))
        self.label_4.setText("Threads:" + str(Logger.active_threads_count))
        self.label_3.setText("Proxies:" + str(len(Proxies.proxies_list)))


def save_data_to_file(**kwargs):
    try:
        data = {}
        with open('data.txt', 'r+') as json_file:
            data = json.load(json_file)

        for key in kwargs:
            data[key] = kwargs[key]

        with open('data.txt', 'w+') as json_file:
            json.dump(data, json_file)

    except KeyError as error:
        print('Cannot find: %s', error.args[0])


def load_data_from_file():
    try:
        params = {}
        if not os.path.exists('data.txt'):
            with open('data.txt', 'w') as f:
                f.write('{"RuCaptchaKey": "", "proxies_url": ""}')

        with open('data.txt') as json_file:
            data = json.load(json_file)

        if 'RuCaptchaKey' in data:
            params['rucaptcha_key'] = data['RuCaptchaKey']

        if 'proxies_url' in data:
            params['proxies_url'] = data['proxies_url']

    except KeyError as error:
        print('Cannot find: %s', error.args[0])
        return None
    else:
        return params


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec_()


if __name__ == '__main__':
    main()
