# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                                             |
| --------------- | -------------------------------------------------------------------- |
| Họ và tên       | Vũ Hữu Trường                                                        |
| MSSV            | 2A202601694                                                          |
| Khóa/Lớp        | K4                                                                   |
| Tên nhóm        | Handsome                                                             |
| Vai trò chính   | Corruption & Integration Owner                                       |
| Repository      | https://github.com/KerryFT/K4_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06                                                           |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable         | File/hàm phụ trách                                      | Input nhận vào               | Output bàn giao                       | Trạng thái |
| -------------------------- | ------------------------------------------------------- | ---------------------------- | ------------------------------------- | ---------- |
| Data Corruption Simulation | src/ingestion/corruption.py / corrupt_clean_dataframe() | data/clean/papers_clean.json | data/clean/papers_clean_corrupted.csv | Hoàn thành |

|Pipeline Integration & Orchestration |src/pipelines/corruption_flow.py / main() | data/raw/crossref_records.json , data/clean/papers_clean.json, data/eval/test_set.json | data/reports/corruption_report.md, data/results/corrupted_metrics.json, data/results/repaizred_metrics.json | Hoàn thành |

|Pipeline Script Runner| script/run_corruption_flow.py | src/pipelines/corruption_flow.py| Khởi chạy toàn bộ Phase 2 end-to-end | Hoàn thành |
Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ----------------------------- | ------- |

| Refactor & Bugfix Phase 1 Pipeline | src/pipelines/phase1.py |Tích hợp lớp LocalEmbeddingIndex.build() và
bổ sung hàm kiểm tra, run_data_quality_checks giúp Phase 1 chạy thông suốt. |

| Khắc phục lỗi Import / Interface | src/retrieval/index.py, src/evaluation/metrics.py | Đồng bộ hóa chữ ký hàm giữa các module Data, Index và Evaluation |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện             | File/hàm/artifact liên quan | Kết quả bàn giao                                | Cách xác minh                             |
| --------------------------------- | --------------------------- | ----------------------------------------------- | ----------------------------------------- |
| Giả lập hỏng dữ liệu có kiểm soát | src/ingestion/corruption.py | papers_clean_corrupted.csv, corruption_log.json | uv run python -m src.ingestion.corruption |

| Tích hợp Luồng Corruption & Repair| src/pipelines/corruption_flow.pysrc/pipelines/corruption_flow.py| corruption_report.md, repaired_metrics.json| uv run python script/run_corruption_flow.py|

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Đã xây dựng thành công pipeline tích hợp end-to-end Phase 2. Giả lập thành công 5 hành vi làm hỏng dữ liệu (Drop latest, Blank summary, Inject noise, Truncate title, Stale date, Duplicate rows), khiến chỉ số retrieval_hit_rate giảm từ 1.0000 xuống 0.8000. Sau khi kích hoạt quy trình Repair từ crossref_records.json, toàn bộ chỉ số đã phục hồi 100% về mức Baseline

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Cần chứng minh tác động của chất lượng dữ liệu lên hệ thống RAG Agent và năng lực phục hồi của hệ thống data pipeline khi xảy ra sự cố dữ liệu bằng cách: 1. Tạo kịch bản gây lỗi có hệ thống trên dữ liệu sạch sao cho vi phạm các Data Quality Checks và đụng trúng tài liệu trong bộ Test Set. 2. Thiết kế luồng tích hợp tự động hóa (Integration Pipeline) thực hiện quy trình: Corrupt -> Re-index -> Evaluate -> Repair -> Re-index -> Re-evaluate -> Export Report

### Cách triển khai

src/ingestion/corruption.py:
Nhận clean_df. Thực hiện xoá bớt bản ghi mới nhất (drop latest)
Chọn các chỉ mục dòng cụ thể để: xóa summary thành rỗng (blank_summary), chèn chuỗi rác vào text (inject_noise), cắt ngắn tiêu đề (truncate_title), đổi published về "2000-01-01" (stale_date), và nhân bản dòng (add_duplicate_row)
Tái tạo lại cột text_for_embedding dựa trên thông tin bị làm hỏng và ghi vết vào output_log_path
src/pipelines/corruption_flow.py:
Đọc baseline_metrics.json và papers_clean.json  
 Tạo corrupted dataset -> Re-build ChromaDB index papers-corrupted -> Đánh giá bằng evaluate_pipeline trên bộ test_set.json frozen
Đọc crossref_records.json thô -> Chạy lại build_clean_dataframe để sửa chữa -> Re-build ChromaDB index papers-repaired -> Đánh giá lại

### Input, output và contract

| Thành phần              | Mô tả                                                                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Input                   | data/clean/papers_clean.json, data/raw/crossref_records.json, data/eval/test_set.json                                                            |
| Output                  | data/clean/papers_clean_corrupted.csv, data/clean/papers_clean_repaired.csv, data/results/corruption_log.json, data/reports/corruption_report.md |
| Module phụ thuộc        | ingestion.cleaning, retrieval.index, evaluation.metrics, observability.quality, observability.reporting                                          |
| Module sử dụng output   | System Observability Dashboard & Báo cáo tổng hợp nhóm.                                                                                          |
| Điều kiện lỗi cần xử lý | Thiếu file baseline_metrics.json hoặc clean_json trước khi chạy Phase 2; kiểm tra đường dẫn thư mục lưu trữ chưa tồn tại                         |

### Cách xác minh

```bash
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:**: Pipeline thực thi thành công qua 8 bước, hiển thị log === HOÀN THÀNH CORRUPTION & REPAIR FLOW! ===, các chỉ số sụt giảm ở trạng thái Corrupted và phục hồi hoàn toàn ở trạng thái Repaired
- **Kết quả thực tế:**: 100% khớp mong đợi.
- **Artifact/log:** data/reports/corruption_report.md và data/results/corruption_log.json

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:**: Lựa chọn chiến lược xây dựng lại tập dữ liệu đã sửa chữa (Repaired State)
- **Các phương án đã cân nhắc:**
  Phương án A: Viết các hàm logic ngược (reverse patch) để chỉ sửa lại đúng những bản ghi bị báo lỗi trong corruption_log.json.
  Phương án B: Khôi phục toàn bộ (Clean Slate Repair) bằng cách đọc lại snapshot dữ liệu thô ban đầu data/raw/crossref_records.json và chạy lại luồng Data Cleaning chuẩn
- **Phương án đã chọn:**: Phương án B
- **Lý do:**
  - Phương án B đảm bảo tính toàn vẹn dữ liệu 100% (data integrity), tránh rủi ro phát sinh thêm lỗi do logic sửa lỗi không triệt để, đúng với triết lý Data Lineage/Immutability trong Data Engineering.
- **Bằng chứng quyết định phù hợp:**
  Chỉ số ở trạng thái Repaired đã khôi phục chính xác từng chữ số so với Baseline (Hit Rate = 1.0000, Token F1 = 0.3200), đồng thời Data Quality Checks đạt PASSED 6/6

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** [Che toàn bộ secret trước khi ghi.]
- **Lệnh hoặc bước tái hiện:** [Lệnh/bước.]
- **Nguyên nhân gốc:** [Root cause, không chỉ mô tả triệu chứng.]
- **Cách xử lý:** [Thay đổi cụ thể.]
- **Cách xác minh sau khi sửa:** [Lệnh và kết quả.]
- **Điều học được:** [Bài học kỹ thuật.]

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** [Module/artifact.]
- **Những gì đã loại trừ:** [Các giả thuyết đã kiểm tra.]
- **Bước tiếp theo:** [Hành động có thể kiểm chứng.]

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**
Luồng dữ liệu từ Crossref đến Vector Index:
Dữ liệu thô (tên bài báo, tóm tắt, tác giả, ngày xuất bản) được gọi từ Crossref REST API qua thư viện requests và lưu snapshot thành crossref_records.json. Tiếp theo, bước Cleaning làm sạch HTML, xóa khoảng trắng thừa và nối tiêu đề, tóm tắt, tác giả thành một chuỗi text hoàn chỉnh text_for_embedding. Chuỗi này được đưa qua mô hình SentenceTransformer (all-MiniLM-L6-v2) để chuyển thành các vector số, sau đó nạp toàn bộ vector và metadata vào cơ sở dữ liệu ChromaDB để phục vụ tìm kiếm.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal        |     Baseline |    Corrupted |     Repaired | Nhận xét của cá nhân                                                                                      |
| -------------------- | -----------: | -----------: | -----------: | --------------------------------------------------------------------------------------------------------- |
| `retrieval_hit_rate` |       1.0000 |       0.8000 |       1.0000 | Tỷ lệ tìm kiếm chính xác sụt giảm 20% khi dữ liệu bị lỗi, phục hồi 100% sau bước repair                   |
| `mean_token_f1`      |       0.3200 |       0.2621 |       0.3200 | Độ chính xác từ ngữ giảm ~0.0579 do thông tin context bị chèn nhiễu/xóa, quay lại mức ban đầu sau repair. |
| `judge_accuracy`     |       0.3000 |       0.2000 |       0.3000 | Tỷ lệ LLM Judge đánh giá đúng giảm 10% khi dữ liệu gặp sự cố                                              |
| `mean_judge_score`   |       1.6000 |       1.4000 |       1.6000 | Điểm chất lượng trung bình của câu trả lời giảm từ 1.6 xuống 1.4 ở trạng thái hỏng                        |
| Quality checks       | 6 / 6 PASSED | 3 / 6 FAILED | 6 / 6 PASSED | Kiểm tra chất lượng phát hiện chính xác các lỗi blank summary, duplicate rows và stale date.              |
| Freshness status     |        FRESH |        STALE |        FRESH | Bị cảnh báo STALE do có bản ghi bị cố tình đẩy ngày xuất bản về năm 2000.                                 |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. [Data corruption] → [quality/freshness signal thay đổi] → [agent metric thay đổi].
2. [Repair action] → [quality/freshness signal phục hồi] → [agent metric phục hồi hoặc chưa phục hồi].

Corruption nào ảnh hưởng rõ nhất và vì sao?

Hành vi xóa tóm tắt (blank_summary) và chèn nhiễu (inject_noise) ảnh hưởng rõ nhất đến RAG Agent. Lý do là RAG dựa hoàn toàn vào việc truy xuất ngữ cảnh (context) từ Vector Database. Khi nội dung tóm tắt bị xóa trắng hoặc bị lấp đầy bằng ký tự rác, mô hình embedding không thể tạo vector biểu diễn ngữ cảnh chính xác, làm cho bước Retrieval bị trượt tài liệu chuẩn (hit_rate giảm 20%) và LLM sinh câu trả lời bị sai lệch.

Kết quả nào khác với kỳ vọng ban đầu?

Chỉ số Recovery trong báo cáo hiển thị giá trị +0.0000. Ban đầu kỳ vọng con số này phải là một số dương lớn. Tuy nhiên, sau khi kiểm tra công thức tính $\text{Recovery} = \text{Repaired Metric} - \text{Baseline Metric}$, kết quả +0.0000 chứng minh rằng luồng repair đã hoạt động hoàn hảo khi khôi phục dữ liệu chính xác 100% về mốc ban đầu mà không gây sai lệch hay mất mát bất kỳ chỉ số nào.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. [Điều học được về data pipeline.]
   Về Data Pipeline: Hiểu rõ nguyên tắc Immutability trong Data Engineering. Việc lưu giữ snapshot dữ liệu thô ban đầu (raw_records.json) là chìa khóa cốt lõi giúp pipeline có thể khôi phục dữ liệu (repair) một cách đáng tin cậy và có khả năng tái lặp (reproducible).
2. [Điều học được về data quality/observability.]
   Về Data Quality / Observability: Data Observability không chỉ dừng lại ở việc xem dữ liệu có chạy qua hay không, mà phải chủ động giám sát thông qua Quality Checks (schema, uniqueness, null values) và Freshness Monitoring để bắt lỗi trước khi dữ liệu xấu đến tay mô hình.
3. [Điều học được về ảnh hưởng của data đến RAG agent.]
   Về ảnh hưởng của Data đến RAG Agent: Mối quan hệ "Garbage in, Garbage out" vô cùng mật thiết. Sự sụt giảm chất lượng dữ liệu ở tầng ETL / Ingestion sẽ tác động tức thì và đo lường được ngay lập tức ở tầng sinh phản hồi của RAG Agent.

### Nếu có thêm thời gian

Tôi sẽ triển khai cơ chế Data Quarantine & Auto-repair Circuit Breaker: Khi bước Quality Check trên dữ liệu mới phát hiện lỗi vượt ngưỡng quy định, hệ thống sẽ tự động cô lập (quarantine) các bản ghi xấu, phát cảnh báo (alert) và kích hoạt luồng Repair từ raw snapshot một cách tự động trước khi bước Re-index ChromaDB được phép thực thi.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Vũ Hữu Trường
**Ngày xác nhận:** [YYYY-MM-DD]
