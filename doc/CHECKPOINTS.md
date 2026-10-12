# Checkpoints K4 Track 3B

Bài nhóm, một repo chung. Ghi người phụ trách và bằng chứng trong `doc/TEAM.md`.
Cài đặt/tải model/indexing/generation là chuẩn bị trước lớp. Thời lượng trên lớp:
15 phút kiểm tra sẵn sàng + ba phase 30 phút.

## CP0 — Trước lớp và kiểm tra sẵn sàng

**Làm:** chuẩn bị Python 3.11/compiler, dependencies theo ENVIRONMENT, cache
model/Qdrant, năm module m1–m5 theo PIPELINE_INTERFACE; sinh 50 answers bằng
`python scripts/setup_answers.py --live` trước lớp.

**Sản phẩm:** môi trường làm lab và `artifacts/answers_50q.json` đủ 50 id, 20/20/10,
answer/contexts tách khỏi reference; generation_mode và generation_model đúng.

**Cần hiểu:** setup tự lắp module và generation, không gọi pipeline.py; resolve
dependencies/unit tests không chứng minh full NeMo/model đã cài chạy được.

**Tự kiểm tra:** pip check/imports, source interface, model cache và số answers.
Trong 15 phút đầu chỉ kiểm tra những thứ đã chuẩn bị và phân công nhóm.
Hoàn thành khi không còn installation/download/indexing lớn phải chờ.

## CP1 — Phase A đúng dữ liệu và nguồn bottom 10

**Làm:** Tasks 1–4; `python -m pytest tests/test_phase_a.py`, rồi
`python scripts/run_experiments.py --phase a --live`.

**Sản phẩm:** `artifacts/ragas_50q.json` và
`doc/reports/failure_clusters.md`.

**Cần hiểu:** matrix thống kê worst_metric của mọi câu; tổng 20/20/10 là số câu,
không đo chất lượng. Nhóm yếu nhất có avg_score trung bình thấp nhất.

**Tự kiểm tra:** 50 results, 4 metric mỗi câu, 10 bottom rows đúng thứ tự,
diagnosis/fix Task 3 giữ nguyên khi export; matrix/means/insight đối chiếu được.
Task 2 trả RagasEvaluation, metadata ghi đúng evaluator_models từ m4;
model generation/evaluator/judge/guard được tách theo vai trò.
Không chấp nhận list rỗng, NaN, missing rows hoặc chọn nhóm lớn làm nhóm yếu.

## CP2 — Phase B đủ hai quy trình judge

**Làm:** Tasks 5–8; tests offline; `python scripts/run_experiments.py --phase b --live`.

**Sản phẩm:** `artifacts/judge_results.json` và `doc/reports/bias_report.md`.

**Cần hiểu:** A/B/tie không phải nhãn 0/1. Năm cặp có ids 1,5,12,21,41; A từ
answers pipeline, B từ model_answer đã cung cấp, reference từ test set.
Mười nhãn binary đánh giá **đúng model_answer của human data**, không answer mới.

**Tự kiểm tra:** 10 pairwise calls (swap cùng reference), 10 binary judgments,
question ids aligned, label là integer 0/1. Không gửi human_label/human_note vào
prompt. κ tính từ nhãn thật; reasoning/scores/bias đúng và không giữ placeholder.

## CP3 — Chặn đúng, không chặn nhầm, latency có phạm vi

**Làm:** Tasks 9a–12; tests mock; chạy runner C với `--latency-samples 20`.

**Sản phẩm:** `artifacts/guard_results.json` chứa 20 attack results, 8 clean
results, 4 output results và latency raw samples/statistics.

**Cần hiểu:** always-block đạt 20/20 attacks nhưng fail clean controls. Expected
không được dùng quyết định actual. Input-layer sequential latency không đo
short-circuit request, RAG, output hay total guard.

**Tự kiểm tra:** attacks ≥15/20; clean 8/8 allowed, false_positive_rate=0; safe
output được giữ, unsafe output được thay/redact. Hai warm-up thực bị loại;
≥20 timed samples; positive durations; percentile tuyến tính từ samples.
Đo vượt budget vẫn ghi số thật. Bonus attacks ≥18/20 kèm clean controls đạt.

## CP4 — Báo cáo và nộp repo chung

**Làm:** điền ba Markdown trong `doc/reports/`, INDIVIDUAL trong TEAM;
chạy `python scripts/check_lab.py`, hoặc chỉ `python scripts/check_lab.py --with-tests` nếu muốn
gộp unit tests. Không chạy integration lại khi batch B/C đã có.

**Sản phẩm:** một repo có source, artifacts thật, reports đầy đủ và commit nộp.

**Cần hiểu:** checker mặc định không gọi API/chạy pytest; hash phát hiện report
stale nhưng không tự chứng minh API execution. Blueprint là đề xuất CI/CD;
phần ngoài phạm vi Task 12 được ghi “chưa đo”, không giữ `?` hoặc placeholder.

**Tự kiểm tra:** đúng schema/counts/sources/statistics, không placeholder hoặc
bảng rỗng trong báo cáo; artifacts có trên GitHub. Trưởng nhóm gửi một link theo
SUBMISSION và deadline coach công bố. Tất cả thành viên đã khai công việc thật.
