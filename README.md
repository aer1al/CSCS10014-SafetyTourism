# CSCS10014---SafetyTourism
Course project

link for the graphs: https://drive.google.com/drive/folders/1E1UaacZRatcRoGdW585JJk4fKy27aN0C?usp=sharing

* Để chạy Model ollama thì vào link: https://ollama.com để download
* Sau khi download thì mở app Ollama lên nhìn thấy ở khung chat có chỗ để chọn model (nằm kế bên dấu +)
  - Chọn gemma:2b để tải
  - Sau khi tải xong thì mở cmd gõ lệnh "ollama list" để kiểm tra trên máy có chưa
  - Trong lúc chạy web thì mở sẵn app Ollama (không đụng vô app gì cả, ẩn đi cũng được)


* Cái này t tạo sẵn database rồi nên bây vô web thôi, còn sau này để mà host thì phải tải Neo4j về desktop
  - Vào link: https://neo4j.com/download/
  - Sau khi tải xong thì vào app Neo4j -> Create
  - Sau khi tạo xòng thì tìm dòng Connection URL, copy đường dẫn đó -> vào file graph_retriever để tìm URL = (nằm ngay đầu trang)
  - Paste đường dẫn vào, còn mật khẩu thì lúc ban đầu tụi bay đặt gì thì thay vô. Nhớ kiểm tra các file thay đổi password (Đừng đặt 12345678 bị trùng với t)
  - Sau khi tạo db xong thì cd vô thư mục rag_engine để chạy file napdulieu.py -> Có một số cái cần chỉnh ở đầu file. Đường truyền các file json bị sai
  - FILES = {
    "school": "schools.json",
    "tourist": "tourism.json",
    "accident": "accident.json",
    "flood": "flood_points.json"
}   các file này năm trong thư mục data nên sửa đường dẫn lại, không thì copy 4 file json bỏ ra cùng cấp với napdulieu.py để chạy
- http://localhost:7474/browser/ Vào link LOCAL HOST này.
- Khi chạy xong thì reload Neo4j lại, nếu có hiện các Node, Relationship thì OK
- Lưu ý là cái này là LOCAL HOST còn HOST lên cho SERVER như nào thì chưa biết -> Cần tìm hiểu, kể cả Ollama cũng vậy
 
