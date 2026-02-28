# Performance Patterns

Reference guide for memory management, UI virtualization, WMI caching, and benchmark accuracy in LaptopTesterPro.

## IDisposable Pattern

Always dispose WMI connections, file handles, and hardware monitors. Use `using` declarations or implement `IDisposable` explicitly.

```csharp
// Services/WmiService.cs
public class WmiService : IWmiService, IDisposable
{
    private ManagementObjectSearcher? _cpuSearcher;
    private bool _disposed;

    public IReadOnlyList<CpuInfo> GetCpuInfo()
    {
        // Reuse cached searcher — don't create in a loop
        _cpuSearcher ??= new ManagementObjectSearcher("SELECT * FROM Win32_Processor");

        var results = new List<CpuInfo>();
        using var collection = _cpuSearcher.Get();
        foreach (ManagementObject obj in collection)
        {
            results.Add(new CpuInfo
            {
                Name = obj["Name"]?.ToString() ?? "Unknown",
                MaxClockSpeed = obj["MaxClockSpeed"] is uint mhz ? mhz : 0,
                NumberOfCores = obj["NumberOfCores"] is uint cores ? cores : 0,
            });
            obj.Dispose();
        }
        return results;
    }

    public void Dispose()
    {
        if (_disposed) return;
        _cpuSearcher?.Dispose();
        _disposed = true;
        GC.SuppressFinalize(this);
    }
}
```

### LibreHardwareMonitor Disposal

```csharp
// Services/HardwareMonitorService.cs
public class HardwareMonitorService : IHardwareMonitorService, IDisposable
{
    private readonly Computer _computer;
    private bool _disposed;

    public HardwareMonitorService()
    {
        _computer = new Computer
        {
            IsCpuEnabled = true,
            IsGpuEnabled = true,
            IsBatteryEnabled = true,
            IsMemoryEnabled = true,
        };
        _computer.Open();
    }

    public float GetCpuTemperature()
    {
        _computer.Hardware[0].Update();
        return _computer.Hardware[0].Sensors
            .FirstOrDefault(s => s.SensorType == SensorType.Temperature)
            ?.Value ?? 0f;
    }

    public void Dispose()
    {
        if (_disposed) return;
        _computer.Close(); // REQUIRED — releases kernel handles
        _disposed = true;
        GC.SuppressFinalize(this);
    }
}
```

Register as singleton so `Dispose` is called once on app shutdown:

```csharp
// App.xaml.cs
services.AddSingleton<IHardwareMonitorService, HardwareMonitorService>();

// On shutdown
protected override void OnExit(ExitEventArgs e)
{
    (_serviceProvider as IDisposable)?.Dispose(); // Disposes all singletons
    base.OnExit(e);
}
```

## VirtualizingStackPanel for Large Lists

Test result lists can grow to hundreds of items. Always enable virtualization:

```xml
<!-- Views/TestResultsView.xaml -->
<ListView ItemsSource="{Binding TestResults}"
          VirtualizingStackPanel.IsVirtualizing="True"
          VirtualizingStackPanel.VirtualizationMode="Recycling"
          ScrollViewer.IsDeferredScrollingEnabled="True">
    <ListView.ItemsPanel>
        <ItemsPanelTemplate>
            <VirtualizingStackPanel />
        </ItemsPanelTemplate>
    </ListView.ItemsPanel>
    <ListView.ItemTemplate>
        <DataTemplate>
            <Border Padding="12,8" BorderThickness="0,0,0,1"
                    BorderBrush="{DynamicResource BorderBrush}">
                <Grid>
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*" />
                        <ColumnDefinition Width="80" />
                        <ColumnDefinition Width="60" />
                    </Grid.ColumnDefinitions>
                    <TextBlock Text="{Binding TestName}" Grid.Column="0" />
                    <TextBlock Text="{Binding Score, StringFormat='{}{0:F1}'}" Grid.Column="1" />
                    <TextBlock Text="{Binding Status}" Grid.Column="2" />
                </Grid>
            </Border>
        </DataTemplate>
    </ListView.ItemTemplate>
</ListView>
```

### When NOT to Use Virtualization

```xml
<!-- ❌ Virtualization breaks with fixed-height containers -->
<!-- Don't set fixed Height on the ListView — let it stretch -->
<ListView Height="200" ...> <!-- Breaks recycling -->

<!-- ✅ Use MaxHeight + stretch instead -->
<ListView MaxHeight="400"
          VirtualizingStackPanel.IsVirtualizing="True" ...>
```

## ManagementObjectSearcher Caching

Never create `ManagementObjectSearcher` inside a loop or timer callback — it's expensive:

```csharp
// ❌ WRONG — creates new searcher on every poll
private async Task PollHardwareAsync(CancellationToken ct)
{
    while (!ct.IsCancellationRequested)
    {
        using var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_Processor"); // Expensive!
        // ...
        await Task.Delay(1000, ct);
    }
}

// ✅ CORRECT — cache searcher, only recreate collection
public class CpuMonitorService : IDisposable
{
    private readonly ManagementObjectSearcher _searcher =
        new("SELECT LoadPercentage FROM Win32_Processor");

    public int GetCpuLoad()
    {
        using var collection = _searcher.Get(); // Only Get() is called each time
        foreach (ManagementObject obj in collection)
        {
            var load = obj["LoadPercentage"] is byte b ? b : (byte)0;
            obj.Dispose();
            return load;
        }
        return 0;
    }

    public void Dispose() => _searcher.Dispose();
}
```

### WMI Result Caching with TTL

For data that doesn't change frequently (CPU name, RAM slots, disk model):

```csharp
public class CachedWmiService : IWmiService
{
    private readonly Dictionary<string, (object Value, DateTime Expiry)> _cache = new();
    private readonly TimeSpan _defaultTtl = TimeSpan.FromSeconds(30);

    public T GetCached<T>(string key, Func<T> factory, TimeSpan? ttl = null)
    {
        if (_cache.TryGetValue(key, out var entry) && DateTime.UtcNow < entry.Expiry)
            return (T)entry.Value;

        var value = factory();
        _cache[key] = (value!, DateTime.UtcNow + (ttl ?? _defaultTtl));
        return value;
    }

    public string GetCpuName() =>
        GetCached("cpu_name", () =>
        {
            using var s = new ManagementObjectSearcher("SELECT Name FROM Win32_Processor");
            using var c = s.Get();
            foreach (ManagementObject o in c)
                return o["Name"]?.ToString() ?? "Unknown";
            return "Unknown";
        }, TimeSpan.FromMinutes(10)); // CPU name never changes — long TTL
}
```

## WeakReference and Event Unsubscription

Prevent memory leaks from event subscriptions in long-lived services:

```csharp
// ❌ WRONG — ViewModel holds strong reference via event, never GC'd
public class DashboardViewModel : ObservableObject
{
    public DashboardViewModel(IHardwareMonitorService monitor)
    {
        monitor.TemperatureUpdated += OnTemperatureUpdated; // Leak if monitor outlives VM
    }
}

// ✅ CORRECT — unsubscribe in Dispose
public class DashboardViewModel : ObservableObject, IDisposable
{
    private readonly IHardwareMonitorService _monitor;

    public DashboardViewModel(IHardwareMonitorService monitor)
    {
        _monitor = monitor;
        _monitor.TemperatureUpdated += OnTemperatureUpdated;
    }

    private void OnTemperatureUpdated(object? sender, float temp)
    {
        CpuTemperature = temp;
    }

    public void Dispose()
    {
        _monitor.TemperatureUpdated -= OnTemperatureUpdated;
    }
}
```

### WeakEventManager Pattern

For cases where unsubscription is impractical:

```csharp
// Use WeakEventManager for UI events that may outlive subscribers
WeakEventManager<IHardwareMonitorService, TemperatureEventArgs>
    .AddHandler(_monitor, nameof(_monitor.TemperatureUpdated), OnTemperatureUpdated);
```

## Median Selection for Benchmark Measurements

Never use a single measurement for benchmark scores — use median of multiple runs to filter outliers:

```csharp
// Services/CpuTestService.cs
public async Task<double> MeasureCpuScoreAsync(int runs, CancellationToken ct)
{
    var measurements = new List<double>(runs);

    for (int i = 0; i < runs; i++)
    {
        ct.ThrowIfCancellationRequested();
        var elapsed = await RunSingleLucasLehmerAsync(ct);
        measurements.Add(elapsed.TotalMilliseconds);
    }

    return CalculateMedian(measurements);
}

private static double CalculateMedian(List<double> values)
{
    if (values.Count == 0) return 0;

    var sorted = values.OrderBy(v => v).ToList();
    int mid = sorted.Count / 2;

    return sorted.Count % 2 == 0
        ? (sorted[mid - 1] + sorted[mid]) / 2.0
        : sorted[mid];
}

// Disk speed — median of 5 sequential reads
public async Task<double> MeasureDiskReadSpeedAsync(string path, CancellationToken ct)
{
    const int runs = 5;
    const int blockSize = 4 * 1024 * 1024; // 4 MB
    var speeds = new List<double>(runs);

    for (int i = 0; i < runs; i++)
    {
        ct.ThrowIfCancellationRequested();
        var sw = Stopwatch.StartNew();
        await ReadBlockAsync(path, blockSize, ct);
        sw.Stop();

        var mbPerSec = blockSize / sw.Elapsed.TotalSeconds / (1024 * 1024);
        speeds.Add(mbPerSec);
    }

    return CalculateMedian(speeds); // Filters thermal throttle spikes
}
```

### Why Median Over Average

| Scenario | Average | Median |
|----------|---------|--------|
| Thermal throttle spike | Skewed high | Unaffected |
| Background process burst | Skewed high | Unaffected |
| Cold start penalty | Skewed high | Unaffected |
| Consistent results | Same | Same |

Always use median for hardware benchmarks. Use average only for cumulative metrics (total bytes written).

## Anti-Patterns to Avoid

```csharp
// ❌ ManagementObjectSearcher in a loop
for (int i = 0; i < 100; i++)
{
    using var s = new ManagementObjectSearcher("SELECT * FROM Win32_Processor"); // 100x overhead
}

// ❌ Not disposing ManagementObject inside foreach
foreach (ManagementObject obj in collection)
{
    var name = obj["Name"]?.ToString();
    // Missing: obj.Dispose() — leaks COM object
}

// ❌ computer.Open() without computer.Close()
var computer = new Computer { IsCpuEnabled = true };
computer.Open();
// Missing: computer.Close() — leaks kernel handles

// ❌ Single measurement for benchmark
var score = await RunSingleTestAsync(); // Unreliable — use median of 5+

// ❌ Non-virtualizing panel for large lists
<ItemsControl ItemsSource="{Binding AllResults}"> <!-- Renders all 500 items at once -->
    <ItemsControl.ItemsPanel>
        <ItemsPanelTemplate>
            <StackPanel /> <!-- No virtualization -->
        </ItemsPanelTemplate>
    </ItemsControl.ItemsPanel>
</ItemsControl>
```

## Checklist

- [ ] All `ManagementObjectSearcher` instances cached (not created in loops/timers)
- [ ] `ManagementObject` disposed inside `foreach` loops
- [ ] `LibreHardwareMonitor` `computer.Close()` called in `Dispose()`
- [ ] `IDisposable` implemented on all services holding unmanaged resources
- [ ] Singleton services disposed on app exit via DI container
- [ ] `VirtualizingStackPanel` with `Recycling` mode on all large lists
- [ ] Event handlers unsubscribed in `Dispose()` or `WeakEventManager` used
- [ ] Benchmark scores use median of 5+ runs, not single measurement
- [ ] WMI static data (CPU name, RAM model) cached with appropriate TTL
