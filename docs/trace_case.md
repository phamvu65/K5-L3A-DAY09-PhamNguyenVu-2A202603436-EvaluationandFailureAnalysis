# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## C-002 — Agent dùng số ngày trễ trong ticket

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, run ID `R-seeded_regression-C-002-s11`. |
| Triệu chứng | Grader Lab 8 báo `status resolved != denied`. Reply và ledger đều ghi 20.000đ. Nhãn kỳ vọng `denied`, 0đ và 0 lần hoàn. |
| Bước sai đầu tiên | Bước 3, `model_override`, `{"delay_days": 5}`. Agent dùng số ngày khách khai trong ticket để thay số ngày trong hồ sơ đơn. |
| Vì sao là bước đầu tiên | Bước 1 chuyển đúng claim `C-002`. Ở bước 2, `lookup_order` trả đơn `O-202` với `delay_days: 2`, khớp hồ sơ gốc. Bước 3 đổi giá trị thành 5, rồi bước 4 áp dụng `SHIP-LATE-03` và tính 20.000đ. |
| Failure mode | `FM-03` (`ticket_trust`). Xem [bảng taxonomy](failure_taxonomy.md). |
| Đối chứng | `fixed C-002@11`, run ID `R-fixed-C-002-s11`. Sau khi tra đơn, bước 3 trả quote `no_entitlement` với 0đ. Trạng thái `denied`, ledger 0đ và 0 lần hoàn, khớp nhãn. |
| Regression test | `test_db_fact_and_ledger_for_c002` trong `src/tests/test_lab9_trace_case.py`. `DbFactKept` trả `False` cho `seeded_regression` và `True` cho `fixed`. Test cũng so số tiền trong ledger với nhãn cho cả hai bản. |
| Giới hạn | Kết luận dựa trên hai lần chạy của `C-002` tại seed 11. Để xác minh số ngày khi CLI cắt dòng `investigator`, tra `C-002` trong `src/data/public_claims.jsonl` và đối chiếu `O-202` trong `src/data/public_world_state.json`. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
