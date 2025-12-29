import json
import os
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "servers": [],
    "discord_webhook_url": "",
    "check_interval": 60,
    "pause_threshold": 30,
    "resume_threshold": 5,
    "hourly_update_enabled": True
}

def ensure_config_dir():
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)

def load_config():
    """Load configuration from file, create default if doesn't exist."""
    ensure_config_dir()
    
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Ensure all required keys exist
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file."""
    ensure_config_dir()
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def add_server(name, url, api_key, web_ui):
    """Add a new server to configuration."""
    config = load_config()
    
    server = {
        "name": name,
        "url": url,
        "api_key": api_key,
        "paused": False,
        "web_ui": web_ui
    }
    
    config["servers"].append(server)
    return save_config(config)

def remove_server(index):
    """Remove a server by index."""
    config = load_config()
    
    if 0 <= index < len(config["servers"]):
        config["servers"].pop(index)
        return save_config(config)
    
    return False

def update_server(index, name, url, api_key, web_ui):
    """Update a server by index."""
    config = load_config()
    
    if 0 <= index < len(config["servers"]):
        config["servers"][index].update({
            "name": name,
            "url": url,
            "api_key": api_key,
            "web_ui": web_ui
        })
        return save_config(config)
    
    return False

def update_discord_webhook(webhook_url):
    """Update Discord webhook URL."""
    config = load_config()
    config["discord_webhook_url"] = webhook_url
    return save_config(config)

def update_settings(check_interval=None, pause_threshold=None, resume_threshold=None, hourly_update_enabled=None):
    """Update monitoring settings."""
    config = load_config()
    
    if check_interval is not None:
        config["check_interval"] = int(check_interval)
    if pause_threshold is not None:
        config["pause_threshold"] = int(pause_threshold)
    if resume_threshold is not None:
        config["resume_threshold"] = int(resume_threshold)
    if hourly_update_enabled is not None:
        config["hourly_update_enabled"] = bool(hourly_update_enabled)
    
    return save_config(config)
