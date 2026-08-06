# Group Report — Day 10: Data Pipeline & Data Observability

> Dùng mẫu này cho báo cáo chung của nhóm 3–5 thành viên. Thay toàn bộ nội dung trong dấu `[ ]` bằng thông tin và kết quả thực tế. Xóa các dòng hướng dẫn không còn cần thiết trước khi nộp.

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | [K3 hoặc K4]              |
| Tên nhóm         | [Tên hoặc mã nhóm]     |
| Repository         | [Đường dẫn repository] |
| Ngày hoàn thành | [YYYY-MM-DD]               |

### Thành viên và phân công

| STT | Họ và tên | Vai trò chính | Module/deliverable sở hữu | Trách nhiệm cụ thể |
| --: | --- | --- | --- | --- |
| 1 | Hoàng Vũ Trung Nguyên | Ingestion & Cleaning Owner | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py` | Gọi Crossref API, parse raw payload, lưu raw artifacts; Cleaning, chuẩn hóa schema, tạo `text_for_embedding` |
| 2 | Hoàng Trung Hải | Evaluation & Observability Owner | `src/evaluation/testset.py`, `src/observability/quality.py`, `src/observability/reporting.py` | Tạo evaluation test set từ cleaned data; Data quality checks, freshness monitoring; Markdown report generation |
| 3 | Vũ Hữu Trường | Corruption & Integration Owner | `src/ingestion/corruption.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` | Simulate data corruption scenarios; Orchestrate baseline pipeline end-to-end; Orchestrate corruption → evaluate → repair → compare flow |

## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

[Viết phần tóm tắt tại đây.]

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref API (`source_query`, `source_filter`) | Fetch với retry/backoff (429/503), parse JSON payload thành `PaperRecord` | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Nguyên |
| Cleaning          | `data/raw/crossref_records.json` | Normalize text, strip HTML, parse dates, tính `age_days`, tạo `text_for_embedding`, drop duplicates/invalid | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Nguyên |
| Embedding/index   | `data/clean/papers_clean.csv` | `all-MiniLM-L6-v2` encode → ChromaDB collection (cosine similarity) | `data/embeddings/papers_embeddings.json`, `data/chroma/` | Trường (trong phase1.py) |
| Evaluation        | Cleaned dataset + test set | Tạo test set từ cleaned data, tính retrieval hit rate / token F1 / judge score | `data/eval/test_set.json`, `data/results/baseline_metrics.json` | Hải |
| Observability     | Cleaned dataset | Data quality checks (completeness, validity, uniqueness), freshness monitoring | `data/quality/freshness_report.json`, `data/quality/` | Hải |
| Corruption/repair | `data/clean/papers_clean.csv` | Drop records, blank summary, noise injection, truncate title, stale dates, duplicates | `data/clean/papers_clean_corrupted.csv`, `data/results/corruption_log.json` | Trường |
| Orchestration     | All modules | Phase 1: ETL → index → eval → quality → report. Phase 2: corrupt → re-eval → repair → compare | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Trường |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | [Giá trị]         |
| `LLM_MODEL`                | [Giá trị]         |
| Embedding model              | [Giá trị]         |
| Số lượng Crossref records | [Giá trị]         |
| Retrieval`top_k`           | [Giá trị]         |
| Freshness threshold          | [Giá trị]         |
| Random seed, nếu có        | [Giá trị]         |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

Chỉ giữ lại cách nhóm đã dùng.

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | [Thành công/Thất bại một phần/Thất bại] | [Thời gian]                  | [Artifact hoặc log đã che secret] |
| Corruption flow   | [Thành công/Thất bại một phần/Thất bại] | [Thời gian]                  | [Artifact hoặc log đã che secret] |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | [Crossref endpoint/dataset thực tế] |
| Query/filter                | [Query hoặc filter]                  |
| Thời điểm lấy dữ liệu | [Timestamp]                           |
| Số record nhận được    | [Số lượng]                         |
| Cơ chế retry/backoff      | [Mô tả ngắn]                       |

### Bảng hợp đồng dữ liệu giữa các module (Data Contracts)

Các module trong pipeline giao tiếp với nhau qua 3 schema rõ ràng. Mỗi module **chỉ đọc** schema của bước trước và **chỉ ghi** schema của bước mình sở hữu.

#### Contract 1 — Raw Schema (`data/raw/crossref_records.json`)

> **Producer:** `crossref.py` (Nguyên) → **Consumer:** `cleaning.py` (Nguyên)

JSON chứa danh sách `PaperRecord` đã parse từ Crossref API.

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | `str` | Có | DOI duy nhất của paper | Bỏ record nếu thiếu DOI |
| `title` | `str` | Có | Tiêu đề bài báo | Bỏ record nếu thiếu title |
| `summary` | `str` | Có | Abstract đã strip JATS/XML tags | Bỏ record nếu abstract rỗng |
| `authors` | `list[str]` | Không | Danh sách "Given Family" | Mảng rỗng `[]` nếu thiếu |
| `categories` | `list[str]` | Không | Crossref `subject` | Mảng rỗng `[]` nếu thiếu |
| `primary_category` | `str` | Không | Phần tử đầu tiên của `categories` | Chuỗi rỗng `""` nếu thiếu |
| `published` | `str` | Không | Ngày xuất bản ISO `YYYY-MM-DD` | Chuỗi rỗng, cleaning sẽ drop |
| `updated` | `str` | Không | Ngày deposit/update ISO | Fallback về `published` |
| `abs_url` | `str` | Không | URL trang bài báo | Tự tạo từ `https://doi.org/{DOI}` |
| `pdf_url` | `str` | Không | URL file PDF | Chuỗi rỗng nếu không có link PDF |
| `comment` | `str` | Không | Ghi chú (dự phòng) | Chuỗi rỗng |

---

#### Contract 2 — Clean Schema (`data/clean/papers_clean.csv` + `papers_clean.json`)

> **Producer:** `cleaning.py` (Nguyên) → **Consumer:** `index.py` (embedding), `testset.py` (Hải), `corruption.py` (Trường)

CSV/JSON với schema chuẩn hóa, sẵn sàng cho embedding và evaluation.

| Trường | Kiểu dữ liệu | Ràng buộc | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | `str` | **Unique, non-null** | DOI — dùng làm document ID | Drop duplicate, bỏ row null |
| `title` | `str` | Non-null | Tiêu đề đã normalize whitespace | Bỏ record nếu rỗng |
| `summary` | `str` | Non-null, ≥ 30 ký tự | Abstract đã clean HTML | Bỏ record nếu < 30 chars |
| `published` | `str` | Non-null, format `YYYY-MM-DD` | Ngày xuất bản đã parse | Bỏ record nếu không parse được |
| `updated` | `str` | Nullable | Ngày update đã parse | Chuỗi rỗng nếu thiếu |
| `age_days` | `int` | ≥ 0 | Số ngày tính từ `run_date` đến `published` | −1 nếu thiếu date (sẽ bị drop) |
| `authors_joined` | `str` | Non-null | `", "`.join(authors) | Chuỗi rỗng nếu không có tác giả |
| `categories_joined` | `str` | Non-null | `", "`.join(categories) | Chuỗi rỗng nếu không có category |
| `summary_chars` | `int` | ≥ 0 | `len(summary)` — dùng cho quality check | Luôn tính được |
| `text_for_embedding` | `str` | Non-null | Kết hợp: `Title: ...\nAuthors: ...\nCategories: ...\nAbstract: ...` | Luôn tạo từ các trường trên |
| `primary_category` | `str` | Nullable | Subject đầu tiên | Chuỗi rỗng nếu thiếu |
| `abs_url` | `str` | Nullable | Link trang bài báo | Chuỗi rỗng |
| `pdf_url` | `str` | Nullable | Link PDF | Chuỗi rỗng |
| `comment` | `str` | Nullable | Ghi chú | Chuỗi rỗng |
| `authors` | `list[str]` | Nullable | Danh sách tên tác giả gốc | Mảng rỗng |
| `categories` | `list[str]` | Nullable | Danh sách subject gốc | Mảng rỗng |

> **Invariant:** DataFrame đã sort theo `published` giảm dần, rồi `title` tăng dần. Không có duplicate `paper_id`.

---

#### Contract 3 — Evaluation Set (`data/eval/test_set.json`)

> **Producer:** `testset.py` (Hải) → **Consumer:** RAG evaluator (`metrics.py`), `phase1.py` (Trường), `corruption_flow.py` (Trường)

JSON chứa danh sách các evaluation sample.

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa |
| --- | --- | --- | --- |
| `id` | `str` | Có | ID duy nhất của sample (ví dụ: `"q_01"`) |
| `question_type` | `str` | Có | Loại câu hỏi: `"factual"`, `"author"`, `"date"`, `"category"` |
| `question` | `str` | Có | Câu hỏi dạng tự nhiên |
| `ground_truth` | `str` | Có | Đáp án kỳ vọng (trích từ metadata paper) |
| `ground_truth_doc_ids` | `list[str]` | Có | Danh sách `paper_id` chứa đáp án (để tính retrieval hit rate) |

> **Invariant:** Test set được giữ nguyên (frozen) khi đánh giá cả baseline, corrupted và repaired để đảm bảo so sánh công bằng.

---

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Mô tả chi tiết | Cách xác minh |
| --- | --- | --- | --- |
| Loại record không có title hoặc abstract | Completeness | Bỏ record nếu `title` rỗng hoặc `summary` rỗng sau khi strip HTML | Đếm record trước/sau trong log |
| Loại record không có DOI | Uniqueness | Bỏ record nếu `paper_id` (DOI) rỗng | Log cảnh báo khi parse |
| Loại record summary quá ngắn (< 30 chars) | Validity | Bỏ record có `summary_chars < 30` — thường là metadata lỗi | Kiểm tra `summary_chars` min trong output |
| Loại record thiếu published date | Timeliness | Bỏ record không parse được ngày xuất bản | Kiểm tra cột `published` không có giá trị rỗng |
| Drop duplicate paper_id | Uniqueness | Giữ bản đầu tiên, bỏ bản sau | `df["paper_id"].is_unique == True` |
| Normalize whitespace | Consistency | Thay `\s+` → `" "` rồi `.strip()` trên title, summary, authors | Không có tab/newline/multi-space trong output |
| Strip HTML/JATS tags | Consistency | `re.sub(r"<[^>]+>", " ", text)` trước khi normalize | Không có `<jats:p>` hay thẻ HTML trong summary |

### Cách tạo `text_for_embedding`, document ID và `age_days`

- **`text_for_embedding`**: Kết hợp 4 thành phần thành một văn bản duy nhất để embedding có ngữ cảnh đầy đủ:
  ```
  Title: {title}
  Authors: {authors_joined}
  Categories: {categories_joined}
  Abstract: {summary}
  ```
  Mỗi phần chỉ xuất hiện nếu có giá trị (authors/categories có thể bỏ qua nếu rỗng).

- **Document ID (`paper_id`)**: Sử dụng DOI làm ID duy nhất. Trong ChromaDB, `record_id` có dạng `"{paper_id}::{index}"` để đảm bảo uniqueness trên từng document.

- **`age_days`**: Tính bằng `max(0, (run_date - published_date).days)`. Dùng cho freshness monitoring — nếu `age_days > freshness_threshold_days` (mặc định 180 ngày) thì paper được coi là stale.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | [Số lượng]                 |
| Các`question_type`                    | [Danh sách]                  |
| Ground-truth document ID                 | [Cách tạo/đối chiếu]     |
| Embedding model                          | [Tên model]                  |
| Vector store/collection                  | [Tên/config]                 |
| Retrieval`top_k`                       | [Giá trị]                   |
| LLM provider/model                       | [Giá trị]                   |
| Test set dùng chung cho ba trạng thái | [Đường dẫn hoặc ID/hash] |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

[Giải thích tại đây.]

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | [Có/Thiếu] | [Ghi chú] |
| Cleaned dataset          | `data/clean/`                        | [Có/Thiếu] | [Ghi chú] |
| Embedding manifest/index | `data/embeddings/`                   | [Có/Thiếu] | [Ghi chú] |
| Evaluation set           | `data/eval/`                         | [Có/Thiếu] | [Ghi chú] |
| Baseline metrics         | `data/results/baseline_metrics.json` | [Có/Thiếu] | [Ghi chú] |
| Quality/freshness        | `data/quality/`                      | [Có/Thiếu] | [Ghi chú] |
| Baseline report          | `data/reports/phase1_report.md`      | [Có/Thiếu] | [Ghi chú] |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     [Giá trị] | [Ý nghĩa trong kết quả của nhóm]  |
| `mean_token_f1`      |     [Giá trị] | [Diễn giải]                           |
| `judge_accuracy`     |     [Giá trị] | [Diễn giải]                           |
| `mean_judge_score`   |     [Giá trị] | [Diễn giải]                           |
| Ragas, nếu có        | [Giá trị/N/A] | [Diễn giải hoặc lý do không chạy] |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| [Tên check] | [Dimension]       | [Ngưỡng]         | [Pass/Fail + giá trị] | [Artifact]   |
| [Tên check] | [Dimension]       | [Ngưỡng]         | [Pass/Fail + giá trị] | [Artifact]   |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | [Dataset/index/artifact]            |
| Timestamp mới nhất       | [Giá trị]                         |
| Ngưỡng freshness         | [Giá trị]                         |
| Trạng thái baseline      | [Fresh/Stale/Unknown]               |
| Lý do                     | [Giải thích dựa trên số liệu] |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| [Loại corruption] | [Mô tả]  |          [Số lượng] | [Kỳ vọng]              | [Artifact/metric]     | [Cách repair] |
| [Loại corruption] | [Mô tả]  |          [Số lượng] | [Kỳ vọng]              | [Artifact/metric]     | [Cách repair] |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: [Có/Thiếu]
- Nhận xét: [Log có đủ loại corruption, record bị tác động và tham số hay không?]

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

[Giải thích tại đây.]

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |
| `mean_token_f1`        |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |
| `judge_accuracy`       |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |
| `mean_judge_score`     |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |
| Quality checks pass/fail |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |
| Freshness status         |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. [Corruption/data change] → [quality/freshness signal] → [retrieval/answer metric].
2. [Repair action] → [quality/freshness recovery] → [agent metric recovery hoặc lý do chưa recovery].

Không kết luận corruption “có tác động” nếu số liệu không cho thấy thay đổi. Nếu kết quả khác kỳ vọng, mô tả giả thuyết và cách nhóm đã kiểm tra.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** [Lỗi hoặc kết quả sai.]
- **Nguyên nhân:** [Root cause.]
- **Cách xử lý:** [Thay đổi đã thực hiện.]
- **Cách xác minh:** [Lệnh và artifact.]

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| [Giới hạn]          | [Ảnh hưởng] | [Đề xuất]                              |
| [Giới hạn]          | [Ảnh hưởng] | [Đề xuất]                              |

## 13. Checklist trước khi nộp

- [ ] Thông tin nhóm và repository chính xác.
- [ ] Phân công khớp với module, artifact và kết quả thực tế.
- [ ] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [ ] Baseline, corrupted và repaired dùng cùng evaluation set.
- [ ] Bảng metrics khớp với các file trong `data/results/`.
- [ ] Quality/freshness conclusions khớp với `data/quality/`.
- [ ] Các đường dẫn báo cáo và artifact truy cập được.
- [ ] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [ ] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
