# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K4 |
| Tên nhóm | Nhóm K4 — Data Pipeline & Data Observability |
| Repository | `K4_Day10_Data-Pipeline-Data-Observability` (workspace local; chưa cung cấp remote URL) |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | Vai trò chính | Module/deliverable sở hữu | Trách nhiệm cụ thể |
| --: | --- | --- | --- | --- |
| 1 | Hoàng Vũ Trung Nguyên — `2A202601076` | Ingestion & Cleaning Owner | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py` | Gọi Crossref API, parse payload, lưu raw artifacts; chuẩn hóa schema và tạo `text_for_embedding` |
| 2 | Hoàng Trung Hải | Evaluation & Observability Owner | `src/evaluation/testset.py`, `src/observability/quality.py`, `src/observability/reporting.py` | Tạo evaluation set; quality/freshness checks; sinh báo cáo Markdown |
| 3 | Vũ Hữu Trường | Corruption & Integration Owner | `src/ingestion/corruption.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` | Tạo corruption; điều phối baseline, corruption, repair và comparison flow |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành pipeline dữ liệu cho hệ thống RAG từ snapshot Crossref đến cleaning, embedding bằng `sentence-transformers/all-MiniLM-L6-v2`, lưu index trong ChromaDB, tạo evaluation set, đánh giá retrieval/answer, theo dõi quality/freshness và mô phỏng corruption–repair. Baseline tạo đầy đủ raw response, raw records, cleaned CSV/JSON, embedding manifest, test set, answers, metrics, quality/freshness JSON và báo cáo Markdown. Dataset baseline có 24 bản ghi, đạt 6/6 quality checks và retrieval hit rate 1.0. Corruption flow thực hiện bảy hành động gồm xóa hai bản ghi mới, làm rỗng summary, thêm noise, cắt title, làm cũ ngày xuất bản và thêm duplicate. Sau corruption, quality giảm còn 3/6, freshness chuyển sang STALE, retrieval hit rate giảm từ 1.0 xuống 0.8, token F1 giảm từ 0.3200 xuống 0.2621 và mean GPT-4o judge score giảm từ 2.9 xuống 2.6. Judge accuracy giữ nguyên 0.4. Repair từ raw snapshot phục hồi 24 bản ghi, quality 6/6, freshness FRESH và toàn bộ metrics trở lại đúng baseline. Năm validation tests đã pass. Evaluation đã gọi OpenAI `gpt-4o`; Ragas chưa được bật.

## 3. Kiến trúc và luồng dữ liệu

```text
Crossref API/snapshot
    -> raw response + PaperRecord
    -> cleaning + data modeling
    -> MiniLM embeddings + ChromaDB
    -> frozen evaluation set + baseline metrics
    -> quality/freshness reports
    -> intentional corruption + re-index + re-evaluate
    -> repair từ raw snapshot
    -> baseline/corrupted/repaired comparison report
```

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref `/works`, query/filter | Retry, parse DOI/title/abstract/authors/date, strip JATS | `data/raw/crossref_response.json`, `crossref_records.json` | Nguyên |
| Cleaning | Raw `PaperRecord` | Normalize, parse date, deduplicate, filter invalid, tạo embedding text | `data/clean/papers_clean.csv/json` | Nguyên |
| Embedding/index | Cleaned dataset | MiniLM encode, cosine Chroma collection | `data/embeddings/`, `data/chroma/` | Trường |
| Evaluation | Frozen test set + index | Retrieval hit, token F1, judge accuracy/score | `data/eval/`, `data/results/` | Hải |
| Observability | Baseline/corrupted/repaired data | Six quality checks và freshness threshold | `data/quality/`, Markdown reports | Hải |
| Corruption/repair | Clean baseline + raw snapshot | Seven corruption actions; repair bằng re-clean raw | Corrupted/repaired datasets và comparison | Trường |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` / `LLM_MODEL` | `openai` / `gpt-4o` |
| Evaluation judge của lượt xác minh | OpenAI `gpt-4o`, structured output gồm score/correct/reasoning |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Crossref records | 24 |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày |
| Corruption seed | Không dùng random; vị trí tác động deterministic |

Môi trường được cài bằng editable package trong `.venv`. Lệnh tái hiện đã dùng:

```powershell
$env:HF_HUB_OFFLINE='1'
$env:EVALUATION_JUDGE=$null
.\.venv\Scripts\python.exe .\script\run_phase1.py
.\.venv\Scripts\python.exe .\script\run_corruption_flow.py
.\.venv\Scripts\python.exe -m unittest discover -s .\tests -v
```

| Lệnh | Trạng thái | Thời điểm gần nhất | Bằng chứng |
| --- | --- | --- | --- |
| Baseline pipeline | Thành công | 2026-08-06 17:14 ICT | `data/reports/phase1_report.md` |
| Corruption flow | Thành công | 2026-08-06 17:16 ICT | `data/reports/corruption_report.md` |
| Validation tests | 5/5 pass | 2026-08-06 | `tests/` và console result |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | `https://api.crossref.org/works` |
| Query | `agentic retrieval augmented generation large language model` |
| Filter | `from-pub-date:<180 ngày trước run date>,has-abstract:true` |
| Snapshot | `data/raw/crossref_response.json`, gồm 24 records hợp lệ sau parse |
| Retry/backoff | Tối đa 5 lần; retry HTTP 429/503 và request errors với backoff tăng dần |

Raw schema dùng DOI làm `paper_id` và gồm title, summary, authors, categories, dates, DOI/URL/PDF. Clean schema giữ các trường trên và bổ sung `age_days`, `authors_joined`, `categories_joined`, `summary_chars`, `text_for_embedding`. Record thiếu DOI/title/abstract hoặc published date bị loại; summary dưới 30 ký tự bị loại; duplicate DOI chỉ giữ bản đầu. Dữ liệu được sort theo published giảm dần rồi title tăng dần.

`text_for_embedding` có dạng:

```text
Title: {title}
Authors: {authors_joined}
Categories: {categories_joined}
Abstract: {summary}
```

Evaluation sample gồm `id`, `question_type`, `question`, `ground_truth` và `ground_truth_doc_ids`. Cùng một file `data/eval/test_set.json` được dùng cho cả ba trạng thái.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 10 |
| `question_type` | `authors`, `factual`, `date` |
| Ground-truth document ID | DOI lấy từ `paper_id` của cleaned record |
| Embedding/vector store | MiniLM-L6-v2; Chroma cosine; collections baseline/corrupted/repaired |
| Retrieval `top_k` | 4 |
| Judge | OpenAI `gpt-4o`; structured score/correct/reasoning; thang 1–5 |
| Test set chung | `data/eval/test_set.json`, SHA-256 bắt đầu bằng `A415760B...` |

Giữ nguyên test set giúp mọi thay đổi metrics phản ánh trạng thái dữ liệu/index, không bị nhiễu bởi việc đổi câu hỏi hoặc ground truth giữa các lần chạy.

## 7. Kết quả baseline

| Artifact | Trạng thái | Bằng chứng |
| --- | --- | --- |
| Raw response/records | Có | `data/raw/` |
| Cleaned dataset | Có, 24 rows | `data/clean/papers_clean.csv/json` |
| Embedding/index | Có | `data/embeddings/`, `data/chroma/` |
| Evaluation set | Có, 10 samples | `data/eval/test_set.json` |
| Baseline metrics/answers | Có | `data/results/baseline_*` |
| Quality/freshness | Có, 6/6 và FRESH | `data/quality/` |
| Baseline report | Có | `data/reports/phase1_report.md` |

| Metric | Baseline | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | Ground-truth DOI xuất hiện trong top-k ở 10/10 samples |
| `mean_token_f1` | 0.3200 | Token overlap trung bình giữa answer và ground truth |
| `judge_accuracy` | 0.4000 | GPT-4o đánh dấu đúng 4/10 answers |
| `mean_judge_score` | 2.9000/5 | Điểm đánh giá trung bình của GPT-4o |
| Ragas | Skipped | Chưa đặt `RUN_RAGAS=1` |

## 8. Data quality và freshness

Baseline pass 6/6 checks: dataframe không rỗng, `paper_id` non-null, `paper_id` unique, title non-empty, summary ít nhất 20 ký tự và `age_days <= 180`. Latest publication là `2026-08-01`, oldest là `2026-02-12`, stale rows bằng 0/24 nên trạng thái FRESH.

## 9. Corruption scenarios và repair

| Corruption | Record tác động | Signal thực tế |
| --- | ---: | --- |
| Drop latest records | 2 | Dataset giảm từ 24 xuống 22 trước khi thêm duplicate; retrieval bị mất ground-truth docs |
| Blank summary | 1 | `summary_length_valid` FAILED |
| Inject noise | 1 | Làm nhiễu embedding context |
| Truncate title | 1 | Giảm chất lượng metadata/retrieval |
| Stale published date | 1 | Freshness FAILED, 1 stale row |
| Add duplicate | 1 | `paper_id_unique` FAILED; tổng corrupted rows thành 23 |

`data/results/corruption_log.json` ghi bảy hành động và record liên quan. Repair không sửa trực tiếp corrupted rows mà đọc lại snapshot `crossref_records.json`, chạy lại cùng cleaning contract, rebuild index và re-evaluate. Hash JSON của baseline và repaired giống nhau, chứng minh phục hồi từ nguồn tin cậy.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi | Kết luận |
| --- | ---: | ---: | ---: | ---: | --- |
| Retrieval hit rate | 1.0000 | 0.8000 | 1.0000 | -0.2000 | Repair phục hồi hoàn toàn |
| Mean token F1 | 0.3200 | 0.2621 | 0.3200 | -0.0579 | Repair phục hồi hoàn toàn |
| Judge accuracy | 0.4000 | 0.4000 | 0.4000 | +0.0000 | Không đổi sau corruption; repaired khớp baseline |
| Mean judge score | 2.9000 | 2.6000 | 2.9000 | -0.3000 | Repair phục hồi hoàn toàn |
| Quality | 6/6 PASS | 3/6 FAIL | 6/6 PASS | -3 checks | Repair phục hồi hoàn toàn |
| Freshness | FRESH | STALE | FRESH | +1 stale row | Repair phục hồi hoàn toàn |

Hai chuỗi bằng chứng: (1) drop records + invalid/duplicate/stale fields → quality/freshness xấu đi → retrieval hit, token F1 và mean GPT-4o judge score giảm; judge accuracy không đổi; (2) re-clean raw snapshot → quality/freshness trở lại baseline → toàn bộ metrics trở lại đúng baseline.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** `judge_backend_counts` chứa các chuỗi như `GPT-3.5`, `GPT-4` hoặc cả câu reasoning dù model cấu hình là `gpt-4o`.
- **Nguyên nhân:** trường kỹ thuật `backend` đang nằm trong `JudgeVerdict` structured-output schema, nên GPT-4o tự sinh giá trị cho trường này thay vì pipeline tự gán metadata.
- **Cách xử lý khi báo cáo:** xác định judge model từ `LLM_PROVIDER=openai` và `LLM_MODEL=gpt-4o`; chỉ sử dụng score/correct/reasoning, không dùng giá trị `backend` do model sinh để nhận diện model.
- **Cách xác minh:** hai flow hoàn tất, answer artifacts chứa verdict riêng cho 10 samples mỗi trạng thái và repaired metrics khớp baseline.

## 12. Giới hạn và hướng cải thiện

| Giới hạn | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| Metadata `judge.backend` bị model tự sinh | `judge_backend_counts` không phản ánh model thực tế | Tách backend khỏi structured-output schema và gán `backend="llm"` trong code sau khi nhận verdict |
| Ragas bị skip | Chưa có faithfulness/context precision/recall | Bật `RUN_RAGAS=1`, lưu đầy đủ Ragas result |
| Test set chỉ 10 samples | Độ phủ câu hỏi còn nhỏ | Tăng sample/category, giữ frozen và so sánh confidence interval |
| Chroma sinh UUID segment directories | Cần quyết định artifact policy khi commit | Commit đầy đủ store hoặc ignore store và tài liệu hóa lệnh rebuild |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository local chính xác; remote URL chưa được cung cấp.
- [x] Phân công khớp với module và artifact.
- [x] Baseline và corruption flow đã chạy lại.
- [x] Ba trạng thái dùng cùng evaluation set.
- [x] Metrics khớp với answer artifacts.
- [x] Quality/freshness conclusions khớp JSON reports.
- [x] Đường dẫn artifact truy cập được.
- [x] Báo cáo vai trò của Hoàng Vũ Trung Nguyên đã hoàn thành.
- [ ] Hai thành viên còn lại cần hoàn thành báo cáo cá nhân riêng.
- [x] `.env` không được Git track; báo cáo không chứa API key/token.
