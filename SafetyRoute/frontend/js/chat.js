// js/chat.js

const chatWidget = document.getElementById('chat-widget');
const chatBtn = document.getElementById('chat-toggle-btn'); // <-- ĐÃ ĐỔI TÊN BIẾN
const closeBtn = document.getElementById('close-chat');
const sendBtn = document.getElementById('send-btn');
const chatInput = document.getElementById('chat-input');
const chatBody = document.getElementById('chat-messages');

// 1. Logic Mở/Đóng Chat
chatBtn.addEventListener('click', () => {  // <-- SỬA LẠI CHỖ NÀY
    chatWidget.classList.add('active');
    chatBtn.style.transform = 'scale(0)'; 
});

closeBtn.addEventListener('click', () => {
    chatWidget.classList.remove('active');
    setTimeout(() => {
        chatBtn.style.transform = 'scale(1)'; // <-- SỬA LẠI CHỖ NÀY
    }, 300);
});

// 2. Hàm thêm tin nhắn vào giao diện
function appendMessage(text, sender) {
    const div = document.createElement('div');
    div.classList.add('message', sender);
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // 👇 SỬA ĐOẠN NÀY:
    // Nếu là Bot -> Dùng marked.parse để hiển thị đẹp (đậm, nghiêng, list)
    // Nếu là User -> Hiển thị text thường (để tránh lỗi bảo mật XSS)
    let contentHtml = '';
    if (sender === 'bot') {
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

// 3. Hàm hiển thị "Bot đang nhập..."
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

// 4. Gửi tin nhắn
async function handleSendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    // Hiện tin nhắn User
    appendMessage(text, 'user');
    chatInput.value = '';

    // Lấy dữ liệu lộ trình hiện tại
    const routeData = window.currentRouteData;
    
    // Nếu chưa tìm đường -> Nhắc nhở nhẹ nhàng
    if (!routeData) {
        // Giả lập độ trễ 500ms cho tự nhiên
        setTimeout(() => {
            appendMessage("⚠️ Bạn chưa chọn lộ trình trên bản đồ. Hãy nhập điểm đi/đến ở thanh bên trái và bấm 'Tìm kiếm' trước nhé!", 'bot');
        }, 500);
        return;
    }

    // Nếu đã có đường -> Gửi ngay cho AI phân tích
    showTypingIndicator();

    try {
        const response = await fetch('http://127.0.0.1:5000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                route_data: routeData
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

// Hàm phụ: Gửi chat khi đã có thông tin đường đi
async function sendChatRequestWithRoute(message) {
    // Lấy dữ liệu lộ trình (có thể là null nếu chưa tìm đường)
    const routeData = window.currentRouteData || null; 
    
    // ❌ XÓA ĐOẠN CODE CHẶN CŨ ĐI (Đoạn if (!routeData) { appendMessage... return; })
    // Thay vì chặn, ta cứ gửi lên Server để AI tự trả lời

    try {
        const response = await fetch('http://127.0.0.1:5000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                route_data: routeData // Gửi null nếu chưa có đường
            })
        });
        const data = await response.json();
        
        removeTypingIndicator();
        appendMessage(data.reply, 'bot');
    } catch (e) {
        removeTypingIndicator();
        console.error(e);
        appendMessage("❌ Lỗi kết nối.", 'bot');
    }
}

// Sự kiện
sendBtn.addEventListener('click', handleSendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSendMessage();
});