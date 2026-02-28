# MVVM Patterns

Patterns cho Model-View-ViewModel architecture trong WPF C#, sử dụng CommunityToolkit.Mvvm.

## Quick Reference

| Pattern | Class/Interface | NuGet |
|---------|----------------|-------|
| Observable properties | `ObservableObject` | `CommunityToolkit.Mvvm` |
| Commands | `RelayCommand`, `AsyncRelayCommand` | `CommunityToolkit.Mvvm` |
| Navigation | `INavigationService` | Custom |
| Shared state | `TestResultsStore` | Custom singleton |
| Collections | `ObservableCollection<T>` | `System.Collections.ObjectModel` |

---

## 1. CommunityToolkit.Mvvm — Modern Pattern

### Setup

```xml
<!-- LaptopTesterPro.UI.csproj -->
<PackageReference Include="CommunityToolkit.Mvvm" Version="8.*" />
```

### ObservableProperty + NotifyPropertyChangedFor

```csharp
// ✅ Modern: source generators — no boilerplate
public partial class BatteryTestViewModel : ObservableObject
{
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(HealthStatus))]
    [NotifyCanExecuteChangedFor(nameof(RunTestCommand))]
    private double _healthPercent;

    [ObservableProperty]
    private bool _isBusy;

    [ObservableProperty]
    private string? _errorMessage;

    [ObservableProperty]
    private string _title = "Battery Test";

    // Computed property — auto-notified when HealthPercent changes
    public string HealthStatus => HealthPercent switch
    {
        >= 80 => "Good",
        >= 60 => "Fair",
        >= 40 => "Weak",
        _ => "Replace"
    };
}
```

```csharp
// ❌ Anti-pattern: manual INotifyPropertyChanged boilerplate
public class BatteryTestViewModel : INotifyPropertyChanged
{
    private double _healthPercent;
    public double HealthPercent
    {
        get => _healthPercent;
        set
        {
            _healthPercent = value;
            OnPropertyChanged(nameof(HealthPercent));
            OnPropertyChanged(nameof(HealthStatus)); // easy to forget
        }
    }
    public event PropertyChangedEventHandler? PropertyChanged;
    protected void OnPropertyChanged(string name) =>
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}
```

### RelayCommand + AsyncRelayCommand

```csharp
public partial class BatteryTestViewModel : ObservableObject
{
    private readonly IBatteryService _batteryService;
    private CancellationTokenSource? _cts;

    public BatteryTestViewModel(IBatteryService batteryService)
    {
        _batteryService = batteryService;
    }

    // ✅ Async command with CancellationToken support
    [RelayCommand(CanExecute = nameof(CanRunTest))]
    private async Task RunTestAsync(CancellationToken ct)
    {
        IsBusy = true;
        ErrorMessage = null;
        try
        {
            HealthPercent = await _batteryService.GetHealthAsync(ct);
        }
        catch (OperationCanceledException)
        {
            ErrorMessage = "Test cancelled";
        }
        catch (Exception ex)
        {
            ErrorMessage = ex.Message;
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private void CancelTest() => RunTestCommand.Cancel();

    private bool CanRunTest() => !IsBusy;
}
```

```xml
<!-- XAML binding -->
<Button Content="Run Test"
        Command="{Binding RunTestCommand}"
        AutomationProperties.Name="Run battery test" />
<Button Content="Cancel"
        Command="{Binding CancelTestCommand}"
        AutomationProperties.Name="Cancel test" />
<ProgressBar IsIndeterminate="{Binding IsBusy}" />
<TextBlock Text="{Binding ErrorMessage}"
           Foreground="{StaticResource ErrorBrush}"
           Visibility="{Binding ErrorMessage, Converter={StaticResource NullToCollapsed}}" />
```

---

## 2. ViewModelBase Pattern

```csharp
// Base class for all ViewModels
public partial class ViewModelBase : ObservableObject
{
    [ObservableProperty]
    private bool _isBusy;

    [ObservableProperty]
    private string? _errorMessage;

    [ObservableProperty]
    private string _title = string.Empty;

    [ObservableProperty]
    private string _statusMessage = string.Empty;

    protected async Task ExecuteSafeAsync(Func<Task> action, string? errorPrefix = null)
    {
        IsBusy = true;
        ErrorMessage = null;
        try
        {
            await action();
        }
        catch (OperationCanceledException)
        {
            StatusMessage = "Operation cancelled";
        }
        catch (Exception ex)
        {
            ErrorMessage = errorPrefix != null ? $"{errorPrefix}: {ex.Message}" : ex.Message;
        }
        finally
        {
            IsBusy = false;
        }
    }
}

// Usage
public partial class DashboardViewModel : ViewModelBase
{
    public DashboardViewModel()
    {
        Title = "Dashboard";
    }

    [RelayCommand]
    private async Task RefreshAsync() =>
        await ExecuteSafeAsync(async () =>
        {
            // load data
        }, "Refresh failed");
}
```

---

## 3. NavigationService — Stack-Based History

### Interface

```csharp
public interface INavigationService
{
    string CurrentPage { get; }
    bool CanGoBack { get; }
    void NavigateTo(string page);
    void GoBack();
    event EventHandler<string>? NavigationChanged;
}
```

### Implementation

```csharp
public class NavigationService : ObservableObject, INavigationService
{
    private readonly IServiceProvider _services;
    private readonly Stack<string> _history = new();

    [ObservableProperty]
    private string _currentPage = "Dashboard";

    [ObservableProperty]
    private bool _canGoBack;

    [ObservableProperty]
    private object? _currentView;

    public event EventHandler<string>? NavigationChanged;

    public NavigationService(IServiceProvider services)
    {
        _services = services;
    }

    public void NavigateTo(string page)
    {
        if (CurrentPage == page) return;

        CleanupCurrentView();           // Dispose IDisposable ViewModels
        _history.Push(CurrentPage);
        CanGoBack = _history.Count > 0;
        CurrentPage = page;
        CurrentView = GetViewModelForPage(page);
        NavigationChanged?.Invoke(this, page);
    }

    public void GoBack()
    {
        if (!_history.TryPop(out var previous)) return;
        CleanupCurrentView();
        CanGoBack = _history.Count > 0;
        CurrentPage = previous;
        CurrentView = GetViewModelForPage(previous);
        NavigationChanged?.Invoke(this, previous);
    }

    private void CleanupCurrentView()
    {
        // ✅ Dispose IDisposable ViewModels to release WMI/hardware handles
        if (CurrentView is IDisposable disposable)
            disposable.Dispose();
    }

    private object GetViewModelForPage(string page) => page switch
    {
        "Dashboard"    => _services.GetRequiredService<DashboardViewModel>(),
        "Battery"      => _services.GetRequiredService<BatteryTestViewModel>(),
        "Hardware"     => _services.GetRequiredService<HardwareViewModel>(),
        "Keyboard"     => _services.GetRequiredService<KeyboardTestViewModel>(),
        _              => throw new ArgumentException($"Unknown page: {page}")
    };
}
```

```csharp
// ❌ Anti-pattern: direct Window instantiation
[RelayCommand]
private void OpenBattery()
{
    var win = new BatteryWindow(); // tight coupling, no DI, no history
    win.Show();
}
```

### XAML — DataTemplate per ViewModel

```xml
<ContentControl Content="{Binding NavigationService.CurrentView}">
    <ContentControl.Resources>
        <DataTemplate DataType="{x:Type vm:DashboardViewModel}">
            <views:DashboardView />
        </DataTemplate>
        <DataTemplate DataType="{x:Type vm:BatteryTestViewModel}">
            <views:BatteryTestView />
        </DataTemplate>
        <DataTemplate DataType="{x:Type vm:HardwareViewModel}">
            <views:HardwareView />
        </DataTemplate>
    </ContentControl.Resources>
</ContentControl>
```

---

## 4. TestResultsStore — Shared State Singleton

```csharp
public enum TestSource { QuickTest, Workflow, Manual }

public class TestResult
{
    public required string TestName { get; init; }
    public required TestSource Source { get; init; }
    public required string Verdict { get; init; }   // "Pass", "Fail", "Warning"
    public double? Score { get; init; }
    public DateTime Timestamp { get; init; } = DateTime.UtcNow;
    public string? Details { get; init; }
}

// ✅ Singleton store — register as Singleton in DI
public class TestResultsStore
{
    private readonly List<TestResult> _results = new();
    private readonly object _lock = new();

    public event EventHandler? ResultsChanged;

    public void UpdateResult(TestResult result)
    {
        lock (_lock)
        {
            _results.RemoveAll(r => r.TestName == result.TestName
                                 && r.Source == result.Source);
            _results.Add(result);
        }
        ResultsChanged?.Invoke(this, EventArgs.Empty);
    }

    public IReadOnlyList<TestResult> GetResultsBySource(TestSource source)
    {
        lock (_lock)
            return _results.Where(r => r.Source == source).ToList();
    }

    public IReadOnlyList<TestResult> GetAll()
    {
        lock (_lock)
            return _results.ToList();
    }

    public TestResult? GetLatest(string testName)
    {
        lock (_lock)
            return _results
                .Where(r => r.TestName == testName)
                .OrderByDescending(r => r.Timestamp)
                .FirstOrDefault();
    }
}
```

```csharp
// DI registration
services.AddSingleton<TestResultsStore>();

// Usage in ViewModel
public partial class QuickTestViewModel : ViewModelBase
{
    private readonly TestResultsStore _store;

    public QuickTestViewModel(TestResultsStore store) => _store = store;

    [RelayCommand]
    private async Task RunQuickTestAsync()
    {
        // ... run test ...
        _store.UpdateResult(new TestResult
        {
            TestName = "Battery",
            Source = TestSource.QuickTest,
            Verdict = "Pass",
            Score = 87.5
        });
    }
}
```

---

## 5. ObservableCollection — Anti-Patterns

```csharp
// ❌ Anti-pattern: replacing collection reference breaks bindings
[RelayCommand]
private async Task LoadResultsAsync()
{
    var data = await _service.GetResultsAsync();
    Results = new ObservableCollection<TestResult>(data); // ❌ breaks XAML binding
}

// ✅ Correct: clear and repopulate
[RelayCommand]
private async Task LoadResultsAsync()
{
    var data = await _service.GetResultsAsync();
    Results.Clear();
    foreach (var item in data)
        Results.Add(item);
}

// ✅ Or use AddRange extension for performance
[RelayCommand]
private async Task LoadResultsAsync()
{
    var data = await _service.GetResultsAsync();
    Results.Clear();
    // Batch add to minimize UI updates
    foreach (var item in data)
        Results.Add(item);
}
```

```csharp
// ✅ Declare as readonly field, expose as property
public partial class ResultsViewModel : ViewModelBase
{
    public ObservableCollection<TestResult> Results { get; } = new();

    // ❌ Don't do this:
    // [ObservableProperty]
    // private ObservableCollection<TestResult> _results = new();
    // Because setting Results = new() in commands breaks bindings
}
```

---

## 6. DataTemplate and DataTemplateSelector

### DataTemplate (Static)

```xml
<ItemsControl ItemsSource="{Binding TestResults}">
    <ItemsControl.ItemTemplate>
        <DataTemplate DataType="{x:Type models:TestResult}">
            <Border Style="{StaticResource CardStyle}" Margin="0,4">
                <Grid>
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*" />
                        <ColumnDefinition Width="Auto" />
                    </Grid.ColumnDefinitions>
                    <TextBlock Text="{Binding TestName}"
                               Style="{StaticResource BodyTextStyle}" />
                    <TextBlock Grid.Column="1"
                               Text="{Binding Verdict}"
                               Foreground="{Binding Verdict,
                                   Converter={StaticResource VerdictToColorConverter}}" />
                </Grid>
            </Border>
        </DataTemplate>
    </ItemsControl.ItemTemplate>
</ItemsControl>
```

### DataTemplateSelector (Dynamic)

```csharp
public class TestResultTemplateSelector : DataTemplateSelector
{
    public DataTemplate? PassTemplate { get; set; }
    public DataTemplate? FailTemplate { get; set; }
    public DataTemplate? WarningTemplate { get; set; }

    public override DataTemplate? SelectTemplate(object item, DependencyObject container)
    {
        if (item is TestResult result)
        {
            return result.Verdict switch
            {
                "Pass"    => PassTemplate,
                "Fail"    => FailTemplate,
                "Warning" => WarningTemplate,
                _         => base.SelectTemplate(item, container)
            };
        }
        return base.SelectTemplate(item, container);
    }
}
```

```xml
<!-- Resources -->
<local:TestResultTemplateSelector x:Key="ResultSelector"
    PassTemplate="{StaticResource PassResultTemplate}"
    FailTemplate="{StaticResource FailResultTemplate}"
    WarningTemplate="{StaticResource WarningResultTemplate}" />

<!-- Usage -->
<ItemsControl ItemsSource="{Binding TestResults}"
              ItemTemplateSelector="{StaticResource ResultSelector}" />
```

---

## Checklist

- [ ] ViewModels inherit from `ObservableObject` (CommunityToolkit.Mvvm)
- [ ] `[ObservableProperty]` used instead of manual `INotifyPropertyChanged`
- [ ] `[RelayCommand]` / `[AsyncRelayCommand]` used for commands
- [ ] Navigation via `INavigationService`, not direct `new Window()`
- [ ] `CleanupCurrentView()` disposes IDisposable ViewModels on navigation
- [ ] `TestResultsStore` registered as Singleton in DI
- [ ] `ObservableCollection` never replaced by reference — use `.Clear()` + `.Add()`
- [ ] `DataTemplateSelector` used for dynamic content rendering
