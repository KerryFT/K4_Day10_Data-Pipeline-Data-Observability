# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Hoàng Trung Hải            |
| MSSV               | 2A202601054        |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | Handsome     |
| Vai trò chính    | Evaluation & Observability Owner|
| Repository         | https://github.com/KerryFT/K4_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06                 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Evaluation Test Set | `src/evaluation/testset.py`<br>`build_test_set()` | Cleaned DataFrame (`papers_clean.csv` / `json`) | `data/eval/test_set.json` (Bộ 10 câu hỏi đóng băng) | Hoàn thành |
| Data Quality & Freshness | `src/observability/quality.py`<br>`run_data_quality_checks()`, `build_freshness_report()` | Cleaned/Corrupted/Repaired DataFrame & `Settings` | `data/quality/quality_*.json`<br>`data/quality/freshness_report.json` | Hoàn thành |
| Report Generation | `src/observability/reporting.py`<br>`generate_phase1_report()`, `generate_corruption_report()` | Dictionary lưu metrics, quality checks & freshness reports | `data/reports/phase1_report.md`<br>`data/reports/corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Tích hợp Baseline Pipeline | Thành viên 1 & Thành viên 3 (`src/pipelines/phase1.py`) | Đảm bảo luồng chạy gọi đúng `build_test_set` và xuất đủ reports |
| Tích hợp Corruption Flow | Thành viên 3 (`src/pipelines/corruption_flow.py`) | Đảm bảo luồng so sánh ghi đúng `corruption_report.md` và `quality_corrupted.json` |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng & đóng băng Eval Set | `src/evaluation/testset.py` | `data/eval/test_set.json` | Lệnh `python -c "from evaluation.testset import build_test_set..."` |
| Cài đặt Data Quality & Freshness Checks | `src/observability/quality.py` | `data/quality/quality_baseline.json`<br>`data/quality/freshness_report.json` | Lệnh `python -c "from observability.quality import run_data_quality_checks..."` |
| Tự động tạo báo cáo Markdown | `src/observability/reporting.py` | `data/reports/phase1_report.md`<br>`data/reports/corruption_report.md` | Đã xuất các file Markdown chuẩn định dạng bảng so sánh |

### Mô tả cụ thể Artifact tạo ra:
- **`data/eval/test_set.json`**: Bộ câu hỏi chuẩn gồm 10 câu hỏi thực tế được phân loại thành 4 loại câu hỏi (`authors`, `factual`, `date`), mỗi câu đều chứa đáp án chuẩn (`ground_truth`) và danh sách ID bài báo chứa đáp án (`ground_truth_doc_ids`).
- **`data/reports/corruption_report.md`**: Báo cáo Markdown tự động so sánh đối chiếu chỉ số của RAG Agent và tình trạng Data Quality qua 3 trạng thái **Baseline**, **Corrupted**, và **Repaired**.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **Thiếu bộ benchmark chuẩn**: RAG Agent cần một bộ test set cố định (Frozen Evaluation Set) để đo lường độ chính xác retrieval và chất lượng câu trả lời.
2. **Thiếu cơ chế cảnh báo dữ liệu xấu**: Cần phát hiện kịp thời các lỗi dữ liệu (dữ liệu rỗng, thiếu tiêu đề, trùng lặp ID, dữ liệu quá cũ) trước khi đưa vào vector index.

### Cách triển khai
1. **Quy tắc tạo Test Set (`build_test_set`)**:
   - Duyệt 10 bài báo đại diện từ DataFrame đã làm sạch.
   - Dùng toán tử chia lấy dư `idx % 4` để xoay vòng tạo 4 loại câu hỏi factual:
     - `authors`: Hỏi tên tác giả bài báo dựa trên `authors_joined`.
     - `factual` (Objective): Hỏi mục tiêu nghiên cứu, trích 2 câu đầu của `summary`.
     - `date`: Hỏi ngày xuất bản dựa trên trường `published`.
     - `factual` (Search): Hỏi bài báo nào thực hiện nghiên cứu dựa trên trích đoạn abstract.
   - Gắn `ground_truth_doc_ids` chính xác bằng `paper_id` và ghi ra JSON.

2. **Quy tắc kiểm tra Data Quality (`run_data_quality_checks`)**:
   - Thực hiện 6 bài test: `non_empty_dataframe`, `paper_id_not_null`, `paper_id_unique`, `title_not_null`, `summary_length_valid` (>= 20 ký tự), và `freshness_within_threshold` (ngưỡng 180 ngày).

3. **Tạo báo cáo tự động (`generate_corruption_report`)**:
   - Nhận vào 3 bộ dictionary metrics của Baseline, Corrupted và Repaired.
   - Tính toán độ lệch (Impact Delta & Recovery Delta) và dựng bảng Markdown so sánh trực quan.

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| Input | Cleaned DataFrame (`pd.DataFrame`), `Settings` đối tượng cấu hình |
| Output | `test_set.json`, `quality_*.json`, `freshness_report.json`, `*.md` reports |
| Module phụ thuộc | `src/core/config.py`, `src/core/utils.py` |
| Module sử dụng output | `src/evaluation/metrics.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | DataFrame rỗng hoặc có dưới 3 bản ghi (throw `ValueError`) |

### Cách xác minh

```bash
uv run python -c "import pandas as pd; from core.config import load_settings; from evaluation.testset import build_test_set; from observability.quality import run_data_quality_checks, build_freshness_report; s = load_settings(); df = pd.read_csv(s.paths.clean_csv); build_test_set(df, s.paths.eval_testset); run_data_quality_checks(df, s, 'quality_baseline.json'); build_freshness_report(df, s, s.paths.freshness_report); print('PASSED ALL VERIFICATIONS!')"
```

- **Kết quả mong đợi:** Tạo thành công `data/eval/test_set.json`, `data/quality/quality_baseline.json`, `data/quality/freshness_report.json` không gặp lỗi.
- **Kết quả thực tế:** `PASSED ALL VERIFICATIONS!` thành công 100%.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương pháp khởi tạo bộ câu hỏi đánh giá (Eval Set): Tự động sinh theo quy tắc đóng băng (Rule-based Auto-generation with Frozen Artifact) vs Nhập tay thủ công (Hardcoded Static JSON).
- **Các phương án đã cân nhắc:**
  1. *Phương án A (Nhập tay static)*: Viết cố định 10 câu hỏi vào file JSON. Nhược điểm: Phụ thuộc vào dữ liệu cố định, không chạy lại được nếu đổi nguồn Crossref khác.
  2. *Phương án B (Tự động sinh theo quy tắc và đóng băng)*: Viết thuật toán đọc DataFrame sạch và sinh ra bộ test set chuẩn schema, sau đó lưu cố định vào `data/eval/test_set.json`.
- **Phương án đã chọn:** Phương án B.
- **Lý do:** Phương án B đảm bảo tính linh hoạt (reproducible khi đổi nguồn query) nhưng vẫn giữ được tính đóng băng (frozen) bằng cách lưu ra artifact JSON để giữ vai trò làm biến kiểm soát (Control Variable) khi so sánh Baseline, Corrupted và Repaired.
- **Bằng chứng quyết định phù hợp:** File `data/eval/test_set.json` sinh ra 10 câu hỏi chính xác 100% với dữ liệu bài báo thực tế trong `papers_clean.csv`.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ModuleNotFoundError: No module named 'datasets'` khi thực thi lệnh python độc lập.
- **Lệnh hoặc bước tái hiện:** `python -c "from evaluation.testset import build_test_set..."`
- **Nguyên nhân gốc:** Câu lệnh chạy bằng Python mặc định của hệ thống (Global Python) thay vì môi trường ảo `.venv` nơi đã được `uv sync` cài đặt đầy đủ các thư viện (`datasets`, `ragas`, `pandas`...).
- **Cách xử lý:** Kích hoạt `.venv` hoặc thực thi lệnh thông qua `uv run python` hoặc đường dẫn môi trường ảo `.\.venv\Scripts\python.exe`.
- **Cách xác minh sau khi sửa:** Lệnh `uv run python -c "..."` chạy mượt mà và không báo lỗi thiếu thư viện.
- **Điều học được:** Luôn sử dụng `uv run` hoặc kích hoạt virtual environment trong dự án để đảm bảo môi trường thực thi đồng nhất.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Crossref API trả về raw JSON ➡️ Ingestion parser đọc thành list các `PaperRecord` ➡️ Cleaning module làm sạch, chuẩn hóa text và tạo cột `text_for_embedding` ➡️ Embedding module dùng `all-MiniLM-L6-v2` mã hóa văn bản thành mảng vector 384 chiều ➡️ Lưu vector và metadata vào ChromaDB collection (`data/chroma/`).

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Mỗi câu hỏi trong test set chứa `ground_truth_doc_ids` (ID bài báo chứa đáp án chuẩn). Khi RAG Agent thực hiện search top-k context từ ChromaDB, nếu trong top-k context có chứa `ground_truth_doc_ids` thì `retrieval_hit_rate = 1.0` (Hit), ngược lại là `0.0` (Miss).

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks**: Kiểm tra tính hợp lệ về cấu trúc dữ liệu tại thời điểm ingest (Null check, trùng ID, tiêu đề rỗng, độ dài summary).
   - **Freshness monitoring**: Giám sát khía cạnh thời gian/độ tươi của dữ liệu (ngày xuất bản gần nhất/xa nhất, số bản ghi bị cũ/stale quá 180 ngày).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Bộ test set đóng vai trò là **Biến kiểm soát (Control Variable)**. Để kết quả so sánh có ý nghĩa khoa học, duy nhất một yếu tố được phép thay đổi giữa 3 pha là **Chất lượng dữ liệu (Data Quality)**.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repair thành công khi:
   - File `quality_repaired.json` đạt `overall_status: PASSED`.
   - File `freshness_report.json` đạt `is_fresh: true` (0 stale rows).
   - Metrics `retrieval_hit_rate` và `mean_token_f1` trong `repaired_metrics.json` quay trở lại bằng mức của `baseline_metrics.json`.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.8000 |   1.0000 | Sụt giảm 20% ở pha Corrupted do mất bài báo, phục hồi 100% sau Repair |
| `mean_token_f1`      |   0.3200 |    0.2621 |   0.3200 | Giảm đáng kể khi summary bị nhiễu/rỗng, khôi phục hoàn toàn khi dữ liệu sạch |
| `judge_accuracy`     |   0.3000 |    0.2000 |   0.3000 | LLM Judge đánh giá độ đúng đắn giảm ở pha Corrupted |
| `mean_judge_score`   |   1.6000 |    1.4000 |   1.6000 | Điểm đánh giá chất lượng câu trả lời sụt giảm khi dữ liệu bị lỗi |
| Quality checks         |   PASSED |   FAILED  |   PASSED | Cảnh báo chính xác khi dữ liệu bị hư hỏng schema/null |
| Freshness status       |    FRESH |    STALE  |    FRESH | Giám sát chính xác các bản ghi có tuổi quá 180 ngày |

### Kết luận từ số liệu

1. **Chuỗi 1 (Corruption)**: `Data corruption (xóa bài báo, rỗng summary, stale date)` ➡️ `Quality checks FAILED, Freshness STALE` ➡️ `Retrieval hit rate giảm từ 1.0 xuống 0.8, Mean Token F1 giảm từ 0.3200 xuống 0.2621`.
2. **Chuỗi 2 (Repair)**: `Re-ingest dữ liệu từ nguồn thô Crossref` ➡️ `Quality checks PASSED, Freshness FRESH` ➡️ `Retrieval hit rate phục hồi về 1.0, Mean Token F1 phục hồi về 0.3200`.

* **Corruption nào ảnh hưởng rõ nhất?**: Việc xóa bản ghi (deleted latest records) và làm rỗng summary (blank summary) ảnh hưởng lớn nhất vì làm Vector Store mất hẳn context chuẩn, khiến RAG Agent không thể trả lời đúng.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Chất lượng dữ liệu quyết định chất lượng RAG Agent**: Dữ liệu thô lỗi (null/nhiễu) lập tức làm suy giảm trực tiếp hiệu năng của mô hình LLM phía sau.
2. **Tầm quan trọng của Data Observability**: Kiểm tra Data Quality và Freshness chủ động giúp phát hiện sớm sự cố dữ liệu trước khi người dùng nhận được câu trả lời sai.
3. **Ý nghĩa của Frozen Evaluation Set**: Đóng băng bộ test set là điều kiện tiên quyết để thực hiện các bài thử nghiệm A/B testing hoặc đo lường impact chính xác.

### Nếu có thêm thời gian
Tôi sẽ viết thêm các bài test nâng cao bằng Great Expectations (GX) cho thư mục `data/quality/gx` và mở rộng thêm các loại câu hỏi phức tạp (Multi-doc reasoning questions) cho test set.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Hoàng Trung Hải  
**Ngày xác nhận:** 2026-08-06
