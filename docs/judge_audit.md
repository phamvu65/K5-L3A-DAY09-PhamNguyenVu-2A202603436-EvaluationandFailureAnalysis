# Judge audit

Chạy từ `src/` bằng `python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5` và lặp lại với `data/eval/judge_helpful_public.csv`. Trong cả hai bộ, `FAIL` là lớp dương vì mục tiêu là phát hiện phản hồi lỗi.

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| `tone_ok` | 100 | 0,757 | 0,857 | 0,800 | Đạt cả ba ngưỡng | Dùng để đánh giá giọng điệu. |
| `helpful` | 100 | 0,375 | 1,000 | 0,300 | Trượt κ và recall | Loại khỏi gate. |

## Các trường hợp bất đồng

| Case | Judge | Người | Kết luận audit | Sửa rubric |
|---|---|---|---|---|
| `H-008` | PASS | FAIL | Người chấm phù hợp. Cách xưng “em” cùng “nha” và “check giúp em” quá suồng sã với khách. | Cho ví dụ xưng hô thân mật vượt chuẩn CSKH và đánh giá cách xưng hô trong cả câu. |
| `H-017` | PASS | FAIL | Người chấm phù hợp theo ghi chú của bộ dữ liệu, trong đó khách lớn tuổi và được gọi là “bạn ơi”. | Cung cấp ngữ cảnh khách hàng cho judge khi rubric phụ thuộc vào cách xưng hô với người nhận. |
| `H-029` | PASS | FAIL | Người chấm phù hợp. Cụm “không cần nhắn thêm” gạt đi nhu cầu liên hệ của khách. | Chấm cả thông điệp. Từ mở đầu lịch sự vẫn có thể đi kèm câu ra lệnh. |
| `H-042` | FAIL | PASS | Người chấm phù hợp. Tin nhắn ngắn vẫn báo rõ đơn hàng, khoản hoàn và thời gian dự kiến. | Cho phép xác nhận ngắn gọn khi giao dịch đã hoàn tất. Chỉ yêu cầu xin lỗi khi tình huống cần. |
| `H-051` | FAIL | PASS | Người chấm phù hợp. Ghi chú xác nhận “refund” là từ được chấp nhận trong ngữ cảnh CSKH này. | Liệt kê các thuật ngữ được phép và chấm giọng điệu dựa trên cách giao tiếp với khách. |
| `HL-015` | PASS | FAIL | Người chấm phù hợp. Phản hồi báo 55.000đ nhưng ledger ghi 40.000đ. | Lấy số tiền đã hoàn từ ledger và kiểm tra bằng code trước khi đánh giá độ hữu ích. |
| `HL-016` | PASS | FAIL | Người chấm phù hợp. Phản hồi xin lỗi nhiều lần và báo 55.000đ, trong khi ledger ghi 35.000đ. | Xác minh nội dung giao dịch trước. Chấm lời xin lỗi trong tiêu chí giọng điệu. |
| `HL-047` | PASS | FAIL | Nhãn người chấm đánh trượt cách xưng hô. Lý do thuộc tiêu chí giọng điệu, đồng thời cụm “xử lý rồi” còn mơ hồ về kết quả. | Tách quy tắc xưng hô sang `tone_ok`. Với `helpful`, yêu cầu nêu kết quả hoặc bước tiếp theo cụ thể. |

## Kết luận

`tone_ok` có TP=24, FP=4, FN=6, TN=66. `helpful` có TP=9, FP=0, FN=21, TN=70. Tất cả 9 lỗi mà `helpful` báo đều đúng, nhưng nó chỉ bắt được 9 trong 30 lỗi theo nhãn người. Dùng nó làm gate sẽ để lọt 21 lỗi trong bộ này.

Hiệu chỉnh Rogan–Gladen đưa tỷ lệ lỗi ước tính của `tone_ok` từ 28% về 30% và của `helpful` từ 9% về 30%. Đây là hiệu chỉnh tỷ lệ trên cả tập. Kết quả chấm từng mẫu giữ nguyên, còn quyết định dùng judge dựa trên các ngưỡng κ, precision và recall.

Hai kết quả dùng verdict phát lại trên CSV công khai. Cần một tập mới có nhãn người chấm để kiểm tra lại sau khi sửa rubric. Tiền hoàn và approval được đối chiếu bằng code với ledger và quyết định của host.
