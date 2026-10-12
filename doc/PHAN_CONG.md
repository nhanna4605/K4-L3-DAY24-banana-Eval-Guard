# Phân công phần việc còn lại (Track 3B)

Trưởng nhóm: Võ Doanh Nhân — 2A202602770. Phần kỹ thuật bắt buộc (Tasks 1–13, bốn artifact live, ba báo cáo) đã xong
ở commit `7a0f68b`; `python scripts/check_lab.py --with-tests` báo 0 failed checks. Hai thành viên làm phần dưới, tự
commit bằng tài khoản GitHub của mình và tự điền mục INDIVIDUAL của mình trong `doc/TEAM.md`.

**Hạn chót cho cả nhóm: 13/10/2026 10:30**, để trưởng nhóm kịp cập nhật SHA và nộp lại trước 11:59.

## Chuẩn bị chung

```bash
git clone https://github.com/nhanna4605/K4-L3-DAY24-VoDoanhNhan-Eval-Guard.git
cd K4-L3-DAY24-VoDoanhNhan-Eval-Guard
docker build -f infra/lab.Dockerfile -t lab24 .
```

Tạo `.env` ở gốc repo bằng **khóa API của chính bạn**: `OPENAI_API_KEY=...` và, nếu dùng gateway tương thích OpenAI,
`OPENAI_BASE_URL=...`. Không bao giờ commit `.env` (đã có trong `.gitignore`), không dán khóa vào chat/báo cáo.

Chạy lệnh trong container:

```bash
docker run --rm -v "$PWD:/lab" -v "$PWD/../hfcache:/hfcache" --env-file .env -w /lab lab24 python scripts/check_lab.py --with-tests
```

Quy tắc: **không ghi đè** bốn file chính trong `artifacts/`. Kết quả thêm lưu ở `artifacts/extra/`. Nếu một runner lỡ
ghi đè file chính, khôi phục bằng `git checkout -- artifacts/`.

## Lê Đức Hùng — 2A202602849: kiểm chứng Phase A/B

1. Chạy `check_lab.py --with-tests` trên máy mình; ghi kết quả vào INDIVIDUAL.
2. Đo dao động RAGAS: chạy `python scripts/run_experiments.py --phase a --live` hai lần; sau mỗi lần chép
   `artifacts/ragas_50q.json` thành `artifacts/extra/ragas_run_hung_1.json`, `..._2.json`, rồi `git checkout --
   artifacts/ragas_50q.json`. So sánh mean từng distribution với dải đã ghi trong `doc/reports/failure_clusters.md`
   (factual 0.869–0.889, multi_hop 0.687–0.701, adversarial 0.815–0.834) và bổ sung một đoạn ngắn vào báo cáo đó.
3. Đọc lại 10 câu bottom-10 (answer/contexts/ground_truth trong `artifacts/ragas_50q.json`) và bảng judge trong
   `doc/reports/bias_report.md`; nếu thấy chẩn đoán hay nhận xét nào sai, sửa và ghi lại trong INDIVIDUAL.
4. Commit, push, điền mục `### LeDucHung-2A202602849` trong `doc/TEAM.md`.

## Đào Đức Hải — 2A202602752: bộ held-out cho Phase C

Policy prompt trong `guardrails/config.yml` đã được chỉnh sau khi thấy lỗi trên chính bộ 20 attacks + 8 clean, nên
kết quả 20/20 có thể lạc quan (xem `doc/reports/blueprint.md`). Việc cần làm:

1. Tự viết `artifacts/extra/heldout_guard_set.json`: ít nhất 10 attacks mới (off-topic, jailbreak, prompt injection,
   đòi dữ liệu cá nhân) và ít nhất 5 câu hợp lệ mới về chính sách HR/IT trong `data/`, cùng định dạng với
   `fixtures/adversarial_set_20.json` (`id`, `category`, `input`, `expected`). Không dùng CCCD/số điện thoại thật.
2. Chạy guard trên bộ này bằng các hàm có sẵn trong `src/phase_c_guard.py` (`setup_presidio`, `setup_nemo_rails`,
   `run_adversarial_suite`), lưu kết quả vào `artifacts/extra/heldout_guard_results.json`.
3. Ghi số attacks bị chặn, số câu hợp lệ bị chặn nhầm và nhận xét vào phần "Monitoring và cải tiến" của
   `doc/reports/blueprint.md`. Không sửa `guardrails/config.yml` sau khi đã chạy bộ held-out.
4. Commit, push, điền mục `### DaoDucHai-2A202602752` trong `doc/TEAM.md`.

## Trưởng nhóm sau khi hai bạn xong

Chạy lại `check_lab.py --with-tests`, ghi SHA cuối vào đầu `doc/TEAM.md`, push và nộp lại link trên VLearn.
