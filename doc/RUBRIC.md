# Rubric K4 Track 3B

**Bài nhóm, một repo chung. Bắt buộc 100 điểm; bonus tối đa 10.**
Chấm source và bằng chứng thật trong artifacts/reports; unit/mock tests không
thay API experiment. TEAM và lịch sử Git là bằng chứng đóng góp cá nhân; tỷ lệ
điểm cá nhân/nhóm theo thông báo coach, repo không tự đặt hệ số.

## Phần bắt buộc — 100 điểm

### Phase A — 30 điểm

| Task | Tiêu chí | Điểm | Bằng chứng |
|---|---|---:|---|
| 1 | Group đúng 20 factual, 20 multi_hop, 10 adversarial | 5 | Source, test set, tests |
| 2 | RagasEvaluation có 50 RagasResult thật, đủ 4 metric hữu hạn [0,1], khớp answers và models từ evaluator | 10 | m4 adapter, per_question và input sources |
| 3 | Bottom đúng 10 câu tăng avg_score; rank/diagnosis/fix đầy đủ và được exporter giữ nguyên | 7 | Task 3, JSON và failure_clusters.md |
| 4 | Matrix đúng; nhóm yếu chọn bằng mean thấp nhất; insight có nghĩa | 8 | Source, counts/means, report |

Không có artifacts/answers_50q.json khiến Phase A không chạy được: Phase A 0 điểm.
Empty list, NaN, missing rows và matrix column counts 20/20/10 dùng làm quality
không đạt tiêu chí tương ứng.

### Phase B — 35 điểm

| Task | Tiêu chí | Điểm | Bằng chứng |
|---|---|---:|---|
| 5 | LLM chọn A/B/tie dựa trên reference, reasoning/scores hợp lệ | 10 | 5 cặp ids 1,5,12,21,41 và nguồn A/B |
| 6 | 2 lượt/cặp, đổi thứ tự; winner/scores quy về A/B ban đầu | 10 | Source, hai lượt và consensus |
| 7 | κ đúng từ 10 nhãn binary trên đúng model_answer gốc | 10 | Helper prompt không leak human labels/notes, ids/labels/kappa |
| 8 | Position/verbosity rates đúng, counts và diễn giải | 5 | JSON và bias_report.md |

Bridge nhãn 0/1 và runner đã được cung cấp. Đánh giá answer mới của pipeline
thay supplied model_answer không phải calibration với bộ nhãn người. Không đưa
human_label/human_note vào prompt; không đổi winner A/B thành nhãn tốt/xấu.

### Phase C — 35 điểm

| Task | Tiêu chí | Điểm | Bằng chứng |
|---|---|---:|---|
| 9a | Presidio detect/redact CCCD/CMND, VN phone, email | 10 | Source và kiểm tra PII |
| 9b | Async input rail phản ánh quyết định rail, không heuristic từ khóa refusal | 5 | Calls/decisions và clean controls |
| 10 | Đủ 20 attacks, ≥15/20 đạt; 8/8 clean allowed, false-positive rate rõ | 10 | Hai nhóm input trong guard_results.json |
| 11 | Output sạch được giữ, output nhạy cảm thay/redact | 5 | 4 output cases và source |
| 12 | Scope input layers; warm-up thật 2 lượt; ≥20 positive timed samples; percentile tuyến tính đúng | 5 | Raw samples/statistics và blueprint |

Always-block không đạt Task 10 dù attacks=20/20. Test logic dùng mocks; thực
nghiệm/API report cần riêng. Budget 500ms là mục tiêu; số đo vượt budget vẫn
phải được ghi đúng và phân tích, không tự sửa số cho đạt.

### Task 13 — Blueprint bắt buộc

Điền kiến trúc, failure actions, CI/monitoring đề xuất, input-layer latency đã
đo và cải tiến. RAG/output/full guard ngoài phạm vi bắt buộc có thể ghi “chưa đo”
kèm kế hoạch. Không dùng input_guard_ms làm full-guard latency.

Blueprint không thêm quỹ điểm ngoài 100 và không phải workflow mặc nhiên đã chạy.
Các biến MIN_* trong ví dụ không tự tạo quality gate nếu script chưa kiểm tra.

## Điều kiện mất điểm

| Lỗi | Hệ quả |
|---|---|
| Còn # TODO trong phase_*.py | Trừ 5/module |
| Student test fail | Trừ 3/test |
| Blueprint trống, giữ placeholder hoặc chỉ giữ mẫu | Trừ 10 |
| Thiếu artifacts/answers_50q.json | Phase A 0 điểm |

Không đạt tiêu chí thì không nhận điểm tiêu chí đó; reports tồn tại không đủ làm
bằng chứng. Nộp muộn/sao chép/sửa sau deadline theo [RULES.md](RULES.md) và thông
báo coach, không tự thêm mức phạt chưa công bố.

## Bonus bài lab — tối đa 10 điểm

| Bonus | Điều kiện | Điểm |
|---|---|---:|
| Phase A | Adversarial mean < factual mean, kèm phân tích bẫy | +4 |
| Phase B | κ >0.6 trên đúng 10 supplied model_answers | +3 |
| Phase C | ≥18/20 attacks và clean 8/8 allowed | +3 |
| Tổng tối đa | Tách khỏi quỹ bắt buộc 100 | +10 |

Adversarial thấp hơn chỉ cho thấy nhóm đó khó hơn; không tự chứng minh pipeline
nhận ra version conflict. Không hạ chất lượng answers/sửa bộ test để đạt bonus.
Bonus bài lab không phải điểm giơ tay, phát biểu hoặc pitching; toàn bài tối đa 110.
