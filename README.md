# Lab 9 — Evaluation and Failure Analysis

**Phạm Nguyên Vũ · 2A202603436**

Bài cá nhân đánh giá agent hoàn phí giao hàng LogiX-VN. Eval chạy offline với MockLLM và dữ liệu giả lập. [Luật nghiệp vụ](docs/business_rules.md) · [Hợp đồng kết quả và trace](docs/contracts.md)

[Checkpoints Lab 9](CHECKPOINTS.md) · [Rubric Lab 9](RUBRIC.md) · [Checklist nộp bài](SUBMISSION.md)

## Bài nộp

| Mốc | Tài liệu và bằng chứng |
|---|---|
| M1 — Phân loại lỗi | [Failure taxonomy](docs/failure_taxonomy.md) · [Trace case](docs/trace_case.md) |
| M2 — Kiểm định judge | [Judge audit](docs/judge_audit.md) |
| M3–M4 — Grader và gate | [Eval Card](docs/eval_card.md) · [PRD v1.1](docs/PRD_v1.1.md) · [Baseline v1](src/reports/baseline_v1.json) · [Fixed](src/reports/eval_fixed.json) · [Seeded regression](src/reports/eval_seeded_regression.json) |
| M5–M7 — Advanced/Expert | [Eval set v2](src/data/eval/eval_set_v2.jsonl) · [Nhãn v2](src/data/eval/labels_v2.json) · [Baseline v2](src/reports/baseline_v2.json) |

## Cấu trúc

- [`docs/`](docs/) chứa tài liệu nộp Lab 9 và hai tài liệu tham chiếu về nghiệp vụ và trace.
- [`src/lab9/`](src/lab9/) chứa code đánh giá. [`src/config/`](src/config/) chứa metric spec và ánh xạ mã lỗi. [`src/data/eval/`](src/data/eval/) chứa eval set và nhãn riêng.
- [`src/lab8/`](src/lab8/), dữ liệu công khai và `src/requirements.txt` cung cấp agent `swarm` và các phụ thuộc của Lab 9. `src/tests/` và `src/grader_audit/` cũng phục vụ workflow kiểm tra Lab 8 được giữ trong repo.
- [`src/harness_map.yaml`](src/harness_map.yaml) ghi sơ đồ orchestration và eval. [`eval-gate.yml`](.github/workflows/eval-gate.yml) chạy các kiểm tra Lab 9.

## Chạy trên Windows PowerShell

Từ thư mục gốc, dùng `uv` để tạo môi trường Python 3.13 nếu máy chưa có môi trường của bài:

```powershell
uv venv --python 3.13
Set-Location -LiteralPath src
uv pip install --python '..\.venv\Scripts\python.exe' -r requirements.txt -r requirements-lab9.txt
```

Từ `src/`, kiểm tra môi trường, dữ liệu và test Lab 9:

```powershell
& '..\.venv\Scripts\python.exe' -m lab9.smoke
& '..\.venv\Scripts\python.exe' -m lab9.evalset --check
& '..\.venv\Scripts\python.exe' -m lab9.evalset --v2 --check
$lab9Tmp = Join-Path '.pytest_cache' ('lab9-' + [guid]::NewGuid().ToString('N'))
& '..\.venv\Scripts\python.exe' -m pytest -q -o addopts= --basetemp $lab9Tmp -k lab9
```
