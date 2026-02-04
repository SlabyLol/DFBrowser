import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar,
    QLineEdit, QFileDialog, QAction, QMessageBox, QDialog,
    QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PySide6.QtCore import QUrl, Qt, QSettings


# ------------------ Browser Page ------------------

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
        if not ok:
            return
        if self.allow_danger_once:
            return
        if self.url().isLocalFile():
            return
        self.toHtml(self.check_html)

    def check_html(self, html):
        if any(k in html.lower() for k in self.keywords):
            self.pending_url = self.url()
            self.setHtml(self.warning_html(self.pending_url.toString()),
                         QUrl("df://warning"))

    def warning_html(self, url):
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
            text-align:center;">
            <h1>WARNING THIS IS A DANGEROUS SITE</h1>
            <p>DFBROWSER IS TRYING TO HELP YOU</p>
            <small>{url}</small>
            <a href="df://continue"
               style="
               margin-top:30px;
               background:black;
               color:white;
               padding:15px 30px;
               text-decoration:none;
               border-radius:6px;">
               I am accepting the risk and I am continuing
            </a>
        </body>
        </html>
        """


# ------------------ Settings Dialog ------------------

class SettingsDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("DFBrowser Settings")
        self.settings = settings

        layout = QVBoxLayout()
        label = QLabel("Start Page URL:")
        self.input = QLineEdit(settings.value("homepage", ""))

        save = QPushButton("Save")
        save.clicked.connect(self.save)

        layout.addWidget(label)
        layout.addWidget(self.input)
        layout.addWidget(save)
        self.setLayout(layout)

    def save(self):
        self.settings.setValue("homepage", self.input.text())
        self.accept()


# ------------------ Main Browser ------------------

class DarkFoxBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DarkFoxBrowser")
        self.showMaximized()

        self.settings = QSettings("DarkFox", "DFBrowser")

        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.downloadRequested.connect(self.handle_download)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)

        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate)

        self.toolbar.addWidget(self.urlbar)

        self.tabs.currentChanged.connect(self.update_urlbar)

        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        open_html = QAction("Open HTML", self)
        open_html.triggered.connect(self.open_html)
        file_menu.addAction(open_html)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)

        homepage = self.settings.value("homepage", "")
        if homepage:
            self.add_tab(QUrl(homepage), "Home")
        else:
            self.load_start_page()

    def load_start_page(self):
        html = """
        <html>
        <body style="
            background:#111;
            color:white;
            font-family:Arial;
            display:flex;
            flex-direction:column;
            justify-content:center;
            align-items:center;
            height:100vh;">
            <h1>Welcome back to DFBrowser</h1>
            <p>Fast. Dark. Private.</p>
            <small>An idea by DarkFox Co.</small>
        </body>
        </html>
        """
        view = self.create_view()
        view.setHtml(html, QUrl("df://start"))
        self.tabs.addTab(view, "Start")

    def create_view(self):
        view = QWebEngineView()
        page = BrowserPage(self.profile, view)
        view.setPage(page)
        return view

    def add_tab(self, url, title):
        view = self.create_view()
        view.setUrl(url)
        self.tabs.addTab(view, title)
        self.tabs.setCurrentWidget(view)

    def navigate(self):
        text = self.urlbar.text()
        if not text.startswith("http"):
            text = "https://" + text
        self.tabs.currentWidget().setUrl(QUrl(text))

    def update_urlbar(self):
        url = self.tabs.currentWidget().url()
        self.urlbar.setText(url.toString())

    def open_html(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open HTML", "", "HTML Files (*.html *.htm)")
        if path:
            self.tabs.currentWidget().setUrl(QUrl.fromLocalFile(path))

    def handle_download(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", download.path())
        if path:
            download.setPath(path)
            download.accept()

    def open_settings(self):
        dlg = SettingsDialog(self.settings)
        if dlg.exec():
            QMessageBox.information(self, "Restart",
                                    "Please restart DFBrowser to apply the new start page.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self.showFullScreen()
        elif event.key() == Qt.Key_Escape:
            self.showNormal()


# ------------------ Run ------------------

app = QApplication(sys.argv)
window = DarkFoxBrowser()
window.show()
sys.exit(app.exec())
