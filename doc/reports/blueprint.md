# Blueprint CI/CD cho RAG và guardrails

Nhóm: banana

Người phụ trách: Võ Doanh Nhân — 2A202602770

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy.
Nguồn kết quả: artifacts/ragas_50q.json, judge_results.json, guard_results.json.
Run timestamp: 2026-10-12T09:38:35.520309+00:00 (guard); guard models: `gpt-4.1-mini` (NeMo self check input/output).
Models generation/evaluator/judge từ A/B: generation `gpt-4.1-mini` (ragas_50q.json, judge_results.json);
evaluator `gpt-4.1-mini` + `text-embedding-3-small` (ragas_50q.json, run 2026-10-12T09:55:57Z); judge
`gpt-4.1-mini` (judge_results.json, run 2026-10-12T09:33:02Z).

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.
Request thực dừng sớm khi bị chặn; khác phép đo input layers chạy đủ hai tầng.

| Tầng | Làm gì | Khi chặn / lỗi | Log |
|---|---|---|---|
| Presidio (local, không gọi mạng) | Regex VN_CCCD (12/9 số), VN_PHONE (0[3-9] + 8 số) và recognizer có sẵn (EMAIL, PHONE_NUMBER, CREDIT_CARD, IBAN...). Chỉ các loại định danh này mới chặn; PERSON/LOCATION/DATE_TIME của spaCy tiếng Anh bị loại vì gán nhầm trên câu tiếng Việt ("v2024", "VPN"). | Chặn ngay, trả câu hướng dẫn bỏ thông tin cá nhân. Input chứa PII không được gửi tới NeMo/LLM. | Chỉ lưu bản `anonymized` (`<VN_CCCD>`), loại entity, thời điểm. |
| NeMo input (self check input) | Một lời gọi LLM phân loại Yes/No theo policy trong `guardrails/config.yml`: phạm vi HR/IT nội bộ, chặn off-topic, jailbreak, giả danh, trích system prompt, đòi dữ liệu người khác. | Trả câu từ chối của `rails.co`. Lỗi/timeout gateway: fail closed (từ chối kèm thông báo tạm thời), retry 1 lần. | Lưu quyết định rail (`activated_rails[].stop`), không lưu raw input chưa qua Presidio. |
| RAG | Hybrid BM25 + BGE-M3 (Qdrant), rerank bge-reranker-v2-m3 top-3, generation gpt-4.1-mini. | Không có context: trả "Không tìm thấy". | Lưu ids chunk, model, thời gian. |
| NeMo output (self check output) | Kiểm tra answer: định danh cá nhân, lương cá nhân, giá trị bí mật (mật khẩu, token) kể cả khi gắn nhãn demo/test. | Thay answer bằng câu từ chối. Lỗi/timeout: fail closed. | Lưu quyết định và lý do, không lưu answer bị chặn ở dạng thô. |

Secrets: khóa API chỉ nằm trong `.env` (có trong `.gitignore`), được nạp vào container bằng `--env-file`, không
đưa vào prompt, artifact hay log. Fallback: không có fallback "cho qua" khi guard lỗi; generation lỗi thì runner
ghi `extractive_fallback` (lượt chạy này 0/50 câu dùng fallback).

Bằng chứng tầng input/output (guard_results.json): attacks 20/20 bị chặn (4 bởi Presidio: id 1–4; 16 bởi NeMo
input: id 5–20), clean 8/8 được cho qua, output 4/4 đúng (201, 202 giữ nguyên; 203 CCCD và 204 mật khẩu bị thay
bằng câu từ chối).

Lịch sử chỉnh policy: lần chạy Phase C đầu tiên đạt 15/20 attacks (5 câu off-topic id 11–15 lọt) và 3/4 output (204
lọt). Log `llm_calls` của NeMo cho thấy nguyên nhân: prompt self check input yêu cầu chặn off-topic nhưng không nêu
phạm vi của trợ lý (phần `instructions` không được đưa vào prompt này), và model bỏ qua mật khẩu vì answer tự ghi
"dữ liệu kiểm thử giả lập". Đã sửa `guardrails/config.yml`: nêu phạm vi HR/IT và ví dụ loại yêu cầu ngoài phạm vi;
định nghĩa credential là giá trị bí mật thật, chặn cả khi gắn nhãn demo/test. Sau sửa: 20/20, 8/8, 4/4. Rủi ro:
prompt được chỉnh sau khi thấy lỗi trên chính bộ 28 input + 4 output này, nên kết quả có thể lạc quan; cần một bộ
held-out (xem Monitoring).

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Số mẫu timed: 20; warm-up: 2;
phương pháp: linear (8 clean inputs xoay vòng, `time.perf_counter`, trong một event loop).

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 5.99 | 19.40 | 26.04 | Đã đo (Task 12), local CPU trong Docker |
| NeMo input | 1486.89 | 2069.39 | 2469.16 | Đã đo (Task 12), 1 lời gọi gpt-4.1-mini qua gateway |
| Input guard sequential | 1499.28 | 2085.03 | 2476.97 | Đã đo (Task 12), vượt target 500ms |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer budget target: 500ms; kết quả thực tế/budget_ok: P95 2085.03 ms, `latency_budget_ok = false`.
Bottleneck là NeMo input: 20 mẫu NeMo nằm trong 1013–2569 ms, Presidio chỉ 3.7–27.7 ms. Thời gian NeMo gần như
toàn bộ là một vòng gọi LLM tới gateway (mạng + hàng đợi + sinh 1 token), nên tối ưu Presidio không giúp được.
Hướng giảm: (1) thay self check bằng classifier local nhỏ (embedding + logistic regression cho topic/injection),
chỉ gọi LLM khi classifier không chắc; (2) chạy NeMo input song song với retrieval và hủy request nếu bị chặn,
để latency guard bị che bởi RAG; (3) cache quyết định cho câu hỏi lặp lại; (4) dùng endpoint gần hơn hoặc model
nhanh hơn, giới hạn output 1 token. Mỗi hướng phải đo lại bằng đúng Task 12 (2 warm-up, ≥20 mẫu) và chạy lại
28 input để chứng minh không tăng false positive.

Kế hoạch đo phần chưa đo: thêm timestamp `perf_counter` quanh retrieval, rerank, generation và output rail
trong cùng request; 2 warm-up, ≥50 request từ bộ 50 câu + 8 clean; báo P50/P95/P99 theo từng tầng và tổng
end-to-end; đo riêng request bị chặn sớm (short-circuit) và request đi hết pipeline.

## CI gates đề xuất

- RAGAS faithfulness ≥0.75, avg_score ≥0.65 trên 50 câu.
- Attacks ≥18/20 cho CI đề xuất; clean 8/8 allowed; output cases đúng.
- Full guard P95 <500ms chỉ áp dụng sau khi thực sự đo full guard.

Mốc bắt buộc lab vẫn attacks ≥15/20; bonus ≥18/20 kèm clean controls đạt.

Đề xuất job (chưa triển khai; repo hiện chỉ có các lệnh, chưa có workflow CI):

1. Mỗi pull request (không tốn API): `python -m pytest tests/ -m "not integration" -q` và
   `python scripts/check_lab.py`. Cả hai đã trả exit code khác 0 khi fail.
2. Nightly hoặc khi đổi prompt/model/policy (tốn API, cần secret của CI):
   `python scripts/setup_answers.py --live`, rồi `python scripts/run_experiments.py --phase a --live`,
   `--phase b --live`, `--phase c --live --latency-samples 20`.
3. Gate ngưỡng: cần viết thêm một script, ví dụ `scripts/quality_gate.py` (chưa có), đọc ba artifact và trả exit
   1 khi MIN_FAITHFULNESS=0.75, MIN_AVG_SCORE=0.65, MIN_ATTACKS_BLOCKED=18, MAX_CLEAN_FP=0 hoặc
   MIN_OUTPUT_CASES=4 không đạt. Các biến MIN_* này chỉ là đề xuất; runner hiện tại không kiểm tra chúng.
   Vì RAGAS dao động giữa các lần chạy (multi_hop 0.687–0.701 trên 5 lần), gate RAGAS nên dùng trung bình ≥3 lần.

## Monitoring và cải tiến

- Guard: tỷ lệ chặn theo tầng (Presidio / NeMo input / NeMo output) theo giờ; cảnh báo khi lệch quá 2 lần so với
  trung bình 7 ngày. False positive: nút "bị chặn nhầm" cho người dùng, mẫu bị báo được người phụ trách đọc lại
  hằng tuần và đưa vào bộ clean controls nếu đúng là chặn nhầm. Bộ held-out: thêm attack/clean mới không dùng để
  chỉnh prompt, chạy trước mỗi lần đổi policy.
- Latency: P95 từng tầng trên traffic thật (sample 100%, chỉ lưu số đo); cảnh báo khi input guard P95 > 2500 ms
  (gần mức P99 đã đo) cho đến khi áp dụng các hướng giảm ở trên.
- Chất lượng RAG: lấy mẫu 5% câu hỏi thật mỗi ngày, chạy faithfulness và answer_relevancy (không cần reference);
  cảnh báo khi trung bình 3 ngày < 0.75. Khi tài liệu chính sách đổi phiên bản: re-index và chạy lại Phase A.
- Judge: tính lại κ với ≥20 nhãn người mỗi khi đổi model/prompt judge; dừng dùng judge tự động nếu κ < 0.6.
- Privacy: log chỉ chứa bản đã anonymize; không log input bị Presidio chặn ở dạng thô; khóa API chỉ trong secret store.
- Người xử lý: trưởng nhóm Võ Doanh Nhân nhận cảnh báo và phân công xử lý trong nhóm; production cần on-call riêng.
- Kết quả kiểm chứng bộ held-out (thực hiện bởi Đào Đức Hải — 2A202602752, nguồn `artifacts/extra/heldout_guard_results.json`):
  Đã bổ sung tập test held-out gồm 18 câu hoàn toàn mới (12 attacks + 6 câu hợp lệ về chính sách HR/IT từ `data/`, lưu tại `artifacts/extra/heldout_guard_set.json`) chưa từng dùng để chỉnh policy prompt.
  + Số attacks bị chặn: **12/12 (100%)**. Trong đó, 2 câu chứa PII (CCCD 12 số, SĐT VN, email) bị Presidio chặn ngay tại tầng đầu; 10 câu (jailbreak, prompt leak, off-topic, giả danh CEO, kịch bản bypass giả tưởng, trộn câu hỏi hợp lệ với đòi lương người khác) bị NeMo self check input chặn hoàn toàn.
  + Số câu hợp lệ bị chặn nhầm (False Positives): **0/6 (0%)**; cả 6 câu hỏi về nghỉ ốm, công tác phí, thử việc, báo cáo sự cố CNTT, cam kết đào tạo và mua sắm (kể cả câu chứa từ "xin lỗi") đều được cho qua (`allowed`).
  + Nhận xét: Bộ guardrails khái quát hóa tốt trên các tấn công và câu hỏi chưa từng thấy, chứng minh kết quả 20/20 attacks và 8/8 clean của bộ mẫu không phải là hiện tượng overfit do chỉnh prompt trên tập test.

RAGAS mean/worst distribution: avg_score 0.792 trên 50 câu; nhóm yếu nhất multi_hop 0.687 (factual 0.879,
adversarial 0.827).
Cohen’s κ: 1.0 (10/10 nhãn trùng human; p_e = 0.52).
Attacks passed: 20/20; clean false_positive_rate: 0.0 (8/8 allowed).

Cải tiến có thể kiểm tra, gắn với bằng chứng:

1. Query decomposition + parent chunk cho multi_hop (9/10 câu bottom-10 là multi_hop, context_recall 0.717):
   chạy lại Phase A ≥3 lần, kỳ vọng mean multi_hop vượt dải 0.687–0.701.
2. Metadata phiên bản/hiệu lực khi index và lọc bản đã thay thế (id 42 trộn quy tắc v2023 và v2024): kiểm tra
   lại 10 câu adversarial, kỳ vọng không còn answer nhắc quy tắc bản cũ khi câu hỏi không hỏi bản cũ.
3. Sửa prefix ngữ cảnh m5 cho file nhiều mục (id 31 gọi mức khách sạn trong nước là "nước ngoài"): kiểm tra
   prefix của các chunk `cong_tac_phi.md` và câu 31 sau khi sinh lại.
4. Classifier local trước NeMo input để giảm P95 input guard từ 2085 ms: đo lại Task 12 và chạy lại 28 input,
   yêu cầu vẫn 20/20 attacks và 8/8 clean.
5. Mở rộng bộ guard bằng held-out attacks/clean mới: Đào Đức Hải đã thực hiện với bộ 18 câu mới (`artifacts/extra/heldout_guard_set.json`), kết quả đạt 12/12 attacks blocked và 0/6 clean false positives (`artifacts/extra/heldout_guard_results.json`), khẳng định tính vững chắc của guard stack khi gặp dữ liệu thực tế.
