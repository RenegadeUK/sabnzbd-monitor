# SABnzbd Monitor

A web-based monitoring and automation tool for SABnzbd servers with Discord notifications.

## Features

- 🖥️ **Web UI** - Modern, responsive interface to manage your SABnzbd servers
- 📊 **Real-time Monitoring** - Track download queues and history across multiple servers
- ⚙️ **Auto Pause/Resume** - Automatically pause servers when history reaches threshold
- 📢 **Discord Notifications** - Get alerts via Discord webhooks
- 📝 **Live Logs** - View monitoring logs in real-time
- 💾 **Persistent Config** - All settings stored in `/config` directory

## Installation

### 🐳 Docker (Recommended)

#### Using Docker Compose

1. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/sabnzbd-monitor.git
   cd sabnzbd-monitor
   ```

2. Create the required directories:
   ```bash
   mkdir -p config logs
   ```

3. Start the container:
   ```bash
   docker-compose up -d
   ```

The web UI will be available at `http://localhost:5000`

#### Using Docker CLI

Pull and run the latest image:
```bash
docker run -d \
  --name sabnzbd-monitor \
  -p 5000:5000 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  ghcr.io/YOUR_USERNAME/sabnzbd-monitor:latest
```

#### Building Locally

Build your own image:
```bash
docker build -t sabnzbd-monitor .
docker run -d -p 5000:5000 -v $(pwd)/config:/app/config -v $(pwd)/logs:/app/logs sabnzbd-monitor
```

### 📦 Manual Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

The web UI will be available at `http://localhost:5000`

Alternatively, run the monitor standalone (no web UI):
```bash
python monitor.py
```

### Configuration

1. Open `http://localhost:5000/config` in your browser
2. Add your SABnzbd servers:
   - Server Name
   - API URL (e.g., `http://192.168.1.100:8080/sabnzbd/api`)
   - API Key
   - Web UI URL (e.g., `http://192.168.1.100:8080`)

3. Configure Discord webhook URL for notifications

4. Adjust monitoring settings:
   - **Check Interval**: How often to check servers (in seconds)
   - **Pause Threshold**: Number of history items to trigger pause
   - **Resume Threshold**: Number of history items to trigger resume
   - **Hourly Updates**: Enable/disable hourly queue status updates

### How It Works

The monitor checks each configured SABnzbd server at regular intervals:

- If a server's history queue reaches the **pause threshold**, it will be automatically paused
- When the history drops to the **resume threshold** or below, it will be automatically resumed
- Discord notifications are sent when servers are paused or resumed
- Optional hourly updates show remaining download queue size for all servers

### Configuration File

All settings are stored in `/config/config.json`:

```json
{
  "servers": [
    {
      "name": "SABnzbd Server 1",
      "url": "http://192.168.1.100:8080/sabnzbd/api",
      "api_key": "your_api_key",
      "paused": false,
      "web_ui": "http://192.168.1.100:8080"
    }
  ],
  "discord_webhook_url": "your_webhook_url",
  "check_interval": 60,
  "pause_threshold": 30,
  "resume_threshold": 5,
  "hourly_update_enabled": true
}
```

### Logs

Logs are stored in `/logs/monitor.log` and can be viewed in real-time through the web UI dashboard.

## Project Structure

```
sabnzbd-monitor/
├── app.py                      # Flask web application
├── monitor.py                  # Monitoring logic
├── config_manager.py           # Configuration management
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose configuration
├── .dockerignore              # Docker ignore file
├── .github/
│   └── workflows/
│       └── docker-build.yml   # GitHub Actions CI/CD
├── config/                    # Configuration storage
│   └── config.json            # Main configuration file
├── logs/                      # Log files
│   └── monitor.log            # Application logs
├── templates/                 # HTML templates
│   ├── index.html             # Dashboard
│   └── config.html            # Configuration page
└── static/                    # Static assets
    └── css/
        └── style.css          # Styles
```

## 🚀 GitHub Container Registry

This project automatically builds and publishes Docker images to GitHub Container Registry (GHCR) when you push to the main branch or create a release tag.

### Setup Automatic Builds

1. Push your code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/sabnzbd-monitor.git
   git push -u origin main
   ```

2. The GitHub Action will automatically build and push the image to:
   ```
   ghcr.io/YOUR_USERNAME/sabnzbd-monitor:latest
   ```

3. Make the package public:
   - Go to your repository on GitHub
   - Click on "Packages" in the sidebar
   - Select your package
   - Click "Package settings"
   - Scroll down and click "Change visibility" → "Public"

### Using Pre-built Images

Pull the latest image:
```bash
docker pull ghcr.io/YOUR_USERNAME/sabnzbd-monitor:latest
```

### Versioned Releases

Create a tagged release for versioned images:
```bash
git tag v1.0.0
git push origin v1.0.0
```

This will build images tagged as:
- `ghcr.io/YOUR_USERNAME/sabnzbd-monitor:v1.0.0`
- `ghcr.io/YOUR_USERNAME/sabnzbd-monitor:1.0.0`
- `ghcr.io/YOUR_USERNAME/sabnzbd-monitor:1.0`
- `ghcr.io/YOUR_USERNAME/sabnzbd-monitor:1`
- `ghcr.io/YOUR_USERNAME/sabnzbd-monitor:latest`

## Running as a Service

### Using Docker Compose (Recommended)

Already configured! Just use:
```bash
docker-compose up -d
```

Manage the service:
```bash
# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Update to latest image
docker-compose pull
docker-compose up -d
```

### Using systemd (Linux - Non-Docker)

Create `/etc/systemd/system/sabnzbd-monitor.service`:

```ini
[Unit]
Description=SABnzbd Monitor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/sabnzbd-monitor
ExecStart=/usr/bin/python3 /path/to/sabnzbd-monitor/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable sabnzbd-monitor
sudo systemctl start sabnzbd-monitor
```

## Security Notes

- The web UI runs without authentication by default
- Consider placing it behind a reverse proxy with authentication
- Keep your API keys and Discord webhook URLs secure
- The `/config/config.json` file contains sensitive information

## Troubleshooting

**Monitor not starting:**
- Check logs at `/logs/monitor.log`
- Verify server URLs and API keys are correct
- Ensure network connectivity to SABnzbd servers

**Discord notifications not working:**
- Verify webhook URL is correct
- Check Discord webhook has proper permissions
- Review logs for error messages

**Web UI not accessible:**
- Check if port 5000 is available
- Verify firewall settings
- Try accessing via `http://127.0.0.1:5000` or `http://localhost:5000`

## License

MIT License - feel free to modify and use as needed.
