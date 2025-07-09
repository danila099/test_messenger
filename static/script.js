document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const messagesDiv = document.getElementById('messages');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const fileForm = document.getElementById('file-form');
    const fileInput = document.getElementById('file-input');
    const avatarForm = document.getElementById('avatar-form');
    const avatarInput = document.getElementById('avatar-input');
    const avatarBtn = document.getElementById('avatar-btn');
    const myAvatar = document.getElementById('my-avatar');

    function addMessage(msg) {
        const div = document.createElement('div');
        div.className = 'message';
        let avatarUrl = msg.avatar ? ('/avatars/' + msg.avatar) : '/static/default-avatar.png';
        let content = `<img src="${avatarUrl}" class="avatar" style="width:32px;height:32px;border-radius:50%;object-fit:cover;vertical-align:middle;margin-right:6px;">`;
        content += `<span class=\"user\">${msg.user}</span>:`;
        if (msg.type === 'text') {
            content += ` <span class=\"text\">${msg.text}</span>`;
        } else if (msg.type === 'file') {
            const ext = msg.filename.split('.').pop().toLowerCase();
            if (["jpg","jpeg","png","gif","bmp","webp"].includes(ext)) {
                content += ` <a href=\"/uploads/${msg.filename}\" target=\"_blank\"><img src=\"/uploads/${msg.filename}\" style=\"max-width:120px;max-height:120px;vertical-align:middle;\"></a>`;
            } else if (["mp4","webm","ogg"].includes(ext)) {
                content += ` <video src=\"/uploads/${msg.filename}\" controls style=\"max-width:180px;max-height:120px;vertical-align:middle;\"></video>`;
            } else {
                content += ` <a href=\"/uploads/${msg.filename}\" target=\"_blank\">${msg.filename}</a>`;
            }
        }
        content += ` <span class=\"time\">${msg.time}</span>`;
        div.innerHTML = content;
        messagesDiv.appendChild(div);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    socket.on('connect', function() {
        socket.emit('join');
    });

    socket.on('init_messages', function(msgs) {
        messagesDiv.innerHTML = '';
        msgs.forEach(addMessage);
    });

    socket.on('message', function(msg) {
        addMessage(msg);
    });

    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const text = messageInput.value.trim();
        if (text) {
            socket.emit('send_message', {text});
            messageInput.value = '';
        }
    });

    fileForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const file = fileInput.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        fetch('/upload', {
            method: 'POST',
            body: formData
        }).then(res => res.json()).then(data => {
            if (data.success) {
                fileInput.value = '';
            } else {
                alert('Ошибка загрузки файла');
            }
        });
    });

    avatarBtn.addEventListener('click', function(e) {
        e.preventDefault();
        avatarInput.click();
    });

    avatarInput.addEventListener('change', function() {
        const file = avatarInput.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('avatar', file);
        fetch('/avatar_upload', {
            method: 'POST',
            body: formData
        }).then(res => res.json()).then(data => {
            if (data.success) {
                myAvatar.src = '/avatars/' + data.filename + '?t=' + Date.now();
            } else {
                alert('Ошибка загрузки аватара: ' + (data.error || ''));
            }
        });
    });

    // Попытка загрузить свой аватар при входе
    fetch('/avatars/' + getUsernameFromHeader() + '.jpg')
        .then(r => { if (r.ok) myAvatar.src = r.url; });
    fetch('/avatars/' + getUsernameFromHeader() + '.png')
        .then(r => { if (r.ok) myAvatar.src = r.url; });
    fetch('/avatars/' + getUsernameFromHeader() + '.jpeg')
        .then(r => { if (r.ok) myAvatar.src = r.url; });
    fetch('/avatars/' + getUsernameFromHeader() + '.webp')
        .then(r => { if (r.ok) myAvatar.src = r.url; });
    fetch('/avatars/' + getUsernameFromHeader() + '.gif')
        .then(r => { if (r.ok) myAvatar.src = r.url; });

    function getUsernameFromHeader() {
        const span = document.querySelector('.chat-header span');
        if (!span) return '';
        return span.textContent.replace('Вы: ', '').trim();
    }
}); 