import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QTabBar, QStackedLayout,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView

os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts.debug=false'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-web-security --disable-features=VizDisplayCompositor'


class CyberBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberBrowser")
        self.resize(1400, 900)
        self.setWindowIcon(QIcon("assets/CyberBrowser.png"))

        self.stack = QStackedLayout()
        self.tab_data = {}  
        self.next_tab_id = 0
        self.tab_id_mapping = {} 

        self.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
                color: #e2e8f0;
                font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            }
            QLabel#title {
                color: #f8fafc;
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QLabel#subtitle {
                color: #94a3b8;
                font-size: 18px;
                margin-bottom: 25px;
            }
            QLineEdit {
                background-color: #1e293b;
                border: 2px solid #334155;
                border-radius: 24px;
                padding: 12px 20px;
                font-size: 16px;
                color: #f1f5f9;
                min-width: 450px;
                max-width: 550px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
            QPushButton {
                background-color: transparent;
                border: 2px solid #3b82f6;
                border-radius: 20px;
                padding: 8px 20px;
                font-size: 15px;
                color: #3b82f6;
                min-width: 100px;
                max-width: 120px;
            }
            QPushButton:hover {
                background-color: #3b82f6;
                color: white;
            }
            QTabBar::tab {
                background: #1e293b;
                border: 1px solid #334155;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 20px;
                margin-right: -1px;
                color: #f1f5f9;
                min-width: 80px;
                max-width: 150px;
            }
            QTabBar::tab:selected {
                background: #334155;
                color: white;
            }
        """)

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(15, 10, 15, 10)

        self.tab_bar = QTabBar()
        self.tab_bar.setMovable(True)
        self.tab_bar.addTab("Home")
        self.tab_bar.addTab("+")
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        self.tab_bar.tabMoved.connect(self.on_tab_moved)

        top_bar.addWidget(self.tab_bar)
        top_bar.addStretch()

        main_layout.addLayout(top_bar)
        main_layout.addLayout(self.stack)

        self.create_home_tab()

        self.setCentralWidget(main_widget)

    def create_home_tab(self):
        tab_id = self.next_tab_id
        self.next_tab_id += 1
        
        home_widget = self.create_home_widget(tab_id)
        self.stack.addWidget(home_widget)
        
        self.tab_data[tab_id] = {
            'widget': home_widget,
            'web_view': None,
            'title': 'Home'
        }
        
        self.tab_id_mapping[0] = tab_id
        
        return tab_id

    def create_home_widget(self, tab_id):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap("assets/CyberBrowser.png").scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        except:
            logo_label.setText("🌐")
            logo_label.setStyleSheet("font-size: 72px;")
        logo_label.setAlignment(Qt.AlignCenter)

        title = QLabel("CyberBrowser")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Fast. Anonymous. Tor-Ready.")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Search or enter a website")
        search_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        search_input.returnPressed.connect(lambda: self.perform_search(tab_id))

        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        start_btn = QPushButton("Start")
        start_btn.clicked.connect(lambda: self.perform_search(tab_id))
        tor_btn = QPushButton("Enable Tor")
        buttons_layout.addWidget(start_btn)
        buttons_layout.addWidget(tor_btn)

        layout.addWidget(logo_label)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(search_input)
        layout.addLayout(buttons_layout)

        widget.search_input = search_input
        widget.tab_id = tab_id
        return widget

    def create_new_tab(self):

        new_tab_index = self.tab_bar.count() - 1
        tab_id = self.next_tab_id
        self.next_tab_id += 1
        
        self.tab_bar.insertTab(new_tab_index, f"New Tab")
        
        new_mapping = {}
        for tab_index, existing_tab_id in self.tab_id_mapping.items():
            if tab_index >= new_tab_index:
                new_mapping[tab_index + 1] = existing_tab_id
            else:
                new_mapping[tab_index] = existing_tab_id
        new_mapping[new_tab_index] = tab_id
        self.tab_id_mapping = new_mapping
        
        home_widget = self.create_home_widget(tab_id)
        self.stack.addWidget(home_widget)
        
        self.tab_data[tab_id] = {
            'widget': home_widget,
            'web_view': None,
            'title': 'New Tab'
        }
        
        self.tab_bar.setCurrentIndex(new_tab_index)

    def on_tab_moved(self, from_index, to_index):

        moved_tab_id = self.tab_id_mapping[from_index]
        
        del self.tab_id_mapping[from_index]
        
        new_mapping = {}
        for tab_index, tab_id in sorted(self.tab_id_mapping.items()):
            if from_index < to_index:  
                if tab_index <= to_index:
                    new_mapping[tab_index - 1] = tab_id
                else:
                    new_mapping[tab_index] = tab_id

                if tab_index >= to_index:
                    new_mapping[tab_index + 1] = tab_id
                else:
                    new_mapping[tab_index] = tab_id
        
        new_mapping[to_index] = moved_tab_id
        self.tab_id_mapping = new_mapping

    def on_tab_changed(self, index):
        if index >= 0 and index < self.tab_bar.count():
            tab_text = self.tab_bar.tabText(index)
            if tab_text == "+":
                self.create_new_tab()
                return
            
            if index in self.tab_id_mapping:
                tab_id = self.tab_id_mapping[index]
                if tab_id in self.tab_data:
                    widget = self.tab_data[tab_id]['widget']
                    self.stack.setCurrentWidget(widget)

    def perform_search(self, tab_id):
        if tab_id not in self.tab_data:
            return
            
        tab_info = self.tab_data[tab_id]
        widget = tab_info['widget']
        
        if not hasattr(widget, 'search_input'):
            return
            
        query = widget.search_input.text().strip()
        if not query:
            return

        if "." in query and " " not in query:
            url = "http://" + query if not query.startswith("http") else query
            search_title = query.split('.')[0].capitalize()
        else:
            url = "https://www.google.com/search?q=" + query.replace(" ", "+")
            search_title = query.capitalize()

        if tab_info['web_view'] is None:
            browser = QWebEngineView()
            browser.load(QUrl(url))
            
            old_widget = tab_info['widget']
            self.stack.removeWidget(old_widget)
            old_widget.deleteLater()
            
            self.stack.addWidget(browser)
            self.stack.setCurrentWidget(browser)
            
            tab_info['widget'] = browser
            tab_info['web_view'] = browser
            tab_info['title'] = search_title
            
            self.update_tab_title(tab_id, search_title)
        else:
            browser = tab_info['web_view']
            browser.load(QUrl(url))
            self.stack.setCurrentWidget(browser)
            
            tab_info['title'] = search_title
            self.update_tab_title(tab_id, search_title)

    def update_tab_title(self, tab_id, title):

        for tab_index, mapped_tab_id in self.tab_id_mapping.items():
            if mapped_tab_id == tab_id:

                display_title = title[:12] + "..." if len(title) > 15 else title
                self.tab_bar.setTabText(tab_index, display_title)
                break


if __name__ == "__main__":
    os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts.debug=false;js.debug=false'
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton, True)
    window = CyberBrowser()
    window.show()
    sys.exit(app.exec_())