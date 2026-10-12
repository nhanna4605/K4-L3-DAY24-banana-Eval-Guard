# Phân tích lỗi Phase A

Nhóm: banana

Người phụ trách: Võ Doanh Nhân — 2A202602770

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T09:55:57.137721+00:00.
Generation mode/fallback và điều kiện chạy: 50/50 câu `generation_mode=llm`, không câu nào dùng
extractive fallback. Pipeline lắp từ m1–m5 của Day 18: hierarchical chunking (parent 2048 / child 256 ký tự,
107 child chunks), enrichment m5 bằng gpt-4.1-mini, hybrid search BM25 (underthesea) + dense BGE-M3 trên
Qdrant v1.9.7, rerank `BAAI/bge-reranker-v2-m3` lấy top-3. Chạy trong Docker (Python 3.11, CPU) qua gateway
tương thích OpenAI. Hai PDF scan ảnh (`BCTC.pdf`, `Nghi_dinh_so_13-2023...pdf`) không có text layer nên bị
bỏ qua khi index; không câu nào trong `test_set_50q.json` hỏi về hai tài liệu này.
Models generation/evaluator: generation `gpt-4.1-mini`; evaluator (từ `metadata.evaluator_models` của m4)
`gpt-4.1-mini` + `text-embedding-3-small`, RAGAS 0.1.22.

Ghi chú về adapter m4: RAGAS 0.1.22 chỉ giữ các câu kết thúc bằng dấu "." khi tách statement cho
faithfulness, nên câu trả lời dạng gạch đầu dòng bị bỏ ý (một câu toàn bullet ra NaN). m4 thêm dấu "." cuối
mỗi dòng của answer gửi cho RAGAS (không đổi từ ngữ, áp dụng cho cả 50 câu); answer lưu trong artifact giữ
nguyên. Câu nào vẫn NaN sau 3 lượt chấm lại thì m4 báo lỗi, không thay bằng 0. Lượt chạy này không có NaN.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 0.983 | 0.752 | 0.967 |
| answer_relevancy | 0.666 | 0.545 | 0.734 |
| context_precision | 0.992 | 0.733 | 0.892 |
| context_recall | 0.875 | 0.717 | 0.717 |
| avg_score | 0.879 | 0.687 | 0.827 |

Trung bình 50 câu: faithfulness 0.887, answer_relevancy 0.631, context_precision 0.868, context_recall 0.780,
avg_score 0.792.

Độ ổn định: Phase A được chạy 5 lần trên cùng `answers_50q.json` (09:24–09:55 UTC, lần cuối là artifact).
Mean theo nhóm dao động factual 0.869–0.889, multi_hop 0.687–0.701, adversarial 0.815–0.834; thứ tự
multi_hop < adversarial < factual giữ nguyên ở cả 5 lần. Điểm từng câu dao động mạnh hơn: id 9 có avg 0.991
ở một lần và 0.657 ở lần khác; faithfulness của id 28 là 1.00 ở 3/5 lần, 0.43 và 0.33 ở hai lần còn lại, dù answer
không đổi. Vì vậy bottom-10 dưới đây là của lần chạy cuối; các câu ở ranh giới (avg ≈ 0.70) có thể đổi chỗ.

## Bottom 10 và nguyên nhân

Bảng chép nguyên văn 10 rows Task 3 trong `bottom_10` của artifact (diagnosis do `_diagnose` sinh từ
answer/contexts/reference của từng câu, không dùng diagnosis mặc định).

| Rank | id | Distribution | Question | avg_score | worst_metric | Diagnosis | Suggested fix |
|---|---|---|---|---|---|---|---|
| 1 | 33 | multi_hop | Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu? | 0.4499 | context_precision | Retrieval miss: part of the answer abstains ('không tìm thấy/không có thông tin') and reference facts ['500.000', '1.000.000'] are not in the top-3 contexts (F=0.78 AR=0.52 CP=0.00 CR=0.50). | Retrieval: decompose the question into one sub-query per asked item and merge the contexts (or raise rerank top_k), so the chunk holding these facts is retrieved. |
| 2 | 22 | multi_hop | Nếu cần mua một chiếc laptop 30 triệu cho nhân viên mới, ai phê duyệt và cần gì từ phòng CNTT? | 0.5104 | answer_relevancy | Retrieval miss: part of the answer abstains ('không tìm thấy/không có thông tin') and reference facts ['10 triệu', '50 triệu'] are not in the top-3 contexts (F=0.88 AR=0.00 CP=0.83 CR=0.33). | Retrieval: decompose the question into one sub-query per asked item and merge the contexts (or raise rerank top_k), so the chunk holding these facts is retrieved. |
| 3 | 39 | multi_hop | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA. | 0.5183 | context_recall | Retrieval miss: part of the answer abstains ('không tìm thấy/không có thông tin') and reference facts ['90'] are not in the top-3 contexts (F=1.00 AR=0.57 CP=0.50 CR=0.00). | Retrieval: decompose the question into one sub-query per asked item and merge the contexts (or raise rerank top_k), so the chunk holding these facts is retrieved. |
| 4 | 28 | multi_hop | Nhân viên cấp Lead nhận tổng phụ cấp hàng tháng (ăn trưa + điện thoại) là bao nhiêu? | 0.5409 | context_precision | No factual error found: the answer reaches every reference value from inputs present in the contexts; RAGAS faithfulness marks the computed statements (totals, percentages) as unsupported because the results are not written in the contexts (F=0.33 AR=0.83 CP=0.00 CR=1.00). | Evaluation: add an arithmetic check (recompute from context values) or a custom metric for derived values; generation: show the formula with the cited context values so each step is attributable. |
| 5 | 27 | multi_hop | Nhân viên có thâm niên 7 năm theo v2024 được nghỉ bao nhiêu ngày phép? Nếu bị trừ thêm 4 ngày ốm không có giấy y tế thì còn lại bao nhiêu? | 0.5471 | context_recall | Answer reaches the reference values, but the rule it uses is not stated in the contexts: the model inferred it from an example instead of a retrieved rule (F=0.33 AR=0.86 CP=1.00 CR=0.00). | Retrieval: retrieve the chunk that states the rule (parent chunk / neighbouring child); generation: forbid extrapolating rules from examples. |
| 6 | 21 | multi_hop | Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào? | 0.6250 | answer_relevancy | Retrieval miss: part of the answer abstains ('không tìm thấy/không có thông tin') and reference facts ['35 triệu'] are not in the top-3 contexts (F=1.00 AR=0.00 CP=1.00 CR=0.50). | Retrieval: decompose the question into one sub-query per asked item and merge the contexts (or raise rerank top_k), so the chunk holding these facts is retrieved. |
| 7 | 31 | multi_hop | Nhân viên đi công tác trong nước, ở khách sạn 2 đêm với giá 1.500.000 VNĐ/đêm. Công ty thanh toán tối đa bao nhiêu cho tiền khách sạn? | 0.6323 | context_precision | Answer omits or miscomputes reference values ['300.000'] although the needed inputs are retrieved (F=0.80 AR=0.56 CP=0.50 CR=0.67). | Generation: list every asked item and compute step by step from the context values; check the answer covers each part of the question. |
| 8 | 35 | multi_hop | Nhân viên Junior P1 có lương cơ bản 12 triệu vừa vào thử việc: nhận lương bao nhiêu và phụ cấp gì tháng đầu tiên? | 0.6352 | context_recall | Multi-hop gap: the contexts cover only part of the reasoning chain; reference facts ['1.000.000'] were not retrieved (F=0.88 AR=0.58 CP=0.58 CR=0.50). | Retrieval: one sub-query per hop and merge the contexts, or return parent chunks instead of 256-character children. |
| 9 | 34 | multi_hop | Nhân viên tạm ứng 4 triệu và một nhân viên khác tạm ứng 7 triệu: quy trình phê duyệt khác nhau thế nào? | 0.6814 | context_precision | Answer omits or miscomputes reference values ['15'] although the needed inputs are retrieved (F=1.00 AR=0.56 CP=0.50 CR=0.67). | Generation: list every asked item and compute step by step from the context values; check the answer covers each part of the question. |
| 10 | 45 | adversarial | Có cần kích hoạt xác thực đa yếu tố (MFA) không? | 0.6991 | answer_relevancy | No factual error found: the answer states the current rule but not the policy version ['v1.0', 'v2.0'] the reference anchors on; only answer_relevancy is low (F=1.00 AR=0.30 CP=1.00 CR=0.50). | Prompt: name the applicable policy version when a topic has several versions; re-run RAGAS to separate a real relevancy gap from metric noise on short Vietnamese answers. |

Đối chiếu answer/contexts/reference của các câu đại diện:

- **Retrieval thiếu ý ở câu nhiều vế (id 33, 22, 21, 39).** Top-3 child chunk 256 ký tự chỉ phủ một vế.
  Id 33 hỏi cả phụ cấp lẫn phép năm của Manager 12 năm: ba contexts đều là chunk nghỉ phép, không có chunk
  phụ cấp (ăn trưa 1.000.000, điện thoại Manager 500.000), nên answer trả lời "Không tìm thấy" cho phụ cấp. Vế
  phép năm cũng sai (18 thay vì 19 ngày) vì chunk quy tắc "+1 ngày mỗi 3 năm" không được lấy; model suy từ ví dụ
  "9 năm được 18 ngày". Id 22: chunk "Thẩm quyền phê duyệt" bị cắt sau dòng "dưới 5 triệu", nên answer đoán
  "Trưởng phòng" rồi tự mâu thuẫn; reference là Giám đốc phòng ban (5–50 triệu) và cần 3 báo giá (trên 10
  triệu). Id 21 và 39: thiếu chunk bảng lương Senior (20–35 triệu) và chunk chứa chu kỳ đổi mật khẩu 90 ngày của
  policy v1.0 (chỉ lấy được phần đầu của `mat_khau_v1.md`).
- **Suy diễn quy tắc từ ví dụ (id 27).** Context recall 0.00: không có chunk quy tắc thâm niên v2024. Answer
  viết "ta có thể suy ra ... khoảng 17 ngày" từ ví dụ 9 năm → 18 ngày, ra đúng 17 và 13 nhưng không có căn cứ;
  faithfulness 0.33 phản ánh đúng việc này.
- **Bỏ sót ý dù đã có input (id 31, 34, 35).** Id 31 trả lời đúng 2.400.000 nhưng không nêu phần vượt 300.000
  VNĐ/đêm nhân viên tự trả. Answer còn gọi mức 1.200.000 là "chi phí công tác nước ngoài": dòng này nằm trong mục
  "Công tác trong nước" của `cong_tac_phi.md`, nhưng prefix ngữ cảnh do m5 sinh cho chunk ghi nhầm là "nước
  ngoài" và generator chép lại. Đây là lỗi enrichment chứ không phải lỗi retrieval. Id 34 bỏ thời hạn hoàn ứng 15
  ngày. Id 35 không nêu số tiền ăn trưa 1.000.000 vì chunk `phu_cap.md` không nằm trong top-3.
- **Điểm thấp do evaluator, không phải lỗi nội dung (id 28, 45).** Id 28 trả lời đúng 1.000.000 + 300.000 =
  1.300.000, cả hai số đều có trong context, nhưng faithfulness 0.33 vì RAGAS coi câu tính tổng là không suy ra
  trực tiếp. Id 45 trả lời đúng "MFA bắt buộc cho email, VPN, hệ thống nội bộ"; chỉ answer_relevancy thấp (0.30).

## Matrix và nhóm yếu nhất

Mỗi câu được đếm một lần theo worst_metric của nó (matrix thống kê, không coi mọi câu là failure):

| worst_metric | factual | multi_hop | adversarial | Tổng |
|---|---|---|---|---|
| faithfulness | 1 | 4 | 1 | 6 |
| answer_relevancy | 14 | 6 | 3 | 23 |
| context_precision | 1 | 6 | 1 | 8 |
| context_recall | 4 | 4 | 5 | 13 |

Nhóm yếu theo mean thấp nhất: multi_hop; mean: 0.687 (adversarial 0.827, factual 0.879).
Worst metric xuất hiện nhiều nhất: answer_relevancy; số câu: 23/50.

Nhóm yếu được chọn theo mean avg_score, không theo tổng cột 20/20/10. Multi_hop yếu vì retrieval: cả
context_precision (0.733) và context_recall (0.717) đều thấp nhất trong ba nhóm, và 9/10 câu bottom-10 là
multi_hop. Câu multi_hop cần 2–3 dữ kiện ở các tài liệu khác nhau (phụ cấp + phép năm, lương + phép), trong
khi pipeline chỉ đưa 3 child chunk 256 ký tự vào prompt. Khi thiếu một vế, generator hoặc từ chối ("Không tìm
thấy") hoặc suy diễn từ ví dụ.

answer_relevancy là worst metric phổ biến nhất nhưng tập trung ở factual (14/20), nơi faithfulness 0.983 và
context_precision 0.992: answer đúng nhưng dài hơn câu hỏi cần (lặp lại ngữ cảnh, nêu tên tài liệu). RAGAS đo
metric này bằng cách sinh lại câu hỏi từ answer rồi so embedding với câu hỏi gốc, nên đây là vấn đề trình bày.
Đòn bẩy cho chất lượng đúng/sai là retrieval của multi_hop; insight tự động trong artifact gợi ý "Improve prompt
template" theo worst metric phổ biến nhất, nhưng đọc từng câu cho thấy prompt chỉ là đòn bẩy thứ hai.

Đề xuất sửa và cách kiểm tra:

1. Tách câu hỏi thành sub-query theo từng vế/hop (LLM hoặc luật theo dấu ":", "và", "Nếu ... thì"), search và
   rerank từng sub-query rồi gộp contexts. Kỳ vọng: context_recall của multi_hop tăng, ít "Không tìm thấy" hơn.
2. Trả parent chunk (2048 ký tự) của child khớp, hoặc ghép child liền kề, để bảng (thẩm quyền phê duyệt, khung
   lương) không bị cắt.
3. Prompt generation: trả lời đủ từng vế, ghi phép tính từ số trong context, cấm suy quy tắc từ ví dụ, câu đầu
   trả lời thẳng câu hỏi. Kiểm tra lại prefix ngữ cảnh của m5 trên các file có nhiều mục (trong nước/nước ngoài).
4. Chạy lại: `python scripts/setup_answers.py --live` rồi `python scripts/run_experiments.py --phase a --live`
   ít nhất 3 lần. Chỉ coi là cải thiện khi mean multi_hop và context_recall vượt dải dao động đã đo
   (0.687–0.701), đồng thời factual không giảm.

## Bẫy adversarial và giới hạn

Adversarial (0.827) thấp hơn factual (0.879) nhưng cao hơn multi_hop (0.687). Đọc từng answer:

- **Version conflict (41–45, 49).** Id 41 trả 15 ngày (v2024), id 43 trả 12 ký tự (v2.0), id 44 trả 120 ngày,
  id 45 trả MFA bắt buộc: dùng đúng bản hiện hành. Id 49 hỏi cả bản cũ và mới: answer nêu đúng v2023 = 12 ngày và
  nói v2024 đang hiệu lực nhưng không nêu số ngày của v2024. Id 42 trộn hai bản: answer nêu cả "mỗi 3 năm"
  (v2024) lẫn "mỗi 5 năm" (v2023 đã thay thế) như cùng hiệu lực, vì cả hai chunk đều được retrieve và chunk v2023
  không ghi rõ trạng thái. Id 42 có avg 0.715 (rank 12 ở lần chạy cuối; ở lần chạy 09:50 nó ở rank 9 với
  diagnosis version conflict).
- **Negation (46–48, 50).** Cả 4 câu trả lời đúng chiều phủ định ("KHÔNG được nghỉ phép năm", "không nên tự xử
  lý", "chưa được hưởng PVI", "không được dùng VPN cá nhân"), avg 0.81–0.97.
- Tổng hợp 10 câu adversarial: 8 câu đúng đủ, 1 câu thiếu ý (49), 1 câu trộn phiên bản (42). Điểm adversarial
  thấp hơn factual chủ yếu do context_recall 0.717: reference của câu bẫy nêu cả giá trị của bản cũ ("v2023 yêu
  cầu 5 năm"), mà context chỉ chứa bản hiện hành thì bị trừ recall dù answer đúng. Vì vậy điểm thấp hơn không tự
  chứng minh pipeline nhận ra bẫy; bằng chứng là việc đọc 10 answer ở trên.

Giới hạn: chỉ 50 câu (adversarial 10 câu, mỗi câu chiếm 1/10 mean nhóm); một lần generation (gpt-4.1-mini,
không cố định seed); evaluator cùng họ model với generator nên có thể ưu ái văn phong của chính nó; RAGAS dao
động giữa các lần chạy như đã nêu; chẩn đoán bottom-10 dựa trên luật đối chiếu số liệu/từ khóa nên cần người
đọc lại (đã đọc lại đủ 10 câu cho báo cáo này); hai PDF scan không được OCR.
