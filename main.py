import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QTabBar, QStackedLayout,
    QToolButton, QStyle, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap


class CyberBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberBrowser")
        self.resize(1400, 900)
        self.setWindowIcon(QIcon("assets/CyberBrowser.png"))

        self.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
                color: #e2e8f0;
                font-family: 'Segoe UI', sans-serif;
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
            QTabBar {
                background-color: #0f172a;
                border: none;
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
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(15, 10, 15, 10)

        self.tab_bar = QTabBar()
        self.tab_bar.addTab("Home")
        self.tab_bar.addTab("+")
        self.tab_bar.setMovable(True)
        self.tab_bar.setTabsClosable(False)
        self.tab_bar.currentChanged.connect(self.handle_tab_change)
        top_bar.addWidget(self.tab_bar)

        top_bar.addStretch()

        settings_button = QToolButton()
        settings_icon = self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        settings_button.setIcon(settings_icon)
        settings_button.setIconSize(QSize(24, 24))
        settings_button.setToolTip("Settings")
        top_bar.addWidget(settings_button)

        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setSpacing(15)

        logo_label = QLabel()
        logo_pixmap = QPixmap("assets/CyberBrowser.png").scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)

        title = QLabel("CyberBrowser")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Fast. Anonymous. Tor-Ready.")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search or enter a website")
        self.search_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        start_btn = QPushButton("Start")
        tor_btn = QPushButton("Enable Tor")
        buttons_layout.addWidget(start_btn)
        buttons_layout.addWidget(tor_btn)

        content_layout.addWidget(logo_label)
        content_layout.addWidget(title)
        content_layout.addWidget(subtitle)
        content_layout.addWidget(self.search_input)
        content_layout.addLayout(buttons_layout)

        stack = QStackedLayout()
        container = QWidget()
        container.setLayout(content_layout)
        stack.addWidget(container)

        main_layout.addLayout(top_bar)
        main_layout.addLayout(stack)
        self.setCentralWidget(main_widget)

    def handle_tab_change(self, index):
        if self.tab_bar.tabText(index) == "+":
            new_index = self.tab_bar.count() - 1
            self.tab_bar.insertTab(new_index, f"Tab {new_index}")
            self.tab_bar.setCurrentIndex(new_index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CyberBrowser()
    window.show()
    sys.exit(app.exec_())
