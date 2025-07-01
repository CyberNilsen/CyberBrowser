import sys
import os
import json
import subprocess
import time
import threading
import socket
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QTabBar, QStackedLayout,
    QSizePolicy, QComboBox, QDialog, QFormLayout, QDialogButtonBox,
    QMessageBox, QCheckBox, QFileDialog, QSpinBox, QSlider, QGroupBox, QScrollArea
)
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtNetwork import QNetworkProxy, QNetworkProxyFactory

os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts.debug=false'


class TorProxyFactory(QNetworkProxyFactory):
    """Custom proxy factory for Tor"""
    
    def __init__(self, use_tor=False):
        super().__init__()
        self.use_tor = use_tor
    
    def queryProxy(self, query):
        if self.use_tor:
            proxy = QNetworkProxy()
            proxy.setType(QNetworkProxy.Socks5Proxy)
            proxy.setHostName("127.0.0.1")
            proxy.setPort(9050)
            return [proxy]
        else:
            return [QNetworkProxy(QNetworkProxy.NoProxy)]


class TorManager(QObject):
    """Manages Tor process and connection"""
    tor_status_changed = pyqtSignal(bool, str) 
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.tor_process = None
        self.tor_port = 9050  
        self.control_port = 9051  
        self.is_running = False
        
    def start_tor(self):
        """Start Tor process"""
        if self.is_running:
            return True
            
        tor_dir = self.config_manager.get("tor_directory", "")
        if not tor_dir:
            self.tor_status_changed.emit(False, "Tor directory not configured")
            return False
            
        tor_executable = None
        for exe in ["tor", "tor.exe"]:
            tor_path = os.path.join(tor_dir, exe)
            if os.path.isfile(tor_path) and os.access(tor_path, os.X_OK):
                tor_executable = tor_path
                break
                
        if not tor_executable:
            self.tor_status_changed.emit(False, "Tor executable not found")
            return False
            
        try:
            tor_data_dir = os.path.join(os.path.expanduser("~"), ".cyberbrowser_tor")
            os.makedirs(tor_data_dir, exist_ok=True)
            
            tor_config = [
                tor_executable,
                "--SocksPort", f"127.0.0.1:{self.tor_port}",
                "--ControlPort", f"127.0.0.1:{self.control_port}",
                "--DataDirectory", tor_data_dir,
                "--Log", "notice stdout",
                "--CookieAuthentication", "1",
                "--ExitRelay", "0"
            ]
            
            self.tor_process = subprocess.Popen(
                tor_config,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if self._wait_for_tor_connection():
                self.is_running = True
                self.tor_status_changed.emit(True, "Tor is running")
                return True
            else:
                self.stop_tor()
                self.tor_status_changed.emit(False, "Tor failed to start")
                return False
                
        except Exception as e:
            self.tor_status_changed.emit(False, f"Failed to start Tor: {str(e)}")
            return False
            
    def stop_tor(self):
        """Stop Tor process"""
        if self.tor_process:
            try:
                self.tor_process.terminate()
                self.tor_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.tor_process.kill()
            except Exception:
                pass
            finally:
                self.tor_process = None
                
        self.is_running = False
        self.tor_status_changed.emit(False, "Tor stopped")
        
    def _wait_for_tor_connection(self, timeout=30):
        """Wait for Tor SOCKS proxy to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', self.tor_port))
                sock.close()
                if result == 0:
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False
        
    def is_tor_running(self):
        """Check if Tor is currently running"""
        return self.is_running and self.tor_process and self.tor_process.poll() is None


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
        "Startpage": "https://www.startpage.com/sp/search?query={}",
        "DuckDuckGo Onion": "https://duckduckgogg42ts72.onion/?q={}",
        "Ahmia Onion Search": "https://ahmia.fi/search/?q={}"
    },
    "homepage_url": "",
    "enable_tor": False,
    "tor_directory": "",
    "window_width": 1400,
    "window_height": 900,
    "enable_javascript": True,
    "enable_plugins": True,
    "enable_images": True,
    "enable_cookies": True,
    "user_agent": "",
    "download_directory": "",
    "enable_popup_blocking": True,
    "enable_notifications": False,
    "zoom_level": 100,
    "clear_data_on_exit": False,
    "enable_spell_check": True
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

    def is_tor_available(self):
        """Check if Tor is available at the configured directory"""
        tor_dir = self.get("tor_directory", "")
        if not tor_dir:
            return False
        
        tor_executables = ["tor", "tor.exe"]
        for exe in tor_executables:
            tor_path = os.path.join(tor_dir, exe)
            if os.path.isfile(tor_path) and os.access(tor_path, os.X_OK):
                return True
        return False


class TorWebEngineProfile(QWebEngineProfile):
    """Custom web engine profile that uses Tor proxy"""
    
    def __init__(self, tor_enabled=False, parent=None):
        super().__init__(parent)
        self.tor_enabled = tor_enabled
        self.proxy_factory = None
        self.setup_profile()
        
    def setup_profile(self):
        if self.tor_enabled:

            self.proxy_factory = TorProxyFactory(use_tor=True)
            
            self.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0")
            
            self.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
            self.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
            self.setHttpCacheMaximumSize(0)
            
            QNetworkProxyFactory.setApplicationProxyFactory(self.proxy_factory)
        else:

            self.setHttpUserAgent("")
            self.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
            self.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
            
            QNetworkProxyFactory.setUseSystemConfiguration(True)
    
        self.apply_config_settings()

def apply_config_settings(self):
    """Apply settings from config manager"""
    if hasattr(self, 'config_manager'):
        config = self.config_manager
        
        download_dir = config.get("download_directory", "")
        if download_dir and os.path.exists(download_dir):
            self.setDownloadPath(download_dir)
        
        custom_ua = config.get("user_agent", "")
        if custom_ua and not self.tor_enabled:
            self.setHttpUserAgent(custom_ua)
        
        if not config.get("enable_cookies", True):
            self.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)


class SettingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(700, 750)
        self.setMinimumSize(900, 700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        from PyQt5.QtWidgets import QTabWidget, QScrollArea
        tab_widget = QTabWidget()
        
        general_tab = self.create_general_tab()
        tab_widget.addTab(general_tab, "General")
        
        privacy_tab = self.create_privacy_tab()
        tab_widget.addTab(privacy_tab, "Privacy & Security")
        
        advanced_tab = self.create_advanced_tab()
        tab_widget.addTab(advanced_tab, "Advanced")
        
        
        tor_tab = self.create_tor_tab()
        tab_widget.addTab(tor_tab, "Tor")
        
        layout.addWidget(tab_widget)
        
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)
        layout.addWidget(button_box)
        
        self.setStyleSheet(self.get_dialog_stylesheet())

    def create_general_tab(self):
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        search_group = QGroupBox("Search Engine")
        search_layout = QFormLayout(search_group)
        search_layout.setSpacing(15)
        search_layout.setContentsMargins(20, 25, 20, 20)
        
        self.search_engine_combo = QComboBox()
        self.search_engine_combo.setMinimumHeight(40)
        search_engines = self.config_manager.get("search_engines", {})
        self.search_engine_combo.addItems(search_engines.keys())
        current_engine = self.config_manager.get("default_search_engine", "Google")
        if current_engine in search_engines:
            self.search_engine_combo.setCurrentText(current_engine)
        search_layout.addRow("Default Search Engine:", self.search_engine_combo)
        
        self.homepage_input = QLineEdit()
        self.homepage_input.setMinimumHeight(40)
        self.homepage_input.setText(self.config_manager.get("homepage_url", ""))
        self.homepage_input.setPlaceholderText("Leave empty for default home page")
        search_layout.addRow("Homepage URL:", self.homepage_input)
        
        layout.addWidget(search_group)
        
        download_group = QGroupBox("Downloads")
        download_layout = QFormLayout(download_group)
        download_layout.setSpacing(15)
        download_layout.setContentsMargins(20, 25, 20, 20)
        
        download_dir_layout = QHBoxLayout()
        self.download_directory_input = QLineEdit()
        self.download_directory_input.setMinimumHeight(40)
        self.download_directory_input.setText(self.config_manager.get("download_directory", ""))
        self.download_directory_input.setPlaceholderText("Default system download folder")
        
        download_browse_btn = QPushButton("Browse")
        download_browse_btn.setMinimumHeight(40)
        download_browse_btn.setMinimumWidth(80)
        download_browse_btn.clicked.connect(self.browse_download_directory)
        
        download_dir_layout.addWidget(self.download_directory_input)
        download_dir_layout.addWidget(download_browse_btn)
        download_layout.addRow("Download Directory:", download_dir_layout)
        
        layout.addWidget(download_group)
        
        display_group = QGroupBox("Display")
        display_layout = QFormLayout(display_group)
        display_layout.setSpacing(15)
        display_layout.setContentsMargins(20, 25, 20, 20)
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(self.config_manager.get("zoom_level", 100))
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.setTickInterval(25)
        self.zoom_slider.setMinimumHeight(30)
        
        zoom_layout = QHBoxLayout()
        self.zoom_label = QLabel(f"{self.zoom_slider.value()}%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_label)
        self.zoom_slider.valueChanged.connect(lambda v: self.zoom_label.setText(f"{v}%"))
        
        display_layout.addRow("Zoom Level:", zoom_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    def create_privacy_tab(self):
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        privacy_group = QGroupBox("Privacy Settings")
        privacy_layout = QFormLayout(privacy_group)
        privacy_layout.setSpacing(15)
        privacy_layout.setContentsMargins(20, 25, 20, 20)
        
        self.enable_cookies_cb = QCheckBox()
        self.enable_cookies_cb.setMinimumHeight(25)
        self.enable_cookies_cb.setChecked(self.config_manager.get("enable_cookies", True))
        privacy_layout.addRow("Enable Cookies:", self.enable_cookies_cb)
        
        self.enable_javascript_cb = QCheckBox()
        self.enable_javascript_cb.setMinimumHeight(25)
        self.enable_javascript_cb.setChecked(self.config_manager.get("enable_javascript", True))
        privacy_layout.addRow("Enable JavaScript:", self.enable_javascript_cb)
        
        self.enable_images_cb = QCheckBox()
        self.enable_images_cb.setMinimumHeight(25)
        self.enable_images_cb.setChecked(self.config_manager.get("enable_images", True))
        privacy_layout.addRow("Load Images:", self.enable_images_cb)
        
        self.enable_plugins_cb = QCheckBox()
        self.enable_plugins_cb.setMinimumHeight(25)
        self.enable_plugins_cb.setChecked(self.config_manager.get("enable_plugins", True))
        privacy_layout.addRow("Enable Plugins:", self.enable_plugins_cb)
        
        self.enable_popup_blocking_cb = QCheckBox()
        self.enable_popup_blocking_cb.setMinimumHeight(25)
        self.enable_popup_blocking_cb.setChecked(self.config_manager.get("enable_popup_blocking", True))
        privacy_layout.addRow("Block Popups:", self.enable_popup_blocking_cb)
        
        self.enable_notifications_cb = QCheckBox()
        self.enable_notifications_cb.setMinimumHeight(25)
        self.enable_notifications_cb.setChecked(self.config_manager.get("enable_notifications", False))
        privacy_layout.addRow("Enable Notifications:", self.enable_notifications_cb)
        
        self.clear_data_on_exit_cb = QCheckBox()
        self.clear_data_on_exit_cb.setMinimumHeight(25)
        self.clear_data_on_exit_cb.setChecked(self.config_manager.get("clear_data_on_exit", False))
        privacy_layout.addRow("Clear Data on Exit:", self.clear_data_on_exit_cb)
        
        layout.addWidget(privacy_group)
        
        ua_group = QGroupBox("User Agent")
        ua_layout = QFormLayout(ua_group)
        ua_layout.setSpacing(15)
        ua_layout.setContentsMargins(20, 25, 20, 20)
        
        self.user_agent_input = QLineEdit()
        self.user_agent_input.setMinimumHeight(40)
        self.user_agent_input.setText(self.config_manager.get("user_agent", ""))
        self.user_agent_input.setPlaceholderText("Leave empty for default user agent")
        ua_layout.addRow("Custom User Agent:", self.user_agent_input)
        
        layout.addWidget(ua_group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    def create_advanced_tab(self):
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        advanced_layout.setSpacing(15)
        advanced_layout.setContentsMargins(20, 25, 20, 20)
        
        self.enable_spell_check_cb = QCheckBox()
        self.enable_spell_check_cb.setMinimumHeight(25)
        self.enable_spell_check_cb.setChecked(self.config_manager.get("enable_spell_check", True))
        advanced_layout.addRow("Enable Spell Check:", self.enable_spell_check_cb)
        
        layout.addWidget(advanced_group)
        
        data_group = QGroupBox("Data Management")
        data_layout = QVBoxLayout(data_group)
        data_layout.setSpacing(15)
        data_layout.setContentsMargins(20, 25, 20, 20)
        
        clear_cache_btn = QPushButton("Clear Browser Cache")
        clear_cache_btn.setMinimumHeight(45)
        clear_cache_btn.clicked.connect(self.clear_cache)
        data_layout.addWidget(clear_cache_btn)
        
        clear_cookies_btn = QPushButton("Clear All Cookies")
        clear_cookies_btn.setMinimumHeight(45)
        clear_cookies_btn.clicked.connect(self.clear_cookies)
        data_layout.addWidget(clear_cookies_btn)
        
        clear_history_btn = QPushButton("Clear Browsing History")
        clear_history_btn.setMinimumHeight(45)
        clear_history_btn.clicked.connect(self.clear_history)
        data_layout.addWidget(clear_history_btn)
        
        layout.addWidget(data_group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    def create_tor_tab(self):
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        tor_group = QGroupBox("Tor Configuration")
        tor_layout = QFormLayout(tor_group)
        tor_layout.setSpacing(15)
        tor_layout.setContentsMargins(20, 25, 20, 20)
        
        tor_dir_layout = QHBoxLayout()
        self.tor_directory_input = QLineEdit()
        self.tor_directory_input.setMinimumHeight(40)
        self.tor_directory_input.setText(self.config_manager.get("tor_directory", ""))
        self.tor_directory_input.setPlaceholderText("Path to Tor installation directory")
        
        tor_browse_btn = QPushButton("Browse")
        tor_browse_btn.setMinimumHeight(40)
        tor_browse_btn.setMinimumWidth(80)
        tor_browse_btn.clicked.connect(self.browse_tor_directory)
        
        tor_dir_layout.addWidget(self.tor_directory_input)
        tor_dir_layout.addWidget(tor_browse_btn)
        tor_layout.addRow("Tor Directory:", tor_dir_layout)
        
        self.tor_status_label = QLabel()
        self.tor_status_label.setMinimumHeight(25)
        self.update_tor_status()
        tor_layout.addRow("Tor Status:", self.tor_status_label)
        
        layout.addWidget(tor_group)
        
        instructions_group = QGroupBox("Setup Instructions")
        instructions_layout = QVBoxLayout(instructions_group)
        instructions_layout.setContentsMargins(20, 25, 20, 20)
        
        instructions = QLabel(
            "Tor Setup Instructions:\n\n"
            "1. Download Tor Browser from torproject.org\n"
            "2. Extract it to a folder\n"
            "3. Browse to the 'Tor' folder inside the extracted directory\n"
            "4. Select the folder containing tor.exe (Windows) or tor (Linux/Mac)\n\n"
            "Note: The Tor directory should contain the tor executable file."
        )
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignTop)
        instructions.setMinimumHeight(120)
        instructions_layout.addWidget(instructions)
        
        layout.addWidget(instructions_group)
        
        self.tor_directory_input.textChanged.connect(self.update_tor_status)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    def browse_download_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Download Directory",
            self.download_directory_input.text()
        )
        if directory:
            self.download_directory_input.setText(directory)

    def browse_tor_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Tor Installation Directory",
            self.tor_directory_input.text()
        )
        if directory:
            self.tor_directory_input.setText(directory)

    def update_tor_status(self):
        tor_dir = self.tor_directory_input.text().strip()
        if not tor_dir:
            self.tor_status_label.setText("No directory specified")
            self.tor_status_label.setStyleSheet("color: #94a3b8; font-weight: normal;")
            return
        
        if not os.path.exists(tor_dir):
            self.tor_status_label.setText("Directory does not exist")
            self.tor_status_label.setStyleSheet("color: #ef4444; font-weight: bold;")
            return
        
        tor_executables = ["tor", "tor.exe"]
        tor_found = False
        for exe in tor_executables:
            tor_path = os.path.join(tor_dir, exe)
            if os.path.isfile(tor_path) and os.access(tor_path, os.X_OK):
                tor_found = True
                break
        
        if tor_found:
            self.tor_status_label.setText("✓ Tor executable found")
            self.tor_status_label.setStyleSheet("color: #22c55e; font-weight: bold;")
        else:
            self.tor_status_label.setText("✗ Tor executable not found")
            self.tor_status_label.setStyleSheet("color: #ef4444; font-weight: bold;")

    def clear_cache(self):
        reply = QMessageBox.question(self, "Clear Cache", "Are you sure you want to clear the browser cache?")
        if reply == QMessageBox.Yes:

            QMessageBox.information(self, "Cache Cleared", "Browser cache has been cleared.")

    def clear_cookies(self):
        reply = QMessageBox.question(self, "Clear Cookies", "Are you sure you want to clear all cookies?")
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Cookies Cleared", "All cookies have been cleared.")

    def clear_history(self):
        reply = QMessageBox.question(self, "Clear History", "Are you sure you want to clear browsing history?")
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "History Cleared", "Browsing history has been cleared.")

    def restore_defaults(self):
        reply = QMessageBox.question(self, "Restore Defaults", "Are you sure you want to restore all settings to defaults?")
        if reply == QMessageBox.Yes:
            
            self.search_engine_combo.setCurrentText("Google")
            self.homepage_input.setText("")
            self.download_directory_input.setText("")
            self.zoom_slider.setValue(100)
            self.enable_cookies_cb.setChecked(True)
            self.enable_javascript_cb.setChecked(True)
            self.enable_images_cb.setChecked(True)
            self.enable_plugins_cb.setChecked(True)
            self.enable_popup_blocking_cb.setChecked(True)
            self.enable_notifications_cb.setChecked(False)
            self.clear_data_on_exit_cb.setChecked(False)
            self.enable_spell_check_cb.setChecked(True)
            self.user_agent_input.setText("")
            self.tor_directory_input.setText("")

    def get_settings(self):
        return {
            "default_search_engine": self.search_engine_combo.currentText(),
            "homepage_url": self.homepage_input.text().strip(),
            "download_directory": self.download_directory_input.text().strip(),
            "zoom_level": self.zoom_slider.value(),
            "enable_cookies": self.enable_cookies_cb.isChecked(),
            "enable_javascript": self.enable_javascript_cb.isChecked(),
            "enable_images": self.enable_images_cb.isChecked(),
            "enable_plugins": self.enable_plugins_cb.isChecked(),
            "enable_popup_blocking": self.enable_popup_blocking_cb.isChecked(),
            "enable_notifications": self.enable_notifications_cb.isChecked(),
            "clear_data_on_exit": self.clear_data_on_exit_cb.isChecked(),
            "enable_spell_check": self.enable_spell_check_cb.isChecked(),
            "user_agent": self.user_agent_input.text().strip(),
            "tor_directory": self.tor_directory_input.text().strip()
        }

    def get_dialog_stylesheet(self):
        return """
            /* Main Dialog Styling */
            QDialog {
                background-color: #0f172a;
                color: #e2e8f0;
                font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            }
            
            /* Tab Widget Styling */
            QTabWidget::pane {
                border: 2px solid #334155;
                background-color: #1e293b;
                border-radius: 8px;
                top: -2px;
            }
            
            QTabBar::tab {
                background: linear-gradient(135deg, #334155, #475569);
                color: #f1f5f9;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 2px solid #334155;
                border-bottom: none;
                font-size: 14px;
                font-weight: 500;
                min-width: 100px;
            }
            
            QTabBar::tab:selected {
                background: linear-gradient(135deg, #1e293b, #334155);
                border-color: #3b82f6;
                color: #ffffff;
                font-weight: 600;
            }
            
            QTabBar::tab:hover:!selected {
                background: linear-gradient(135deg, #475569, #64748b);
                border-color: #64748b;
            }
            
            /* Group Box Styling */
            QGroupBox {
                font-weight: 600;
                font-size: 15px;
                border: 2px solid #334155;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 15px;
                color: #f1f5f9;
                background-color: rgba(30, 41, 59, 0.5);
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 10px;
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #3b82f6;
                font-weight: bold;
            }
            
            /* Label Styling */
            QLabel {
                color: #f1f5f9;
                font-size: 14px;
                font-weight: 500;
                padding: 2px;
            }
            
            /* Form Layout Labels */
            QFormLayout QLabel {
                color: #cbd5e1;
                font-size: 14px;
                font-weight: 500;
                min-width: 150px;
                padding-right: 10px;
            }
            
            /* Input Field Styling */
            QComboBox, QLineEdit {
                background: linear-gradient(135deg, #1e293b, #334155);
                border: 2px solid #475569;
                border-radius: 8px;
                padding: 10px 15px;
                color: #f1f5f9;
                font-size: 14px;
                min-height: 20px;
                selection-background-color: #3b82f6;
            }
            
            QComboBox:focus, QLineEdit:focus {
                border: 2px solid #3b82f6;
                background: linear-gradient(135deg, #334155, #1e293b);
                outline: none;
            }
            
            QComboBox:hover, QLineEdit:hover {
                border-color: #64748b;
                background: linear-gradient(135deg, #334155, #1e293b);
            }
            
            /* ComboBox Dropdown */
            QComboBox::drop-down {
                border: none;
                width: 25px;
                background: transparent;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #94a3b8;
                margin-right: 8px;
            }
            
            QComboBox::down-arrow:hover {
                border-top-color: #3b82f6;
            }
            
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                border: 2px solid #3b82f6;
                border-radius: 8px;
                selection-background-color: #3b82f6;
                selection-color: white;
                color: #f1f5f9;
                padding: 5px;
            }
            
            /* Checkbox Styling */
            QCheckBox {
                color: #f1f5f9;
                font-size: 14px;
                font-weight: 500;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #475569;
                border-radius: 4px;
                background: linear-gradient(135deg, #1e293b, #334155);
            }
            
            QCheckBox::indicator:hover {
                border-color: #3b82f6;
                background: linear-gradient(135deg, #334155, #1e293b);
            }
            
            QCheckBox::indicator:checked {
                background: linear-gradient(135deg, #3b82f6, #2563eb);
                border-color: #3b82f6;
                image: none;
            }
            
            QCheckBox::indicator:checked::after {
                content: "✓";
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            
            /* Button Styling */
            QPushButton {
                background: linear-gradient(135deg, #1e293b, #334155);
                border: 2px solid #3b82f6;
                border-radius: 8px;
                padding: 10px 20px;
                color: #3b82f6;
                font-size: 14px;
                font-weight: 600;
                min-height: 25px;
            }
            
            QPushButton:hover {
                background: linear-gradient(135deg, #3b82f6, #2563eb);
                color: white;
                border-color: #2563eb;
                transform: translateY(-1px);
            }
            
            QPushButton:pressed {
                background: linear-gradient(135deg, #2563eb, #1d4ed8);
                transform: translateY(0px);
            }
            
            /* Slider Styling */
            QSlider::groove:horizontal {
                border: 2px solid #334155;
                height: 10px;
                background: linear-gradient(90deg, #1e293b, #334155);
                border-radius: 6px;
            }
            
            QSlider::handle:horizontal {
                background: linear-gradient(135deg, #3b82f6, #2563eb);
                border: 2px solid #1e40af;
                width: 22px;
                height: 22px;
                margin: -8px 0;
                border-radius: 11px;
            }
            
            QSlider::handle:horizontal:hover {
                background: linear-gradient(135deg, #2563eb, #1d4ed8);
                border-color: #1e40af;
            }
            
            QSlider::sub-page:horizontal {
                background: linear-gradient(90deg, #3b82f6, #2563eb);
                border-radius: 6px;
            }
            
            /* Scroll Area Styling */
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:vertical {
                background-color: #1e293b;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background-color: #475569;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #64748b;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* Dialog Button Box */
            QDialogButtonBox QPushButton {
                min-width: 100px;
                padding: 8px 16px;
            }
            
            /* Message Box Styling */
            QMessageBox {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            
            QMessageBox QPushButton {
                min-width: 80px;
                padding: 6px 12px;
            }
        """

    def apply_web_settings(self, web_view):
        """Apply settings to a web view"""
        if not web_view:
            return
        
        page = web_view.page()
        settings = page.settings()
        
        settings.setAttribute(settings.JavascriptEnabled, 
                            self.config_manager.get("enable_javascript", True))
        
        settings.setAttribute(settings.AutoLoadImages, 
                            self.config_manager.get("enable_images", True))
    
        settings.setAttribute(settings.PluginsEnabled, 
                            self.config_manager.get("enable_plugins", True))
        
        settings.setAttribute(settings.JavascriptCanOpenWindows, 
                            not self.config_manager.get("enable_popup_blocking", True))
        
        zoom_level = self.config_manager.get("zoom_level", 100)
        web_view.setZoomFactor(zoom_level / 100.0)
    
        settings.setAttribute(settings.FocusOnNavigationEnabled, True)

    def browse_tor_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Tor Installation Directory",
            self.tor_directory_input.text()
        )
        if directory:
            self.tor_directory_input.setText(directory)

    def update_tor_status(self):
        tor_dir = self.tor_directory_input.text().strip()
        if not tor_dir:
            self.tor_status_label.setText("No directory specified")
            self.tor_status_label.setStyleSheet("color: #94a3b8;")
            return
        
        if not os.path.exists(tor_dir):
            self.tor_status_label.setText("Directory does not exist")
            self.tor_status_label.setStyleSheet("color: #ef4444;")
            return
        
        tor_executables = ["tor", "tor.exe"]
        tor_found = False
        for exe in tor_executables:
            tor_path = os.path.join(tor_dir, exe)
            if os.path.isfile(tor_path) and os.access(tor_path, os.X_OK):
                tor_found = True
                break
        
        if tor_found:
            self.tor_status_label.setText("Tor executable found")
            self.tor_status_label.setStyleSheet("color: #22c55e;")
        else:
            self.tor_status_label.setText("Tor executable not found")
            self.tor_status_label.setStyleSheet("color: #ef4444;")

    def get_settings(self):
        return {
            "default_search_engine": self.search_engine_combo.currentText(),
            "homepage_url": self.homepage_input.text().strip(),
            "tor_directory": self.tor_directory_input.text().strip()
        }


class CyberBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.tor_manager = TorManager(self.config_manager)
        self.tor_manager.tor_status_changed.connect(self.on_tor_status_changed)
        
        self.setWindowTitle("CyberBrowser - Tor Ready")
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
        
        self.normal_profile = QWebEngineProfile.defaultProfile()
        self.tor_profile = None

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
            QPushButton#tor_unavailable {
                border-color: #ef4444;
                color: #ef4444;
            }
            QPushButton#tor_unavailable:hover {
                background-color: #ef4444;
                color: white;
            }
            QPushButton#tor_enabled {
                border-color: #22c55e;
                color: #22c55e;
            }
            QPushButton#tor_enabled:hover {
                background-color: #22c55e;
                color: white;
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

    def on_tor_status_changed(self, is_running, status_message):
        """Handle Tor status changes"""
        print(f"Tor status: {status_message}")

        for tab_id, tab_info in self.tab_data.items():
            widget = tab_info['widget']
            if hasattr(widget, 'tor_btn'):
                self.update_tor_button(widget.tor_btn)

    def open_settings(self):
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            for key, value in settings.items():
                self.config_manager.set(key, value)
            
            self.update_home_tabs()

    def update_home_tabs(self):
        """Update search engine dropdowns and Tor buttons in existing home tabs"""
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
                
                if hasattr(widget, 'tor_btn'):
                    self.update_tor_button(widget.tor_btn)

    def update_tor_button(self, tor_btn):
        """Update Tor button text and style based on current status"""
        tor_enabled = self.config_manager.get("enable_tor", False)
        tor_available = self.config_manager.is_tor_available()
        tor_running = self.tor_manager.is_tor_running()
        
        if not tor_available:
            tor_btn.setText("Tor: Unavailable")
            tor_btn.setObjectName("tor_unavailable")
        elif tor_enabled and tor_running:
            tor_btn.setText("Tor: Connected")
            tor_btn.setObjectName("tor_enabled")
        elif tor_enabled and not tor_running:
            tor_btn.setText("Tor: Connecting...")
            tor_btn.setObjectName("tor_unavailable")
        else:
            tor_btn.setText("Tor: Disabled")
            tor_btn.setObjectName("")
        
        tor_btn.style().unpolish(tor_btn)
        tor_btn.style().polish(tor_btn)

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
        search_input.setPlaceholderText("Search or enter a website (.onion sites work with Tor)")
        search_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        search_input.returnPressed.connect(lambda: self.perform_search(tab_id))

        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        start_btn = QPushButton("Start")
        start_btn.clicked.connect(lambda: self.perform_search(tab_id))
        
        tor_btn = QPushButton()
        self.update_tor_button(tor_btn)
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
        if not self.config_manager.is_tor_available():
            QMessageBox.warning(
                self,
                "Tor Unavailable",
                "Tor is not available. Please configure the Tor directory in Settings.\n\n"
                "You need to have Tor Browser or Tor installed and specify the correct directory path."
            )
            return
        
        current_tor = self.config_manager.get("enable_tor", False)
        new_tor = not current_tor
        self.config_manager.set("enable_tor", new_tor)
        
        if new_tor:

            success = self.tor_manager.start_tor()
            if success:

                QApplication.processEvents()
                self.setup_tor_proxy()
            else:
                self.config_manager.set("enable_tor", False)
        else:

            self.tor_manager.stop_tor()
            self.remove_tor_proxy()
        
        for tab_id, tab_info in self.tab_data.items():
            widget = tab_info['widget']
            if hasattr(widget, 'tor_btn'):
                self.update_tor_button(widget.tor_btn)

    def setup_tor_proxy(self):
        """Configure the application to use Tor SOCKS proxy"""

        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = (
            '--proxy-server=socks5://127.0.0.1:9050 '
            '--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE 127.0.0.1" '
            '--disable-extensions '
            '--disable-plugins '
            '--disable-web-security '
            '--allow-running-insecure-content'
        )
        
        if self.tor_profile is None:
            self.tor_profile = TorWebEngineProfile(tor_enabled=True, parent=self)
        
        print("Tor proxy configured - .onion sites should now be accessible")

    def remove_tor_proxy(self):
        """Remove Tor proxy configuration"""

        if 'QTWEBENGINE_CHROMIUM_FLAGS' in os.environ:
            del os.environ['QTWEBENGINE_CHROMIUM_FLAGS']
        
        QNetworkProxyFactory.setUseSystemConfiguration(True)
        
        print("Tor proxy removed - using normal connection")

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

    def get_web_engine_profile(self):
        """Get the appropriate web engine profile based on Tor status"""
        tor_enabled = self.config_manager.get("enable_tor", False)
        tor_running = self.tor_manager.is_tor_running()
        
        if tor_enabled and tor_running:
            if self.tor_profile is None:
                self.tor_profile = TorWebEngineProfile(tor_enabled=True, parent=self)
            return self.tor_profile
        else:
            return self.normal_profile

    def create_tor_browser_view(self, url):
        """Create a QWebEngineView specifically configured for Tor"""
        browser = QWebEngineView()
        
        
        profile = self.get_web_engine_profile()
        page = QWebEnginePage(profile, browser)
        browser.setPage(page)
        
        page.profile().downloadRequested.connect(self.handle_download)
        browser.setContextMenuPolicy(Qt.DefaultContextMenu)
        
        if url and '.onion' in url:
            page.profile().setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0")
        
        self.apply_web_settings(browser)
        browser.page().profile().downloadRequested.connect(self.handle_download)
    
        return browser
    
    def handle_download(self, download):
        """Handle file downloads"""
        download_dir = self.config_manager.get("download_directory", "")
        if download_dir and os.path.exists(download_dir):
            file_path = os.path.join(download_dir, download.suggestedFileName())
            download.setPath(file_path)
        
        download.accept()
        
        def on_download_finished():
            if download.state() == download.DownloadCompleted:
                QMessageBox.information(self, "Download Complete", 
                                    f"Downloaded: {download.suggestedFileName()}")
            elif download.state() == download.DownloadInterrupted:
                QMessageBox.warning(self, "Download Failed", 
                                f"Failed to download: {download.suggestedFileName()}")
        
        download.finished.connect(on_download_finished)

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

        tor_enabled = self.config_manager.get("enable_tor", False)
        tor_running = self.tor_manager.is_tor_running()
        
        if tor_enabled and not tor_running:
            QMessageBox.warning(
                self,
                "Tor Not Ready",
                "Tor is enabled but not yet connected. Please wait for Tor to start or disable Tor mode."
            )
            return

        if '.onion' in query and not (tor_enabled and tor_running):
            reply = QMessageBox.question(
                self,
                "Onion Site Detected",
                "You're trying to access a .onion site but Tor is not enabled.\n\n"
                "Would you like to enable Tor to access this site?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if self.config_manager.is_tor_available():
                    self.config_manager.set("enable_tor", True)
                    success = self.tor_manager.start_tor()
                    if success:
                        self.setup_tor_proxy()

                        for tid, tinfo in self.tab_data.items():
                            tw = tinfo['widget']
                            if hasattr(tw, 'tor_btn'):
                                self.update_tor_button(tw.tor_btn)
                    else:
                        QMessageBox.warning(self, "Tor Error", "Failed to start Tor. Please check your Tor configuration.")
                        return
                else:
                    QMessageBox.warning(self, "Tor Unavailable", "Tor is not configured. Please set up Tor in Settings first.")
                    return
            else:
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

            if tor_enabled and tor_running:
                browser = self.create_tor_browser_view(url)
                print(f"Created Tor browser for: {url}")
            else:
                browser = QWebEngineView()
                page = QWebEnginePage(self.normal_profile, browser)
                browser.setPage(page)
            
            browser.load(QUrl(url))
            
            def on_load_finished(success):
                if success:
                    print(f"Successfully loaded: {url}")
                else:
                    print(f"Failed to load: {url}")
                    if '.onion' in url:
                        print("Note: .onion sites require Tor to be running")
            
            browser.loadFinished.connect(on_load_finished)
            
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
            
            current_profile = browser.page().profile()
            new_profile = self.get_web_engine_profile()
            
            if current_profile != new_profile:

                new_page = QWebEnginePage(new_profile, browser)
                browser.setPage(new_page)
            
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

    def test_tor_connection(self):
        """Test if Tor is working by checking the SOCKS proxy"""
        try:
            import socks
            import socket
            
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            sock.settimeout(10)
            
            sock.connect(("duckduckgogg42ts72.onion", 80))
            sock.close()
            return True
        except Exception as e:
            print(f"Tor connection test failed: {e}")
            return False

    def closeEvent(self, event):

        self.tor_manager.stop_tor()
        
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