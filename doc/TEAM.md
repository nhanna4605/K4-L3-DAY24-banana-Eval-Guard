# Nhóm thực hiện K4 Track 3A

Tên nhóm: VoDoanhNhan (nhóm 1 người)

Repo chung: https://github.com/nhanna4605/K4-L3-DAY24-VoDoanhNhan-Eval-Guard

Trưởng nhóm/người nộp: Võ Doanh Nhân — 2A202602770

Ngày lab/deadline áp dụng: lab ngày 2026-10-12; hạn nộp 13/10/2026 11:59 theo trang nộp bài VLearn — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: 7a0f68bd01ab5611b8b95b2c09dc686fb8407f90 (commit cuối trên main chỉ ghi SHA này vào TEAM)

Mỗi nhóm nộp một repo. Nhóm này có một thành viên nên bảng chỉ có một row và một mục INDIVIDUAL.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Võ Doanh Nhân | 2A202602770 | Toàn bộ bài: lắp m1–m5 từ Day 18 và sửa m2/m4; Phase A Tasks 1–4 (`src/phase_a_ragas.py`); Phase B Tasks 5–8 (`src/phase_b_judge.py`); Phase C Tasks 9a–12 (`src/phase_c_guard.py`, policy prompt `guardrails/config.yml`); chạy setup và ba runner live; ba báo cáo | Lịch sử commit của repo; `artifacts/*.json`; `doc/reports/*.md` |

Người tích hợp/chạy batch/nộp link: Võ Doanh Nhân — chạy `setup_answers.py --live`, runner A/B/C `--live`,
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

- Phần được giao và phần thực tế đã làm: làm toàn bộ bài vì nhóm có một người. Phase A: nhóm 50 câu
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

## Cập nhật sau khi nộp

Phiên bản nộp là commit ghi ở đầu file; các commit sau đó trên nhánh main chỉ sửa file này (ghi SHA và hạn nộp). Chưa có cập
nhật sau khi nộp.
