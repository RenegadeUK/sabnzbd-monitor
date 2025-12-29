from flask import Flask, render_template, request, jsonify, redirect, url_for
import config_manager
import os
from pathlib import Path

app = Flask(__name__)

# Path to log file
LOG_FILE = Path(__file__).parent / "logs" / "monitor.log"

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
    return jsonify({'success': success})

@app.route('/api/servers/<int:index>', methods=['DELETE'])
def delete_server(index):
    """Delete a server."""
    success = config_manager.remove_server(index)
    return jsonify({'success': success})

@app.route('/api/discord', methods=['POST'])
def update_discord():
    """Update Discord webhook URL."""
    data = request.json
    success = config_manager.update_discord_webhook(data.get('webhook_url'))
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

if __name__ == '__main__':
    # Ensure log directory exists
    LOG_FILE.parent.mkdir(exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.touch()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
