# Bộ dữ liệu ASUNA – tư thế yoga

Bộ dữ liệu cho bài tập CS232: tìm ảnh tư thế yoga tương tự từ một ảnh đầu vào.

- **50 ảnh tìm kiếm** (`raw_images/db/P01_01.jpg` … `P10_05.jpg`): 10 tư thế × 5 ảnh.
- **10 ảnh truy vấn** (`raw_images/query/Q01.jpg` … `Q10.jpg`): mỗi tư thế một ảnh.
- Mọi ảnh là frame cắt từ video YouTube. Link, kênh, mốc thời gian và giấy phép ghi trong `sources.csv`.

Ảnh, đoạn video và âm thanh **không được đưa lên GitHub** (thuộc bản quyền các kênh, có hình người thật). Muốn có lại đúng bộ ảnh, chạy `collect_frames.py` (xem bên dưới).

## Tiêu chí tương tự

Hai ảnh được coi là tương tự khi **cùng một tư thế (asana)**, không phụ thuộc người tập, quần áo, bối cảnh hay góc quay. Tư thế đổi bên (trái/phải) vẫn tính là cùng tư thế.

| Mã | Tư thế | Dễ nhầm với |
|---|---|---|
| P01 | Chiến binh I (Warrior I) | P02 |
| P02 | Chiến binh II (Warrior II) | P01 |
| P03 | Rắn hổ mang (Cobra) | P04 |
| P04 | Chó ngửa mặt (Upward-Facing Dog) | P03 |
| P05 | Chó úp mặt (Downward-Facing Dog) | P06 |
| P06 | Tấm ván (Plank) | P05 |
| P07 | Cái cây (Tree) | P08 |
| P08 | Núi (Mountain) | P07 |
| P09 | Tam giác (Triangle) | – |
| P10 | Em bé (Child's Pose) | – |

## Quy ước

- Chỉ lấy frame lúc người tập đang giữ yên tư thế.
- Chống rò rỉ dữ liệu: 5 ảnh của mỗi tư thế lấy từ 5 video khác nhau; video truy vấn không dùng cho kho; không huấn luyện viên nào xuất hiện ở cả kho và truy vấn với cùng một tư thế.
- Tư thế Núi (P08) gồm cả hai kiểu Tadasana: tay xuôi (P08_01, P08_05) và tay giơ cao (P08_02–P08_04).
- P07_02, P08_02, P09_01 là video hoạt hình 3D (cùng nhân vật, cùng phòng, khác tư thế), giữ lại như một ca khó có chủ đích.

## Khóa đáp án

`ground_truth.csv` ghi ID các ảnh phù hợp với từng truy vấn, được tạo và khóa ngày 27/11/2026, **trước khi chạy bất kỳ phương pháp tìm kiếm nào**. SHA-256:

```
980db2d25ff8e2533c5dd2fddaebe25cfa871f6a456910c964cd49739a4174ab
```

## Tạo lại bộ ảnh

```
pip install yt-dlp pillow
winget install ffmpeg          (macOS: brew install ffmpeg)

cd data
python collect_frames.py --sheet
```

Script đọc `frames_plan.csv`, chỉ tải đoạn 20 giây quanh mỗi mốc thời gian, rồi tạo:

| Đầu ra | Nội dung |
|---|---|
| `raw_images/db/`, `raw_images/query/` | 60 frame |
| `audio/` | âm thanh 20 giây quanh mỗi frame (dùng cho ASR) |
| `clips/` | đoạn video 20 giây quanh mỗi frame (dùng cho temporal) |
| `checks/` | ảnh ghép mỗi tư thế để kiểm tra bằng mắt |
| `sources.csv`, `ground_truth.csv` | nguồn ảnh và đáp án |

Nếu yt-dlp báo thiếu JavaScript runtime và tải lỗi, cài thêm Deno: `winget install DenoLand.Deno`.
