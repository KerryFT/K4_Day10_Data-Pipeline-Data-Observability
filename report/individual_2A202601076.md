# Member Role Report — Hoàng Vũ Trung Nguyên

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Hoàng Vũ Trung Nguyên |
| MSSV | 2A202601076 |
| Khóa/Lớp | K4 |
| Tên nhóm | Nhóm K4 — Data Pipeline & Data Observability |
| Vai trò chính | Ingestion & Cleaning Owner |
| Repository | `K4_Day10_Data-Pipeline-Data-Observability` (workspace local) |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input | Output | Trạng thái |
| --- | --- | --- | --- | --- |
| Raw ingestion | `src/ingestion/crossref.py`: `fetch_source_records`, `parse_crossref_payload`, `load_raw_records` | Crossref `/works` response | Raw response và danh sách `PaperRecord` | Hoàn thành |
| Cleaning/data model | `src/ingestion/cleaning.py`: `build_clean_dataframe` | `list[PaperRecord]`, `run_date` | Cleaned DataFrame 16 columns, CSV/JSON | Hoàn thành |
| Data contract | Raw/clean schema và cleaning rules | Crossref metadata | Schema dùng chung cho embedding/evaluation/corruption | Hoàn thành |

### Hỗ trợ ngoài phạm vi chính

| Hoạt động | Module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Kiểm tra repair data | `corruption_flow.py` | Baseline và repaired JSON giống nhau; cùng 24 rows |
| Kiểm tra artifact integration | Index/evaluation | `paper_id`, dates và `text_for_embedding` đáp ứng consumer contract |

## 3. Kết quả theo vai trò

| Nhiệm vụ | File/artifact | Kết quả | Cách xác minh |
| --- | --- | --- | --- |
| Parse Crossref | `crossref.py`, `data/raw/crossref_records.json` | 24 records có DOI, title, abstract và metadata chuẩn hóa | Load snapshot và đếm records |
| Lưu raw provenance | `data/raw/crossref_response.json` | Giữ payload gốc để trace và repair | Mở JSON và đối chiếu records |
| Clean dữ liệu | `cleaning.py`, `data/clean/papers_clean.*` | 24 rows, 16 columns, unique DOI, valid dates/summaries | Baseline quality 6/6 PASS |
| Tạo embedding text | `text_for_embedding` | Kết hợp title/authors/categories/abstract | Kiểm tra cleaned JSON/CSV |
| Hỗ trợ repair | `papers_clean_repaired.json` | Phục hồi đúng baseline | Equality test pass |

Output quan trọng nhất của tôi là cleaned dataset: nó là contract chung cho Chroma index, evaluation set, quality checks và corruption flow. Nếu schema hoặc document identity không ổn định, phép so sánh ba trạng thái sẽ không còn hợp lệ.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Metadata Crossref có XML/JATS trong abstract, ngày tháng không đồng nhất, trường authors/categories có thể thiếu và một số record không đủ dữ liệu cho embedding. Phần ingestion/cleaning phải tạo một schema ổn định, có thể trace về raw payload và dùng lại khi repair.

### Cách triển khai

Ingestion gọi `https://api.crossref.org/works` với query, filter `has-abstract:true`, rows limit và retry/backoff cho 429/503 hoặc request errors. Payload được lưu nguyên bản trước khi parse. Parser dùng DOI làm `paper_id`, lấy title đầu tiên, strip XML/JATS khỏi abstract, ghép tên tác giả, đọc subjects, ưu tiên các date fields hợp lệ và fallback DOI URL nếu cần.

Cleaning normalize whitespace/HTML, parse các dạng `%Y-%m-%d`, `%Y-%m`, `%Y`, tính `age_days`, tạo các joined/helper fields và `text_for_embedding`. Sau đó drop duplicate DOI, summary dưới 30 ký tự và record thiếu published date; cuối cùng sort deterministic theo published giảm dần và title tăng dần.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input ingestion | Crossref JSON `message.items` |
| Output ingestion | `list[PaperRecord]`, raw response/records JSON |
| Input cleaning | `list[PaperRecord]`, timezone-aware `run_date` |
| Output cleaning | DataFrame 16 columns và cleaned CSV/JSON |
| Module sử dụng output | `index.py`, `testset.py`, `quality.py`, `corruption.py` |
| Điều kiện lỗi | Thiếu DOI/title/abstract/date, summary quá ngắn, duplicate DOI, HTTP 429/503 |

### Cách xác minh

```powershell
$env:HF_HUB_OFFLINE='1'
$env:EVALUATION_JUDGE='heuristic'
.\.venv\Scripts\python.exe .\script\run_phase1.py
.\.venv\Scripts\python.exe .\script\run_corruption_flow.py
.\.venv\Scripts\python.exe -m unittest discover -s .\tests -v
```

- Kết quả: 24 cleaned rows, baseline quality 6/6, repaired dataset bằng baseline, 5/5 tests pass.
- Artifact: `data/raw/`, `data/clean/`, `data/quality/baseline_quality_report.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** cần document identity ổn định qua baseline, corrupted và repaired.
- **Phương án cân nhắc:** dùng index dòng/title hoặc dùng DOI từ Crossref.
- **Phương án chọn:** dùng DOI làm `paper_id`, còn Chroma `record_id` dùng `{paper_id}::{index}`.
- **Lý do:** DOI ổn định qua các lần clean/repair và phù hợp ground-truth document IDs; index dòng thay đổi khi drop/duplicate, title có thể bị truncate hoặc trùng.
- **Bằng chứng:** repaired JSON giống baseline và retrieval hit rate phục hồi từ 0.8 về 1.0.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** metadata từ nguồn có JATS/XML, missing fields và date structure khác nhau; nếu đưa thẳng vào embedding sẽ có noise hoặc lỗi schema.
- **Nguyên nhân gốc:** Crossref tổng hợp metadata từ nhiều publisher nên độ đầy đủ/định dạng không đồng nhất.
- **Cách xử lý:** strip tags, normalize whitespace, fallback date fields/DOI URL, bỏ record thiếu trường bắt buộc, parse date có kiểm soát và deduplicate DOI.
- **Cách xác minh:** cleaned baseline đạt 6/6 quality checks; không có null/duplicate `paper_id`, empty title, short summary hoặc stale record.
- **Điều học được:** lưu raw payload trước cleaning là cần thiết để audit và repair, không chỉ để debug.

Blocker tích hợp còn lại ngoài phạm vi ingestion là Gemini judge trả 404/429. Lượt xác minh cuối dùng heuristic backend có khai báo; chưa được coi là bằng chứng live LLM agent.

## 7. Hiểu biết về luồng end-to-end

1. Crossref payload được lưu raw, parse thành `PaperRecord`, clean thành schema ổn định, tạo `text_for_embedding`, encode bằng MiniLM và nạp vào ChromaDB.
2. Evaluation set lưu câu hỏi, đáp án và DOI ground truth. Retrieval hit kiểm tra DOI có nằm trong top-k; token F1/judge so sánh answer với ground truth.
3. Quality checks đo completeness, uniqueness và validity trên từng dataset; freshness tập trung vào tuổi/ngày xuất bản và stale rows.
4. Dùng cùng test set giúp cô lập biến số là chất lượng dữ liệu/index, tránh việc đổi câu hỏi làm sai phép so sánh.
5. Repair thành công khi repaired data trở lại baseline, quality/freshness phục hồi và agent metrics trở lại giá trị baseline.

## 8. Phân tích kết quả

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| --- | ---: | ---: | ---: | --- |
| Retrieval hit rate | 1.0000 | 0.8000 | 1.0000 | Mất latest records làm giảm khả năng tìm ground truth |
| Mean token F1 | 0.3200 | 0.2621 | 0.3200 | Missing/noisy content làm answer overlap giảm |
| Judge accuracy | 0.3000 | 0.2000 | 0.3000 | Heuristic judge; phục hồi đúng baseline |
| Mean judge score | 1.6000 | 1.4000 | 1.6000 | Thang 1–5; không phải live LLM judge |
| Quality checks | 6/6 PASS | 3/6 FAIL | 6/6 PASS | Duplicate, short summary và stale date bị phát hiện |
| Freshness | FRESH | STALE | FRESH | Corruption tạo 1 stale row |

Chuỗi nguyên nhân–bằng chứng:

1. Drop hai latest records và làm hỏng metadata → quality/freshness chuyển xấu → retrieval hit giảm 0.2 và token F1 giảm 0.0579.
2. Rebuild từ raw snapshot bằng cùng cleaning contract → repaired data bằng baseline → quality/freshness và cả bốn metrics phục hồi hoàn toàn.

Corruption ảnh hưởng trực tiếp nhất đến retrieval là drop ba latest records vì test set vẫn tham chiếu các DOI baseline. Stale date và duplicate tác động rõ nhất đến observability nhưng không nhất thiết trực tiếp làm answer sai.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Raw provenance và data contract ổn định là nền tảng để repair có thể kiểm chứng.
2. Quality/freshness signals giúp phát hiện lỗi trước khi chỉ nhìn thấy agent metrics giảm.
3. Retrieval/answer quality phụ thuộc trực tiếp vào completeness và tính sạch của corpus.

Nếu có thêm thời gian, tôi sẽ bổ sung unit tests riêng cho parser với payload thiếu DOI/date, nested JATS và duplicate records; đồng thời tăng evaluation set để đo ảnh hưởng theo từng corruption scenario độc lập.

## 10. Cam kết của thành viên

- [x] Nội dung phản ánh đúng vai trò Ingestion & Cleaning Owner.
- [x] Tôi có thể giải thích luồng end-to-end và dependencies của module mình.
- [x] Kết luận có artifact hoặc metric để đối chiếu.
- [x] Không nhận live LLM/Ragas là đã thành công khi chưa được xác minh.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo cá nhân tập trung vào phần việc của tôi, không sao chép nguyên báo cáo nhóm.

**Họ và tên:** Hoàng Vũ Trung Nguyên

**MSSV:** 2A202601076

**Ngày xác nhận:** 2026-08-06
