# Error Handling Patterns

Reference guide for robust error handling in LaptopTesterPro — covering WMI failures, hardware access errors, and graceful degradation.

## ILogger Service Pattern

Use `Microsoft.Extensions.Logging` throughout — never `Console.WriteLine` or `Debug.WriteLine` in production code.

```csharp
// Services/CpuTestService.cs
public class CpuTestService : ICpuTestService
{
    private readonly ILogger<CpuTestService> _logger;
    private readonly IWmiService _wmi;

    public CpuTestService(ILogger<CpuTestService> logger, IWmiService wmi)
    {
        _logger = logger;
        _wmi = wmi;
    }

    public async Task<CpuTestResult> RunStressTestAsync(CancellationToken ct)
    {
        _logger.LogInformation("Starting CPU stress test");
        try
        {
            var result = await RunLucasLehmerAsync(ct);
            _logger.LogInformation("CPU stress test completed: {Score}", result.Score);
            return result;
        }
        catch (OperationCanceledException)
        {
            _logger.LogWarning("CPU stress test cancelled by user");
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "CPU stress test failed unexpectedly");
            throw;
        }
    }
}
```

Register in DI:
```csharp
// App.xaml.cs
services.AddLogging(builder =>
{
    builder.AddDebug();
    builder.AddFile("logs/laptoptester-{Date}.log"); // Serilog.Extensions.Logging.File
    builder.SetMinimumLevel(LogLevel.Information);
});
```

## Specific Exception Catching

Always catch the most specific exception first. For hardware diagnostics:

```csharp
public async Task<BatteryInfo?> GetBatteryInfoAsync()
{
    try
    {
        return await _wmi.QueryBatteryAsync();
    }
    catch (ManagementException ex) when (ex.ErrorCode == ManagementStatus.NotFound)
    {
        _logger.LogWarning("WMI BatteryStaticData class not found — no battery present");
        return null;
    }
    catch (ManagementException ex)
    {
        _logger.LogError(ex, "WMI query failed: {ErrorCode}", ex.ErrorCode);
        return null;
    }
    catch (UnauthorizedAccessException ex)
    {
        _logger.LogWarning(ex, "Insufficient permissions for battery WMI query");
        return null; // Degrade gracefully — show "N/A" in UI
    }
    catch (IOException ex)
    {
        _logger.LogError(ex, "I/O error reading battery data");
        return null;
    }
}
```

### WMI Exception Hierarchy

| Exception | Cause | Action |
|-----------|-------|--------|
| `ManagementException (NotFound)` | Class/instance missing | Return null, show "Not Available" |
| `ManagementException (AccessDenied)` | No admin rights | Prompt elevation or degrade |
| `UnauthorizedAccessException` | OS-level permission | Degrade gracefully |
| `IOException` | Hardware read failure | Log + return null |
| `COMException` | WMI service crash | Restart WMI or show error |
| `TimeoutException` | WMI query timeout | Retry once, then fail |

## Global Unhandled Exception Handler

Catch all unhandled exceptions at the application boundary:

```csharp
// App.xaml.cs
public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // WPF UI thread exceptions
        DispatcherUnhandledException += OnDispatcherUnhandledException;

        // Non-UI thread exceptions
        AppDomain.CurrentDomain.UnhandledException += OnDomainUnhandledException;

        // Async task exceptions
        TaskScheduler.UnobservedTaskException += OnUnobservedTaskException;
    }

    private void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
    {
        var logger = _serviceProvider.GetRequiredService<ILogger<App>>();
        logger.LogCritical(e.Exception, "Unhandled UI exception");

        MessageBox.Show(
            $"An unexpected error occurred:\n{e.Exception.Message}\n\nThe application will continue.",
            "LaptopTester Error",
            MessageBoxButton.OK,
            MessageBoxImage.Error);

        e.Handled = true; // Prevent crash — allow user to save results
    }

    private void OnDomainUnhandledException(object sender, UnhandledExceptionEventArgs e)
    {
        var logger = _serviceProvider.GetRequiredService<ILogger<App>>();
        logger.LogCritical(e.ExceptionObject as Exception, "Fatal unhandled exception");
        // IsTerminating = true means app will crash — log and exit cleanly
    }

    private void OnUnobservedTaskException(object sender, UnobservedTaskExceptionEventArgs e)
    {
        var logger = _serviceProvider.GetRequiredService<ILogger<App>>();
        logger.LogError(e.Exception, "Unobserved task exception");
        e.SetObserved(); // Prevent process termination
    }
}
```

## Admin Rights Graceful Degradation

Some hardware tests require elevation. Never crash — degrade gracefully:

```csharp
public class AdminGuard
{
    public static bool IsRunningAsAdmin()
    {
        using var identity = WindowsIdentity.GetCurrent();
        var principal = new WindowsPrincipal(identity);
        return principal.IsInRole(WindowsBuiltInRole.Administrator);
    }

    public static bool TryRequireAdmin(string featureName, ILogger logger)
    {
        if (IsRunningAsAdmin()) return true;

        logger.LogWarning("Feature '{Feature}' requires admin rights — degrading", featureName);
        return false;
    }
}

// Usage in DiskTestService
public async Task<DiskSmartResult?> ReadSmartDataAsync(string diskId)
{
    if (!AdminGuard.TryRequireAdmin("SMART disk data", _logger))
    {
        // Return partial result without SMART data
        return new DiskSmartResult
        {
            DiskId = diskId,
            SmartAvailable = false,
            Note = "Admin rights required for SMART data. Run as Administrator for full results."
        };
    }

    // Proceed with SMART query...
    return await ReadSmartInternalAsync(diskId);
}
```

### Elevation Prompt Pattern

```csharp
// ViewModels/MainViewModel.cs
[RelayCommand]
private async Task RunFullDiagnosticsAsync()
{
    if (!AdminGuard.IsRunningAsAdmin())
    {
        var result = MessageBox.Show(
            "Some tests (SMART data, kernel-level CPU) require Administrator rights.\n\n" +
            "Restart as Administrator for complete results?",
            "Elevation Required",
            MessageBoxButton.YesNo,
            MessageBoxImage.Question);

        if (result == MessageBoxResult.Yes)
        {
            RestartAsAdmin();
            return;
        }
        // User chose No — continue with limited tests
    }

    await RunDiagnosticsAsync();
}

private static void RestartAsAdmin()
{
    var psi = new ProcessStartInfo
    {
        FileName = Environment.ProcessPath,
        UseShellExecute = true,
        Verb = "runas"
    };
    Process.Start(psi);
    Application.Current.Shutdown();
}
```

## Result\<T\> Pattern

Use `Result<T>` for operations that can fail without throwing — keeps ViewModels clean:

```csharp
// Models/Result.cs
public readonly struct Result<T>
{
    public T? Value { get; }
    public string? Error { get; }
    public bool IsSuccess { get; }

    private Result(T value) { Value = value; IsSuccess = true; Error = null; }
    private Result(string error) { Value = default; IsSuccess = false; Error = error; }

    public static Result<T> Ok(T value) => new(value);
    public static Result<T> Fail(string error) => new(error);

    public Result<TOut> Map<TOut>(Func<T, TOut> mapper) =>
        IsSuccess ? Result<TOut>.Ok(mapper(Value!)) : Result<TOut>.Fail(Error!);
}

// Services/RamTestService.cs
public async Task<Result<RamTestResult>> RunMemoryTestAsync(CancellationToken ct)
{
    try
    {
        if (!AdminGuard.IsRunningAsAdmin())
            return Result<RamTestResult>.Fail("Memory pattern test requires Administrator rights.");

        var result = await RunPatternTestInternalAsync(ct);
        return Result<RamTestResult>.Ok(result);
    }
    catch (OutOfMemoryException)
    {
        return Result<RamTestResult>.Fail("Insufficient memory to run test. Close other applications.");
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "RAM test failed");
        return Result<RamTestResult>.Fail($"Test failed: {ex.Message}");
    }
}

// ViewModel usage
var result = await _ramService.RunMemoryTestAsync(ct);
if (result.IsSuccess)
    RamScore = result.Value!.Score;
else
    RamError = result.Error;
```

## Null-Safe WMI Data Access

WMI properties can be null even when the query succeeds. Always use null-safe access:

```csharp
// WRONG — throws NullReferenceException if property missing
var capacity = (ulong)obj["MaxCapacity"];
var name = obj["Name"].ToString();

// CORRECT — null-safe with fallback
var capacity = obj["MaxCapacity"] is ulong cap ? cap : 0UL;
var name = obj["Name"]?.ToString() ?? "Unknown";
var voltage = obj["DesignVoltage"] is uint v ? v : (uint?)null;

// Pattern for numeric WMI values
private static int GetWmiInt(ManagementObject obj, string property, int fallback = 0)
{
    try
    {
        var val = obj[property];
        return val is null ? fallback : Convert.ToInt32(val);
    }
    catch (ManagementException)
    {
        return fallback;
    }
}

// Usage
var clockSpeed = GetWmiInt(cpuObj, "MaxClockSpeed");
var coreCount = GetWmiInt(cpuObj, "NumberOfCores", 1);
```

### Safe WMI Query Wrapper

```csharp
public async Task<IReadOnlyList<Dictionary<string, object?>>> SafeQueryAsync(
    string wmiClass,
    string[] properties,
    CancellationToken ct = default)
{
    var results = new List<Dictionary<string, object?>>();

    try
    {
        using var searcher = new ManagementObjectSearcher($"SELECT * FROM {wmiClass}");
        using var collection = await Task.Run(() => searcher.Get(), ct);

        foreach (ManagementObject obj in collection)
        {
            var row = new Dictionary<string, object?>();
            foreach (var prop in properties)
            {
                try { row[prop] = obj[prop]; }
                catch { row[prop] = null; } // Property not available on this hardware
            }
            results.Add(row);
            obj.Dispose();
        }
    }
    catch (ManagementException ex)
    {
        _logger.LogWarning(ex, "WMI class {Class} not available", wmiClass);
    }

    return results;
}
```

## Measurement Disclaimer Pattern

Hardware measurements have inherent uncertainty. Surface this in the UI:

```csharp
// Models/TestResult.cs
public record TestResult
{
    public double Score { get; init; }
    public string? Disclaimer { get; init; }
    public MeasurementConfidence Confidence { get; init; }
}

public enum MeasurementConfidence { High, Medium, Low, NotAvailable }

// Services/BatteryTestService.cs
public BatteryTestResult BuildResult(uint designCapacity, uint fullChargeCapacity)
{
    var health = designCapacity > 0
        ? (double)fullChargeCapacity / designCapacity * 100
        : 0;

    return new BatteryTestResult
    {
        HealthPercent = health,
        Confidence = designCapacity > 0 ? MeasurementConfidence.High : MeasurementConfidence.Low,
        Disclaimer = designCapacity == 0
            ? "Design capacity unavailable — health estimate may be inaccurate."
            : health > 100
                ? "Reported capacity exceeds design spec — battery data may be unreliable."
                : null
    };
}
```

```xml
<!-- Views/BatteryView.xaml -->
<StackPanel>
    <TextBlock Text="{Binding BatteryResult.HealthPercent, StringFormat='{}{0:F1}%'}"
               Style="{StaticResource ScoreTextStyle}" />

    <!-- Disclaimer — only visible when set -->
    <Border Background="#FFF3CD" CornerRadius="4" Padding="8,4"
            Visibility="{Binding BatteryResult.Disclaimer,
                         Converter={StaticResource NullToCollapsedConverter}}">
        <TextBlock Text="{Binding BatteryResult.Disclaimer}"
                   Foreground="#856404" FontSize="11"
                   TextWrapping="Wrap" />
    </Border>
</StackPanel>
```

## Anti-Patterns to Avoid

```csharp
// ❌ Swallowing exceptions silently
catch (Exception) { } // Never do this

// ❌ Catching Exception for control flow
try { var x = int.Parse(input); }
catch (Exception) { x = 0; } // Use int.TryParse instead

// ❌ Re-throwing incorrectly (loses stack trace)
catch (Exception ex) { throw ex; } // Use: throw;

// ❌ Logging and rethrowing the same exception twice
catch (Exception ex)
{
    _logger.LogError(ex, "Failed");
    throw; // OK only if caller won't log again
}

// ✅ Correct rethrow
catch (Exception ex)
{
    _logger.LogError(ex, "WMI query failed for {Class}", wmiClass);
    throw; // Preserves original stack trace
}
```

## Checklist

- [ ] All services use `ILogger<T>` — no Console/Debug.WriteLine
- [ ] WMI properties accessed with null-safe `?.ToString()` or `is` pattern
- [ ] `ManagementException` caught before generic `Exception`
- [ ] `DispatcherUnhandledException` registered in App.xaml.cs
- [ ] Admin-required features degrade gracefully with user message
- [ ] `Result<T>` used for operations that can fail without throwing
- [ ] Measurement disclaimers shown when confidence is Low
- [ ] No silent `catch (Exception) { }` blocks
