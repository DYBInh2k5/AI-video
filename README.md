# AI Video Translator & Voice Clone Pro

Trang web tự động dịch video và lồng tiếng bằng AI với tính năng Clone giọng nói, tương tự ElevenLabs nhưng hoàn toàn miễn phí và mã nguồn mở.

## Tính năng
- **Dịch Video tự động**: Chuyển đổi ngôn ngữ trong video sang bất kỳ ngôn ngữ nào.
- **Voice Cloning**: Sử dụng công nghệ XTTS v2 để clone giọng nói của người trong video gốc sang ngôn ngữ đích.
- **Giao diện hiện đại**: UI/UX cao cấp, dễ sử dụng.
- **Hỗ trợ đa ngôn ngữ**: Tiếng Việt, Anh, Nhật, Hàn, Pháp, Đức, Tây Ban Nha...

## Ưu điểm vượt trội: 100% Private & Free
Khác với các dịch vụ khác yêu cầu API Key (OpenAI, Supabase, Anthropic) và tính phí theo ký tự, hệ thống này:
- **Không cần API Key**: Không cần OpenAI, không cần Supabase, không cần ElevenLabs.
- **Chạy Local (Offline)**: Toàn bộ dữ liệu video và giọng nói của bạn được xử lý ngay trên máy của bạn (hoặc server riêng của bạn).
- **Không giới hạn**: Bạn có thể dịch bao nhiêu video tùy thích mà không tốn một xu.

## Yêu cầu hệ thống
- Docker & Docker Compose
- GPU NVIDIA (Khuyến khích để xử lý nhanh, nếu không sẽ chạy trên CPU chậm hơn)

## Cách cài đặt và chạy

1. **Clone project và truy cập thư mục**:
   ```bash
   cd AI
   ```

2. **Chạy bằng Docker Compose**:
   ```bash
   docker-compose up --build
   ```

3. **Truy cập**:
   - Giao diện người dùng: `http://localhost:3000`
   - API Backend: `http://localhost:8000`

## Cấu trúc thư mục
- `/backend`: Xử lý AI (Whisper, XTTS v2, MoviePy).
- `/frontend`: Giao diện người dùng (Next.js, Tailwind CSS, Framer Motion).
- `/uploads`: Thư mục lưu trữ video tải lên.
- `/outputs`: Thư mục lưu trữ video kết quả.

## Lưu ý quan trọng
- Lần chạy đầu tiên sẽ mất thời gian để tải các model AI (Whisper và XTTS v2) nặng khoảng 2-3GB.
- Nếu bạn không có GPU, hãy chỉnh sửa `backend/processor.py` để ép buộc chạy trên `cpu`.

## Giấy phép
Mã nguồn mở - Tự do sử dụng và phát triển.
