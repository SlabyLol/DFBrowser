## THIS IS COPYRIGHT TO DarkFox Co.
## I TOLD YOU TO NOT DOWNLOADING THE CODE OR COPYING THE CODE
## PLS CALL 911 AND SAY "I STOLE A CODE FROM SOMEONE WHITHOUT PERMISSON AND I AM GOING TO JAIL"

import sys
import os
import json

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar,
    QAction, QLineEdit, QFileDialog, QDialog,
    QLabel, QPushButton, QVBoxLayout, QMessageBox
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView, QWebEngineProfile, QWebEnginePage
)
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtCore import QUrl, QStandardPaths


# ==================================================
# CONFIG
# ==================================================
APPDATA = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
CONFIG_PATH = os.path.join(APPDATA, "dfbrowser_config.json")

DEFAULT_CONFIG = {
    "homepage": ""
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)


# ==================================================
# AD / TRACKER BLOCKER
# ==================================================
class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.blocked_domains = [
            "doubleclick.net",
            "googlesyndication.com",
            "googleadservices.com",
            "adsystem.com",
            "adservice.",
            "analytics",
            "tracking",
            "facebook.net",
            "fbcdn.net"
        ]

    def interceptRequest(self, info):
        url = info.requestUrl().toString().lower()
        if "google.com" in url or "gstatic.com" in url:
            return
        if any(d in url for d in self.blocked_domains):
            info.block(True)


# ==================================================
# SETTINGS
# ==================================================
class SettingsDialog(QDialog):
    def __init__(self, parent, homepage):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(420, 160)

        label = QLabel("Start page URL or local HTML file path:")
        self.input = QLineEdit(homepage)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.input)
        layout.addWidget(save_btn)

    def homepage(self):
        return self.input.text().strip()


# ==================================================
# CUSTOM PAGE
# ==================================================
class BrowserPage(QWebEnginePage):
    def __init__(self, profile, parent=None, main_window=None):
        super().__init__(profile, parent)
        self.main_window = main_window
        self.fullScreenRequested.connect(self.handle_fullscreen)
        self.pending_danger_url = None

        # simple local danger keywords
        self.danger_keywords = [
            "malware",
            "phishing",
            "keygen",
            "crack",
            "free-money",
            "hacked"
        ]

    def handle_fullscreen(self, request):
        request.accept()
        if request.toggleOn():
            self.main_window.enter_fullscreen()
        else:
            self.main_window.exit_fullscreen()

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        url_str = url.toString().lower()

        # Internal start page
        if url.scheme() == "df" and url.host() == "start":
            self.setHtml(self.start_page_html(), QUrl("df://start"))
            return False

        # User accepted risk
        if url.scheme() == "df" and url.host() == "continue":
            if self.pending_danger_url:
                real = self.pending_danger_url
                self.pending_danger_url = None
                self.setUrl(real)
            return False

        # Dangerous site detection
        if is_main_frame and any(k in url_str for k in self.danger_keywords):
            self.pending_danger_url = url
            self.setHtml(self.danger_page_html(url_str), QUrl("df://warning"))
            return False

        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    def start_page_html(self):
        return """
        <html>
        <body style="background:#121212;color:white;
                     font-family:Arial;
                     display:flex;
                     flex-direction:column;
                     justify-content:center;
                     align-items:center;
                     height:100vh;">
            <h1>Welcome back to DFBrowser</h1>
            <p style="color:#888;position:absolute;bottom:20px;">
                An idea by DarkFox Co.
            </p>
        </body>
        </html>
        """

    def danger_page_html(self, url):
        return f"""
        <html>
        <body style="
            background:#b00000;
            color:white;
            font-family:Arial;
            display:flex;
            flex-direction:column;
            justify-content:center;
            align-items:center;
            height:100vh;
            text-align:center;
            padding:40px;">
            
            <h1 style="font-size:40px;margin-bottom:20px;">
                WARNING THIS IS A DANGEROUS SITE
            </h1>

            <h2 style="margin-bottom:30px;">
                DFBROWSER IS TRYING TO HELP YOU
            </h2>

            <p style="opacity:0.9;margin-bottom:40px;">
                {url}
            </p>

            <a href="df://continue"
               style="
                background:#000;
                color:white;
                padding:15px 30px;
                text-decoration:none;
                font-size:16px;
                border-radius:5px;">
                I am accepting the risk and I am continuing
            </a>
        </body>
        </html>
        """


# ==================================================
# MAIN WINDOW
# ==================================================
class DarkFoxBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.fullscreen = False

        self.setWindowTitle("DFBrowser")
        self.setGeometry(100, 100, 1300, 850)

        profile_path = os.path.join(APPDATA, "DarkFoxProfile")
        os.makedirs(profile_path, exist_ok=True)

        self.profile = QWebEngineProfile("DFBrowser", self)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        self.profile.setUrlRequestInterceptor(AdBlocker())

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.tabs.removeTab)
        self.setCentralWidget(self.tabs)

        bar = QToolBar()
        self.addToolBar(bar)

        bar.addAction("Back", lambda: self.current().back())
        bar.addAction("Forward", lambda: self.current().forward())
        bar.addAction("Reload", lambda: self.current().reload())
        bar.addAction("New Tab", self.add_tab)
        bar.addAction("Settings", self.open_settings)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate)
        bar.addWidget(self.urlbar)

        self.add_tab()

    def current(self):
        return self.tabs.currentWidget()

    def start_url(self):
        hp = self.config.get("homepage", "")
        if not hp:
            return QUrl("df://start")
        if os.path.exists(hp):
            return QUrl.fromLocalFile(hp)
        return QUrl(hp)

    def add_tab(self):
        view = QWebEngineView()
        page = BrowserPage(self.profile, view, self)
        view.setPage(page)
        view.setUrl(self.start_url())

        i = self.tabs.addTab(view, "New Tab")
        self.tabs.setCurrentIndex(i)

        view.urlChanged.connect(lambda u: self.urlbar.setText(u.toString()))
        view.loadFinished.connect(lambda: self.tabs.setTabText(i, view.page().title()))

    def navigate(self):
        text = self.urlbar.text().strip()
        if not text.startswith(("http", "df://")):
            text = "https://" + text
        self.current().setUrl(QUrl(text))

    def open_settings(self):
        dlg = SettingsDialog(self, self.config.get("homepage", ""))
        if dlg.exec_():
            self.config["homepage"] = dlg.homepage()
            save_config(self.config)

    def enter_fullscreen(self):
        self.showFullScreen()
        self.fullscreen = True

    def exit_fullscreen(self):
        self.showNormal()
        self.fullscreen = False

    def keyPressEvent(self, e):
        if e.key() == 16777264:  # F11
            self.enter_fullscreen() if not self.fullscreen else self.exit_fullscreen()
        elif e.key() == 16777216 and self.fullscreen:  # ESC
            self.exit_fullscreen()


# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("DFBrowser")
    win = DarkFoxBrowser()
    win.show()
    sys.exit(app.exec_())
