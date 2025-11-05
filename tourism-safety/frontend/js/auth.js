// URL của API backend (hãy đảm bảo Flask đang chạy trên cổng 5000)
const API_URL = 'http://localhost:5000/api';

// Lấy các element từ DOM
const signInForm = document.getElementById('sign-in-form');
const signUpForm = document.getElementById('sign-up-form');

// Thêm sự kiện 'submit' cho form Đăng nhập
if (signInForm) {
    signInForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Ngăn form submit theo cách truyền thống

        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

        // Gọi hàm xử lý đăng nhập
        await handleLogin(username, password);
    });
}

// Thêm sự kiện 'submit' cho form Đăng ký
if (signUpForm) {
    signUpForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Ngăn form submit

        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        // const address = document.getElementById('register-address').value; // Bỏ comment nếu bạn thêm trường address

        // Gọi hàm xử lý đăng ký
        await handleRegister(username, email, password);
    });
}

/**
 * Xử lý logic Đăng nhập
 * Gọi API /api/login
 */
async function handleLogin(username, password) {
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            // Nếu server trả về lỗi (400, 401, 500...)
            throw new Error(data.error || 'Login failed');
        }

        // ĐĂNG NHẬP THÀNH CÔNG
        // alert('Login successful! Redirecting...'); // <-- ĐÃ XÓA DÒNG NÀY
        
        // Lưu access token vào localStorage
        localStorage.setItem('accessToken', data.access_token);
        
        // SỬA ĐỔI Ở ĐÂY: Chuyển hướng người dùng đến trang home (index.html)
        window.location.href = 'index.html'; 

    } catch (error) {
        console.error('Login Error:', error);
        alert(`Login failed: ${error.message}`);
    }
}

/**
 * Xử lý logic Đăng ký
 * Gọi API /api/register
 */
async function handleRegister(username, email, password, address = null) {
    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, password, address }),
        });

        const data = await response.json();

        if (!response.ok) {
            // Nếu server trả về lỗi (409, 400...)
            throw new Error(data.error || 'Registration failed');
        }

        // ĐĂNG KÝ THÀNH CÔNG
        alert('Registration successful! Please sign in.');
        
        // Tùy chọn: Tự động chuyển sang tab đăng nhập
        const signInBtn = document.getElementById('sign-in-btn');
        if(signInBtn) {
            signInBtn.click(); // Giả lập một cú click để chuyển panel
        }
        
        // Xóa các trường trong form đăng ký
        if(signUpForm) {
            signUpForm.reset();
        }

    } catch (error) {
        console.error('Registration Error:', error);
        alert(`Registration failed: ${error.message}`);
    }
}