from flask import Flask, render_template, request, jsonify
import config_manager
from pathlib import Path
from monitor import get_monitor

app = Flask(__name__)

# Path to log file
LOG_FILE = Path(__file__).parent / "logs" / "monitor.log"

# Start monitor on app startup
monitor = get_monitor()
monitor.start()

@app.route('/')
def index():
    """Main dashboard page."""
    config = config_manager.load_config()
    
    # Read recent logs
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r') as f:
                # Get last 100 lines
                logs = f.readlines()[-100:]
                logs.reverse()  # Most recent first
        except Exception as e:
            logs = [f"Error reading logs: {e}"]
    
    return render_template('index.html', 
                         config=config, 
                         logs=logs,
                         monitor_running=monitor.running,
                         enumerate=enumerate)

@app.route('/config')
def config_page():
    """Configuration page."""
    config = config_manager.load_config()
    return render_template('config.html', config=config, enumerate=enumerate)

@app.route('/api/servers', methods=['POST'])
def add_server():
    """Add a new server."""
    data = request.json
    success = config_manager.add_server(
        data.get('name'),
        data.get('url'),
        data.get('api_key'),
        data.get('web_ui')
    )
    if success:
        monitor.reload_config()
    return jsonify({'success': success})

@app.route('/api/servers/<int:index>', methods=['PUT'])
def update_server(index):
    """Update an existing server."""
    data = request.json
    success = config_manager.update_server(
        index,
        data.get('name'),
        data.get('url'),
        data.get('api_key'),
        data.get('web_ui')
    )
    if success:
        monitor.reload_config()
    return jsonify({'success': success})

@app.route('/api/servers/<int:index>', methods=['DELETE'])
def delete_server(index):
    """Delete a server."""
    success = config_manager.remove_server(index)
    if success:
        monitor.reload_config()
    return jsonify({'success': success})

@app.route('/api/discord', methods=['POST'])
def update_discord():
    """Update Discord webhook URL."""
    data = request.json
    success = config_manager.update_discord_webhook(data.get('webhook_url'))
    if success:
        monitor.reload_config()
    return jsonify({'success': success})

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update monitoring settings."""
    data = request.json
    success = config_manager.update_settings(
        check_interval=data.get('check_interval'),
        pause_threshold=data.get('pause_threshold'),
        resume_threshold=data.get('resume_threshold'),
        hourly_update_enabled=data.get('hourly_update_enabled')
    )
    if success:
        monitor.reload_config()
    return jsonify({'success': success})

@app.route('/api/logs')
def get_logs():
    """Get logs via API."""
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r') as f:
                logs = f.readlines()[-100:]
                logs.reverse()
        except Exception as e:
            logs = [f"Error reading logs: {e}"]
    
    return jsonify({'logs': logs})

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Clear log file."""
    try:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        LOG_FILE.parent.mkdir(exist_ok=True)
        LOG_FILE.touch()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/monitor/start', methods=['POST'])
def start_monitor():
    """Start the monitoring service."""
    success = monitor.start()
    return jsonify({'success': success, 'running': monitor.running})

@app.route('/api/monitor/stop', methods=['POST'])
def stop_monitor():
    """Stop the monitoring service."""
    success = monitor.stop()
    return jsonify({'success': success, 'running': monitor.running})

@app.route('/api/monitor/status')
def monitor_status():
    """Get monitor status."""
    return jsonify({'running': monitor.running})

@app.route('/api/stats')
def get_stats():
    """Get aggregated stats from all servers."""
    try:
        config = config_manager.load_config()
        stats = monitor.get_aggregated_stats(config.get('servers', []))
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Ensure log directory exists
    LOG_FILE.parent.mkdir(exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.touch()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
