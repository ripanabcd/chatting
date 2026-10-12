import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret_chat_key_123')

# Initialize SocketIO. eventlet is used for high-performance async concurrency.
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Track connected users safely in memory
connected_users = {}

@app.route('/')
def index():
    """Renders the main chat interface."""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {connected_users}")

@socketio.on('register_user')
def handle_user_registration(data):
    """Binds a username to the unique session ID."""
    username = data.get('username', 'Anonymous').strip()
    if not username:
        username = "Anonymous"
        
    connected_users[connected_users] = username
    print(f"User registered: {username}")
    
    # Notify everyone that a new user has arrived
    emit('status_message', {'msg': f"🚀 {username} joined the room!"}, broadcast=True)
    emit('update_user_count', {'count': len(connected_users)}, broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    """Receives a message from a user and broadcasts it to everyone."""
    username = data.get('username', 'Anonymous')
    message = data.get('message', '').strip()
    
    if message:
        emit('receive_message', {
            'username': username,
            'message': message
        }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    """Cleans up the user list when someone leaves."""
    if connected_users in connected_users:
        username = connected_users.pop(connected_users)
        emit('status_message', {'msg': f"👋 {username} left the room."}, broadcast=True)
        emit('update_user_count', {'count': len(connected_users)}, broadcast=True)

if __name__ == '__main__':
    # Fallback configuration for local testing
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
