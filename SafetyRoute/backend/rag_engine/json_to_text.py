# rag_engine/json_to_text.py

class TrafficReportFormatter:
    """
    Class chuyên dụng để chuyển đổi JSON dữ liệu giao thông
    thành văn bản có cấu trúc (Structured Text) cho LLM đọc.
    """

    @staticmethod
    def format(data):
        if not data:
            return "Không có dữ liệu."

        # Xác định tiêu đề dựa trên loại query
        target_name = data.get('street') or data.get('name') or "Địa điểm chưa rõ"
        district = data.get('district', 'TP.HCM')

        # 1. HEADER
        report = f"=== BÁO CÁO TÌNH TRẠNG: {target_name.upper()} ===\n"
        report += f"📍 Khu vực: {district}\n\n"

        # 2. THỜI TIẾT (Weather)
        report += TrafficReportFormatter._format_weather(data.get('current_weather'))

        # 3. RỦI RO (Hazards)
        if 'hazards' in data:
            report += TrafficReportFormatter._format_hazards(data['hazards'])

        # 4. GIAO THÔNG & ĐỊA ĐIỂM (Traffic & Places)
        # Xử lý cả 2 trường hợp: Street (list places) và Place (single traffic_info)
        if 'places' in data:
            report += TrafficReportFormatter._format_places_traffic(data['places'])
        elif 'traffic_info' in data:
            # Nếu input là Place Info, ta giả lập structure list để dùng chung hàm
            single_place = {
                'name': target_name,
                'traffic_impact': data['traffic_info'][0] if data['traffic_info'] else None
            }
            # Nếu traffic_info là list, lấy phần tử đầu hoặc loop (tuỳ logic DB)
            if isinstance(data['traffic_info'], list) and data['traffic_info']:
                # Trường hợp đặc biệt: Place có nhiều khung giờ
                # Nhưng để đơn giản ta format tay ở đây luôn
                report += "--- 3. ĐIỂM NÓNG GIAO THÔNG ---\n"
                report += f"[*] {target_name}\n"
                for info in data['traffic_info']:
                    report += f"    - Khung giờ: {info.get('time', 'N/A')} ({info.get('days', '')})\n"
                    report += f"    - Nguyên nhân gốc: {info.get('cause', 'N/A')}\n"
            else:
                report += "--- 3. ĐIỂM NÓNG GIAO THÔNG ---\n(Không có ghi nhận ùn tắc đặc biệt)\n"

        return report

    @staticmethod
    def _format_weather(w):
        if not w: return "--- 1. THỜI TIẾT ---\n(Không có dữ liệu)\n\n"
        
        text = "--- 1. THÔNG TIN THỜI TIẾT ---\n"
        text += f"- Tình trạng: {w.get('condition', 'N/A')}\n"
        text += f"- Nhiệt độ: {w.get('temperature', 'N/A')}\n"
        
        flood_warn = w.get('flood_warning', 'Không')
        # Thêm icon cảnh báo nếu có ngập
        icon = "⚠️" if flood_warn != "KHÔNG" and flood_warn != "Không" else "✅"
        text += f"- Cảnh báo ngập do mưa: {icon} {flood_warn}\n\n"
        return text

    @staticmethod
    def _format_hazards(hazards):
        text = "--- 2. CẢNH BÁO RỦI RO (HAZARDS) ---\n"
        if not hazards:
            text += "(Không ghi nhận sự cố/điểm đen nào)\n\n"
            return text

        for h in hazards:
            severity = h.get('severity', 'Vừa')
            icon = "⛔" if severity in ['High', 'Critical'] else "⚠️"
            
            text += f"{icon} {h.get('name')} (Mức độ: {severity})\n"
            # Fallback nếu desc rỗng
            desc = h.get('desc') if h.get('desc') else "Chưa có mô tả chi tiết."
            text += f"    Chi tiết: {desc}\n"
        text += "\n"
        return text

    @staticmethod
    def _format_places_traffic(places):
        text = "--- 3. ĐIỂM NÓNG GIAO THÔNG (TRAFFIC HOTSPOTS) ---\n"
        
        # Lọc ra những nơi có Traffic Impact (Giờ cao điểm)
        # Hoặc những nơi là Trường học/Du lịch (để AI biết ngữ cảnh)
        active_places = [p for p in places if 'traffic_impact' in p]

        if not active_places:
            text += "(Giao thông ổn định, không có điểm ùn tắc thường xuyên)\n"
            return text

        for p in active_places:
            impact = p.get('traffic_impact', {})
            text += f"[*] {p.get('name')}\n"
            text += f"    - Giờ cao điểm: {impact.get('time', 'N/A')} ({impact.get('days', '')})\n"
            text += f"    - Nguyên nhân gốc: {impact.get('cause', 'N/A')}\n"
        

        return text
