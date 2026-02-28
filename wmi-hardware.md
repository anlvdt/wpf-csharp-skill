# WMI & Hardware Integration

WMI patterns, SMART data, battery health, USB detection cho WPF C# hardware diagnostic tools.

## Quick Reference

| Topic | Class/Namespace |
|-------|----------------|
| WMI abstraction | `IWmiService` / `WindowsWmiService` |
| CPU info | `Win32_Processor` (root\cimv2) |
| Battery health | `BatteryFullChargedCapacity` (root\wmi) |
| SMART status | `MSStorageDriver_ATAPISmartData` (root\wmi) |
| NVMe health | `MSFT_PhysicalDisk` (root\microsoft\windows\storage) |
| Hardware sensors | `LibreHardwareMonitorLib` |

---

## 1. IWmiService Interface — Testability

```csharp
// ✅ Interface for testability — mock in unit tests
public interface IWmiService
{
    IEnumerable<Dictionary<string, object?>> Query(
        string wmiClass,
        string? namespacePath = null,
        string? condition = null);
}

// Production implementation
public class WindowsWmiService : IWmiService
{
    public IEnumerable<Dictionary<string, object?>> Query(
        string wmiClass,
        string? namespacePath = null,
        string? condition = null)
    {
        var ns = namespacePath ?? @"root\cimv2";
        var query = condition != null
            ? $"SELECT * FROM {wmiClass} WHERE {condition}"
            : $"SELECT * FROM {wmiClass}";

        using var searcher = new ManagementObjectSearcher(ns, query);
        foreach (ManagementObject obj in searcher.Get())
        {
            var dict = new Dictionary<string, object?>();
            foreach (var prop in obj.Properties)
                dict[prop.Name] = prop.Value;
            yield return dict;
        }
    }
}

// DI registration
services.AddSingleton<IWmiService, WindowsWmiService>();
```

---

## 2. WMI Classes Reference Table

| Class | Namespace | Use Case |
|-------|-----------|---------|
| `Win32_Processor` | root\cimv2 | CPU name, MaxClockSpeed, NumberOfCores, NumberOfLogicalProcessors |
| `Win32_VideoController` | root\cimv2 | GPU name, AdapterRAM, DriverVersion |
| `Win32_PhysicalMemory` | root\cimv2 | RAM modules, Capacity, Speed, Manufacturer |
| `Win32_DiskDrive` | root\cimv2 | Disk model, Size, InterfaceType, SerialNumber |
| `Win32_Battery` | root\cimv2 | BatteryStatus, EstimatedChargeRemaining, EstimatedRunTime |
| `BatteryStaticData` | root\wmi | DesignedCapacity (mWh) |
| `BatteryFullChargedCapacity` | root\wmi | FullChargedCapacity (mWh) — for health calculation |
| `BatteryCycleCount` | root\wmi | CycleCount (OEM dependent, may be 0) |
| `MSStorageDriver_FailurePredictStatus` | root\wmi | PredictFailure (bool), Reason |
| `MSStorageDriver_ATAPISmartData` | root\wmi | VendorSpecific (512 bytes raw SMART data) |
| `MSFT_PhysicalDisk` | root\microsoft\windows\storage | MediaType, HealthStatus, OperationalStatus (NVMe) |
| `Win32_PnPEntity` | root\cimv2 | USB/Bluetooth devices, DeviceID, Description |
| `Win32_USBController` | root\cimv2 | USB host controllers, Name (for speed detection) |

```csharp
// Example: query CPU info
public CpuInfo GetCpuInfo()
{
    var result = _wmi.Query("Win32_Processor").FirstOrDefault();
    if (result == null) return CpuInfo.Unknown;

    return new CpuInfo
    {
        Name = result["Name"]?.ToString()?.Trim() ?? "Unknown",
        Cores = Convert.ToInt32(result["NumberOfCores"] ?? 0),
        Threads = Convert.ToInt32(result["NumberOfLogicalProcessors"] ?? 0),
        MaxClockSpeedMhz = Convert.ToInt32(result["MaxClockSpeed"] ?? 0),
        Architecture = result["Architecture"]?.ToString() ?? "Unknown"
    };
}
```

---

## 3. SMART Data Parsing — 12-Byte Attribute Structure

```csharp
// MSStorageDriver_ATAPISmartData.VendorSpecific = 512 bytes
// Attribute structure: offset 2 = start of attributes
// Each attribute: 12 bytes
//   [0]   = Attribute ID
//   [1]   = Status flags (low byte)
//   [2]   = Current value (0-253, higher = better)
//   [3]   = Worst value ever recorded
//   [4-9] = Raw value (6 bytes, little-endian)
//   [10-11] = Reserved

public class SmartAttribute
{
    public byte Id { get; init; }
    public byte CurrentValue { get; init; }
    public byte WorstValue { get; init; }
    public long RawValue { get; init; }
}

public List<SmartAttribute> ParseSmartData(byte[] vendorSpecific)
{
    var attributes = new List<SmartAttribute>();
    const int startOffset = 2;
    const int attributeSize = 12;
    const int maxAttributes = 30;

    for (int i = 0; i < maxAttributes; i++)
    {
        int offset = startOffset + (i * attributeSize);
        if (offset + attributeSize > vendorSpecific.Length) break;

        byte id = vendorSpecific[offset];
        if (id == 0) continue; // empty slot

        long rawValue = 0;
        for (int j = 0; j < 6; j++)
            rawValue |= (long)vendorSpecific[offset + 4 + j] << (j * 8);

        attributes.Add(new SmartAttribute
        {
            Id = id,
            CurrentValue = vendorSpecific[offset + 2],
            WorstValue = vendorSpecific[offset + 3],
            RawValue = rawValue
        });
    }

    return attributes;
}
```

---

## 4. Critical SMART Attributes

| ID | Name | Weight | Meaning |
|----|------|--------|---------|
| 5 | Reallocated Sectors Count | -5 per sector | Bad sectors remapped — critical |
| 9 | Power-On Hours | Info only | Drive age in hours |
| 187 | Reported Uncorrectable Errors | -4 per error | Errors that couldn't be corrected |
| 197 | Current Pending Sector Count | -3 per sector | Sectors waiting to be remapped |
| 198 | Offline Uncorrectable Sector Count | -4 per sector | Sectors that failed offline scan |

```csharp
// SMART health scoring algorithm (CrystalDiskInfo-style)
public int CalculateSmartHealth(List<SmartAttribute> attributes, bool predictFailure)
{
    int health = 100;

    foreach (var attr in attributes)
    {
        switch (attr.Id)
        {
            case 5:   // Reallocated Sectors
                health -= (int)Math.Min(50, attr.RawValue * 5);
                break;
            case 187: // Reported Uncorrectable
                health -= (int)Math.Min(40, attr.RawValue * 4);
                break;
            case 197: // Current Pending Sector
                health -= (int)Math.Min(30, attr.RawValue * 3);
                break;
            case 198: // Offline Uncorrectable
                health -= (int)Math.Min(40, attr.RawValue * 4);
                break;
        }
    }

    // WMI predict failure override
    if (predictFailure)
        health = Math.Min(health, 10);

    return Math.Max(0, health);
}
```

---

## 5. Battery Health Formula

```csharp
// ✅ Battery health calculation with division-by-zero guard
public BatteryHealthResult CalculateBatteryHealth()
{
    var fullChargeData = _wmi.Query("BatteryFullChargedCapacity", @"root\wmi")
        .FirstOrDefault();
    var staticData = _wmi.Query("BatteryStaticData", @"root\wmi")
        .FirstOrDefault();

    uint fullCharge = Convert.ToUInt32(fullChargeData?["FullChargedCapacity"] ?? 0u);
    uint designCap = Convert.ToUInt32(staticData?["DesignedCapacity"] ?? 0u);

    // Guard: division by zero
    if (designCap == 0)
        return new BatteryHealthResult { HealthPercent = 0, Status = "Unknown" };

    double healthPercent = Math.Round((double)fullCharge / designCap * 100, 1);

    // Clamp to reasonable range (some batteries report slightly over 100%)
    healthPercent = Math.Min(healthPercent, 150);

    return new BatteryHealthResult
    {
        HealthPercent = healthPercent,
        FullChargeCapacityMwh = fullCharge,
        DesignCapacityMwh = designCap,
        Status = healthPercent switch
        {
            >= 80 => "Good",
            >= 60 => "Fair",
            >= 40 => "Weak",
            _ => "Replace"
        }
    };
}

// Battery health thresholds (industry standard)
// > 80%: Good    — normal operation
// 60-80%: Fair   — reduced runtime, monitor
// 40-60%: Weak   — significant degradation
// < 40%: Replace — battery needs replacement
```

---

## 6. Graceful WMI Fallback Pattern

```csharp
// ✅ Multi-layer fallback for RAM detection
public long GetTotalRamBytes()
{
    // Layer 1: WMI Win32_PhysicalMemory (most accurate)
    try
    {
        var modules = _wmi.Query("Win32_PhysicalMemory");
        var total = modules.Sum(m => Convert.ToInt64(m["Capacity"] ?? 0L));
        if (total > 0) return total;
    }
    catch (ManagementException) { /* fall through */ }

    // Layer 2: Kernel32 GlobalMemoryStatusEx
    try
    {
        var memStatus = new MEMORYSTATUSEX { dwLength = (uint)Marshal.SizeOf<MEMORYSTATUSEX>() };
        if (GlobalMemoryStatusEx(ref memStatus))
            return (long)memStatus.ullTotalPhys;
    }
    catch { /* fall through */ }

    // Layer 3: WMI Win32_ComputerSystem (least accurate)
    try
    {
        var cs = _wmi.Query("Win32_ComputerSystem").FirstOrDefault();
        return Convert.ToInt64(cs?["TotalPhysicalMemory"] ?? 0L);
    }
    catch { return 0; }
}

// ✅ Null-safe WMI property access
public string GetCpuName()
{
    var cpu = _wmi.Query("Win32_Processor").FirstOrDefault();
    return cpu?["Name"]?.ToString()?.Trim() ?? "Unknown CPU";
}
```

---

## 7. LibreHardwareMonitor Integration

```csharp
// NuGet: LibreHardwareMonitorLib
public class HardwareSensorService : IDisposable
{
    private readonly Computer _computer;

    public HardwareSensorService()
    {
        _computer = new Computer
        {
            IsCpuEnabled = true,
            IsGpuEnabled = true,
            IsStorageEnabled = true,
            IsBatteryEnabled = true,
            IsMotherboardEnabled = false // not needed for most diagnostics
        };
        _computer.Open();
    }

    public double GetCpuTemperature()
    {
        _computer.Accept(new UpdateVisitor());

        foreach (var hardware in _computer.Hardware)
        {
            if (hardware.HardwareType != HardwareType.Cpu) continue;
            foreach (var sensor in hardware.Sensors)
            {
                if (sensor.SensorType == SensorType.Temperature
                    && sensor.Name.Contains("Package"))
                    return sensor.Value ?? 0;
            }
        }
        return 0;
    }

    public void Dispose()
    {
        _computer.Close(); // ✅ REQUIRED: releases hardware handles
    }
}

public class UpdateVisitor : IVisitor
{
    public void VisitComputer(IComputer computer) => computer.Traverse(this);
    public void VisitHardware(IHardware hardware)
    {
        hardware.Update();
        foreach (var sub in hardware.SubHardware)
            sub.Accept(this);
    }
    public void VisitSensor(ISensor sensor) { }
    public void VisitParameter(IParameter parameter) { }
}
```

---

## 8. USB Speed Detection

```csharp
// USB speed from controller/device name strings
public static string DetectUsbSpeed(string controllerName)
{
    var name = controllerName.ToUpperInvariant();

    if (name.Contains("USB4") || name.Contains("THUNDERBOLT 4"))
        return "USB4/TB4 (40 Gbps)";
    if (name.Contains("GEN 2X2") || name.Contains("GEN2X2"))
        return "USB 3.2 Gen 2x2 (20 Gbps)";
    if (name.Contains("GEN 2") || name.Contains("GEN2") || name.Contains("10GBPS"))
        return "USB 3.2 Gen 2 (10 Gbps)";
    if (name.Contains("GEN 1") || name.Contains("GEN1") || name.Contains("3.0") || name.Contains("5GBPS"))
        return "USB 3.2 Gen 1 (5 Gbps)";
    if (name.Contains("2.0") || name.Contains("EHCI") || name.Contains("HIGH SPEED"))
        return "USB 2.0 (480 Mbps)";
    if (name.Contains("1.1") || name.Contains("UHCI") || name.Contains("OHCI"))
        return "USB 1.1 (12 Mbps)";

    return "USB (speed unknown)";
}

// Query USB controllers
public List<UsbController> GetUsbControllers()
{
    return _wmi.Query("Win32_USBController")
        .Select(c => new UsbController
        {
            Name = c["Name"]?.ToString() ?? "Unknown",
            Speed = DetectUsbSpeed(c["Name"]?.ToString() ?? ""),
            DeviceId = c["DeviceID"]?.ToString() ?? ""
        })
        .ToList();
}
```

---

## 9. WMI Event Watcher — Real-Time Device Monitoring

```csharp
// ✅ USB insert/remove monitoring with IDisposable cleanup
public class UsbMonitorService : IDisposable
{
    private ManagementEventWatcher? _insertWatcher;
    private ManagementEventWatcher? _removeWatcher;

    public event EventHandler<string>? DeviceInserted;
    public event EventHandler<string>? DeviceRemoved;

    public void StartMonitoring()
    {
        var insertQuery = new WqlEventQuery(
            "SELECT * FROM __InstanceCreationEvent WITHIN 2 " +
            "WHERE TargetInstance ISA 'Win32_USBHub'");

        _insertWatcher = new ManagementEventWatcher(insertQuery);
        _insertWatcher.EventArrived += (s, e) =>
        {
            var device = (ManagementBaseObject)e.NewEvent["TargetInstance"];
            DeviceInserted?.Invoke(this, device["DeviceID"]?.ToString() ?? "");
        };
        _insertWatcher.Start();

        var removeQuery = new WqlEventQuery(
            "SELECT * FROM __InstanceDeletionEvent WITHIN 2 " +
            "WHERE TargetInstance ISA 'Win32_USBHub'");

        _removeWatcher = new ManagementEventWatcher(removeQuery);
        _removeWatcher.EventArrived += (s, e) =>
        {
            var device = (ManagementBaseObject)e.NewEvent["TargetInstance"];
            DeviceRemoved?.Invoke(this, device["DeviceID"]?.ToString() ?? "");
        };
        _removeWatcher.Start();
    }

    public void Dispose()
    {
        _insertWatcher?.Stop();
        _insertWatcher?.Dispose();
        _removeWatcher?.Stop();
        _removeWatcher?.Dispose();
    }
}
```

---

## Checklist

- [ ] WMI access abstracted behind `IWmiService` interface
- [ ] All WMI queries use null-safe property access: `obj["Prop"]?.ToString()`
- [ ] Battery health formula guards against `designCapacity == 0`
- [ ] SMART parsing handles all 5 critical attribute IDs (5, 9, 187, 197, 198)
- [ ] LibreHardwareMonitor: `computer.Close()` called in `Dispose()`
- [ ] WMI event watchers stopped and disposed in `Dispose()`
- [ ] RAM detection has 3-layer fallback (WMI → Kernel32 → ComputerSystem)
- [ ] USB speed detection covers USB4/TB4 through USB 1.1
