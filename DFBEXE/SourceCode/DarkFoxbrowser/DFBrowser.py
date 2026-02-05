import sys, os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar,
    QLineEdit, QFileDialog, QDialog, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtCore import QUrl, Qt, QSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineDownloadRequest
from PySide6.QtWebChannel import QWebChannel
from sneedyai_backend import SneedyAI

# ----------------- Browser Page -----------------
class BrowserPage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.pending_url = None
        self.allow_once = False
        self.keywords = ["hack", "malware", "phishing", "keygen", "crack"]

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if url.scheme() == "df" and url.host() == "continue":
            self.allow_once = True
            if self.pending_url:
                self.setUrl(self.pending_url)
                self.pending_url = None
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    def inspect_html(self, html):
        if self.allow_once:
            self.allow_once = False
            return
        if any(k in html.lower() for k in self.keywords):
            self.pending_url = self.url()
            self.setHtml(self.warning_html(), QUrl("df://warning"))

    def warning_html(self):
        return """
        <html><body style="background:#b00000;color:white;
        font-family:Arial;display:flex;flex-direction:column;
        justify-content:center;align-items:center;height:100vh;text-align:center;">
        <h1>WARNING THIS IS A DANGEROUS SITE</h1>
        <p>DFBROWSER IS TRYING TO HELP YOU</p>
        <a href="df://continue" style="margin-top:30px;
        background:black;color:white;padding:15px 30px;
        text-decoration:none;border-radius:6px;">
        I am accepting the risk and I am continuing
        </a></body></html>
        """

# ----------------- Settings -----------------
class SettingsDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("DFBrowser Settings")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Start page URL:"))
        self.input = QLineEdit(settings.value("homepage", ""))
        layout.addWidget(self.input)
        btn = QPushButton("Save")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

    def save(self):
        self.settings.setValue("homepage", self.input.text())
        self.accept()

# ----------------- Main Browser -----------------
class DarkFoxBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DarkFoxBrowser")
        self.showMaximized()
        self.settings = QSettings("DarkFox", "DFBrowser")
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.downloadRequested.connect(self.handle_download)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.tabs.removeTab)
        self.tabs.currentChanged.connect(self.update_urlbar)
        self.setCentralWidget(self.tabs)
        self.downloads = []

        self.create_toolbar()
        self.create_menu()
        self.create_shortcuts()

        homepage = self.settings.value("homepage", "")
        if homepage:
            self.add_tab(QUrl(homepage))
        else:
            self.load_start_page()

    # ----------------- Toolbar -----------------
    def create_toolbar(self):
        bar = QToolBar()
        self.addToolBar(bar)
        bar.addAction(QAction("←", self, triggered=lambda: self.current().back()))
        bar.addAction(QAction("→", self, triggered=lambda: self.current().forward()))
        bar.addAction(QAction("⟳", self, triggered=lambda: self.current().reload()))
        bar.addAction(QAction("Home", self, triggered=self.go_home))
        bar.addAction(QAction("+", self, triggered=self.new_tab))
        bar.addAction(QAction("SneedyAI", self, triggered=lambda: self.load_sneedyai_tab()))

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate)
        bar.addWidget(self.urlbar)

    # ----------------- Menu -----------------
    def create_menu(self):
        menu = self.menuBar().addMenu("File")
        menu.addAction(QAction("Open HTML", self, triggered=self.open_html))
        menu.addAction(QAction("Settings", self, triggered=self.open_settings))

    # ----------------- Shortcuts -----------------
    def create_shortcuts(self):
        QShortcut(QKeySequence("F11"), self, activated=self.showFullScreen)
        QShortcut(QKeySequence("Escape"), self, activated=self.showNormal)

    # ----------------- Tabs -----------------
    def create_view(self):
        view = QWebEngineView()
        page = BrowserPage(self.profile, view)
        view.setPage(page)
        view.urlChanged.connect(lambda url, v=view: self.update_urlbar())
        view.titleChanged.connect(lambda title, v=view: self.update_tab_title(v, title))
        view.loadFinished.connect(lambda ok, p=page: p.toHtml(p.inspect_html))
        return view

    def add_tab(self, url):
        view = self.create_view()
        view.setUrl(url)
        index = self.tabs.addTab(view, "Loading...")
        self.tabs.setCurrentIndex(index)

    def new_tab(self):
        self.add_tab(QUrl("https://www.google.com"))

    def current(self):
        return self.tabs.currentWidget()

    def update_tab_title(self, view, title):
        index = self.tabs.indexOf(view)
        if index >= 0:
            self.tabs.setTabText(index, title if title else "New Tab")

    # ----------------- Navigation -----------------
    def navigate(self):
        url = self.urlbar.text()
        if not url.startswith("http"):
            url = "https://" + url
        self.current().setUrl(QUrl(url))

    def update_urlbar(self):
        if self.current():
            self.urlbar.setText(self.current().url().toString())

    def go_home(self):
        homepage = self.settings.value("homepage", "")
        if homepage:
            self.current().setUrl(QUrl(homepage))
        else:
            self.load_start_page()

    # ----------------- Start Page -----------------
    def load_start_page(self):
        html = f"""
        <html>
        <head>
        <meta charset="UTF-8">
        <title>DFBrowser Start</title>
        <style>
            body {{
                background: url('file:///{os.path.abspath('dfbstartbg.png')}') no-repeat center center fixed;
                background-size: cover;
                color: white;
                font-family: Arial, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                text-align: center;
            }}
            h1 {{
                font-size: 48px;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px #000;
            }}
            button {{
                margin-top: 30px;
                padding: 15px 30px;
                font-size: 18px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                background-color: rgba(0,0,0,0.7);
                color: white;
            }}
            small {{
                margin-top: 40px;
                font-size: 14px;
                text-shadow: 1px 1px 2px #000;
            }}
        </style>
        </head>
        <body>
            <h1>Welcome back to DFBrowser</h1>
            <button onclick="location.href='df://sneedyai'">SneedyAI</button>
            <small>An idea by DarkFox Co.</small>
        </body>
        </html>
        """
        view = self.create_view()
        channel = QWebChannel()
        backend = SneedyAI()
        channel.registerObject("sneedy", backend)
        view.page().setWebChannel(channel)
        view.setHtml(html, QUrl("df://start"))
        self.tabs.addTab(view, "Start")
        self.tabs.setCurrentWidget(view)

    def load_sneedyai_tab(self):
        sneedy_view = self.create_view()
        channel = QWebChannel()
        backend = SneedyAI()
        channel.registerObject("sneedy", backend)
        sneedy_view.page().setWebChannel(channel)
        sneedy_view.setUrl(QUrl.fromLocalFile(os.path.abspath("sneedyai.html")))
        index = self.tabs.addTab(sneedy_view, "SneedyAI")
        self.tabs.setCurrentIndex(index)

    # ----------------- Files & Downloads -----------------
    def open_html(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open HTML", "", "HTML Files (*.html *.htm)"
        )
        if path:
            self.current().setUrl(QUrl.fromLocalFile(path))

    def handle_download(self, download: QWebEngineDownloadRequest):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save File", download.downloadFileName()
        )
        if path:
            download.setDownloadDirectory(QUrl.fromLocalFile(path).adjusted(QUrl.RemoveFilename).path())
            download.setDownloadFileName(QUrl.fromLocalFile(path).fileName())
            download.accept()
            self.downloads.append(download)

    # ----------------- Settings -----------------
    def open_settings(self):
        dlg = SettingsDialog(self.settings)
        dlg.exec()

# ----------------- Run App -----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DarkFoxBrowser()
    window.show()
    sys.exit(app.exec())
