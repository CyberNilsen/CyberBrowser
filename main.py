import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QTabBar, QStackedLayout,
    QSizePolicy, QComboBox, QDialog, QFormLayout, QDialogButtonBox,
    QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView

os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts.debug=false'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-web-security --disable-features=VizDisplayCompositor'


class ConfigManager:
    def __init__(self):
        self.config_file = "cyberbrowser_config.json"
        self.default_config = {
            "default_search_engine": "Google",
            "search_engines": {
                "Google": "https://www.google.com/search?q={}",
                "DuckDuckGo": "https://duckduckgo.com/?q={}",
                "Bing": "https://www.bing.com/search?q={}",
                "Yahoo": "https://search.yahoo.com/search?p={}",
                "Yandex": "https://yandex.com/search/?text={}",
                "Searx": "https://searx.org/search?q={}",
                "Startpage": "https://www.startpage.com/sp/search?query={}"
            },
            "homepage_url": "",
            "enable_tor": False,
            "window_width": 1400,
            "window_height": 900
        }
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)

                config = self.default_config.copy()
                config.update(loaded_config)
                return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.default_config.copy()
        else:
            self.save_config(self.default_config)
            return self.default_config.copy()

    def save_config(self, config=None):
        if config is None:
            config = self.config
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def get_search_url(self, engine_name, query):
        search_engines = self.config.get("search_engines", {})
        if engine_name in search_engines:
            return search_engines[engine_name].format(query.replace(" ", "+"))
        
        return f"https://www.google.com/search?q={query.replace(' ', '+')}"


class SettingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.search_engine_combo = QComboBox()
        search_engines = self.config_manager.get("search_engines", {})
        self.search_engine_combo.addItems(search_engines.keys())
        current_engine = self.config_manager.get("default_search_engine", "Google")
        if current_engine in search_engines:
            self.search_engine_combo.setCurrentText(current_engine)
        
        form_layout.addRow("Default Search Engine:", self.search_engine_combo)
        
        self.homepage_input = QLineEdit()
        self.homepage_input.setText(self.config_manager.get("homepage_url", ""))
        self.homepage_input.setPlaceholderText("Leave empty for default home page")
        form_layout.addRow("Homepage URL:", self.homepage_input)
        
        self.tor_checkbox = QCheckBox()
        self.tor_checkbox.setChecked(self.config_manager.get("enable_tor", False))
        form_layout.addRow("Enable Tor (Experimental):", self.tor_checkbox)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            QLabel {
                color: #f1f5f9;
                font-size: 14px;
            }
            QComboBox, QLineEdit {
                background-color: #1e293b;
                border: 2px solid #334155;
                border-radius: 6px;
                padding: 8px;
                color: #f1f5f9;
                font-size: 14px;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
            QCheckBox {
                color: #f1f5f9;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #334155;
                border-radius: 3px;
                background-color: #1e293b;
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
            QPushButton {
                background-color: #1e293b;
                border: 2px solid #3b82f6;
                border-radius: 6px;
                padding: 8px 16px;
                color: #3b82f6;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3b82f6;
                color: white;
            }
        """)

    def get_settings(self):
        return {
            "default_search_engine": self.search_engine_combo.currentText(),
            "homepage_url": self.homepage_input.text().strip(),
            "enable_tor": self.tor_checkbox.isChecked()
        }


class CyberBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        
        self.setWindowTitle("CyberBrowser")
        window_width = self.config_manager.get("window_width", 1400)
        window_height = self.config_manager.get("window_height", 900)
        self.resize(window_width, window_height)
        
        try:
            self.setWindowIcon(QIcon("assets/CyberBrowser.png"))
        except:
            pass

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
            QPushButton#settings_btn {
                border-radius: 15px;
                min-width: 80px;
                max-width: 100px;
                padding: 6px 15px;
                font-size: 13px;
            }
            QComboBox {
                background-color: #1e293b;
                border: 2px solid #334155;
                border-radius: 15px;
                padding: 6px 15px;
                font-size: 14px;
                color: #f1f5f9;
                min-width: 120px;
                max-width: 150px;
            }
            QComboBox:focus {
                border: 2px solid #3b82f6;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #94a3b8;
                margin-right: 5px;
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

        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("settings_btn")
        settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(settings_btn)

        main_layout.addLayout(top_bar)
        main_layout.addLayout(self.stack)

        self.create_home_tab()

        self.setCentralWidget(main_widget)

    def open_settings(self):
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            for key, value in settings.items():
                self.config_manager.set(key, value)
            
            self.update_home_tabs()

    def update_home_tabs(self):
        """Update search engine dropdowns in existing home tabs"""
        for tab_id, tab_info in self.tab_data.items():
            widget = tab_info['widget']
            if hasattr(widget, 'search_engine_combo') and hasattr(widget, 'tab_id'):

                current_text = widget.search_engine_combo.currentText()
                widget.search_engine_combo.clear()
                search_engines = self.config_manager.get("search_engines", {})
                widget.search_engine_combo.addItems(search_engines.keys())
                
                default_engine = self.config_manager.get("default_search_engine", "Google")
                if default_engine in search_engines:
                    widget.search_engine_combo.setCurrentText(default_engine)
                elif current_text in search_engines:
                    widget.search_engine_combo.setCurrentText(current_text)

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

        search_engine_layout = QHBoxLayout()
        search_engine_layout.setAlignment(Qt.AlignCenter)
        
        engine_label = QLabel("Search with:")
        engine_label.setStyleSheet("color: #94a3b8; font-size: 14px; margin-right: 10px;")
        
        search_engine_combo = QComboBox()
        search_engines = self.config_manager.get("search_engines", {})
        search_engine_combo.addItems(search_engines.keys())
        default_engine = self.config_manager.get("default_search_engine", "Google")
        if default_engine in search_engines:
            search_engine_combo.setCurrentText(default_engine)
        
        search_engine_layout.addWidget(engine_label)
        search_engine_layout.addWidget(search_engine_combo)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Search or enter a website")
        search_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        search_input.returnPressed.connect(lambda: self.perform_search(tab_id))

        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        start_btn = QPushButton("Start")
        start_btn.clicked.connect(lambda: self.perform_search(tab_id))
        
        tor_status = "Enabled" if self.config_manager.get("enable_tor", False) else "Disabled"
        tor_btn = QPushButton(f"Tor: {tor_status}")
        tor_btn.clicked.connect(self.toggle_tor)
        
        buttons_layout.addWidget(start_btn)
        buttons_layout.addWidget(tor_btn)

        layout.addWidget(logo_label)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(search_engine_layout)
        layout.addWidget(search_input)
        layout.addLayout(buttons_layout)

        widget.search_input = search_input
        widget.search_engine_combo = search_engine_combo
        widget.tor_btn = tor_btn
        widget.tab_id = tab_id
        
        return widget

    def toggle_tor(self):
        current_tor = self.config_manager.get("enable_tor", False)
        new_tor = not current_tor
        self.config_manager.set("enable_tor", new_tor)
        
        for tab_id, tab_info in self.tab_data.items():
            widget = tab_info['widget']
            if hasattr(widget, 'tor_btn'):
                status = "Enabled" if new_tor else "Disabled"
                widget.tor_btn.setText(f"Tor: {status}")

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
            else:
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

        selected_engine = "Google"  
        if hasattr(widget, 'search_engine_combo'):
            selected_engine = widget.search_engine_combo.currentText()

        if "." in query and " " not in query and not query.startswith("http"):
            url = "http://" + query
            search_title = query.split('.')[0].capitalize()
        elif query.startswith("http"):
            url = query
            search_title = query.split('/')[2] if '/' in query else query
        else:
            url = self.config_manager.get_search_url(selected_engine, query)
            search_title = f"{selected_engine}: {query[:20]}..."

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

    def closeEvent(self, event):
        self.config_manager.set("window_width", self.width())
        self.config_manager.set("window_height", self.height())
        super().closeEvent(event)


if __name__ == "__main__":
    os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts.debug=false;js.debug=false'
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton, True)
    window = CyberBrowser()
    window.show()
    sys.exit(app.exec_())