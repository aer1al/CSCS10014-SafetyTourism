import sys
import os
import json

# --- SETUP ĐƯỜNG DẪN IMPORT ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from rag_engine.traffic_query import TrafficService

# --- MÀU SẮC ĐỂ DỄ NHÌN ---
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def debug_query(service, street_name):
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"🔍 ĐANG TRUY VẤN: {Colors.YELLOW}'{street_name}'{Colors.ENDC}")
    print(f"{'='*60}{Colors.ENDC}")

    # Gọi hàm thực tế
    data = service.get_street_status(street_name)

    if not data:
        print(f"{Colors.RED}❌ Không tìm thấy thông tin hoặc đường không tồn tại.{Colors.ENDC}")
        return

    # 1. IN THÔNG TIN CƠ BẢN
    print(f"📍 Quận: {Colors.GREEN}{data.get('district')}{Colors.ENDC}")
    print(f"☁️ Thời tiết: {data.get('current_weather', {}).get('condition')} | {data.get('current_weather', {}).get('temperature')}")

    # 2. IN CHI TIẾT HAZARDS (Để soi cái Description)
    print(f"\n{Colors.BOLD}--- 💥 DANH SÁCH RỦI RO (HAZARDS) ---{Colors.ENDC}")
    hazards = data.get('hazards', [])
    if not hazards:
        print("   (Không có dữ liệu)")
    else:
        for i, h in enumerate(hazards, 1):
            print(f"   {i}. Tên: {h.get('name')}")
            print(f"      Loại: {h.get('type')} | Mức độ: {h.get('severity')}")
            # In dòng này màu vàng để bạn dễ check xem nó có bị None không
            print(f"      📝 Mô tả (Desc): {Colors.YELLOW}'{h.get('desc')}'{Colors.ENDC}") 

    # 3. IN CHI TIẾT PLACES (Để soi cái Traffic Pattern)
    print(f"\n{Colors.BOLD}--- 🏫 DANH SÁCH ĐỊA ĐIỂM (PLACES) ---{Colors.ENDC}")
    places = data.get('places', [])
    if not places:
        print("   (Không có dữ liệu)")
    else:
        for i, p in enumerate(places, 1):
            print(f"   {i}. {p.get('name')} ({p.get('type')})")
            
            # Kiểm tra xem có lấy được Pattern không
            if 'traffic_impact' in p:
                impact = p['traffic_impact']
                print(f"      🚦 {Colors.CYAN}TRAFFIC IMPACT:{Colors.ENDC}")
                print(f"         - Giờ: {impact.get('time')}")
                print(f"         - Ngày: {impact.get('days')}")
                print(f"         - Nguyên nhân: {impact.get('cause')}")
            else:
                print(f"      ❌ {Colors.RED}Không có thông tin giờ cao điểm{Colors.ENDC}")

    # 4. IN JSON THÔ (RAW) NẾU MUỐN COPY
    print(f"\n{Colors.BOLD}--- 📜 JSON RAW DATA (Dùng để check format) ---{Colors.ENDC}")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def run_debug():
    service = TrafficService()

    # --- TEST CASE 1: CHECK HAZARD DESC ---
    # Đường Tỉnh Lộ 43 (Nơi có điểm đen tai nạn)
    debug_query(service, "Tỉnh Lộ 43")

    # --- TEST CASE 2: CHECK SCHOOL PATTERN ---
    # Đường Nguyễn Văn Cừ (Nơi có ĐH Khoa học Tự nhiên)
    debug_query(service, "Nguyễn Văn Cừ")

    service.close()

if __name__ == "__main__":
    run_debug()