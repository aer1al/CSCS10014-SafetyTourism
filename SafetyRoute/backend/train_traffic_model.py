# file: train_traffic_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import pickle
import os

def generate_dummy_data(n_samples=5000):
    print(f"🎲 Đang sinh {n_samples} dòng dữ liệu giả lập...")
    
    # 1. Sinh ngẫu nhiên các đặc trưng (Features)
    # Giờ trong ngày (0.0 đến 24.0)
    hours = np.random.uniform(0, 24, n_samples)
    
    # Là cuối tuần? (0: Ngày thường, 1: Cuối tuần)
    is_weekend = np.random.choice([0, 1], n_samples, p=[0.7, 0.3])
    
    # Điểm thời tiết (0.0: Đẹp trời -> 1.0: Bão lớn)
    weather_score = np.random.beta(2, 5, n_samples) # Dùng phân phối Beta để thiên về số nhỏ (trời đẹp nhiều hơn bão)
    
    # 2. Tạo nhãn (Label - Kết quả mong muốn) dựa trên LUẬT GIẢ ĐỊNH
    # Công thức này mô phỏng thực tế để máy "học" lại
    traffic_scores = []
    
    for h, wkd, rain in zip(hours, is_weekend, weather_score):
        score = 0.1 # Mặc định đường vắng
        
        # Logic kẹt xe ngày thường
        if wkd == 0:
            if 7 <= h <= 9: score += 0.7   # Cao điểm sáng
            elif 17 <= h <= 19: score += 0.9 # Cao điểm chiều (Kẹt cứng)
            elif 9 < h < 17: score += 0.3  # Giờ làm việc
        else:
            # Cuối tuần
            if 18 <= h <= 21: score += 0.5 # Tối cuối tuần đi chơi
            
        # Mưa càng to càng dễ kẹt (thêm tối đa 0.3)
        score += rain * 0.3
        
        # Nhiễu ngẫu nhiên (Noise) để dữ liệu giống thật hơn
        noise = np.random.normal(0, 0.05)
        score += noise
        
        # Kẹp kết quả trong 0.0 - 1.0
        traffic_scores.append(max(0.0, min(1.0, score)))
        
    # Đóng gói vào DataFrame
    df = pd.DataFrame({
        'hour': hours,
        'is_weekend': is_weekend,
        'weather_score': weather_score,
        'traffic_score': traffic_scores
    })
    
    return df

def train_model():
    # 1. Tạo dữ liệu
    data = generate_dummy_data()
    
    # 2. Tách Feature (X) và Label (y)
    X = data[['hour', 'is_weekend', 'weather_score']]
    y = data['traffic_score']
    
    # 3. Khởi tạo và Train model (Random Forest)
    print("🚀 Đang huấn luyện AI (Random Forest)...")
    model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
    model.fit(X, y)
    
    # 4. Lưu model ra file
    filename = 'traffic_model.pkl'
    with open(filename, 'wb') as f:
        pickle.dump(model, f)
        
    print(f"✅ Đã train xong! Model được lưu tại: {filename}")
    print("Test thử dự đoán:")
    # Thử dự đoán: 18h chiều thứ 2 (weekend=0), trời mưa to (weather=0.8)
    test_input = [[21.30, 0, 1.0]] 
    pred = model.predict(test_input)[0]
    print(f" - Input: 18h, Ngày thường, Mưa to -> Dự báo kẹt xe: {pred:.2f}/1.0")

if __name__ == '__main__':
    train_model()