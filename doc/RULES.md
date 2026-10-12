# Quy định K4 Track 3B

**Hình thức: bài nhóm, một repo chung và một lần nộp link do trưởng nhóm thực hiện.**

## Làm bài và hợp tác trong nhóm

Các thành viên cùng hoàn thành ba phase, tích hợp pipeline và kiểm tra bản cuối.
Nhóm tự phân công; một người có thể hỗ trợ nhiều phase. Ghi công việc thực tế
của từng người trong bảng thành viên và mục `INDIVIDUAL` của `doc/TEAM.md`.

Mã chung của nhóm là sản phẩm bài nhóm. Không yêu cầu mỗi thành viên tạo một
repo bài nộp khác. Mỗi thành viên cần giải thích được phần đã khai và cách phần
đó tham gia luồng đánh giá hoặc bảo vệ pipeline. Việc nhận kết quả của nhóm khác
phải được phân biệt với hợp tác trong nhóm mình.

## Sử dụng AI và nguồn tham khảo

Áp dụng chính sách AI do coach công bố cho buổi học; repo này không bổ sung
một quyền sử dụng AI hoặc một lệnh cấm khác với thông báo lớp. Khi có dùng AI,
ghi công cụ, phần được hỗ trợ và cách kiểm chứng trong `doc/TEAM.md`.

Nhóm chịu trách nhiệm về mã và kết quả nộp, kể cả phần có AI hỗ trợ. Không coi
mã sinh ra là bằng chứng đã chạy; không dùng AI để điền số đo, nhãn judge hoặc
báo cáo giả. Chỉ ghi các kết quả có thể đối chiếu với lần chạy thực tế.

Ghi nguồn khi dùng mã hoặc tài liệu ngoài starter. Mã pipeline từ bài trước
được đưa vào theo yêu cầu lab; ghi nguồn nếu đó là phần đã làm chung ở bài trước.
Không khai mã, kết quả hoặc đóng góp của người khác thành phần tự thực hiện.
Cách xử lý sao chép và mức phạt theo quy định của khóa học do coach công bố.

## Bảo mật API key và dữ liệu

Giữ key trong `.env` hoặc biến môi trường. `.env.example` chỉ chứa tên biến,
không chứa key thật. Không đưa secrets vào mã nguồn, commit, log, ảnh chụp,
report hoặc nội dung gửi tới công cụ AI.

Dùng corpus và dữ liệu mẫu của lab để thử guardrails. Không thay bằng CCCD,
điện thoại, bảng lương hoặc thông tin nhân viên thật. Các chuỗi PII trong bộ
test là dữ liệu kiểm thử; trước khi commit báo cáo, kiểm tra không có dữ liệu
cá nhân thật hoặc secrets ngoài dữ liệu mẫu. Nếu lộ key, thu hồi/thay key và xử
lý lịch sử Git theo hướng dẫn bảo mật của đơn vị cung cấp.

## Nộp bài, nộp muộn và sửa sau deadline

Trưởng nhóm nộp một link repo theo [SUBMISSION.md](SUBMISSION.md). Thành viên,
MSSV và đóng góp phải đầy đủ trong `doc/TEAM.md`; không dùng việc chưa kê khai để
quy phần đã làm cho một người khác.

Deadline mặc định là **23:59 ngày diễn ra lab, Asia/Ho_Chi_Minh (UTC+07:00)**.
Thông báo điều chỉnh của key coach trong 48 giờ sau lab được áp dụng theo quy
ước chung. Ngày cụ thể và kênh nhận bài lấy từ thông báo lớp.

Nộp muộn bị trừ điểm; mức trừ cụ thể theo thông báo của key coach. Repo không
tự đặt mức phạt theo giờ/ngày khi khóa học chưa cung cấp mức đó.

Khi nộp, lưu commit SHA trong `doc/TEAM.md` và thông tin gửi bài. Nếu sửa sau
deadline, ghi rõ commit và thời điểm sửa; việc dùng bản cập nhật để chấm theo
quyết định của key coach. Không trình bày thay đổi sau deadline như thể đã có
trong phiên bản nộp đúng hạn.

## Điểm bắt buộc và bonus

Điểm kỹ thuật và các điều kiện mất điểm nằm trong [RUBRIC.md](RUBRIC.md).
Bonus của bài lab cộng tối đa 10 điểm trên thang bắt buộc 100 điểm. Đây là bonus
bài lab, không phải điểm giơ tay, phát biểu hoặc pitching.

Các kết quả chung của repo là bằng chứng kỹ thuật của nhóm. `doc/TEAM.md` và lịch
sử Git là bằng chứng đóng góp cá nhân; repo này không tự thêm một tỷ lệ chấm
cá nhân/nhóm hoặc hệ số điểm đóng góp ngoài thông báo của coach.
