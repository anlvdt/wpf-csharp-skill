# DI Architecture

Dependency Injection patterns cho WPF C# — App.xaml.cs setup, service lifetimes, FeatureGate.

## Quick Reference

| Lifetime | Use For | Example |
|----------|---------|---------|
| Singleton | Stateful services, caches, stores | `IWmiService`, `TestResultsStore` |
| Transient | ViewModels, per-operation | `DashboardViewModel`, `BatteryTestViewModel` |
| Scoped | Per-request context | Rarely used in WPF |

---

## 1. App.xaml.cs — DI Setup

```csharp
public partial class App : Application
{
    public static IServiceProvider Services { get; private set; } = null!;

    protected override void OnStartup(StartupEventArgs e)
    {
        var services = new ServiceCollection();
        ConfigureServices(services);
        Services = services.BuildServiceProvider();

        var mainWindow = Services.GetRequiredService<MainWindow>();
        mainWindow.Show();

        base.OnStartup(e);
    }

    private static void ConfigureServices(IServiceCollection services)
    {
        // Infrastructure — Singleton (stateful, shared)
        services.AddSingleton<IWmiService, WindowsWmiService>();
        services.AddSingleton<ILocalizationService, LocalizationService>();
        services.AddSingleton<IFeatureGateService, FeatureGateService>();
        services.AddSingleton<INavigationService, NavigationService>();
        services.AddSingleton<TestResultsStore>();

        // Logging
        services.AddLogging(builder =>
        {
            builder.AddDebug();
            builder.SetMinimumLevel(LogLevel.Information);
        });

        // Hardware Services — Singleton (expensive to create, cache results)
        services.AddSingleton<IHardwareService, HardwareService>();
        services.AddSingleton<IBatteryService, BatteryTestService>();
        services.AddSingleton<ISmartDataService, SmartDataService>();
        services.AddSingleton<ITemperatureService, TemperatureService>();

        // ViewModels — Transient (new instance per navigation)
        services.AddTransient<MainViewModel>();
        services.AddTransient<DashboardViewModel>();
        services.AddTransient<BatteryTestViewModel>();
        services.AddTransient<HardwareViewModel>();
        services.AddTransient<KeyboardTestViewModel>();
        services.AddTransient<DiskTestViewModel>();
        services.AddTransient<SettingsViewModel>();

        // Windows
        services.AddTransient<MainWindow>();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        // Dispose singleton services that hold hardware handles
        if (Services is IDisposable disposable)
            disposable.Dispose();
        base.OnExit(e);
    }
}
```

---

## 2. Service Lifetime Patterns

```csharp
// ✅ Singleton: stateful, expensive to create, shared across app
// Use for: WMI service, hardware cache, settings, TestResultsStore
services.AddSingleton<IWmiService, WindowsWmiService>();
services.AddSingleton<TestResultsStore>();

// ✅ Transient: new instance every time — use for ViewModels
// ViewModels should be fresh on each navigation to avoid stale state
services.AddTransient<BatteryTestViewModel>();

// ❌ Anti-pattern: Singleton ViewModel
// services.AddSingleton<BatteryTestViewModel>(); // stale state, memory leak

// ❌ Anti-pattern: Transient for expensive services
// services.AddTransient<IWmiService, WindowsWmiService>(); // creates new WMI connection each time
```

---

## 3. Interface-First Design

```csharp
// ✅ Every service MUST have an interface
public interface IHardwareService
{
    CpuInfo GetCpuInfo();
    GpuInfo GetGpuInfo();
    RamInfo GetRamInfo();
    IReadOnlyList<DiskInfo> GetDiskInfo();
    Task<double> GetCpuTemperatureAsync();
}

public class HardwareService : IHardwareService
{
    private readonly IWmiService _wmi;
    private readonly ITemperatureService _temp;

    public HardwareService(IWmiService wmi, ITemperatureService temp)
    {
        _wmi = wmi;
        _temp = temp;
    }

    public CpuInfo GetCpuInfo()
    {
        var result = _wmi.Query("Win32_Processor").FirstOrDefault();
        return result == null ? CpuInfo.Unknown : new CpuInfo
        {
            Name = result["Name"]?.ToString()?.Trim() ?? "Unknown",
            Cores = Convert.ToInt32(result["NumberOfCores"] ?? 0),
            Threads = Convert.ToInt32(result["NumberOfLogicalProcessors"] ?? 0),
            MaxClockSpeedMhz = Convert.ToInt32(result["MaxClockSpeed"] ?? 0)
        };
    }
    // ... other methods
}

// ❌ Anti-pattern: service duplication
// Don't create HardwareService, HardwareInfoService, HardwareDetectionService
// Consolidate into single IHardwareService with clear method boundaries
```

---

## 4. ViewModelLocator Pattern

```csharp
// ViewModelLocator — resolves ViewModels from DI for XAML DataContext
public class ViewModelLocator
{
    public MainViewModel Main =>
        App.Services.GetRequiredService<MainViewModel>();

    public DashboardViewModel Dashboard =>
        App.Services.GetRequiredService<DashboardViewModel>();

    public BatteryTestViewModel BatteryTest =>
        App.Services.GetRequiredService<BatteryTestViewModel>();

    public SettingsViewModel Settings =>
        App.Services.GetRequiredService<SettingsViewModel>();
}
```

```xml
<!-- App.xaml — register locator as resource -->
<Application.Resources>
    <ResourceDictionary>
        <local:ViewModelLocator x:Key="Locator" />
        <!-- ... other resources -->
    </ResourceDictionary>
</Application.Resources>
```

```xml
<!-- MainWindow.xaml — bind DataContext via locator -->
<Window DataContext="{Binding Source={StaticResource Locator}, Path=Main}">
    <!-- ... -->
</Window>

<!-- Or in UserControl -->
<UserControl DataContext="{Binding Source={StaticResource Locator}, Path=BatteryTest}">
    <!-- ... -->
</UserControl>
```

---

## 5. Service Duplication Warning

```csharp
// ❌ Anti-pattern: multiple overlapping hardware services
services.AddSingleton<HardwareService>();        // reads CPU, GPU, RAM
services.AddSingleton<HardwareInfoService>();    // also reads CPU, GPU
services.AddSingleton<HardwareDetectionService>(); // also reads CPU

// ✅ Correct: single consolidated service
services.AddSingleton<IHardwareService, HardwareService>();
// IHardwareService has ALL hardware methods: GetCpuInfo, GetGpuInfo, GetRamInfo, etc.

// ✅ Separate services only when truly distinct domains
services.AddSingleton<IHardwareService, HardwareService>();   // static hardware info
services.AddSingleton<IBatteryService, BatteryTestService>(); // battery-specific tests
services.AddSingleton<ISmartDataService, SmartDataService>(); // SMART/disk health
```

---

## 6. FeatureGate Pattern

```csharp
// Interface — controls feature availability by license/tier
public interface IFeatureGateService
{
    bool CanExportPdf();
    bool CanExportHtml();
    bool CanUseAIAdvisor();
    bool CanRunBatteryTest();
    bool CanDetectFakeSpecs();
    bool CanRunFullDiagnostics();
}

// Implementation — checks license tier
public class FeatureGateService : IFeatureGateService
{
    private readonly ILicenseService _license;

    public FeatureGateService(ILicenseService license) => _license = license;

    public bool CanExportPdf() =>
        _license.Tier >= LicenseTier.Pro;

    public bool CanUseAIAdvisor() =>
        _license.Tier >= LicenseTier.Pro && _license.IsActivated;

    public bool CanRunBatteryTest() =>
        true; // available in all tiers

    public bool CanDetectFakeSpecs() =>
        _license.Tier >= LicenseTier.Standard;
}

// Usage in ViewModel — RelayCommand CanExecute integration
public partial class ReportViewModel : ViewModelBase
{
    private readonly IFeatureGateService _featureGate;
    private readonly IReportService _reportService;

    public ReportViewModel(IFeatureGateService featureGate, IReportService reportService)
    {
        _featureGate = featureGate;
        _reportService = reportService;
    }

    [RelayCommand(CanExecute = nameof(CanExportPdf))]
    private async Task ExportPdfAsync(CancellationToken ct)
    {
        await _reportService.ExportPdfAsync(ct);
    }

    private bool CanExportPdf() => _featureGate.CanExportPdf();

    [RelayCommand(CanExecute = nameof(CanUseAI))]
    private async Task GetAIAdviceAsync(CancellationToken ct)
    {
        await _aiService.GetAdviceAsync(ct);
    }

    private bool CanUseAI() => _featureGate.CanUseAIAdvisor();
}
```

```xml
<!-- XAML — show upgrade prompt when feature locked -->
<Button Command="{Binding ExportPdfCommand}"
        AutomationProperties.Name="Export PDF report"
        Content="Export PDF" />

<!-- Show lock icon when feature unavailable -->
<TextBlock Text="&#xE72E;" FontFamily="Segoe MDL2 Assets"
           Visibility="{Binding ExportPdfCommand.CanExecute,
               Converter={StaticResource InverseBoolToVisible}}"
           ToolTip="Upgrade to Pro to export PDF" />
```

---

## 7. Service Registration Validation

```csharp
// ✅ Validate DI container at startup (catch missing registrations early)
protected override void OnStartup(StartupEventArgs e)
{
    var services = new ServiceCollection();
    ConfigureServices(services);
    var provider = services.BuildServiceProvider(
        new ServiceProviderOptions { ValidateOnBuild = true }); // throws if misconfigured
    Services = provider;
    // ...
}
```

---

## Checklist

- [ ] All services registered in `App.xaml.cs` `ConfigureServices`
- [ ] Every service has a corresponding `IServiceName` interface
- [ ] Hardware services registered as Singleton (expensive to create)
- [ ] ViewModels registered as Transient (fresh state per navigation)
- [ ] `TestResultsStore` registered as Singleton
- [ ] No duplicate services for same domain (single `IHardwareService`)
- [ ] `IFeatureGateService` controls all license-gated features
- [ ] `RelayCommand.CanExecute` wired to `IFeatureGateService` methods
- [ ] `ValidateOnBuild = true` in development to catch missing registrations
