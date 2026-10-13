# Nhóm thực hiện K4 Track 3B

Tên nhóm: banana (3 thành viên)

Repo chung: https://github.com/nhanna4605/K4-L3-DAY24-banana-Eval-Guard

Trưởng nhóm/người nộp: Võ Doanh Nhân — 2A202602770

Ngày lab/deadline áp dụng: lab ngày 2026-10-12; hạn nộp 13/10/2026 11:59 theo trang nộp bài VLearn — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: 12384b6bf38e1e4b60c59df2adc90a3b8e64309e (bản đầy đủ của nhóm; commit sau đó chỉ ghi SHA này vào TEAM).

Mỗi nhóm nộp một repo. Lớp chuyển sang Track 3B làm nhóm sau khi Võ Doanh Nhân đã hoàn thành phần kỹ thuật; hai thành viên
còn lại nhận phần kiểm chứng và mở rộng ghi trong bảng dưới (hướng dẫn chi tiết: `doc/PHAN_CONG.md`). Mỗi người chỉ
khai phần mình thực sự làm.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Võ Doanh Nhân | 2A202602770 | Toàn bộ bài: lắp m1–m5 từ Day 18 và sửa m2/m4; Phase A Tasks 1–4 (`src/phase_a_ragas.py`); Phase B Tasks 5–8 (`src/phase_b_judge.py`); Phase C Tasks 9a–12 (`src/phase_c_guard.py`, policy prompt `guardrails/config.yml`); chạy setup và ba runner live; ba báo cáo; tích hợp, rà soát phần của hai thành viên và chạy bổ sung một lần RAGAS (`artifacts/extra/ragas_run_leader_1.json`) | Lịch sử commit của repo; `artifacts/*.json`; `doc/reports/*.md` |
| 2 | Lê Đức Hùng | 2A202602849 | Kiểm chứng Phase A/B: chạy lại tests và `check_lab.py --with-tests` trên máy mình; chạy thêm 2 lần RAGAS để đo dao động; đọc lại bottom-10, bảng judge và sửa báo cáo nếu phát hiện sai (hai lần RAGAS chưa chạy được vì không có khóa API; trưởng nhóm chạy bổ sung một lần) | Commit cb9155d; `artifacts/extra/phase_ab_verification_hung.md` và log |
| 3 | Đào Đức Hải | 2A202602752 | Mở rộng Phase C: bộ held-out ≥10 attacks + ≥5 câu hợp lệ mới (chưa dùng để chỉnh policy), chạy guard trên bộ đó, bổ sung kết quả vào phần Monitoring của blueprint | Commit 5694dcb; `artifacts/extra/heldout_guard_*.json`, `scripts/run_heldout_guard.py` |

Người tích hợp/chạy batch/nộp link: Võ Doanh Nhân (trưởng nhóm) — chạy `setup_answers.py --live`, runner A/B/C `--live`,
`check_lab.py --with-tests`, push repo và nộp link; bằng chứng là bốn artifact có `run_kind=live` và commit trên.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: host Windows 11 Home; toàn bộ lab chạy trong Docker Desktop 29.7.2, image tự build từ
`python:3.11-slim` (Python 3.11.16, build-essential cho Annoy), torch bản CPU.
Virtualenv/dependencies/imports: trong image chạy `pip install -r requirements/requirements.txt -c
requirements/constraints-core.txt`, `python -m spacy download en_core_web_lg`, `pip check` → "No broken requirements
found". Phiên bản thực tế: ragas 0.1.22, nemoguardrails 0.10.0, numpy 1.26.4, qdrant-client 1.9.2. Lỗi gặp và cách
xử lý: requirements không pin pyarrow/pandas nên pip cài pyarrow 26.0.0 và pandas 3.0.6, cần NumPy 2; lần chạy
setup đầu tiên dừng ở bước index với "pyarrow requires NumPy 2.0 or newer, found 1.26.4". Image được thêm một
layer pin `pyarrow==17.0.0` và `pandas==2.2.3`, sau đó `pip check` sạch và import ragas/nemoguardrails/presidio/
qdrant_client/sentence_transformers/underthesea đều chạy. Requirements của repo giữ nguyên.
`python -m pytest -q` trong container: 86 passed, 3 deselected (integration).
Models/Qdrant/50 answers đã chuẩn bị: Qdrant v1.9.7 bằng `docker compose -f infra/docker-compose.yml up -d`;
container lab dùng chung network namespace với Qdrant nên `localhost:6333` là Qdrant thật (đã kiểm tra client
là `QdrantRemote`, không phải `:memory:`). BGE-M3 và bge-reranker-v2-m3 tải về HF cache cục bộ. LLM
gpt-4.1-mini và embedding text-embedding-3-small qua một gateway tương thích OpenAI (`OPENAI_BASE_URL` trong
`.env`, không commit). `artifacts/answers_50q.json`: 50/50 câu `generation_mode=llm`, model `gpt-4.1-mini`,
không fallback. Giới hạn: `BCTC.pdf` và `Nghi_dinh_so_13-2023...pdf` là PDF scan không có text layer nên m1 bỏ qua
(không câu test nào dùng hai tài liệu này). NeMo full runtime đã chạy thật (guard_results.json, model guard
gpt-4.1-mini), không chỉ dựa trên unit test.

## INDIVIDUAL

### VoDoanhNhan-2A202602770

- Phần được giao và phần thực tế đã làm: làm toàn bộ phần kỹ thuật trước khi lớp chuyển sang làm nhóm. Phase A: nhóm 50 câu
  (Task 1), adapter `run_ragas_50q` lấy model từ metadata m4 và từ chối NaN (Task 2), `bottom_10` với chẩn đoán
  theo bằng chứng của từng câu: số liệu reference có trong contexts/answer hay không, giá trị suy ra bằng phép
  tính, câu trả lời từ chối, quy tắc của bản chính sách đã thay thế (Task 3), `cluster_analysis` chọn nhóm yếu theo
  mean (Task 4). Phase B: pairwise judge JSON có reference, swap-and-average, Cohen κ chính xác, bias report
  (Tasks 5–8). Phase C: `pii_scan` với Presidio, input/output rail đọc quyết định `activated_rails[].stop`, suite
  một event loop bỏ qua NeMo khi Presidio đã chặn, đo latency 2 warm-up + 20 mẫu (Tasks 9a–12). Pipeline: m1–m5
  từ bài Day 18; sửa m4 (khai báo evaluator LLM/embedding, trả `metadata.evaluator_models`, chuẩn hóa dấu câu để
  RAGAS không bỏ ý bullet, chấm lại NaN thay vì đổi thành 0) và m2 (tương thích API `search` của qdrant-client
  1.9). Đổi model trong `config.py`, `guardrails/config.yml`, m5 sang gpt-4.1-mini; viết lại policy prompt self
  check input/output.
- Bằng chứng: lịch sử commit trên GitHub; `artifacts/answers_50q.json`, `ragas_50q.json`, `judge_results.json`,
  `guard_results.json` (`run_kind=live`, `format_version=2`); `doc/reports/failure_clusters.md`, `bias_report.md`,
  `blueprint.md`.
- Cách kiểm tra: unit/mock tests `python -m pytest -q` (86 passed, gồm 26 student tests);
  `python scripts/check_lab.py --with-tests` (0 failed checks); live: `python scripts/setup_answers.py --live`,
  `python scripts/run_experiments.py --phase a|b --live`, `--phase c --live --latency-samples 20`. Kết quả: avg
  RAGAS 0.792 (multi_hop yếu nhất 0.687), κ = 1.0 trên 10 nhãn, attacks 20/20, clean 8/8, output 4/4, input guard
  P95 2085 ms. Đọc lại answer/contexts của đủ 10 câu bottom-10 và log `llm_calls` của NeMo để đối chiếu chẩn đoán.
- Điều đã học: điểm RAGAS cần đọc cùng answer/contexts vì metric có thể sai theo cả hai chiều (câu đúng có phép
  tính bị chấm faithfulness thấp; điểm dao động giữa các lần chạy). Nhóm yếu phải chọn theo mean chất lượng chứ
  không theo số câu. Judge cần swap-and-average và calibration với nhãn người, và tỷ lệ verbosity cao chưa chắc là
  bias khi winner dài hơn cũng đúng hơn. Guardrail chỉ đánh giá được khi có clean controls; self-check bằng LLM chỉ
  tốt bằng policy prompt của nó, và là nút thắt latency.
- Giới hạn/cách xử lý: (1) RAGAS NaN do ragas 0.1.22 bỏ câu không kết thúc bằng "." → chuẩn hóa dấu câu trong
  m4, kiểm chứng bằng chạy lại không còn NaN. (2) RAGAS dao động giữa 5 lần chạy → ghi dải dao động trong báo cáo,
  đề xuất gate dùng trung bình nhiều lần. (3) Lần chạy Phase C đầu đạt 15/20 attacks và 3/4 output → đọc prompt và
  completion thật của NeMo, sửa policy (nêu phạm vi, định nghĩa credential), chạy lại đạt 20/20, 8/8, 4/4; rủi ro
  là prompt được chỉnh trên chính bộ test, đã ghi trong blueprint. (4) Latency input guard vượt target 500 ms → ghi
  số thật và hướng giảm, không sửa số.
- Nguồn/AI hỗ trợ: m1–m5 lấy từ bài Day 18 của chính tôi
  (https://github.com/nhanna4605/K4-Track3A-DAY18-VoDoanhNhan-2A202602770-ProductionRAG, commit f5eff53). Dùng Claude
  Code (Anthropic) hỗ trợ đọc đề, viết mã Tasks 1–12 và các sửa lỗi m2/m4/config, dựng môi trường Docker, chạy các
  lệnh live, soạn nháp ba báo cáo và file này. Cách kiểm chứng: unit tests và `check_lab.py`, đọc lại từng câu
  bottom-10, đọc log prompt/completion của NeMo, mọi số trong báo cáo lấy từ artifact của lần chạy thật (bảng
  bottom-10, cặp A/B và nhãn nhị phân được chèn bằng script từ JSON). Không dùng AI để tạo số đo hay nhãn.

### LeDucHung-2A202602849

- Phần được giao và phần thực tế đã làm: được giao kiểm chứng Phase A/B (`doc/PHAN_CONG.md`, mục Lê Đức Hùng). Đã làm:
  (1) chạy `check_lab.py --with-tests` trong Docker (image `lab24` tự build); (2) đọc lại cả 10 câu bottom-10 (answer, 3
  contexts, ground truth, 4 metric) và đối chiếu từng ô của bảng với `bottom_10` trong artifact; (3) đọc lại 5 cặp pairwise
  và 10 nhãn nhị phân của Phase B, tính lại κ; (4) sửa báo cáo: ba chẩn đoán trong `failure_clusters.md` (id 28, 34, 39) và
  thêm một ghi chú vào `bias_report.md`. **Chưa làm được:** hai lần RAGAS live, vì máy của tôi không có khóa API/`.env`.
  Vì vậy tôi chưa đo được dao động RAGAS; chỉ tính lại mean của baseline (factual 0.8791, multi_hop 0.6867, adversarial 0.8272).
- Bằng chứng: `artifacts/extra/phase_ab_verification_hung.md` (báo cáo tổng hợp), `check_lab_with_tests_hung.log` và
  `check_lab_with_tests_hung_lf.log`, `ragas_live_attempt_blocked_hung.log`; mục "Kiểm chứng bổ sung 2026-10-12" cuối
  `doc/reports/failure_clusters.md`, các đoạn đã đánh dấu "đã sửa 2026-10-12" cùng đoạn bổ sung cuối danh sách giới hạn của
  `doc/reports/bias_report.md`. SHA của commit nằm trong lịch sử git của repo (không ghi vào file để tránh vòng lặp).
- Cách kiểm tra: `docker build -f infra/lab.Dockerfile -t lab24 .` (exit 0); `docker run ... lab24 python scripts/check_lab.py
  --with-tests` trên working tree Windows: exit 1, `86 passed`, nhưng 3 FAIL "Stale experiment source" ở Phase A/B/C artifact vì
  `core.autocrlf=true` đổi file sang CRLF làm lệch SHA-256 so với metadata (blob git LF của `answers_50q.json` là `5ee7c22a...`
  trùng metadata); chạy lại trên bản clone LF của cùng commit cộng các sửa tài liệu: exit 0, `86 passed`, `0 failed checks`. Thử
  `python scripts/run_experiments.py --phase a --live` trong bản sao cô lập: exit 2, thiếu `OPENAI_API_KEY`, không gọi API. Các
  phép tính lại (mean, κ, đối chiếu chuỗi nguồn A/B/reference) chạy bằng script Python đọc thẳng JSON. Bốn artifact chính được
  băm SHA-256 trước và sau, không đổi.
- Điều đã học: không tin điểm tổng hợp. Id 28 có answer đúng, đủ số liệu, nhưng context_precision 0.00 và faithfulness
  0.33; chỉ đọc contexts mới thấy hai chunk cần thiết đã có, nên đó là nhiễu evaluator chứ không phải lỗi retrieval. Id 34 bị
  gán nhầm cho generation vì luật chẩn đoán coi 15 là "giá trị suy ra" (20 triệu − 5 triệu), trong khi 15 ngày là chunk chưa được
  retrieve. κ = 1.0 trên 10 nhãn chỉ chứng minh nhãn trùng: reasoning của judge ở id 12 gán cho answer một điều kiện (6 tháng)
  mà answer không nêu. Mẫu 5 cặp quá nhỏ để kết luận verbosity bias.
- Giới hạn/cách xử lý: không có khóa API nên thiếu hai lần chạy RAGAS và thiếu so sánh baseline với run 1–2; tôi ghi rõ chuyện
  này, không điền số thay thế, và để lại bước chạy cho người có khóa. Kết luận "nhiễu evaluator" ở id 28/39 là suy luận từ mâu
  thuẫn giữa các metric và lịch sử 5 lần chạy trong báo cáo, chưa được kiểm bằng chấm lại. Judge pairwise không lưu phản hồi thô
  lượt 2 nên điểm sau khi đảo chỉ kiểm được qua reasoning và mã. Không sửa artifact, fixtures hay mã.
- Nguồn/AI hỗ trợ nếu có: dùng Claude Code (Anthropic) để đọc repo, viết các script Python kiểm tra, chạy các lệnh Docker/pytest ở
  trên và soạn nháp các đoạn báo cáo; kết quả lệnh và số liệu lấy từ log/JSON thật trong `artifacts/extra/` và artifact gốc. AI không
  tạo số đo hay nhãn mới, và không chạy RAGAS hay judge live. Tôi cần đọc lại các sửa đổi trước khi nộp.

### DaoDucHai-2A202602752

- Phần được giao và phần thực tế đã làm: Mở rộng kiểm chứng Phase C bằng bộ dữ liệu held-out độc lập (18 câu gồm 12 attacks và 6 clean inputs từ data/) nhằm đánh giá khách quan guard stack, tránh overfitting vào bộ 28 inputs mẫu ban đầu. Viết bộ dữ liệu `artifacts/extra/heldout_guard_set.json`, xây dựng script `scripts/run_heldout_guard.py` và chạy kiểm thử guard stack lưu tại `artifacts/extra/heldout_guard_results.json`, cập nhật kết quả và phân tích vào mục "Monitoring và cải tiến" của `doc/reports/blueprint.md`.
- Bằng chứng: Commit của thành viên trên Git; file `artifacts/extra/heldout_guard_set.json`, `artifacts/extra/heldout_guard_results.json`, `scripts/run_heldout_guard.py`; mục kết quả kiểm chứng bộ held-out trong `doc/reports/blueprint.md`.
- Cách kiểm tra: Chạy `python scripts/run_heldout_guard.py` đối chiếu với hợp đồng dữ liệu; chạy `python scripts/check_lab.py --with-tests` đạt 0 failed checks (86 tests passed). Kết quả: 12/12 attacks bị chặn (2 bởi Presidio, 10 bởi NeMo input rail), 6/6 clean inputs được allowed (false positive rate = 0.0), không có trường hợp chặn nhầm.
- Điều đã học: Khi đánh giá hệ thống Guardrails, việc đánh giá trên cùng tập kiểm thử đã dùng để tinh chỉnh prompt tiềm ẩn rủi ro overfit cao. Bộ held-out độc lập cho thấy Presidio xử lý hiệu quả PII tiếng Việt/quốc tế tại tầng mạng cục bộ trước khi gọi LLM, trong khi NeMo input rail phân định ranh giới nghiệp vụ HR/IT chuẩn xác, cho phép các câu hỏi lịch sự có từ "xin lỗi" đi qua mà không tạo false positive.
- Giới hạn/cách xử lý: Bộ held-out 18 câu đã bao quát các kỹ thuật tấn công chính (jailbreak, roleplay, prompt leak, off-topic, pii extraction, mixed attack) và các chính sách HR/IT chính, nhưng vẫn cần mở rộng thêm các ca đa ngữ và prompt injection lồng ghép phức tạp khi đưa lên môi trường production.
- Nguồn/AI hỗ trợ nếu có: Sử dụng Antigravity AI pair programmer hỗ trợ thiết kế bộ test case held-out và kiểm tra cú pháp schema, toàn bộ logic kiểm tra và số liệu đều được chạy thực nghiệm và kiểm chứng độc lập.

## Cập nhật sau khi nộp

Lần nộp đầu: 12/10/2026 17:07 (mã BN-261012-40595), khi bài còn làm một người theo Track 3A, commit 7a0f68b. Sau đó lớp
chuyển sang Track 3B làm nhóm: repo được cập nhật tiêu đề theo starter 3B (code, tests, fixtures, rubric không đổi), thêm
hai thành viên và phần việc của họ; nhóm đặt tên banana và repo được đổi tên thành
K4-L3-DAY24-banana-Eval-Guard. Hai thành viên commit phần của mình (cb9155d, 5694dcb); trưởng nhóm rà soát, chạy bổ sung một lần RAGAS, sửa
một nhận xét nói quá trong blueprint, ghi SHA cuối ở đầu file và nộp lại link mới trước hạn 13/10/2026 11:59.
