# Đánh giá LLM Judge Phase B

Nhóm: banana

Người phụ trách: Võ Doanh Nhân — 2A202602770

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T09:33:02.502450+00:00.
Models generation/judge: generation `gpt-4.1-mini` (answer A trong `answers_50q.json`); judge `gpt-4.1-mini`
(pairwise Task 5 và helper nhị phân, temperature 0, `response_format=json_object`).

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ artifacts/answers_50q.json:answer; B từ
fixtures/human_labels_10q.json:model_answer; reference từ fixtures/test_set_50q.json:ground_truth.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

Lượt 1 judge(q, A, B); lượt 2 judge(q, B, A) rồi quy winner và scores về A/B gốc. Final = winner khi hai lượt
đồng ý, ngược lại là tie. Prompt chấm theo thứ tự chính xác (khớp reference, đúng phiên bản, giữ phủ định/điều
kiện) → đầy đủ → súc tích, nói rõ độ dài và vị trí không mang thông tin.

| id | Answer A (pipeline) | Answer B (model_answer cho sẵn) | winner_pass1 | winner_pass2 (quy về gốc) | final_winner | position_consistent | scores_pass1 | scores_pass2 (quy về gốc) |
|---|---|---|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc khi kết hôn. | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | B | B | B | True | A 0.7 / B 1.0 | A 0.7 / B 1.0 |
| 5 | Muốn mua thiết bị trị giá 55 triệu cần Tổng Giám đốc (CEO) phê duyệt. | Cần Giám đốc phòng ban phê duyệt. | A | A | A | True | A 1.0 / B 0.0 | A 1.0 / B 0.2 |
| 12 | Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là 1 tháng lương. | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | A | A | A | True | A 1.0 / B 0.6 | A 1.0 / B 0.8 |
| 21 | Một nhân viên Senior có 9 năm thâm niên được nghỉ 18 ngày phép năm (15 + 3) theo ví dụ trong phần quy định sử dụng. Tuy nhiên, thông tin về mức lương trong khoảng nào không được cung cấp trong đoạn văn đã cho. Vậy, số ngày phép năm là 18 ngày, còn lương thì "Không tìm thấy." | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | B | B | B | True | A 0.6 / B 1.0 | A 0.6 / B 1.0 |
| 41 | Mỗi nhân viên chính thức được hưởng 15 ngày phép năm có lương theo chính sách nghỉ phép năm phiên bản 2024. | Nhân viên được nghỉ 12 ngày phép năm. | A | A | A | True | A 1.0 / B 0.3 | A 1.0 / B 0.3 |

Reasoning của hai lượt (lượt 2 viết theo thứ tự đã đảo, tức "Answer A" của lượt 2 là B gốc):

- id 1 — lượt 1: Answer B chính xác hơn vì có đầy đủ thông tin về 3 ngày làm việc có lương, trong khi Answer A thiếu phần 'có lương'. Cả hai đều trả lời đúng số ngày nghỉ, nhưng B đầy đủ hơn. Cả hai đều súc tích và không thừa ý.
  Lượt 2: Answer A chính xác và đầy đủ hơn vì có đề cập rõ là nghỉ có lương, đúng với reference. Answer B thiếu thông tin về lương, làm giảm độ chính xác và đầy đủ.
- id 5 — lượt 1: Answer A chính xác khớp với reference về số tiền và người phê duyệt, đầy đủ ý hỏi, và súc tích. Answer B sai người phê duyệt, không đúng chính sách.
  Lượt 2: Answer B chính xác và đầy đủ theo chính sách tham chiếu, nêu rõ mức giá trên 50 triệu cần CEO phê duyệt. Answer A sai về người phê duyệt và không đúng con số.
- id 12 — lượt 1: Answer A chính xác và đầy đủ hơn khi nêu rõ điều kiện 'có từ 6 tháng trở lên' và mức thưởng tối thiểu là 1 tháng lương, khớp với reference. Answer B thiếu điều kiện về thời gian làm việc, nên không chính xác và không đầy đủ.
  Lượt 2: Cả hai đáp án đều chính xác và đầy đủ về con số thưởng Tết tối thiểu là 1 tháng lương. Tuy nhiên, đáp án B nêu rõ đối tượng là nhân viên chính thức có từ 6 tháng trở lên, đúng với câu hỏi và reference, trong khi đáp án A thiếu phần điều kiện này, nên đáp án B đầy đủ và chính xác hơn. Cả hai đều súc tích.
- id 21 — lượt 1: Answer B chính xác và đầy đủ hơn khi cung cấp cả số ngày phép và khoảng lương đúng theo chính sách tham chiếu. Answer A thiếu thông tin về lương, không đầy đủ. Cả hai đều súc tích, nhưng B vượt trội về độ chính xác và đầy đủ.
  Lượt 2: Answer A chính xác và đầy đủ theo chính sách v2024, nêu rõ số ngày phép (18 ngày) và khoảng lương (20-35 triệu). Answer B thiếu thông tin về lương, không đầy đủ. Cả hai đều súc tích, nhưng A vượt trội về độ chính xác và đầy đủ.
- id 41 — lượt 1: Answer A chính xác theo chính sách v2024 hiện hành (15 ngày), đầy đủ hơn khi nêu rõ phiên bản chính sách. Answer B chỉ đúng với chính sách cũ 2023, không đúng với yêu cầu ưu tiên phiên bản 2024. Cả hai đều súc tích.
  Lượt 2: Answer B chính xác theo chính sách v2024 hiện hành (15 ngày), đầy đủ và không sai lệch. Answer A chỉ nêu 12 ngày, là chính sách cũ đã bị thay thế, nên không chính xác. Cả hai đều súc tích, nhưng B đúng và đầy đủ hơn.

Position bias count/rate: 0/5 cặp không nhất quán; rate 0.0.
Verbosity win rate: 0.8 (4/5); decisive cases: 5 (A thắng và dài hơn 3, B thắng và dài hơn 1).

Không có cặp nào đổi winner khi đảo thứ tự: reasoning lượt 2 gọi đúng tên answer theo vị trí mới (ví dụ id 41,
lượt 2 nói "Answer B chính xác theo v2024 (15 ngày)", B lúc đó là answer A gốc). Verbosity 0.8 vượt ngưỡng 0.6
về mặt thống kê, nhưng đọc nội dung thì cả 4 winner dài hơn đều thắng vì có thêm dữ kiện đúng mà answer kia
thiếu: id 1 B thêm "có lương"; id 5 A nêu đúng CEO cho đơn 55 triệu trong khi B sai người duyệt; id 12 A nêu điều
kiện "từ 6 tháng trở lên"; id 41 A dùng đúng v2024 (15 ngày) còn B dùng bản cũ (12 ngày). Cặp còn lại (id 21)
winner là answer ngắn hơn (B, 82 ký tự) vì A dài (278 ký tự) nhưng bỏ trống phần lương. Với 5 cặp, tỷ lệ 0.8 là
dấu hiệu thống kê yếu; nội dung không cho thấy judge thưởng cho độ dài. Muốn kết luận về verbosity bias cần
cặp có độ dài khác nhau nhưng nội dung tương đương (ví dụ thêm câu đệm vào answer sai) và nhiều cặp hơn.

## Calibration đúng model_answer

Helper đánh giá đúng question/model_answer đang có trong fixtures/human_labels_10q.json;
không lấy answer mới của pipeline. Prompt chỉ nhận question, answer, reference.
Không gửi human_label, human_note hoặc phân bố nhãn human vào prompt.

| question_id | model_answer gốc | Nhãn judge | Reasoning của judge | human_label | agree |
|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | Câu trả lời đúng và đầy đủ theo tham chiếu, nêu rõ số ngày nghỉ và có lương khi kết hôn. | 1 | yes |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | Câu trả lời sai vì theo reference, đơn hàng trên 50 triệu cần Tổng Giám đốc phê duyệt, không phải Giám đốc phòng ban. | 0 | yes |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | Câu trả lời chính xác, đầy đủ ý về mức thưởng Tết tối thiểu cho nhân viên chính thức từ 6 tháng trở lên theo đúng nội dung tham chiếu. | 1 | yes |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | Câu trả lời đúng theo chính sách v2024, nêu rõ số ngày phép là 18 (15 cơ bản + 3 thâm niên) và mức lương Senior từ 20 đến 35 triệu, khớp với reference. | 1 | yes |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | Câu trả lời chính xác theo chính sách: nhân viên nghỉ việc sau 8 tháng (chưa đủ 1 năm cam kết) nên phải hoàn trả toàn bộ 25 triệu. | 1 | yes |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | Answer thiếu phê duyệt của Kế toán trưởng theo reference và không nêu rõ phí phạt áp dụng cho quá hạn 15 ngày, không chỉ 2% tháng trên toàn bộ 8 triệu. | 0 | yes |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | Câu trả lời đúng theo chính sách: phép năm 19 ngày (15 ngày cơ bản + 4 ngày thâm niên) và tổng phụ cấp 1.500.000 VNĐ/tháng (1.000.000 ăn trưa + 500.000 điện thoại Manager). | 1 | yes |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | Câu trả lời chỉ nêu 12 ngày phép năm theo chính sách cũ v2023, trong khi chính sách hiện hành v2024 quy định 15 ngày cơ bản cộng thêm 1 ngày mỗi 3 năm thâm niên, nên câu trả lời không chính xác theo phiên bản mới nhất. | 0 | yes |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | Câu trả lời khẳng định nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần, hoàn toàn phù hợp với nội dung tham khảo, bao gồm cả phủ định và điều kiện phê duyệt. | 1 | yes |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | Câu trả lời cho rằng được phép dùng VPN cá nhân miễn đảm bảo an toàn, trong khi chính sách rõ ràng cấm sử dụng VPN cá nhân và bắt buộc dùng VPN của công ty. | 0 | yes |

Cohen’s κ: 1.0.
Observed/chance agreement và diễn giải: p_o = 10/10 = 1.0; judge và human đều có 6 nhãn 1 và 4 nhãn 0 nên
p_e = 0.6 × 0.6 + 0.4 × 0.4 = 0.52; κ = (1.0 − 0.52) / (1 − 0.52) = 1.0 (almost perfect theo Landis–Koch). κ
được tính bằng `cohen_kappa` (Task 7) từ hai list nhãn trong `calibration`.

## Giới hạn và cách dùng judge

- Mẫu nhỏ: 5 cặp pairwise và 10 nhãn nhị phân. κ = 1.0 trên 10 câu có khoảng tin cậy rộng; chỉ một nhãn lệch
  đã kéo κ xuống 0.78–0.80 (p_o = 0.9, p_e = 0.50–0.54). Kết quả này chưa đủ để dùng judge thay người trên tập câu khác.
- Judge và generator cùng là gpt-4.1-mini, nên có thể ưu ái văn phong của chính nó (self-preference). Ở đây A
  (pipeline) thắng 3/5 và B (answer cho sẵn) thắng 2/5; cả 3 lần A thắng đều do B sai hoặc thiếu điều kiện theo
  reference. Nên kiểm tra thêm bằng một judge khác họ model.
- Bộ 10 câu calibration đều có reference rõ, nhiều câu là lỗi dễ thấy (sai phiên bản, sai người duyệt, đảo phủ
  định). Câu trả lời đúng một phần (id 29: đúng người duyệt cấp 1 nhưng thiếu Kế toán trưởng) cũng được judge
  chấm 0 trùng human, nhưng chưa có đủ ca mơ hồ để đo độ ổn định.
- Bổ sung 2026-10-12 (đọc lại, không chạy lại judge): nhãn trùng human nhưng reasoning của judge không phải lúc nào
  cũng bám đúng answer. Ở id 12 (calibration) judge ghi answer "đầy đủ ý ... cho nhân viên chính thức từ 6 tháng trở
  lên", trong khi `model_answer` "Nhân viên được thưởng Tết tối thiểu 1 tháng lương." không nêu điều kiện 6 tháng; ở
  lượt pairwise của cùng answer này (B), judge lại trừ điểm vì thiếu đúng điều kiện đó (B 0.6/0.8) còn human gắn nhãn
  1 ("Đúng và súc tích"). Id 46 tương tự: reasoning nhắc "điều kiện phê duyệt" mà answer không nêu. Vì vậy trong id 12
  chiến thắng của A (dài hơn) dựa trên chênh lệch độ đầy đủ mà human không coi là lỗi, nên đây là cặp mỏng nhất trong
  4 winner dài hơn. κ = 1.0 chỉ so khớp nhãn, không chứng minh lập luận của judge đúng.
- Cách dùng: judge là tín hiệu sàng lọc có reference, không phải đáp án tuyệt đối. Luôn chạy swap-and-average,
  lưu reasoning, lấy mẫu định kỳ các ca judge và human có thể bất đồng để người đọc lại, và tính lại κ khi đổi
  model hoặc prompt judge.
