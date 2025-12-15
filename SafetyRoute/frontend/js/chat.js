// js/chat.js

const chatWidget = document.getElementById('chat-widget');
const chatBtn = document.getElementById('chat-toggle-btn');
const closeBtn = document.getElementById('close-chat');
const sendBtn = document.getElementById('send-btn');
const chatInput = document.getElementById('chat-input');
const chatBody = document.getElementById('chat-messages');

// 1. Logic Mở/Đóng Chat
if (chatBtn && chatWidget && closeBtn) {
    chatBtn.addEventListener('click', () => {
        chatWidget.classList.add('active');
        chatBtn.style.transform = 'scale(0)'; 
    });

    closeBtn.addEventListener('click', () => {
        chatWidget.classList.remove('active');
        setTimeout(() => {
            chatBtn.style.transform = 'scale(1)';
        }, 300);
    });
}

// 2. Hàm thêm tin nhắn vào giao diện
function appendMessage(text, sender) {
    const div = document.createElement('div');
    div.classList.add('message', sender);
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    let contentHtml = '';
    // Kiểm tra nếu thư viện marked đã load thì dùng, không thì hiện text thường
    if (sender === 'bot' && typeof marked !== 'undefined') {
        contentHtml = marked.parse(text);
    } else {
        contentHtml = text;
    }

    div.innerHTML = `
        <div class="msg-content">${contentHtml}</div>
        <div class="msg-time">${time}</div>
    `;
    
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight; 
}

// 3. Hiệu ứng đang nhập...
function showTypingIndicator() {
    const div = document.createElement('div');
    div.classList.add('message', 'bot', 'typing-indicator');
    div.id = 'typing-indicator';
    div.innerHTML = `
        <div class="msg-content" style="background: #e6e6e6; padding: 10px 15px;">
            <span class="dot-typing">...</span>
        </div>`;
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

// 4. Gửi tin nhắn (Logic chính)
async function handleSendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    // A. Hiện tin nhắn User
    appendMessage(text, 'user');
    chatInput.value = '';

    // B. Lấy dữ liệu lộ trình (nếu có)
    const routeData = window.currentRouteData || null; 

    // C. Lấy thời gian hiện tại (Cho Case 1)
    const now = new Date();
    const currentTimeStr = now.getHours() + ":" + String(now.getMinutes()).padStart(2, '0');

    // D. Gửi lên Server
    showTypingIndicator();

    try {
        const response = await fetch('http://127.0.0.1:5000/api/chat', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                route_data: routeData,       
                current_time: currentTimeStr 
            })
        });

        const data = await response.json();
        
        removeTypingIndicator();
        appendMessage(data.reply, 'bot');

    } catch (error) {
        removeTypingIndicator();
        appendMessage("❌ Lỗi kết nối AI.", 'bot');
        console.error(error);
    }
}

// 5. BẮT SỰ KIỆN (QUAN TRỌNG: Đã sửa để chống Reload)

// A. Sự kiện Click nút Gửi
sendBtn.addEventListener('click', (e) => {
    e.preventDefault(); // <--- Chặn reload khi click chuột
    handleSendMessage();
});

// B. Sự kiện Nhấn phím Enter
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.keyCode === 13) {
        e.preventDefault(); // <--- Chặn reload khi nhấn Enter
        handleSendMessage();
    }
});
