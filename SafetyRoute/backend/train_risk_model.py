# file: train_risk_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import pickle

def generate_risk_data(n_samples=5000):
    print(f"🎲 Đang sinh {n_samples} dữ liệu mẫu về rủi ro đường đi...")
    
    # 1. Sinh ngẫu nhiên các chỉ số đầu vào (Features)
    # Disaster: 0.0 (Không) -> 1.0 (Tâm bão/Sạt lở)
    disaster_score = np.random.choice([0.0, 0.5, 1.0], n_samples, p=[0.9, 0.08, 0.02])
    
    # Weather: 0.0 (Nắng) -> 1.0 (Mưa bão lớn)
    weather_score = np.random.beta(2, 5, n_samples)
    
    # Crowd: 0.0 (Vắng) -> 1.0 (Chen chúc)
    crowd_score = np.random.uniform(0, 1, n_samples)
    
    # 2. Tạo nhãn (Label - Penalty thực tế) dựa trên logic phức tạp
    # Đây là chỗ AI sẽ học được sự "thông minh" mà công thức cộng không làm được
    penalties = []
    
    for d, w, c in zip(disaster_score, weather_score, crowd_score):
        p = 0
        
        # LOGIC 1: Thiên tai là nguy hiểm nhất (Ưu tiên tuyệt đối)
        if d > 0.8: 
            p = 100.0 # Chặn đường ngay lập tức (Penalty cực lớn)
        elif d > 0.3:
            p = 50.0 # Rất nguy hiểm
            
        # LOGIC 2: Cộng hưởng (Mưa + Đông = Thảm họa)
        # Nếu chỉ mưa: phạt 5 điểm. Nếu chỉ đông: phạt 2 điểm.
        # Nhưng nếu vừa Mưa to (>0.7) vừa Đông (>0.7) -> Phạt 20 điểm (Gấp 3 lần tổng lẻ)
        elif w > 0.7 and c > 0.7:
            p = 20.0 
        
        # LOGIC 3: Các trường hợp thường
        else:
            p = (w * 10) + (c * 2)
            
        # Thêm chút nhiễu cho giống đời thật
        p += np.random.normal(0, 0.5)
        penalties.append(max(0, p))

    # Đóng gói
    df = pd.DataFrame({
        'disaster': disaster_score,
        'weather': weather_score,
        'crowd': crowd_score,
        'penalty': penalties
    })
    return df

def train():
    df = generate_risk_data()
    
    X = df[['disaster', 'weather', 'crowd']]
    y = df['penalty']
    
    print("🚀 Đang train model đánh giá rủi ro (Risk AI)...")
    # Random Forest rất giỏi học các luật "If-Else" phức tạp
    model = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42)
    model.fit(X, y)
    
    with open('risk_model.pkl', 'wb') as f:
        pickle.dump(model, f)
        
    print("✅ Đã tạo xong 'risk_model.pkl'. Sẵn sàng tích hợp!")

if __name__ == '__main__':
    train()