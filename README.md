# WPF C# Skill — AI Coding Assistant Reference

**English / Tiếng Việt**

---

## What is this / Đây là gì

**English:**
A structured reference skill for AI coding assistants (Kiro, Claude Code, Cursor, Antigravity) working on WPF C# desktop applications. Contains 10 reference files covering MVVM, XAML, async patterns, WMI hardware integration, testing, DI architecture, error handling, localization, and performance — all derived from real-world experience building LaptopTesterPro, a hardware diagnostic tool for Windows.

**Tiếng Việt:**
Bộ tài liệu tham chiếu có cấu trúc dành cho các AI coding assistant (Kiro, Claude Code, Cursor, Antigravity) khi làm việc với ứng dụng WPF C# desktop. Bao gồm 10 file tham chiếu về MVVM, XAML, async patterns, tích hợp phần cứng qua WMI, kiểm thử, kiến trúc DI, xử lý lỗi, đa ngôn ngữ và hiệu năng — được rút ra từ kinh nghiệm thực tế xây dựng LaptopTesterPro, công cụ chẩn đoán phần cứng cho Windows.

---

## Who is this for / Dành cho ai

**English:**
- Developers building WPF desktop applications on Windows
- Teams using AI coding assistants who want consistent, project-aware guidance
- Anyone working with WMI, hardware diagnostics, or Windows-specific APIs in C#

**Tiếng Việt:**
- Lập trình viên xây dựng ứng dụng WPF desktop trên Windows
- Nhóm sử dụng AI coding assistant muốn có hướng dẫn nhất quán, phù hợp với dự án
- Bất kỳ ai làm việc với WMI, chẩn đoán phần cứng, hoặc Windows API trong C#

---

## File Structure / Cấu trúc file

```
wpf-csharp/
  SKILL.md                  Entry point — AI reads this first
  mvvm-patterns.md          MVVM, ObservableProperty, NavigationService
  xaml-best-practices.md    ResourceDictionary, accessibility, animations
  async-patterns.md         async void safety, CancellationToken, IProgress
  wmi-hardware.md           IWmiService, 13 WMI classes, SMART, battery health
  hardware-testing.md       CPU stress, RAM test, anti-fake, VM detection
  testing-patterns.md       xUnit + Moq + FluentAssertions, ISO 25010, TDD
  di-architecture.md        App.xaml.cs DI setup, service lifetimes, FeatureGate
  error-handling.md         ILogger, Result<T>, graceful degradation
  localization.md           ResourceDictionary i18n, runtime switching
  performance.md            IDisposable, VirtualizingStackPanel, WMI caching
  validate_skill.py         Validation script — checks structure and code blocks
```

---

## Installation / Cài đặt

**English:**
Copy the `wpf-csharp/` folder to the appropriate path for your AI tool:

**Tiếng Việt:**
Sao chép thư mục `wpf-csharp/` vào đường dẫn phù hợp với AI tool bạn đang dùng:

| Tool | Path |
|------|------|
| Kiro / Antigravity | `.agent/skills/skills/wpf-csharp/` |
| Claude Code | `.claude/skills/wpf-csharp/` |
| Cursor | `.cursor/skills/wpf-csharp/` |

**PowerShell (Windows):**
```powershell
# Clone and copy to your project
git clone https://github.com/YOUR_USERNAME/wpf-csharp-skill.git
Copy-Item -Recurse wpf-csharp-skill/wpf-csharp .agent/skills/skills/wpf-csharp
```

---

## How to use / Cách sử dụng

**English:**
Once installed, tell your AI assistant to use the skill:

**Tiếng Việt:**
Sau khi cài đặt, yêu cầu AI assistant sử dụng skill:

```
# Kiro / Antigravity
Use wpf-csharp skill

# Claude Code
/wpf-csharp implement battery health calculation

# Cursor
@wpf-csharp how do I handle WMI exceptions?
```

**English:**
The AI will automatically load the relevant reference files based on your question — MVVM patterns for ViewModel questions, WMI reference for hardware queries, etc.

**Tiếng Việt:**
AI sẽ tự động tải các file tham chiếu phù hợp dựa trên câu hỏi của bạn — MVVM patterns cho câu hỏi về ViewModel, WMI reference cho truy vấn phần cứng, v.v.

---

## What the skill covers / Nội dung skill

### MVVM Patterns
**EN:** CommunityToolkit.Mvvm with `[ObservableProperty]`, `[RelayCommand]`, `[AsyncRelayCommand]`. ViewModelBase with IsBusy/ErrorMessage. Stack-based NavigationService. TestResultsStore singleton.

**VI:** CommunityToolkit.Mvvm với `[ObservableProperty]`, `[RelayCommand]`, `[AsyncRelayCommand]`. ViewModelBase với IsBusy/ErrorMessage. NavigationService dạng stack. TestResultsStore singleton.

### XAML Best Practices
**EN:** ResourceDictionary for all colors and styles. AutomationProperties for accessibility. DynamicResource for runtime theme switching. VirtualizingStackPanel for large lists. WindowChrome for custom title bars.

**VI:** ResourceDictionary cho tất cả màu sắc và style. AutomationProperties cho khả năng tiếp cận. DynamicResource cho chuyển đổi theme runtime. VirtualizingStackPanel cho danh sách lớn. WindowChrome cho thanh tiêu đề tùy chỉnh.

### Async Patterns
**EN:** Safe `async void` with try/catch. IsBusy + linked CancellationToken. Dispatcher.InvokeAsync for background-to-UI updates. IProgress for progress reporting. Deadlock prevention with ConfigureAwait.

**VI:** `async void` an toàn với try/catch. IsBusy + linked CancellationToken. Dispatcher.InvokeAsync cho cập nhật từ background lên UI. IProgress cho báo cáo tiến trình. Phòng tránh deadlock với ConfigureAwait.

### WMI and Hardware Integration
**EN:** IWmiService interface with 13 WMI class reference table. SMART data parsing with 12-byte attribute structure. Battery health formula with division-by-zero guard. Multi-layer RAM fallback. USB speed detection.

**VI:** Interface IWmiService với bảng tham chiếu 13 WMI class. Phân tích dữ liệu SMART với cấu trúc thuộc tính 12 byte. Công thức sức khỏe pin với bảo vệ chia cho 0. Fallback nhiều lớp cho RAM. Phát hiện tốc độ USB.

### Hardware Testing
**EN:** CPU stress test using Lucas-Lehmer algorithm. RAM pattern test (0x00, 0xFF, 0xAA, 0x55). Disk speed with FileOptions.WriteThrough. Anti-fake validation via WMI/Registry cross-check. VM detection for Hyper-V, VMware, VirtualBox.

**VI:** Kiểm tra tải CPU dùng thuật toán Lucas-Lehmer. Kiểm tra RAM theo mẫu (0x00, 0xFF, 0xAA, 0x55). Tốc độ đĩa với FileOptions.WriteThrough. Xác thực chống giả mạo qua đối chiếu WMI/Registry. Phát hiện máy ảo Hyper-V, VMware, VirtualBox.

### Testing Patterns
**EN:** xUnit + Moq + FluentAssertions setup. TDD with BatteryLifePrediction example. ISO/IEC 25010 quality characteristics mapping. Scoring consistency between QuickTest and Full Report. CI/CD strategy.

**VI:** Cài đặt xUnit + Moq + FluentAssertions. TDD với ví dụ BatteryLifePrediction. Ánh xạ đặc tính chất lượng ISO/IEC 25010. Nhất quán điểm số giữa QuickTest và Full Report. Chiến lược CI/CD.

### DI Architecture
**EN:** Microsoft.Extensions.DependencyInjection in App.xaml.cs. Service lifetime patterns (Singleton/Transient/Scoped). ViewModelLocator for XAML DataContext. FeatureGateService for feature flags.

**VI:** Microsoft.Extensions.DependencyInjection trong App.xaml.cs. Mẫu vòng đời service (Singleton/Transient/Scoped). ViewModelLocator cho XAML DataContext. FeatureGateService cho feature flags.

### Error Handling
**EN:** ILogger with Microsoft.Extensions.Logging. Specific WMI exception hierarchy. Global DispatcherUnhandledException handler. Result<T> pattern for non-throwing failures. Null-safe WMI property access.

**VI:** ILogger với Microsoft.Extensions.Logging. Phân cấp exception WMI cụ thể. Xử lý toàn cục DispatcherUnhandledException. Mẫu Result<T> cho lỗi không ném exception. Truy cập thuộc tính WMI an toàn với null.

### Localization
**EN:** Hybrid .resx + ResourceDictionary approach. DynamicResource for runtime language switching without restart. ILocalizationService interface. Technical units (MHz, GB, Wh) are never translated.

**VI:** Kết hợp .resx + ResourceDictionary. DynamicResource cho chuyển đổi ngôn ngữ runtime không cần khởi động lại. Interface ILocalizationService. Đơn vị kỹ thuật (MHz, GB, Wh) không bao giờ được dịch.

### Performance
**EN:** IDisposable for WMI connections and hardware monitors. ManagementObjectSearcher caching (never in loops). WeakEventManager for event leak prevention. Median of 5+ runs for benchmark accuracy.

**VI:** IDisposable cho kết nối WMI và hardware monitor. Cache ManagementObjectSearcher (không tạo trong vòng lặp). WeakEventManager phòng tránh rò rỉ event. Trung vị của 5+ lần chạy cho độ chính xác benchmark.

---

## Validation / Kiểm tra

**English:**
Run the included validation script to verify the skill structure is intact:

**Tiếng Việt:**
Chạy script kiểm tra đi kèm để xác nhận cấu trúc skill còn nguyên vẹn:

```bash
python validate_skill.py
```

**English:**
The script checks: SKILL.md frontmatter validity, all 10 reference files present, each file has at least one fenced code block.

**Tiếng Việt:**
Script kiểm tra: tính hợp lệ của frontmatter SKILL.md, đủ 10 file tham chiếu, mỗi file có ít nhất một code block có tag ngôn ngữ.

---

## Background / Bối cảnh

**English:**
This skill was extracted from the development of LaptopTesterPro — a WPF C# application for hardware diagnostics used in laptop refurbishment workflows. The patterns here reflect real decisions made when dealing with WMI quirks, hardware variability, multi-language support (English, Vietnamese, Japanese), and the need for reliable benchmark scores across diverse hardware configurations.

**Tiếng Việt:**
Skill này được rút ra từ quá trình phát triển LaptopTesterPro — ứng dụng WPF C# dùng để chẩn đoán phần cứng trong quy trình tân trang laptop. Các mẫu ở đây phản ánh những quyết định thực tế khi xử lý các đặc thù của WMI, sự đa dạng phần cứng, hỗ trợ đa ngôn ngữ (tiếng Anh, tiếng Việt, tiếng Nhật), và yêu cầu điểm benchmark đáng tin cậy trên nhiều cấu hình phần cứng khác nhau.

---

## License / Giấy phép

MIT
