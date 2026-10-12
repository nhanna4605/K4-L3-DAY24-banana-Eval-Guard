# Kiểm chứng độc lập Phase A/B — Lê Đức Hùng (2A202602849)

Ngày: 2026-10-12. Repo: https://github.com/nhanna4605/K4-L3-DAY24-banana-Eval-Guard, nhánh `main`.
Commit bắt đầu: `8dbd1315e014cb6378bf347680fdb8153d05b963`. Git author của máy: Biocuatoe <hungleduc2005@gmail.com>.

Tóm tắt trung thực: checker và tests đã chạy thật; **hai lần RAGAS live không chạy được** (không có khóa API); phần đọc lại
bottom-10 và bảng judge đã làm đủ trên artifact gốc và tìm ra 3 chẩn đoán cần sửa trong báo cáo Phase A cùng 1 ghi chú bổ sung cho báo cáo Phase B.

## 1. Checker và tests

Môi trường: Windows 10 Pro 10.0.19045, Docker 29.8.0; image `lab24` tự build từ `infra/lab.Dockerfile` ngày 2026-10-12
(build exit 0), Python 3.11.17 trong container; không dùng `--env-file` (máy không có `.env`; checker và tests chạy offline) và không mount HF cache.

| Lần chạy | Log | Exit code | Kết quả thật |
|---|---|---|---|
| Working tree Windows (CRLF) | `check_lab_with_tests_hung.log` | 1 | 22 PASS tài liệu/module/answers, `86 passed, 3 deselected`, nhưng 3 FAIL: Phase A/B/C artifact "Stale experiment source" |
| Bản export LF của cùng commit cộng các sửa tài liệu | `check_lab_with_tests_hung_lf.log` | 0 | `86 passed, 3 deselected`, `0 failed checks` |

Nguyên nhân 3 FAIL là môi trường, không phải dự án: máy này đặt `core.autocrlf=true` nên working tree checkout file thành CRLF
(`git ls-files --eol`: `i/lf w/crlf`), SHA-256 của file khác với `metadata.source_sha256` trong artifact. Bằng chứng: SHA-256 của
`answers_50q.json` ở blob git (LF) là `5ee7c22a...` trùng đúng metadata, còn working tree là `e5cd773c...`. Không sửa file nào để
vượt qua; bản LF được sinh từ `git clone --config core.autocrlf=false` rồi chép đè các file báo cáo đã sửa (đổi sang LF). Người chấm
trên Linux hoặc clone với autocrlf tắt sẽ thấy 0 failed checks. Các log cũ hơn (nếu có) được giữ với hậu tố thời gian UTC.

## 2. Hai lần RAGAS live: không thực hiện được

Lệnh thật đã thử: `python scripts/run_experiments.py --phase a --live` (trong container, ở bản sao LF cô lập) → exit code 2,
`error: Set OPENAI_API_KEY in .env; never put the key in source.` Log: `ragas_live_attempt_blocked_hung.log`. Máy không có `.env`
và biến `OPENAI_API_KEY`/`OPENAI_BASE_URL` không tồn tại; khóa của nhóm/gateway không có trên máy này. Không có lệnh gọi API nào được gửi, **không có**
`ragas_run_hung_1.json`/`_2.json`/`.log`, và không số nào trong báo cáo này đến từ lần chạy thêm. Việc cần làm khi có khóa: đặt `.env`
rồi chạy hai lần như `doc/PHAN_CONG.md` mô tả (ưu tiên bản sao cô lập, hoặc sao lưu rồi khôi phục đúng file `artifacts/ragas_50q.json`).

## 3. Mean theo distribution (chỉ baseline)

Tính trực tiếp từ `per_question` của `artifacts/ragas_50q.json` (run 2026-10-12T09:55:57Z): avg_score là trung bình 4 metric từng câu, rồi trung bình nhóm; trùng `per_distribution`.

| Distribution | n | baseline | Run 1 | Run 2 | Dải lịch sử | Kết luận |
|---|---|---|---|---|---|---|
| factual | 20 | 0.879112 | không chạy | không chạy | 0.869–0.889 | trong dải |
| multi_hop | 20 | 0.686658 | không chạy | không chạy | 0.687–0.701 | 0.6867 thấp hơn 0.687 ở 4 chữ số; làm tròn 3 chữ số (độ chính xác của dải) là 0.687 nên nằm trong dải, sát biên |
| adversarial | 10 | 0.827235 | không chạy | không chạy | 0.815–0.834 | trong dải |

Mean từng metric (50 câu): faithfulness 0.8874, answer_relevancy 0.6313, context_precision 0.8683, context_recall 0.7800; avg 0.7918.
Thứ tự multi_hop < adversarial < factual đúng với baseline. Không tính được min/max qua ba lần hay metric nào dao động nhiều nhất vì chỉ có một quan sát;
dải lịch sử 5 lần (đã gồm chính baseline) vẫn là số đo của người phụ trách trước, chưa được tái lập độc lập ở đây.

## 4. Bottom-10: đã đọc lại cả 10 câu

Đối chiếu bảng trong `doc/reports/failure_clusters.md` với `bottom_10`: 10/10 hàng trùng nguyên văn ở cả 8 cột; thứ hạng, id, avg_score
tính lại từ per_question trùng khớp (id 33, 22, 39, 28, 27, 21, 31, 35, 34, 45). Chi tiết từng câu nằm ở mục "Kiểm chứng bổ sung 2026-10-12"
của báo cáo đó. Tóm tắt:

| id | Kết luận | Điểm chính |
|---|---|---|
| 33 | Xác nhận | retrieval thiếu chunk phụ cấp và chunk quy tắc +1 ngày/3 năm; generation suy rộng từ ví dụ 9 năm (18 thay vì 19 ngày) |
| 22 | Xác nhận | bảng thẩm quyền bị cắt; answer tự mâu thuẫn |
| 39 | Xác nhận, bổ sung | thêm: "12 ký tự" của v2.0 cũng không được retrieve (diagnosis coi 12 là giá trị suy ra do 14−2); context_recall 0.00 thấp hơn thực tế |
| 28 | **Sửa** | answer đúng, retrieval đủ số liệu (context_recall 1.00); context_precision 0.00 (worst metric) không giải thích được và diagnosis chỉ nhắc faithfulness; giả thuyết "câu tính tổng" bị phản bác bởi faithfulness 1.00 ở 3/5 lần chạy trước. Kết luận: nhiễu evaluator, không phải lỗi retrieval hay generation |
| 27 | Xác nhận | thiếu chunk quy tắc, answer suy rộng nhưng ra đúng 17/13 |
| 21 | Xác nhận | thiếu bảng lương Senior (có trong index, xuất hiện ở context của id 28 và 35) |
| 31 | Xác nhận, làm rõ | 2.400.000 đúng; 300.000 là phần suy ra không được hỏi, nhãn "miscomputes" của diagnosis không đúng; lỗi thật là prefix m5 ghi "nước ngoài" |
| 35 | Xác nhận | thiếu chunk ăn trưa 1.000.000 và phụ cấp điện thoại |
| 34 | **Sửa** | phần được hỏi trả lời đúng; "15 ngày hoàn ứng" không có trong câu hỏi và không có trong context nào (diagnosis coi 15 là suy ra do 20.000.000−5.000.000) nên là retrieval chưa lấy chunk, không phải generation bỏ sót |
| 45 | Xác nhận | answer đúng; AR 0.30 là hiện tượng metric, recall 0.50 vì không có chunk v1.0 |

## 5. Phase B

Nguồn đã kiểm bằng so khớp chuỗi trong code Python: A = `artifacts/answers_50q.json:answer`, B = `fixtures/human_labels_10q.json:model_answer`,
reference = `fixtures/test_set_50q.json:ground_truth`; question khớp `test_set`; 5 id là 1, 5, 12, 21, 41; 10/10 `binary_judgments` có `model_answer` và `question`
đúng bằng fixture, thứ tự `question_ids` khớp.

| id | winner_pass1 | winner_pass2 (đã quy về gốc) | final | consistent | Độ dài A/B | Kiểm tra reasoning lượt 2 |
|---|---|---|---|---|---|---|
| 1 | B | B | B | True | 48/57 | "Answer A" lượt 2 là B gốc (có "có lương"): đúng |
| 5 | A | A | A | True | 69/33 | "Answer B" lượt 2 là A gốc (CEO): đúng |
| 12 | A | A | A | True | 85/50 | "đáp án B" lượt 2 là A gốc (điều kiện 6 tháng): đúng |
| 21 | B | B | B | True | 278/82 | "Answer A" lượt 2 là B gốc (18 ngày và 20–35 triệu): đúng |
| 41 | A | A | A | True | 107/37 | "Answer B" lượt 2 là A gốc (15 ngày v2024): đúng |

`swap_and_average` ánh xạ lượt 2 bằng `SWAP_BACK` và đảo `scores` A↔B; kết quả lưu khớp. Hạn chế: JSON không lưu phản hồi thô lượt 2 nên điểm
sau khi đảo chỉ kiểm được bằng nội dung reasoning và mã, không so được với bản thô. Position bias 0/5 = 0.0. Verbosity: winner dài hơn ở 4/5 (A thắng và dài hơn 3: id 5, 12, 41; B thắng và dài hơn 1: id 1;
id 21 winner ngắn hơn) = 0.8, đúng với `bias_report` của artifact và báo cáo. Đọc nội dung: bốn winner dài hơn đều có thêm dữ kiện đúng; id 12 là cặp mỏng nhất vì human gắn nhãn 1 cho
answer ngắn hơn. Với n = 5 chỉ là tín hiệu rất yếu.

Calibration: 10/10 cặp judge–human trùng; judge_labels và human_labels đều là [1,0,1,1,1,0,1,0,1,0] (6 nhãn 1, 4 nhãn 0). Tính lại: p_o = 1.0,
p_e = 0.6·0.6 + 0.4·0.4 = 0.52, κ = (1 − 0.52)/(1 − 0.52) = 1.0, khớp giá trị lưu `cohen_kappa = 1.0`. Kiểm tra độ nhạy: đổi bất kỳ 1 nhãn judge
thì p_o = 0.9, p_e 0.50–0.54, κ 0.7826–0.8000, khớp câu "0.78–0.80" của báo cáo. Giải thích κ và Landis–Koch ("almost perfect" cho 0.8–1.0) đúng về toán học.
Báo cáo không phát biểu quá mức (đã nói mẫu nhỏ, chưa thay được người).

Điều cần ghi thêm (đã thêm vào `bias_report.md`): reasoning của judge không luôn bám answer. Ở id 12 judge viết answer "đầy đủ ... nhân viên chính thức từ 6 tháng trở lên"
trong khi `model_answer` không nêu điều kiện đó; cùng answer ấy ở pairwise bị trừ điểm vì thiếu chính điều kiện này. Id 46 nhắc "điều kiện phê duyệt" mà answer không có. Nhãn vẫn trùng human,
nên κ không phản ánh lỗi này. Không có nhãn hay kết quả nào bị sửa.

## 6. Thay đổi báo cáo và bằng chứng

| File | Thay đổi | Bằng chứng |
|---|---|---|
| `doc/reports/failure_clusters.md` | id 34: thời hạn 15 ngày là chunk chưa retrieve | contexts không có "15 ngày"; `data/tam_ung.md` mục "Thời hạn thanh toán"; luật `_present(15, derived)` đúng nhờ 20.000.000 − 5.000.000 |
| `doc/reports/failure_clusters.md` | id 28: hạ nguyên nhân thành giả thuyết, nêu context_precision 0.00 | context 1–2 chứa 300.000 và 1.000.000, context_recall 1.00; faithfulness 1.00 ở 3/5 lần theo chính báo cáo |
| `doc/reports/failure_clusters.md` | id 39: thêm "12 ký tự" chưa retrieve | contexts không có "12 ký tự"; có trong `data/mat_khau_v2.md` |
| `doc/reports/failure_clusters.md` | thêm mục "Kiểm chứng bổ sung 2026-10-12" | mục 3 và 4 ở trên |
| `doc/reports/bias_report.md` | thêm ghi chú reasoning id 12 và id 46 | so sánh `model_answer` với reasoning trong `judge_results.json` |

Không sửa: bốn artifact chính, fixtures, mã Phase A/B/C, `guardrails/config.yml`, phần của hai thành viên khác trong `doc/TEAM.md`. Bảng bottom-10 "chép nguyên văn" được giữ nguyên.

## 7. Giới hạn

- Không có lần chạy RAGAS thêm nên độ dao động chưa được đo độc lập; so sánh min/max/ordering chỉ có một điểm.
- Kết luận "nhiễu evaluator" ở id 28 và id 39 dựa trên mâu thuẫn nội tại giữa các metric và dữ liệu lịch sử trong báo cáo, không phải trên lần chấm lại.
- Phase B chỉ đọc lại, không chạy lại judge; phản hồi thô lượt 2 không được lưu.
- Mẫu nhỏ (50 câu, 10 adversarial, 5 cặp, 10 nhãn). Checker trên working tree Windows (CRLF) báo 3 FAIL do autocrlf (mục 1).
- Lịch sử 5 lần chạy RAGAS trước đó không còn artifact nên không kiểm lại được.

## 8. SHA-256 của bốn artifact chính

Ghi trước khi sửa bất cứ gì (working tree CRLF, và blob git LF), kiểm lại ở cuối:

| File | Working tree | Blob git (HEAD) | Kiểm lại cuối |
|---|---|---|---|
| `artifacts/answers_50q.json` | `e5cd773caa5c08db5dde01d56845a6594fde88635df962e9036fdf0cbb1733d9` | `5ee7c22ab53590b75d16843c403c3e4c3ea3ff04ac262e8c8ec88bfb3d2799f6` | trùng |
| `artifacts/ragas_50q.json` | `db1ec2788b757f36784be3acd7fda8a3a13bab26190e3b5127703c5b61a5f86b` | `e706a343ce61b6f479536e541f5c4e546df49d3b4480010a89d259090335c0ac` | trùng |
| `artifacts/judge_results.json` | `b1edbd53ad5b9f1391c36c0935b685efe7f5c7e22e67d29b12f5285cb6a398be` | `701c2e915a787346d3275c3398b37d1f0842996d076638ffc3d7140643d10fcc` | trùng |
| `artifacts/guard_results.json` | `766eab39f777ce8c47f0f2f8897e363506076bade808ff1a4a2c469d7bbe1bcb` | `4b386ed84b84cd14f57c37f72735d85764f1c71bdaa8460f96f2dae5999934be` | trùng |
