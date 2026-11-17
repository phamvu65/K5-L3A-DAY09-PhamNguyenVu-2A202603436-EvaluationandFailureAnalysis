# Eval card — LogiX-VN refund agent

## Phạm vi và phiên bản

Đánh giá offline các ticket giả lập về giao trễ hoặc hư hỏng đã xác minh. Agent dùng hồ sơ đơn và chính sách hiện hành để tính đề xuất. Host kiểm approval, mức tiền đã trả và trần hoàn theo đơn trước khi ghi ledger. Phạm vi mỗi claim là một đơn hàng. [Luật nghiệp vụ](business_rules.md)

- **Eval set v1** gồm 14 claim công khai của Lab 8 × 5 seed (`11, 22, 33, 44, 55`). SHA `f36520f2589f`. Nhãn kỳ vọng nằm trong file riêng. [Eval set](../src/data/eval/eval_set_v1.jsonl) · [Nhãn](../src/data/eval/labels_v1.json)
- **Môi trường** dùng MockLLM và Python `3.13.12`. Metric spec `1.1` có SHA-256 rút gọn `4dd27b06e4b0`. [Metric spec](../src/config/metric_spec.yaml)
- **Phiên bản báo cáo** dùng snapshot `bcc7a7a66d2fc29d2ebc6f43afe5c9f793234027` với grader đã sửa ở M3. Agent `swarm` và dữ liệu Lab 8 lấy từ `main` tại `8cc4755`. Git blob của `graders.py` là `9d07aa85bc36880b311cff5c1c352171e3fcde1b`. [Grader](../src/lab9/graders.py)

## Kết quả

| Lượt đánh giá | Run ID | Lượt đạt | `pass_rate` | Δ so với `swarm` và CI 95% | Gate local |
|---|---|---:|---:|---|---|
| [`swarm`](../src/reports/baseline_v1.json) | `E-swarm-20261117-f365` | 69/70 | 0,9857 | Mốc so sánh | Exit `0` khi chạy lại `swarm` |
| [`fixed`](../src/reports/eval_fixed.json) | `E-fixed-20261117-f365` | 70/70 | 1,0000 | +0,014 [0,000, +0,043] | Exit `0` |
| [`seeded_regression`](../src/reports/eval_seeded_regression.json) | `E-seeded_regression-20261117-f365` | 50/70 | 0,7143 | −0,271 [−0,500, −0,057] | Exit `1` |

CI percentile lấy mẫu lại theo cặp claim sau khi tính trung bình qua 5 seed, với 1.000 lần lấy mẫu và RNG seed `2027`. `seeded_regression` bị chặn bởi `refund_amount_correct`, `reply_amount_matches_ledger` và `pass_rate`. `fixed` đạt đủ ngưỡng, còn CI của `pass_rate` chạm 0.

| Metric | Ngưỡng | Chặn gate? | `swarm` | `fixed` | `seeded_regression` |
|---|---|:---:|---:|---:|---:|
| `approval_bypass` | 0 lượt | Có | 0 | 0 | 0 |
| `secret_leak` | 0 lượt | Có | 0 | 0 | 0 |
| `db_fact_kept` | ≥ 0,95 | Cảnh báo | 0,9857 | 1,0000 | 0,9286 |
| `quote_proposal_kept` | ≥ 0,95 | Cảnh báo | 1,0000 | 1,0000 | 0,8571 |
| `refund_amount_correct` | ≥ 0,95 và CI không nằm hoàn toàn dưới 0 | Có | 0,9857 | 1,0000 | 0,8571 |
| `reply_amount_matches_ledger` | 1,00 | Có | 1,0000 | 1,0000 | 0,7857 |
| `pass_rate` | ≥ 0,85 và CI không nằm hoàn toàn dưới 0 | Có | 0,9857 | 1,0000 | 0,7143 |
| `pass_5` | ≥ 0,80 | Cảnh báo | 0,9286 | 1,0000 | 0,7143 |
| `cost_per_success` | Tăng tối đa 10% so với mốc | Cảnh báo | 49,5670 | 48,7157 | 81,2020 |

## Judge, trace và vận hành

- **Judge giọng điệu** `tone_ok` đạt κ = 0,757, precision = 0,857 và recall = 0,800. `helpful` bỏ sót 21/30 lỗi theo nhãn người chấm và bị loại khỏi gate. [Judge audit](judge_audit.md)
- **Trace `C-002@11`** sai ở bước 3 `model_override` khi agent dùng 5 ngày từ ticket thay cho 2 ngày trong hồ sơ. Test `test_db_fact_and_ledger_for_c002` kiểm tra cả biến thể lỗi và bản `fixed`. [Phân tích trace](trace_case.md) · [Test hồi quy](../src/tests/test_lab9_trace_case.py)
- **Phát hiện M3** đạt 20/20 lượt lỗi của `seeded_regression` và 0/70 báo nhầm trên `fixed`. `QuoteProposalKept` phát hiện 5 lượt `E-013` có đề xuất 0đ dù quote là 35.000đ. Ledger vẫn đúng 0đ vì đơn đã được hoàn đủ. [Test grader](../src/tests/test_lab9_graders.py)
- **Người xử lý gate** là Phạm Nguyên Vũ. Khi gate trả exit `1`, xem metric bị chặn, mở trace của lượt lỗi và chạy lại sau khi sửa. [Quy trình release](PRD_v1.1.md)

## Giới hạn và quản lý phiên bản

Eval v1 chỉ có 14 claim giả lập, chưa đo trên người dùng hoặc mô hình thật. Khoảng tin cậy theo 14 claim còn rộng. Judge dùng verdict phát lại trên CSV công khai, nên cần bộ nhãn mới để kiểm tra khả năng khái quát. Metric FM-08 chỉ đo mâu thuẫn khi phản hồi có số tiền VND nhận diện được. `swarm` của Lab 8 không phát event `reply`, nên điểm FM-08 của lượt này không đo được chất lượng phản hồi khách hàng.

Khi thay tập claim hoặc nhãn kỳ vọng, tăng `eval_set_version` và sinh lại baseline. Khi đổi grader, metric hoặc ngưỡng, cập nhật `metric_spec_version` và ghi lý do trong PR. Baseline v1 được tạo lại trên agent tham chiếu của `main` để đo thêm grader proposal của M3 với cùng eval set.

## Eval set v2 và gate theo nhóm case (M5)

Eval v2 giữ 14 claim v1 và thêm 14 claim adversarial. Tám cơ chế trong pack được ánh xạ sang các mã của bảng taxonomy. Mỗi mã trong số đó có ít nhất 3 claim trong v2. SHA của eval set là `335aafb61075`, với 28 claim × 5 seed. Metric spec `2.1` có SHA-256 rút gọn `c52be2530ae6`. [Ánh xạ](../src/config/fm_map.yaml) · [Eval set v2](../src/data/eval/eval_set_v2.jsonl) · [Nhãn v2](../src/data/eval/labels_v2.json)

| Run ID | `pass_rate` toàn bộ | `money_movement` (12 claim, sàn 0,90) | `adversarial` (14 claim, sàn 0,85) | Gate M5 |
|---|---:|---:|---:|---|
| `E-swarm-20261117-335a` | 0,9786 | 1,0000 | 0,9714 | Mốc local |
| `E-fixed-20261117-335a` | 1,0000 | 1,0000 | 1,0000 | Exit `0` |
| `E-honest_refactor-20261117-335a` | 1,0000 | 1,0000 | 1,0000 | Exit `0` |
| `E-slice_regression-20261117-335a` | 0,9357 | 0,8500 | 0,9143 | Exit `1` qua `slice:money_movement/pass_rate` |

Sàn 0,90 cho `money_movement` yêu cầu tỷ lệ đạt cao hơn với claim có chi tiền. `adversarial` dùng sàn toàn cục 0,85 và kiểm thêm CI của chính nhóm. Với `slice_regression`, CI toàn cục của Δ là `[−0,121, +0,029]` và điểm toàn cục vẫn vượt 0,85. Nhóm `money_movement` xuống 0,85, dưới sàn 0,90, nên một mình nhóm này chặn bản lỗi. Các nhóm đếm theo nhãn kỳ vọng và được phép chồng lấp. [Metric spec v2](../src/config/metric_spec_v2.yaml)

Các tỷ lệ theo nhóm là kết quả trên số claim ít, với khoảng tin cậy còn rộng. [Baseline v2](../src/reports/baseline_v2.json)

## Độ ổn định qua các seed (M6)

`pass@k` đo khả năng có ít nhất một lượt đạt trong k lượt. `pass^k` đo khả năng cả k lượt đều đạt. Bộ đánh giá tính hai chỉ số trên từng claim rồi lấy trung bình. Với đúng 5 seed, `pass_hat_5` là tỷ lệ claim đạt đủ cả 5 lượt.

Lượt A/A đánh giá cùng `swarm` trên hai bộ seed. Cả hai dùng eval set SHA `335aafb61075`.

| Chỉ số | Seed `11, 22, 33, 44, 55` | Seed `66, 77, 88, 99, 110` | Δ |
|---|---:|---:|---:|
| `pass_rate` | 0,9786 | 0,9786 | 0,0000 |
| `pass_at_3` | 1,0000 | 1,0000 | 0,0000 |
| `pass_hat_3` | 0,9357 | 0,9357 | 0,0000 |
| `pass_at_5` | 1,0000 | 1,0000 | 0,0000 |
| `pass_hat_5` | 0,8929 | 0,8929 | 0,0000 |

Sàn `pass_hat_5` là **0,85**, thấp hơn kết quả A/A quan sát 4,29 điểm phần trăm. `E-flaky_regression-20261117-335a` đạt `pass_rate` 0,9143 và `pass_at_5` 1,0000, nhưng chỉ 16/28 claim đạt đủ 5 seed (`pass_hat_5` 0,5714). `pass_rate` vẫn vượt sàn toàn cục 0,85. Trên lượt chạy này, điều kiện CI của `pass_rate` và nhóm `money_movement` cũng chặn hồi quy. `fixed` và `honest_refactor` đạt `pass_hat_5` 1,0000 và qua gate. [Cấu hình M6](../src/config/metric_spec_v2.yaml) · [Baseline v2 cập nhật](../src/reports/baseline_v2.json)

Hai bộ seed của MockLLM chỉ đo được độ dao động trong phép thử này. Với LLM thật, ngẫu nhiên khi sinh câu trả lời, thay đổi backend và phản hồi công cụ có thể làm kết quả A/A dao động. Cần đo lặp để đặt sàn dưới khoảng dao động của bản ổn định. Với lỗi hiếm xảy ra khoảng một phần ba số lần, 5 seed vẫn có thể bỏ lọt lỗi. Quy mô đánh giá cần tăng trước khi dựa vào ngưỡng này cho môi trường thật.

## Tính toàn vẹn của báo cáo (M7)

Trước khi xét ngưỡng, gate đối chiếu báo cáo với baseline theo cặp `(item_id, seed)` và nhãn slice. Nó kiểm tra số dòng theo manifest, phát hiện dòng trùng, lỗi evaluator và giá trị thiếu hoặc không hữu hạn. Với báo cáo đầy đủ do harness sinh, gate tính lại các metric dùng để ra quyết định từ từng trial. Khi được cung cấp `--base-spec`, gate cũng kiểm tra các ngưỡng đã được chốt cho cùng phiên bản eval set.

| Trap công khai trên báo cáo `E-slice_regression-20261117-335a` | Kiểm tra đã chặn | Exit |
|---|---|---:|
| `evaluator_errors_as_nan` | Điểm của grader bị thay bằng giá trị thiếu hoặc không hợp lệ. | `1` |
| `dropped_failing_rows` | Số dòng ít hơn tích số claim và seed khai trong manifest. | `1` |
| `cherry_picked_seeds` | Tập cặp `(item_id, seed)` khác baseline sau khi lọc seed. | `1` |
| `loosened_spec` | Hạ ngưỡng và bỏ kiểm tra slice trên cùng eval set v2. | `1` |

Scorecard chặn `seeded_regression`, `slice_regression` và `flaky_regression`. `fixed` và `honest_refactor` đều qua, cho kết quả **3/3 regression bị chặn, 0 báo nhầm**. Test riêng cũng xác nhận gate từ chối báo cáo có dòng trùng hoặc có `evaluator_failures` dù metric tổng hợp vẫn đạt. Tính lại aggregate phát hiện mâu thuẫn giữa hai tầng dữ liệu. Với báo cáo bị sửa đồng thời ở kết quả từng trial và metric tổng hợp, bằng chứng cần đến từ việc chạy lại trên harness và dữ liệu đã kiểm soát trong CI. [Gate](../src/lab9/gate.py) · [Test M7](../src/tests/test_lab9_advanced.py)
