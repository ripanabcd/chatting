import os
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret_chat_key_123')

# Force eventlet mode so Render can handle long-polling WebSockets
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

connected_users = {}

# Simple, single HTML page string inside Python code
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-Time Chat</title>
    <script src="https://tailwindcss.com"></script>
    <script src="https://cloudflare.com"></script>
</head>
<body class="bg-gray-100 h-screen flex flex-col justify-center items-center font-sans">
    <div id="login-overlay" class="fixed inset-0 bg-gray-900 bg-opacity-70 flex justify-center items-center z-50 p-4">
        <div class="bg-white rounded-lg p-6 shadow-2xl w-full max-w-sm text-center">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">Enter Chatroom</h2>
            <input type="text" id="username-input" placeholder="Type your username..." class="w-full px-4 py-2 border rounded-lg mb-4 focus:outline-none">
            <button id="join-btn" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg">Join Chat</button>
        </div>
    </div>
    <div class="w-full max-w-2xl h-[85vh] bg-white rounded-xl shadow-lg flex flex-col overflow-hidden m-4 hidden" id="chat-container">
        <div class="bg-blue-600 px-6 py-4 flex justify-between items-center text-white">
            <div>
                <h1 class="text-xl font-bold">Global Chatroom</h1>
                <p class="text-xs opacity-80" id="user-count">0 users active</p>
            </div>
            </span>
        </div>
        <div class="flex-1 p-6 overflow-y-auto space-y-4 bg-gray-50" id="message-board"></div>
        <form id="chat-form" class="p-4 border-t bg-white flex items-center space-x-3">
            <input type="text" id="message-input" autocomplete="off" placeholder="Write your message..." class="flex-1 px-4 py-3 border rounded-lg focus:outline-none">
            <button type="submit" class="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold">Send</button>
        </form>
    </div>
    <script>
        const socket = io();
        let myUsername = "";
        const loginOverlay = document.getElementById('login-overlay');
        const chatContainer = document.getElementById('chat-container');
        const usernameInput = document.getElementById('username-input');
        const joinBtn = document.getElementById('join-btn');
        const chatForm = document.getElementById('chat-form');
        const messageInput = document.getElementById('message-input');
        const messageBoard = document.getElementById('message-board');
        const userCountText = document.getElementById('user-count');
        const identityBadge = document.getElementById('display-identity');

        joinBtn.addEventListener('click', () => {
            myUsername = usernameInput.value.trim();
            if (!myUsername) return alert("Please type a username.");
            loginOverlay.classList.add('hidden');
            chatContainer.classList.remove('hidden');
            identityBadge.textContent = myUsername;
            socket.emit('register_user', { username: myUsername });
            messageInput.focus();
        });

        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const text = messageInput.value.trim();
            if (!text) return;
            socket.emit('send_message', { username: myUsername, message: text });
            messageInput.value = '';
        });

        socket.on('receive_message', (data) => {
            const msgRow = document.createElement('div');
            msgRow.className = data.username === myUsername ? "flex flex-col items-end" : "flex flex-col items-start";
            msgRow.innerHTML = `
                <span class="text-xs text-gray-500">${data.username}</span>
                <div class="${data.username === myUsername ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'} rounded-lg px-4 py-2 max-w-md break-words">${data.message}</div>
            `;
            messageBoard.appendChild(msgRow);
            messageBoard.scrollTop = messageBoard.scrollHeight;
        });

        socket.on('status_message', (data) => {
            const statusDiv = document.createElement('div');
            statusDiv.className = "text-center text-xs text-gray-400 italic my-2";
            statusDiv.textContent = data.msg;
            messageBoard.appendChild(statusDiv);
            messageBoard.scrollTop = messageBoard.scrollHeight;
        });

        socket.on('update_user_count', (data) => {
            userCountText.textContent = `${data.count} users active`;
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Render the HTML template directly from our string above
    return render_template_string(HTML_TEMPLATE)

@socketio.on('register_user')
def handle_user_registration(data):
    username = data.get('username', 'Anonymous').strip() or "Anonymous"
    connected_users[connected_users] = username
    emit('status_message', {'msg': f"🚀 {username} joined!"}, broadcast=True)
    emit('update_user_count', {'count': len(connected_users)}, broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    username = data.get('username', 'Anonymous')
    message = data.get('message', '').strip()
    if message:
        emit('receive_message', {'username': username, 'message': message}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if connected_users in connected_users:
        username = connected_users.pop(connected_users)
        emit('status_message', {'msg': f"👋 {username} left."}, broadcast=True)
        emit('update_user_count', {'count': len(connected_users)}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
