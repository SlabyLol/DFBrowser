import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar,
    QLineEdit, QFileDialog, QMessageBox, QDialog,
    QVBoxLayout, QLabel, QPushButton
)

from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtCore import QUrl, Qt, QSettings

from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineProfile, QWebEngineDownloadRequest
)

# ==================================================
# Browser Page (Danger Detection)
# ==================================================

class BrowserPage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.pending_url = None
        self.allow_danger_once = False

        self.keywords = [
            "hack", "malware", "phishing",
            "keygen", "crack", "free money"
        ]

        self.loadFinished.connect(self.inspect_page)

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if url.isLocalFile():
            return True

        if url.scheme() == "df" and url.host() == "continue":
            self.allow_danger_once = True
            if self.pending_url:
                self.setUrl(self.pending_url)
                self.pending_url = None
            return False

        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    def inspect_page(self, ok):
        if not ok or self.allow_danger_once or self.url().isLocalFile():
            return
        self.toHtml(self.check_html)

    def check_html(self, html):
        if any(k in html.lower() for k in self.keywords):
            self.pending_url = self.url()
            self.setHtml(
                self.warning_html(self.pending_url.toString()),
                QUrl("df://warning")
            )

    def warning_html(self, url):
        return f"""
        <html>
        <body style="background:#b00000;color:white;
        font-family:Arial;display:flex;flex-direction:column;
        justify-content:center;align-items:center;height:100vh;
        text-align:center;">
            <h1>WARNING THIS IS A DANGEROUS SITE</h1>
            <p>DFBROWSER IS TRYING TO HELP YOU</p>
            <small>{url}</small>
            <a href="df://continue"
               style="margin-top:30px;background:black;
               color:white;padding:15px 30px;
               text-decoration:none;border-radius:6px;">
               I am accepting the risk and I am continuing
            </a>
        </body>
        </html>
        """

# ==================================================
# Settings Dialog
# ==================================================

class SettingsDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("DFBrowser Settings")
        self.settings = settings

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

# ==================================================
# Main Browser
# ==================================================

class DarkFoxBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DarkFoxBrowser")
        self.showMaximized()

        self.settings = QSettings("DarkFox", "DFBrowser")
        self.downloads = []  # KEEP REFERENCES

        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.downloadRequested.connect(self.handle_download)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.tabs.removeTab)
        self.tabs.currentChanged.connect(self.update_urlbar)
        self.setCentralWidget(self.tabs)

        self.create_toolbar()
        self.create_menu()
        self.setup_shortcuts()

        homepage = self.settings.value("homepage", "")
        if homepage:
            self.add_tab(QUrl(homepage))
        else:
            self.load_start_page()

    # ---------- SHORTCUTS ----------
    def setup_shortcuts(self):
        QShortcut(QKeySequence("F11"), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence("Esc"), self, activated=self.exit_fullscreen)

    def toggle_fullscreen(self):
        self.showFullScreen()

    def exit_fullscreen(self):
        self.showNormal()

    # ---------- TOOLBAR ----------
    def create_toolbar(self):
        bar = QToolBar()
        self.addToolBar(bar)

        bar.addAction(QAction("←", self, triggered=lambda: self.current().back()))
        bar.addAction(QAction("→", self, triggered=lambda: self.current().forward()))
        bar.addAction(QAction("⟳", self, triggered=lambda: self.current().reload()))
        bar.addAction(QAction("Home", self, triggered=self.go_home))
        bar.addAction(QAction("+", self, triggered=self.new_tab))

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate)
        bar.addWidget(self.urlbar)

    # ---------- MENU ----------
    def create_menu(self):
        menu = self.menuBar().addMenu("File")
        menu.addAction(QAction("Open HTML", self, triggered=self.open_html))
        menu.addAction(QAction("Settings", self, triggered=self.open_settings))

    # ---------- TABS ----------
    def create_view(self):
        view = QWebEngineView()
        view.setPage(BrowserPage(self.profile, view))
        return view

    def add_tab(self, url):
        view = self.create_view()
        view.setUrl(url)
        self.tabs.addTab(view, "Tab")
        self.tabs.setCurrentWidget(view)

    def new_tab(self):
        self.add_tab(QUrl("https://www.google.com"))

    def current(self):
        return self.tabs.currentWidget()

    # ---------- NAV ----------
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

    # ---------- START PAGE ----------
    def load_start_page(self):
        html = """
        <html><body style="background:#111;color:white;
        font-family:Arial;display:flex;flex-direction:column;
        justify-content:center;align-items:center;height:100vh;">
        <h1>Welcome back to DFBrowser</h1>
        <small>An idea by DarkFox Co.</small>
        </body></html>
        """
        view = self.create_view()
        view.setHtml(html, QUrl("df://start"))
        self.tabs.addTab(view, "Start")
        self.tabs.setCurrentWidget(view)

    # ---------- FILES & DOWNLOADS ----------
    def open_html(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open HTML", "", "HTML (*.html *.htm)"
        )
        if path:
            self.current().setUrl(QUrl.fromLocalFile(path))

    def handle_download(self, download: QWebEngineDownloadRequest):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save File", download.downloadFileName()
        )
        if not path:
            download.cancel()
            return

        download.setDownloadDirectory(str(QUrl.fromLocalFile(path).adjusted(QUrl.RemoveFilename).path()))
        download.setDownloadFileName(QUrl.fromLocalFile(path).fileName())
        download.accept()

        self.downloads.append(download)

    # ---------- SETTINGS ----------
    def open_settings(self):
        dlg = SettingsDialog(self.settings)
        dlg.exec()

# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DarkFoxBrowser()
    window.show()
    sys.exit(app.exec())
