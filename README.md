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

## ISO/IEC 25010 Quality Standards / Tiêu chuẩn chất lượng ISO/IEC 25010

**English:**
The skill applies ISO/IEC 25010 (SQuaRE — Systems and Software Quality Requirements and Evaluation) as the quality framework. All 7 characteristics with their sub-characteristics are mapped to concrete WPF C# patterns, giving teams a traceable link between quality requirements and code decisions.

**Tiếng Việt:**
Skill áp dụng ISO/IEC 25010 (SQuaRE — Yêu cầu và đánh giá chất lượng hệ thống và phần mềm) làm khung chất lượng. Toàn bộ 7 đặc tính cùng các đặc tính con được ánh xạ sang mẫu WPF C# cụ thể, giúp nhóm có liên kết có thể truy vết giữa yêu cầu chất lượng và quyết định code.

### 1. Functional Suitability / Tính phù hợp chức năng

Sub-characteristics: Functional Completeness, Functional Correctness, Functional Appropriateness

| Sub-characteristic | WPF Implementation |
|-------------------|-------------------|
| Functional Correctness | 100% unit test coverage on battery health formula, SMART scoring algorithm |
| Functional Completeness | All 13 WMI classes documented and tested; all hardware test types covered |
| Functional Appropriateness | TDD pattern ensures features match requirements before implementation |

**EN:** Critical calculations (battery health, SMART score) require 100% test coverage. The BatteryLifePrediction TDD pattern in `testing-patterns.md` demonstrates this approach.

**VI:** Các phép tính quan trọng (sức khỏe pin, điểm SMART) yêu cầu độ phủ test 100%. Mẫu TDD BatteryLifePrediction trong `testing-patterns.md` minh họa cách tiếp cận này.

### 2. Reliability / Độ tin cậy

Sub-characteristics: Maturity, Availability, Fault Tolerance, Recoverability

| Sub-characteristic | WPF Implementation |
|-------------------|-------------------|
| Fault Tolerance | `async void` try/catch, graceful WMI fallbacks, `Result<T>` pattern |
| Recoverability | `DispatcherUnhandledException` global handler, allow user to save results after error |
| Availability | IDisposable cleanup prevents resource exhaustion; WMI caching reduces query failures |
| Maturity | Multi-layer RAM fallback (WMI → Kernel32 → ComputerSystem); SMART fallback chain |

**EN:** Every WMI query must have a fallback. Every `async void` must have try/catch. The `error-handling.md` file covers the full exception hierarchy for hardware access.

**VI:** Mọi truy vấn WMI phải có fallback. Mọi `async void` phải có try/catch. File `error-handling.md` bao gồm toàn bộ phân cấp exception cho truy cập phần cứng.

### 3. Performance Efficiency / Hiệu quả hiệu năng

Sub-characteristics: Time Behaviour, Resource Utilization, Capacity

| Sub-characteristic | WPF Implementation |
|-------------------|-------------------|
| Time Behaviour | Median of 5+ benchmark runs to filter thermal throttle spikes |
| Resource Utilization | `ManagementObjectSearcher` caching; `computer.Close()` in Dispose; WMI TTL cache |
| Capacity | `VirtualizingStackPanel` with Recycling mode for lists of 100+ items |

**EN:** Never create `ManagementObjectSearcher` in a loop. Always use median (not average) for benchmark scores. See `performance.md` for the full caching and disposal patterns.

**VI:** Không bao giờ tạo `ManagementObjectSearcher` trong vòng lặp. Luôn dùng trung vị (không phải trung bình) cho điểm benchmark. Xem `performance.md` để biết đầy đủ mẫu cache và disposal.

### 4. Usability / Khả năng sử dụng

Sub-characteristics: Appropriateness Recognizability, Learnability, Operability, User Error Protection, Accessibility, User Interface Aesthetics

| Sub-characteristic | WPF Implementation |
|-------------------|-------------------|
| Accessibility | `AutomationProperties.Name` on all icon-only buttons; keyboard navigation via Button style |
| Operability | `IsBusy` + `CancellationToken` for all long operations; progress reporting via `IProgress<T>` |
| User Error Protection | Input validation before hardware tests; admin rights check before elevation-required features |
| Learnability | Localization completeness — all user-visible strings via `DynamicResource` |

**EN:** Interactive `Border` elements must be converted to `Button` with custom style for keyboard accessibility. Technical units (MHz, GB, Wh) are never localized — they are international standards.

**VI:** Các phần tử `Border` tương tác phải được chuyển thành `Button` với style tùy chỉnh để có thể điều hướng bằng bàn phím. Đơn vị kỹ thuật (MHz, GB, Wh) không bao giờ được dịch — chúng là tiêu chuẩn quốc tế.

### 5. Security / Bảo mật

Sub-characteristics: Confidentiality, Integrity, Non-repudiation, Authenticity, Accountability

| Sub-characteristic | WPF Implementation |
|-------------------|-------------------|
| Integrity | Anti-fake validation: CPU clock range check, WMI vs Registry cross-validation |
| Authenticity | VM detection (Hyper-V, VMware, VirtualBox, QEMU, Parallels) to flag non-physical hardware |
| Accountability | `ILogger` structured logging for all hardware access and test results |
| Confidentiality | No hardcoded secrets; admin rights detection with graceful degradation |

**EN:** The skill distinguishes safe monitoring tools (CPU-Z, HWiNFO, GPU-Z) from spoofing tools (DMIEdit, RWEverything, HWIDChanger). See `hardware-testing.md` for the anti-fake detection patterns.

**VI:** Skill phân biệt công cụ giám sát an toàn (CPU-Z, HWiNFO, GPU-Z) với công cụ giả mạo (DMIEdit, RWEverything, HWIDChanger). Xem `hardware-testing.md` để biết mẫu phát hiện chống giả mạo.

### 6. Maintainability / Khả năng bảo trì

Sub-characteristics: Modularity, Reusability, Analysability, Modifiability, Testability

| Sub-characteristic | WPF Implementation |
|-------------------|-------------------|
| Modularity | MVVM separation; interface-first design; no service duplication |
| Testability | `IWmiService` abstraction; Moq-compatible interfaces for all hardware services |
| Modifiability | `FeatureGateService` for license-based feature control without code changes |
| Reusability | `TestResultsStore` singleton; `NavigationService` interface reusable across ViewModels |
| Analysability | Scoring consistency: QuickTest verdict must equal Full Report verdict for same hardware state |

**EN:** Every service that touches hardware must have an `IServiceName` interface. This is non-negotiable — it is what makes unit testing possible without real hardware.

**VI:** Mọi service chạm vào phần cứng phải có interface `IServiceName`. Đây là điều bắt buộc — đây là điều làm cho unit test có thể thực hiện mà không cần phần cứng thật.

### 7. Portability / Tính di động

Sub-characteristics: Adaptability, Installability, Replaceability

| Sub-characteristic | WPF Implementation |
|-------------------|-------------------|
| Adaptability | WinPE compatibility checklist: no installer dependencies, offline operation, no AppData reliance |
| Installability | No hardcoded paths; Registry-based dynamic path detection for external tools |
| Replaceability | `IWmiService`, `IHardwareService` interfaces allow swapping implementations |

**EN:** WinPE is a minimal Windows environment with no user profile, no AppData, and limited services. The skill includes a WinPE compatibility checklist in `hardware-testing.md`.

**VI:** WinPE là môi trường Windows tối giản không có user profile, không có AppData, và dịch vụ hạn chế. Skill bao gồm danh sách kiểm tra tương thích WinPE trong `hardware-testing.md`.

### ISO 25010 Test Coverage Summary / Tóm tắt độ phủ test ISO 25010

| Characteristic | Test Approach | Coverage Target |
|---------------|---------------|-----------------|
| Functional Suitability | Unit tests with Moq | 100% critical calculations, 80% business logic |
| Reliability | Unit tests for all fallback paths | All exception handlers covered |
| Performance Efficiency | Benchmark tests, median measurement | 5+ runs per benchmark |
| Usability | AutomationProperties, keyboard nav tests | All interactive controls |
| Security | Anti-fake validation tests, VM detection | All validation rules |
| Maintainability | Scoring consistency tests | QuickTest = Full Report |
| Portability | WinPE checklist, path-independence tests | No hardcoded paths |

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
