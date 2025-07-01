# CyberBrowser

A privacy-focused Python web browser with integrated Tor support for secure and anonymous browsing.

![CyberBrowser](https://github.com/user-attachments/assets/f51f0848-04c2-4c81-9f97-767947f38e60)

## 🚀 Features

### Core Browser Features
- **Multi-tab browsing** with intuitive tab management
- **Customizable search engines** (Google, DuckDuckGo, Bing, Yahoo, Yandex, Searx, Startpage)
- **Dark theme UI** with modern cyberpunk aesthetics
- **Zoom control** (50% - 200%)
- **Download management** with custom directory selection
- **Homepage customization**

### Privacy & Security
- **Tor integration** for anonymous browsing (.onion sites supported)
- **JavaScript toggle** for enhanced security
- **Cookie management** with privacy controls
- **Popup blocking** built-in
- **Custom user agent** support
- **Clear data on exit** option
- **No persistent cookies mode** when using Tor

### Advanced Features
- **Onion search engines** (DuckDuckGo Onion, Ahmia)
- **Spell checking** support
- **Image loading toggle** for faster browsing
- **Plugin management**
- **Notification controls**
- **Cache and history management**

## 📋 Requirements

### System Requirements
- Python 3.7 or higher
- PyQt5
- Operating System: Windows, macOS, or Linux

### Dependencies
```
PyQt5
PyQtWebEngine
```

### For Tor Functionality
- Tor Browser Bundle or standalone Tor installation

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/CyberNilsen/CyberBrowser.git
cd CyberBrowser
```

### 2. Install Python Dependencies
```bash
pip install PyQt5 PyQtWebEngine
```

### 3. Install Tor (Optional but Recommended)
#### Windows:
1. Download Tor Browser from [torproject.org](https://www.torproject.org/)
2. Extract to a folder (e.g., `C:\Tor Browser\`)
3. Note the path to the `Tor` folder containing `tor.exe`

#### Linux:
```bash
sudo apt-get install tor
# Or download Tor Browser Bundle
```

#### macOS:
```bash
brew install tor
# Or download Tor Browser Bundle
```

## 🚀 Usage

### Running CyberBrowser
```bash
python main.py
```

### Setting Up Tor
1. Launch CyberBrowser
2. Open Settings (⚙️ icon or Ctrl+,)
3. Go to the "Tor" tab
4. Browse and select your Tor installation directory
5. The status will show "✓ Tor executable found" when configured correctly

### Tor Browsing
- The Tor toggle will appear in the browser interface once Tor is configured
- Click the Tor toggle to enable/disable anonymous browsing
- When enabled, all traffic routes through the Tor network
- Access .onion sites directly when Tor is active

## ⚙️ Configuration

CyberBrowser stores settings in `cyberbrowser_config.json`. Key configurations include:

### Search Engines
- Default: Google
- Available: Google, DuckDuckGo, Bing, Yahoo, Yandex, Searx, Startpage
- Tor-friendly: DuckDuckGo Onion, Ahmia Onion Search

### Privacy Settings
- JavaScript enable/disable
- Cookie management
- Image loading control
- Popup blocking
- Custom user agent strings

### Tor Configuration
- Tor directory path
- Automatic Tor process management
- SOCKS5 proxy on port 9050
- Control port on 9051

## 🔧 Settings Overview

### General Tab
- **Search Engine**: Choose your default search provider
- **Homepage**: Set custom homepage URL
- **Downloads**: Configure download directory
- **Display**: Adjust zoom levels (50-200%)

### Privacy & Security Tab
- **Cookies**: Enable/disable cookie storage
- **JavaScript**: Toggle JavaScript execution
- **Images**: Control image loading
- **Plugins**: Manage browser plugins
- **Popups**: Block unwanted popups
- **Notifications**: Control web notifications
- **Data Clearing**: Clear data on browser exit
- **User Agent**: Set custom user agent strings

### Advanced Tab
- **Spell Check**: Enable/disable spell checking
- **Cache Management**: Clear browser cache
- **Cookie Management**: Clear stored cookies
- **History Management**: Clear browsing history

### Tor Tab
- **Tor Directory**: Path to Tor installation
- **Status Display**: Real-time Tor connectivity status
- **Setup Instructions**: Step-by-step Tor configuration guide

## 🛡️ Security Features

### Normal Browsing Mode
- Standard web engine with configurable privacy settings
- Customizable user agent
- Optional cookie and JavaScript blocking

### Tor Mode
- All traffic routed through Tor network
- Enhanced privacy user agent
- Memory-only cache and no persistent cookies
- Access to .onion hidden services
- Automatic proxy configuration

## 🎨 Interface

### Modern Dark Theme
- Cyberpunk-inspired design
- Gradient backgrounds and modern UI elements
- Intuitive tab management
- Responsive layout with proper spacing

### Tab Management
- Add/remove tabs dynamically
- Independent browsing contexts
- Tab-specific Tor toggle (when available)

## Known Issues
- Some settings dont get applied correctly like for example zoom setting

## 🐛 Troubleshooting

### Tor Not Working
1. Verify Tor installation path in Settings → Tor tab
2. Ensure Tor executable has proper permissions
3. Check if ports 9050/9051 are available
4. Try restarting CyberBrowser after configuration

### JavaScript Issues
- Some sites may not work with JavaScript disabled
- Toggle JavaScript in Privacy & Security settings
- Refresh the page after changing settings

### Performance Issues
- Disable image loading for faster browsing
- Clear cache regularly
- Adjust zoom level for better performance

## 📁 Project Structure

```
CyberBrowser/
├── main.py                 # Main application file
├── assets/
│   └── CyberBrowser.png   # Application icon
├── cyberbrowser_config.json # Configuration file (auto-generated)
├── README.md              # This file
├── .gitignore            # Git ignore rules
└── .gitattributes        # Git attributes
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is open source. Please check the repository for license details.

## 👨‍💻 Author

**Andreas Nilsen (CyberNilsen)**
- GitHub: [@CyberNilsen](https://github.com/CyberNilsen)

## ⚠️ Disclaimer

CyberBrowser is designed for educational and privacy purposes. Users are responsible for complying with their local laws and regulations when using Tor or accessing content through anonymous networks. The developers are not responsible for any misuse of this software.

## 🙏 Acknowledgments

- The Tor Project for providing the Tor network infrastructure
- Qt/PyQt5 developers for the excellent GUI framework
- The Python community for ongoing support and development

---

*Built with ❤️ for privacy and security enthusiasts*
