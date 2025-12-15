# CSCS10014---SafetyTourism
Course project

link for the graphs: https://drive.google.com/drive/folders/1E1UaacZRatcRoGdW585JJk4fKy27aN0C?usp=sharing

* Để chạy Model ollama thì vào link: https://ollama.com để download
* Sau khi download thì mở app Ollama lên nhìn thấy ở khung chat có chỗ để chọn model (nằm kế bên dấu +)
  -> Chọn gemma3:4b để tải và gemma3:1b để tải
  -> Sau khi tải xong thì mở cmd gõ lệnh "ollama list" để kiểm tra trên máy có chưa
  -> Trong lúc chạy web thì mở sẵn app Ollama (không đụng vô app gì cả, ẩn đi cũng được)

* Host Neo4j database:
  - Vào link này: http://localhost:7474/browser
  - password: 12345678
* Cái này t tạo sẵn database rồi nên bây vô web thôi, còn sau này để mà host thì phải tải Neo4j về desktop
  - Vào link: https://neo4j.com/download/
  - Sau khi tải xong thì vào app Neo4j -> Create
  - Sau khi tạo xòng thì tìm dòng Connection URL, copy đường dẫn đó -> vào file graph_retriever để tìm URL = (nằm ngay đầu trang)
  - Paste đường dẫn vào, còn mật khẩu thì lúc ban đầu tụi bay đặt gì thì thay vô
 
