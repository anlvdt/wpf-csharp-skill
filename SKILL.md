---
name: wpf-csharp
description: >
  Comprehensive WPF C# development skill covering MVVM patterns, WMI hardware
  integration, async/await, TDD with ISO 25010, accessibility, localization,
  and enterprise patterns. Use when building WPF desktop applications, XAML UI,
  Windows desktop apps, hardware diagnostic tools, WMI queries, MVVM architecture,
  or any Windows-specific C# application. Derived from real-world LaptopTesterPro
  experience — the first community skill specialized for WPF C#.
metadata:
  model: inherit
tags:
  - wpf
  - csharp
  - dotnet
  - mvvm
  - xaml
  - windows
  - hardware
  - wmi
  - testing
  - desktop
---

## Use this skill when

- Building or modifying a WPF (Windows Presentation Foundation) application
- Implementing MVVM architecture in C# desktop apps
- Writing XAML UI with styles, animations, or accessibility requirements
- Integrating WMI (Windows Management Instrumentation) for hardware data
- Building hardware diagnostic or system information tools
- Implementing async/await patterns in WPF (UI responsiveness, background tasks)
- Setting up DI (Dependency Injection) in a WPF app
- Writing unit tests or integration tests for WPF C# code (xUnit, Moq)
- Handling localization, error handling, or performance in WPF
- Working with Windows-specific APIs: Registry, Win32, keyboard hooks, audio, camera
- Targeting WinPE (Windows Preinstallation Environment) compatibility

## Do not use this skill when

- Building web applications (use React, Vue, or ASP.NET Core skills instead)
- Building cross-platform UI (use MAUI, Avalonia, or Flutter skills instead)
- Writing pure C# library code with no WPF dependency
- Building ASP.NET Core APIs or Blazor apps
- Working on non-Windows platforms

## Quick Start

```csharp
// 1. ViewModel — always start with ObservableObject
public partial class MyViewModel : ObservableObject
{
    [ObservableProperty] private bool _isBusy;
    [ObservableProperty] private string? _errorMessage;

    [RelayCommand]
    private async Task LoadAsync(CancellationToken ct)
    {
        IsBusy = true;
        try { /* work */ }
        catch (Exception ex) { ErrorMessage = ex.Message; }
        finally { IsBusy = false; }
    }
}

// 2. DI setup in App.xaml.cs
services.AddSingleton<IWmiService, WindowsWmiService>();
services.AddTransient<MyViewModel>();
```

```xml
<!-- 3. XAML — always use ResourceDictionary, never hardcode colors -->
<Button Command="{Binding LoadCommand}"
        AutomationProperties.Name="Load data"
        IsEnabled="{Binding IsBusy, Converter={StaticResource InverseBool}}" />
```

## Reference Files

| File | Contents |
|------|----------|
| [MVVM Patterns](./mvvm-patterns.md) | ObservableProperty, RelayCommand, NavigationService, TestResultsStore |
| [XAML Best Practices](./xaml-best-practices.md) | ResourceDictionary, accessibility, animations, keyboard nav |
| [Async Patterns](./async-patterns.md) | async void safety, IsBusy+CancellationToken, Dispatcher, IProgress |
| [WMI & Hardware](./wmi-hardware.md) | IWmiService, 13 WMI classes, SMART, battery health, USB speed |
| [Hardware Testing](./hardware-testing.md) | CPU stress, RAM test, anti-fake, keyboard hook, audio/camera |
| [Testing Patterns](./testing-patterns.md) | xUnit+Moq+FluentAssertions, TDD, ISO 25010, test categories |
| [DI Architecture](./di-architecture.md) | App.xaml.cs setup, service lifetimes, FeatureGate |
| [Error Handling](./error-handling.md) | ILogger, Result<T>, graceful degradation, disclaimers |
| [Localization](./localization.md) | ResourceDictionary i18n, runtime switching, ILocalizationService |
| [Performance](./performance.md) | IDisposable, VirtualizingStackPanel, WMI caching, median benchmarks |

## Cross-Platform Deployment

This skill uses the universal SKILL.md format (open standard, works on 20+ AI tools):

| Tool | Install Path | Invocation |
|------|-------------|-----------|
| Antigravity | `.agent/skills/skills/wpf-csharp/` | `Use wpf-csharp skill` |
| Kiro | `.agent/skills/skills/wpf-csharp/` | `Use wpf-csharp skill` |
| Claude Code | `.claude/skills/wpf-csharp/` | `/wpf-csharp ...` |
| Cursor | `.cursor/skills/wpf-csharp/` | `@wpf-csharp in Chat` |

**Deploy to additional paths (Windows, run as Admin or with Developer Mode):**
```powershell
New-Item -ItemType SymbolicLink -Path ".claude\skills\wpf-csharp" `
  -Target "LaptopTesterPro\.agent\skills\skills\wpf-csharp"
New-Item -ItemType SymbolicLink -Path ".cursor\skills\wpf-csharp" `
  -Target "LaptopTesterPro\.agent\skills\skills\wpf-csharp"
```

## Pre-Delivery Checklist

### Async Safety
- [ ] All `async void` event handlers have try/catch blocks
- [ ] No `.Result` or `.Wait()` on Tasks in UI thread
- [ ] Long operations use IsBusy + CancellationToken

### Memory & Resources
- [ ] Services with WMI/hardware handles implement IDisposable
- [ ] LibreHardwareMonitor: `computer.Close()` called in Dispose
- [ ] WMI event watchers unsubscribed in Dispose

### XAML & Accessibility
- [ ] No hardcoded hex colors (use ResourceDictionary)
- [ ] All icon-only buttons have `AutomationProperties.Name`
- [ ] Interactive Borders converted to Button with custom style
- [ ] DynamicResource used for theme-switchable values

### Testing
- [ ] Business logic services have IWmiService/IHardwareService interfaces
- [ ] Unit tests use Moq, not real hardware
- [ ] Integration tests tagged `[Trait("Category", "Integration")]`
- [ ] Critical calculations (battery health, SMART score) have 100% coverage

### Localization
- [ ] All user-visible strings use DynamicResource
- [ ] Technical units (MHz, GB, MB/s) NOT localized
- [ ] New strings added to ALL language files

### Architecture
- [ ] No service duplication (single IHardwareService)
- [ ] Feature gating via IFeatureGateService
- [ ] Evaluation logic consistent: QuickTest score = Full Report verdict
- [ ] Admin rights: graceful degradation, not crash
