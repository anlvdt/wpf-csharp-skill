# Async Patterns

Async/await patterns cho WPF C# — UI responsiveness, thread safety, cancellation.

## Quick Reference

| Pattern | Rule |
|---------|------|
| `async void` | Only for event handlers — ALWAYS wrap in try/catch |
| Long operations | Use `IsBusy` + `CancellationToken` |
| Constructor async | Use `Loaded` event or factory method |
| Background → UI | Use `Dispatcher.InvokeAsync` or CommunityToolkit auto-dispatch |
| Library code | Use `ConfigureAwait(false)` |
| Progress | Use `IProgress<T>` |
| `.Result`/`.Wait()` | NEVER on UI thread — deadlock risk |

---

## 1. async void Safety Rule

```csharp
// ❌ DANGEROUS: unhandled exception crashes the entire app
private async void Button_Click(object sender, RoutedEventArgs e)
{
    await DoHeavyWorkAsync(); // If this throws, app crashes silently
}

// ❌ DANGEROUS: async void in non-event context
private async void LoadData() // Should be async Task
{
    await _service.LoadAsync();
}
```

```csharp
// ✅ SAFE: async void event handler with try/catch
private async void RunTest_Click(object sender, RoutedEventArgs e)
{
    try
    {
        await ViewModel.RunTestCommand.ExecuteAsync(null);
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "RunTest button click failed");
        MessageBox.Show($"Error: {ex.Message}", "Error",
            MessageBoxButton.OK, MessageBoxImage.Error);
    }
}

// ✅ PREFERRED: use RelayCommand instead of code-behind
// In ViewModel:
[RelayCommand]
private async Task RunTestAsync(CancellationToken ct)
{
    // exceptions handled by RelayCommand automatically
}
// In XAML:
// <Button Command="{Binding RunTestCommand}" />
// No code-behind needed!
```

---

## 2. IsBusy + CancellationToken Pattern

```csharp
public partial class HardwareTestViewModel : ViewModelBase
{
    private CancellationTokenSource? _cts;

    [ObservableProperty]
    private int _progress;

    [ObservableProperty]
    private string _statusMessage = string.Empty;

    [RelayCommand(CanExecute = nameof(CanStart))]
    private async Task StartTestAsync()
    {
        _cts = new CancellationTokenSource();
        IsBusy = true;
        Progress = 0;
        StatusMessage = "Starting test...";

        try
        {
            await _testService.RunAsync(
                new Progress<(int percent, string message)>(p =>
                {
                    Progress = p.percent;
                    StatusMessage = p.message;
                }),
                _cts.Token);

            StatusMessage = "Test completed successfully";
        }
        catch (OperationCanceledException)
        {
            StatusMessage = "Test cancelled by user";
        }
        catch (Exception ex)
        {
            ErrorMessage = $"Test failed: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
            _cts?.Dispose();
            _cts = null;
        }
    }

    [RelayCommand(CanExecute = nameof(CanCancel))]
    private void CancelTest()
    {
        _cts?.Cancel();
        StatusMessage = "Cancelling...";
    }

    private bool CanStart() => !IsBusy;
    private bool CanCancel() => IsBusy && _cts != null;
}
```

```xml
<!-- XAML -->
<StackPanel>
    <Button Content="Start Test"
            Command="{Binding StartTestCommand}"
            AutomationProperties.Name="Start hardware test" />
    <Button Content="Cancel"
            Command="{Binding CancelTestCommand}"
            AutomationProperties.Name="Cancel test" />
    <ProgressBar Value="{Binding Progress}" Maximum="100"
                 Visibility="{Binding IsBusy, Converter={StaticResource BoolToVisible}}" />
    <TextBlock Text="{Binding StatusMessage}" />
</StackPanel>
```

### Linked CancellationTokenSource (Timeout + User Cancel)

```csharp
// ✅ Combine user cancellation with timeout
private async Task RunWithTimeoutAsync(CancellationToken userToken)
{
    using var timeoutCts = new CancellationTokenSource(TimeSpan.FromSeconds(30));
    using var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(
        userToken, timeoutCts.Token);

    try
    {
        await _service.RunAsync(linkedCts.Token);
    }
    catch (OperationCanceledException) when (timeoutCts.IsCancellationRequested)
    {
        ErrorMessage = "Operation timed out after 30 seconds";
    }
    catch (OperationCanceledException)
    {
        StatusMessage = "Cancelled by user";
    }
}
```

---

## 3. Async Initialization — Loaded Event / Factory Method

```csharp
// ❌ WRONG: async in constructor — fire-and-forget, unhandled exceptions
public BatteryTestViewModel()
{
    LoadDataAsync(); // returns Task, not awaited — dangerous!
}

// ❌ WRONG: async void constructor workaround
public BatteryTestViewModel()
{
    _ = InitializeAsync(); // suppresses warning but still dangerous
}
```

```csharp
// ✅ OPTION 1: Loaded event in code-behind
public partial class BatteryTestView : UserControl
{
    public BatteryTestView()
    {
        InitializeComponent();
        Loaded += OnLoaded;
    }

    private async void OnLoaded(object sender, RoutedEventArgs e)
    {
        Loaded -= OnLoaded; // unsubscribe to prevent re-trigger
        try
        {
            await ((BatteryTestViewModel)DataContext).InitializeAsync();
        }
        catch (Exception ex)
        {
            // handle error
        }
    }
}

// ✅ OPTION 2: Factory method pattern
public partial class BatteryTestViewModel : ViewModelBase
{
    private BatteryTestViewModel(IBatteryService service)
    {
        _service = service;
    }

    public static async Task<BatteryTestViewModel> CreateAsync(IBatteryService service)
    {
        var vm = new BatteryTestViewModel(service);
        await vm.InitializeAsync();
        return vm;
    }

    private async Task InitializeAsync()
    {
        await ExecuteSafeAsync(async () =>
        {
            HealthPercent = await _service.GetHealthAsync(CancellationToken.None);
        });
    }
}

// ✅ OPTION 3: Lazy initialization on first command
[RelayCommand]
private async Task EnsureLoadedAsync()
{
    if (_isLoaded) return;
    await LoadDataAsync();
    _isLoaded = true;
}
```

---

## 4. Dispatcher.InvokeAsync — Background → UI Updates

```csharp
// ❌ WRONG: updating UI from background thread — InvalidOperationException
private async Task ProcessDataAsync()
{
    var results = await Task.Run(() => _service.GetHeavyData());
    Results.Add(results); // ❌ Cross-thread exception!
}

// ✅ CORRECT: Dispatcher.InvokeAsync
private async Task ProcessDataAsync()
{
    var results = await Task.Run(() => _service.GetHeavyData());

    await Application.Current.Dispatcher.InvokeAsync(() =>
    {
        foreach (var item in results)
            Results.Add(item);
        StatusMessage = $"Loaded {results.Count} items";
    });
}

// ✅ BETTER: CommunityToolkit.Mvvm handles dispatch automatically
// ObservableProperty changes are automatically dispatched to UI thread
// when using [ObservableProperty] — no manual Dispatcher needed for simple properties

// ✅ For background service callbacks
public class HardwareMonitorService
{
    private readonly SynchronizationContext? _uiContext;

    public HardwareMonitorService()
    {
        _uiContext = SynchronizationContext.Current; // capture UI context
    }

    private void OnTemperatureChanged(double temp)
    {
        _uiContext?.Post(_ =>
        {
            TemperatureChanged?.Invoke(this, temp); // fire on UI thread
        }, null);
    }
}
```

---

## 5. ConfigureAwait(false) — Library vs UI Code

```csharp
// ❌ WRONG in library/service code: captures UI SynchronizationContext unnecessarily
public class BatteryService : IBatteryService
{
    public async Task<double> GetHealthAsync(CancellationToken ct)
    {
        var data = await _wmi.QueryAsync("BatteryFullChargedCapacity", ct); // no ConfigureAwait
        return Calculate(data);
    }
}

// ✅ CORRECT in library/service code: ConfigureAwait(false) — no UI context needed
public class BatteryService : IBatteryService
{
    public async Task<double> GetHealthAsync(CancellationToken ct)
    {
        var data = await _wmi.QueryAsync("BatteryFullChargedCapacity", ct)
            .ConfigureAwait(false); // don't capture UI context
        return Calculate(data);
    }
}

// ✅ CORRECT in ViewModel (UI code): NO ConfigureAwait(false)
// ViewModels need to update UI properties — must stay on UI thread
[RelayCommand]
private async Task LoadAsync()
{
    var health = await _batteryService.GetHealthAsync(CancellationToken.None);
    // No ConfigureAwait(false) here — we need UI thread to update HealthPercent
    HealthPercent = health; // ✅ safe — still on UI thread
}
```

**Rule:** `ConfigureAwait(false)` in services/libraries. No `ConfigureAwait` in ViewModels/code-behind.

---

## 6. IProgress<T> — Progress Reporting

```csharp
// Service interface
public interface ICpuStressService
{
    Task<CpuStressResult> RunAsync(
        int durationSeconds,
        IProgress<StressProgress>? progress,
        CancellationToken ct);
}

public record StressProgress(int PercentComplete, double CurrentTempC, string Phase);

// Service implementation
public class CpuStressService : ICpuStressService
{
    public async Task<CpuStressResult> RunAsync(
        int durationSeconds,
        IProgress<StressProgress>? progress,
        CancellationToken ct)
    {
        var startTime = DateTime.UtcNow;
        var elapsed = TimeSpan.Zero;

        while (elapsed.TotalSeconds < durationSeconds && !ct.IsCancellationRequested)
        {
            // Do CPU work...
            await Task.Delay(500, ct).ConfigureAwait(false);

            elapsed = DateTime.UtcNow - startTime;
            var percent = (int)(elapsed.TotalSeconds / durationSeconds * 100);
            var temp = await GetCpuTempAsync(ct).ConfigureAwait(false);

            progress?.Report(new StressProgress(percent, temp, "Stress testing..."));
        }

        return new CpuStressResult { /* ... */ };
    }
}

// ViewModel usage
[RelayCommand]
private async Task RunCpuStressAsync(CancellationToken ct)
{
    IsBusy = true;
    var progress = new Progress<StressProgress>(p =>
    {
        // Progress<T> automatically marshals to UI thread
        Progress = p.PercentComplete;
        StatusMessage = $"{p.Phase} — {p.CurrentTempC:F1}°C";
    });

    try
    {
        var result = await _cpuService.RunAsync(30, progress, ct);
        StatusMessage = result.Stable ? "CPU stable" : $"Errors: {result.Errors}";
    }
    finally
    {
        IsBusy = false;
    }
}
```

---

## 7. .Result / .Wait() — Deadlock Warning

```csharp
// ❌ DEADLOCK: .Result on UI thread blocks the thread that async needs to resume on
private void Button_Click(object sender, RoutedEventArgs e)
{
    var result = _service.GetDataAsync().Result; // DEADLOCK!
    var result2 = _service.GetDataAsync().GetAwaiter().GetResult(); // also DEADLOCK!
    _service.GetDataAsync().Wait(); // also DEADLOCK!
}

// ❌ DEADLOCK in ViewModel constructor
public MyViewModel()
{
    _data = LoadDataAsync().Result; // DEADLOCK if called from UI thread
}
```

```csharp
// ✅ CORRECT: always await
private async void Button_Click(object sender, RoutedEventArgs e)
{
    try
    {
        var result = await _service.GetDataAsync();
        ProcessResult(result);
    }
    catch (Exception ex)
    {
        ErrorMessage = ex.Message;
    }
}

// ✅ EXCEPTION: .Result is safe AFTER Task.WhenAll completes
private async Task LoadAllAsync(CancellationToken ct)
{
    var batteryTask = _batteryService.GetHealthAsync(ct);
    var cpuTask = _cpuService.GetInfoAsync(ct);
    var ramTask = _ramService.GetInfoAsync(ct);

    await Task.WhenAll(batteryTask, cpuTask, ramTask); // wait for all

    // ✅ Safe to use .Result here — tasks are already completed
    BatteryHealth = batteryTask.Result;
    CpuInfo = cpuTask.Result;
    RamInfo = ramTask.Result;
}
```

---

## Checklist

- [ ] All `async void` methods (except event handlers) converted to `async Task`
- [ ] All `async void` event handlers have try/catch blocks
- [ ] Long operations use `IsBusy = true` + `CancellationToken`
- [ ] No async initialization in constructors — use `Loaded` event or factory method
- [ ] Background thread UI updates use `Dispatcher.InvokeAsync`
- [ ] Service/library code uses `ConfigureAwait(false)`
- [ ] Progress reporting uses `IProgress<T>` (auto-marshals to UI thread)
- [ ] No `.Result` or `.Wait()` on UI thread (except post-`Task.WhenAll`)
- [ ] `CancellationTokenSource` disposed in `finally` block
