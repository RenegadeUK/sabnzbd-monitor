import requests
import time
import threading
import logging
from pathlib import Path
from datetime import datetime
import config_manager

# Set up logging
LOG_DIR = Path("/logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "monitor.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Track time for hourly updates
last_status_update = time.time()

class SABnzbdMonitor:
    def __init__(self):
        self.config = config_manager.load_config()
        self.running = False
        self.monitor_thread = None
    
    def reload_config(self):
        """Reload configuration from file."""
        self.config = config_manager.load_config()
        logger.info("Configuration reloaded")
    
    def send_discord_alert(self, message):
        """Send alerts to Discord."""
        webhook_url = self.config.get('discord_webhook_url')
        if not webhook_url:
            logger.warning("Discord webhook URL not configured")
            return
        
        payload = {
            "content": message,
            "username": "SABnzbd Alert Bot"
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("Discord alert sent successfully")
            else:
                logger.error(f"Failed to send alert to Discord. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error posting to Discord: {e}")
    
    def get_history_length(self, server):
        """Get the history length for a specific server."""
        try:
            url = f"{server['url']}?mode=history&start=0&limit=100&apikey={server['api_key']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            history_length = len(data['history']['slots'])
            logger.info(f"{server['name']} history length is: {history_length}")
            return history_length
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 403:
                logger.error(f"Access forbidden for {server['name']}: Check API key or permissions")
            else:
                logger.error(f"HTTP error for {server['name']}: {http_err}")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error for {server['name']}: {req_err}")
        except ValueError as val_err:
            logger.error(f"Response parsing error for {server['name']}: {val_err}")
        except Exception as e:
            logger.error(f"Unexpected error for {server['name']}: {e}")
        
        return -1
    
    def get_queue_data_left(self, server):
        """Get the download queue size in GB for a specific server."""
        try:
            url = f"{server['url']}?mode=queue&apikey={server['api_key']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            queue_data_left_mb = float(data['queue']['mbleft'])
            queue_data_left_gb = queue_data_left_mb / 1024
            logger.info(f"{server['name']} download queue data left: {queue_data_left_gb:.2f} GB")
            return queue_data_left_gb
        except Exception as e:
            logger.error(f"Error fetching queue data for {server['name']}: {e}")
            return -1    
    def get_queue_count(self, server):
        """Get the number of items in download queue."""
        try:
            url = f"{server['url']}?mode=queue&apikey={server['api_key']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return len(data['queue']['slots'])
        except Exception as e:
            logger.error(f"Error fetching queue count for {server['name']}: {e}")
            return 0
    
    def get_warnings_count(self, server):
        """Get the number of warnings from history."""
        try:
            url = f"{server['url']}?mode=history&start=0&limit=100&apikey={server['api_key']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            warnings = 0
            for item in data['history']['slots']:
                if item.get('status') == 'Failed' or item.get('fail_message'):
                    warnings += 1
            return warnings
        except Exception as e:
            logger.error(f"Error fetching warnings for {server['name']}: {e}")
            return 0
    
    def get_aggregated_stats(self, servers):
        """Get aggregated stats from all servers."""
        total_queue_count = 0
        total_history_count = 0
        total_warnings = 0
        total_queue_data_gb = 0.0
        
        for server in servers:
            total_queue_count += self.get_queue_count(server)
            history_length = self.get_history_length(server)
            if history_length != -1:
                total_history_count += history_length
            total_warnings += self.get_warnings_count(server)
            
            queue_data = self.get_queue_data_left(server)
            if queue_data != -1:
                total_queue_data_gb += queue_data
        
        return {
            'queue_count': total_queue_count,
            'history_count': total_history_count,
            'warnings_count': total_warnings,
            'queue_data': f'{total_queue_data_gb:.1f} GB'
        }    
    def pause_sabnzbd(self, server):
        """Pause SABnzbd for a specific server."""
        if not server.get("paused", False):
            logger.info(f'Pausing {server["name"]}...')
            try:
                url = f"{server['url']}?mode=pause&apikey={server['api_key']}"
                requests.get(url, timeout=10)
                
                message = (
                    f"{server['name']} has been paused because the history queue "
                    f"reached {self.config['pause_threshold']} or more items.\n"
                    f"[Open {server['name']} UI]({server['web_ui']})"
                )
                self.send_discord_alert(message)
                
                # Update server status in config
                self.update_server_paused_status(server['name'], True)
                
            except Exception as e:
                logger.error(f"Error pausing {server['name']}: {e}")
    
    def resume_sabnzbd(self, server):
        """Resume SABnzbd for a specific server."""
        if server.get("paused", False):
            logger.info(f'Resuming {server["name"]}...')
            try:
                url = f"{server['url']}?mode=resume&apikey={server['api_key']}"
                requests.get(url, timeout=10)
                
                message = (
                    f"{server['name']} has been resumed because the history queue "
                    f"is now {self.config['resume_threshold']} or fewer items.\n"
                    f"[Open {server['name']} UI]({server['web_ui']})"
                )
                self.send_discord_alert(message)
                
                # Update server status in config
                self.update_server_paused_status(server['name'], False)
                
            except Exception as e:
                logger.error(f"Error resuming {server['name']}: {e}")
    
    def update_server_paused_status(self, server_name, paused):
        """Update the paused status of a server in the config."""
        config = config_manager.load_config()
        for server in config['servers']:
            if server['name'] == server_name:
                server['paused'] = paused
        config_manager.save_config(config)
        self.config = config
    
    def monitor_servers(self):
        """Main monitoring loop."""
        global last_status_update
        
        logger.info("SABnzbd Monitor started")
        
        while self.running:
            try:
                # Reload config in case it changed
                self.reload_config()
                
                if not self.config.get('servers'):
                    logger.warning("No servers configured, waiting...")
                    time.sleep(self.config.get('check_interval', 60))
                    continue
                
                for server in self.config['servers']:
                    # Monitor history length and pause/resume as needed
                    history_length = self.get_history_length(server)
                    
                    if history_length == -1:
                        logger.warning(f"Error fetching history length for {server['name']}, will retry")
                    elif history_length >= self.config['pause_threshold']:
                        self.pause_sabnzbd(server)
                    elif history_length <= self.config['resume_threshold']:
                        self.resume_sabnzbd(server)
                
                # Post an hourly update to Discord with the amount of data left
                if self.config.get('hourly_update_enabled', True):
                    if time.time() - last_status_update >= 3600:
                        queue_status_message = "📊 Hourly Download Queue Update:\n\n"
                        
                        for server in self.config['servers']:
                            queue_data_left_gb = self.get_queue_data_left(server)
                            if queue_data_left_gb >= 0:
                                queue_status_message += (
                                    f"**{server['name']}**: {queue_data_left_gb:.2f} GB remaining\n"
                                    f"[Open {server['name']} UI]({server['web_ui']})\n\n"
                                )
                        
                        self.send_discord_alert(queue_status_message)
                        last_status_update = time.time()
                
                # Wait before checking again
                time.sleep(self.config.get('check_interval', 60))
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
        
        logger.info("SABnzbd Monitor stopped")
    
    def start(self):
        """Start the monitor in a separate thread."""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self.monitor_servers, daemon=True)
            self.monitor_thread.start()
            logger.info("Monitor thread started")
            return True
        return False
    
    def stop(self):
        """Stop the monitor."""
        if self.running:
            self.running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            logger.info("Monitor stopped")
            return True
        return False

# Global monitor instance
_monitor_instance = None

def get_monitor():
    """Get the global monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SABnzbdMonitor()
    return _monitor_instance

if __name__ == '__main__':
    # Run standalone
    monitor = SABnzbdMonitor()
    monitor.running = True
    
    try:
        monitor.monitor_servers()
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
        monitor.stop()
