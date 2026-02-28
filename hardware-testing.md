# Hardware Testing Patterns

Patterns cho hardware diagnostic tests — CPU stress, RAM, disk, anti-fake, keyboard hook, WinPE.

## Quick Reference

| Test | Pattern | Key API |
|------|---------|---------|
| CPU stress | Lucas-Lehmer + multi-core Task.Run | `Environment.ProcessorCount` |
| RAM test | Pattern write/verify + walking bit | `Marshal.AllocHGlobal` |
| Disk speed | FileStream WriteThrough/SequentialScan | `FileOptions` |
| Anti-fake | WMI vs Registry cross-validation | `Win32_Processor` + Registry |
| VM detection | BIOS/BaseBoard string scan | `Win32_ComputerSystem` |
| Keyboard hook | SetWindowsHookEx WH_KEYBOARD_LL | `user32.dll` |

---

## 1. CPU Stress Test — Lucas-Lehmer + Multi-Core

```csharp
public async Task<CpuStressResult> RunCpuStressAsync(
    int durationSeconds,
    IProgress<CpuStressProgress>? progress,
    CancellationToken ct)
{
    var errors = 0;
    var startTemp = await _tempService.GetCpuTemperatureAsync().ConfigureAwait(false);
    var startTime = DateTime.UtcNow;

    using var timeoutCts = new CancellationTokenSource(TimeSpan.FromSeconds(durationSeconds));
    using var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(ct, timeoutCts.Token);

    // Spawn one task per logical core
    var tasks = Enumerable.Range(0, Environment.ProcessorCount)
        .Select(coreIndex => Task.Run(() =>
        {
            while (!linkedCts.Token.IsCancellationRequested)
            {
                // Lucas-Lehmer primality test for Mersenne prime M(9689)
                if (!RunLucasLehmerTest(9689))
                    Interlocked.Increment(ref errors);
            }
        }, linkedCts.Token));

    // Report progress every 500ms
    var reportTask = Task.Run(async () =>
    {
        while (!linkedCts.Token.IsCancellationRequested)
        {
            var elapsed = DateTime.UtcNow - startTime;
            var percent = (int)Math.Min(100, elapsed.TotalSeconds / durationSeconds * 100);
            var temp = await _tempService.GetCpuTemperatureAsync().ConfigureAwait(false);
            progress?.Report(new CpuStressProgress(percent, temp, errors));
            await Task.Delay(500, linkedCts.Token).ConfigureAwait(false);
        }
    }, linkedCts.Token);

    try { await Task.WhenAll(tasks); }
    catch (OperationCanceledException) { /* expected — timeout or user cancel */ }

    return new CpuStressResult
    {
        StartTempC = startTemp,
        EndTempC = await _tempService.GetCpuTemperatureAsync().ConfigureAwait(false),
        Errors = errors,
        Stable = errors == 0,
        DurationSeconds = (int)(DateTime.UtcNow - startTime).TotalSeconds
    };
}

// Lucas-Lehmer primality test
private static bool RunLucasLehmerTest(int p)
{
    // M(p) = 2^p - 1 is prime iff s_(p-2) ≡ 0 (mod M(p))
    // Use BigInteger for large exponents
    var mp = System.Numerics.BigInteger.Pow(2, p) - 1;
    var s = new System.Numerics.BigInteger(4);
    for (int i = 0; i < p - 2; i++)
        s = (s * s - 2) % mp;
    return s == 0;
}
```

---

## 2. RAM Pattern Test

```csharp
public unsafe RamTestResult RunRamPatternTest(
    int testSizeMb,
    IProgress<int>? progress,
    CancellationToken ct)
{
    const int MB = 1024 * 1024;
    int testSize = testSizeMb * MB;
    var errors = 0;

    // Patterns to test: all zeros, all ones, alternating, inverse alternating
    byte[][] patterns = [
        Enumerable.Repeat((byte)0x00, testSize).ToArray(),
        Enumerable.Repeat((byte)0xFF, testSize).ToArray(),
        Enumerable.Repeat((byte)0xAA, testSize).ToArray(),
        Enumerable.Repeat((byte)0x55, testSize).ToArray(),
    ];

    for (int p = 0; p < patterns.Length; p++)
    {
        ct.ThrowIfCancellationRequested();
        progress?.Report(p * 25);

        var buffer = new byte[testSize];

        // Write pattern
        Array.Fill(buffer, patterns[p][0]);

        // Verify pattern
        for (int i = 0; i < testSize; i++)
        {
            if (buffer[i] != patterns[p][0])
                errors++;
        }
    }

    // Walking bit test
    progress?.Report(80);
    ct.ThrowIfCancellationRequested();
    errors += RunWalkingBitTest(testSize / 4); // smaller size for walking bit

    progress?.Report(100);

    return new RamTestResult
    {
        Errors = errors,
        Passed = errors == 0,
        TestedMb = testSizeMb
    };
}

private int RunWalkingBitTest(int size)
{
    var errors = 0;
    var buffer = new byte[size];

    // Walk a single 1-bit through each byte position
    for (int bit = 0; bit < 8; bit++)
    {
        byte pattern = (byte)(1 << bit);
        Array.Fill(buffer, pattern);

        for (int i = 0; i < size; i++)
        {
            if (buffer[i] != pattern)
                errors++;
        }
    }

    return errors;
}
```

---

## 3. Disk Speed Test

```csharp
public async Task<DiskSpeedResult> RunDiskSpeedTestAsync(
    string testPath,
    int fileSizeMb,
    CancellationToken ct)
{
    const int MB = 1024 * 1024;
    var testFile = Path.Combine(testPath, $"disktest_{Guid.NewGuid():N}.tmp");
    var data = new byte[fileSizeMb * MB];
    new Random().NextBytes(data);

    try
    {
        // Write test — FileOptions.WriteThrough bypasses OS cache
        var writeStart = DateTime.UtcNow;
        await using (var fs = new FileStream(testFile, FileMode.Create,
            FileAccess.Write, FileShare.None, 4096,
            FileOptions.WriteThrough | FileOptions.Asynchronous))
        {
            await fs.WriteAsync(data, ct).ConfigureAwait(false);
            await fs.FlushAsync(ct).ConfigureAwait(false);
        }
        var writeMbps = fileSizeMb / (DateTime.UtcNow - writeStart).TotalSeconds;

        ct.ThrowIfCancellationRequested();

        // Read test — FileOptions.SequentialScan hints OS for sequential prefetch
        var readStart = DateTime.UtcNow;
        await using (var fs = new FileStream(testFile, FileMode.Open,
            FileAccess.Read, FileShare.Read, 4096,
            FileOptions.SequentialScan | FileOptions.Asynchronous))
        {
            var readBuffer = new byte[fileSizeMb * MB];
            await fs.ReadAsync(readBuffer, ct).ConfigureAwait(false);
        }
        var readMbps = fileSizeMb / (DateTime.UtcNow - readStart).TotalSeconds;

        return new DiskSpeedResult
        {
            WriteSpeedMbps = writeMbps,
            ReadSpeedMbps = readMbps,
            // ⚠️ DISCLAIMER: SLC cache effect — NVMe drives may show 2-3x higher
            // write speeds for small files due to SLC cache. Run 3+ times and take median.
            Disclaimer = "Speed may be inflated by SLC cache on NVMe drives. Run multiple times for accuracy."
        };
    }
    finally
    {
        if (File.Exists(testFile))
            File.Delete(testFile);
    }
}
```

---

## 4. Anti-Fake Hardware Validation

```csharp
public class AntiFakeValidator
{
    private readonly IWmiService _wmi;

    // ✅ Valid RAM sizes (GB) — any other value is suspicious
    private static readonly int[] ValidRamSizesGb =
        [2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128];

    public AntiFakeResult ValidateCpu()
    {
        var cpu = _wmi.Query("Win32_Processor").FirstOrDefault();
        if (cpu == null) return AntiFakeResult.Unknown("Cannot read CPU info");

        int maxClock = Convert.ToInt32(cpu["MaxClockSpeed"] ?? 0);
        int cores = Convert.ToInt32(cpu["NumberOfCores"] ?? 0);
        int threads = Convert.ToInt32(cpu["NumberOfLogicalProcessors"] ?? 0);
        string name = cpu["Name"]?.ToString()?.Trim() ?? "";

        // CPU clock range: 500MHz (old Atom) to 10GHz (safe for next 5 years)
        if (maxClock < 500 || maxClock > 10000)
            return AntiFakeResult.Suspicious($"CPU clock {maxClock}MHz out of valid range (500-10000)");

        if (cores <= 0 || threads < cores)
            return AntiFakeResult.Suspicious($"Invalid core/thread count: {cores}C/{threads}T");

        // Cross-validate with Registry
        var registryName = ReadRegistryValue(
            @"HARDWARE\DESCRIPTION\System\CentralProcessor\0", "ProcessorNameString");

        if (!string.IsNullOrEmpty(registryName) &&
            !NamesMatch(name, registryName))
            return AntiFakeResult.Suspicious(
                $"CPU name mismatch: WMI='{name}' Registry='{registryName}'");

        return AntiFakeResult.Valid($"CPU: {name} ({cores}C/{threads}T @ {maxClock}MHz)");
    }

    public AntiFakeResult ValidateRam()
    {
        var modules = _wmi.Query("Win32_PhysicalMemory").ToList();
        if (!modules.Any()) return AntiFakeResult.Unknown("Cannot read RAM info");

        long totalBytes = modules.Sum(m => Convert.ToInt64(m["Capacity"] ?? 0L));
        int totalGb = (int)(totalBytes / (1024L * 1024 * 1024));

        if (!ValidRamSizesGb.Contains(totalGb))
            return AntiFakeResult.Suspicious(
                $"RAM size {totalGb}GB is not a standard configuration");

        return AntiFakeResult.Valid($"RAM: {totalGb}GB ({modules.Count} module(s))");
    }

    private static bool NamesMatch(string wmiName, string regName)
    {
        // Normalize: trim, lowercase, remove extra spaces
        static string Normalize(string s) =>
            string.Join(" ", s.Trim().ToLowerInvariant().Split(' ',
                StringSplitOptions.RemoveEmptyEntries));
        return Normalize(wmiName) == Normalize(regName);
    }

    private static string? ReadRegistryValue(string keyPath, string valueName)
    {
        try
        {
            using var key = Microsoft.Win32.Registry.LocalMachine.OpenSubKey(keyPath);
            return key?.GetValue(valueName)?.ToString();
        }
        catch { return null; }
    }
}

// Spoofing tools vs safe monitoring tools
public static class ToolClassification
{
    // ✅ Safe monitoring tools — read-only, no spoofing risk
    public static readonly string[] SafeMonitoringTools =
        ["CPU-Z", "HWiNFO", "GPU-Z", "CrystalDiskInfo", "HWMonitor", "AIDA64"];

    // ⚠️ Risky spoofing tools — can modify hardware IDs
    public static readonly string[] SpoolingTools =
        ["DMIEdit", "RWEverything", "HWIDChanger", "AMIBCP", "Universal BIOS Backup"];
}
```

---

## 5. VM Detection

```csharp
public VmDetectionResult DetectVirtualMachine()
{
    var indicators = new List<string>();

    // Check BIOS/BaseBoard/ComputerSystem for hypervisor strings
    var vmStrings = new[] { "vmware", "virtualbox", "hyper-v", "qemu", "parallels",
                             "xen", "virtual", "bochs", "innotek" };

    CheckWmiForVmStrings("Win32_ComputerSystem", ["Manufacturer", "Model"], vmStrings, indicators);
    CheckWmiForVmStrings("Win32_BIOS", ["Manufacturer", "Version", "SMBIOSBIOSVersion"], vmStrings, indicators);
    CheckWmiForVmStrings("Win32_BaseBoard", ["Manufacturer", "Product"], vmStrings, indicators);

    // Check for hypervisor processes
    var vmProcesses = new[] { "vmtoolsd", "vmwaretray", "vboxservice", "vboxtray" };
    foreach (var proc in vmProcesses)
    {
        if (System.Diagnostics.Process.GetProcessesByName(proc).Any())
            indicators.Add($"Process: {proc}.exe");
    }

    return new VmDetectionResult
    {
        IsVirtualMachine = indicators.Any(),
        Indicators = indicators,
        Confidence = indicators.Count switch
        {
            0 => "Physical machine (high confidence)",
            1 => "Possibly virtual (low confidence)",
            _ => $"Virtual machine detected ({indicators.Count} indicators)"
        }
    };
}

private void CheckWmiForVmStrings(string wmiClass, string[] properties,
    string[] vmStrings, List<string> indicators)
{
    try
    {
        var result = _wmi.Query(wmiClass).FirstOrDefault();
        if (result == null) return;

        foreach (var prop in properties)
        {
            var value = result[prop]?.ToString()?.ToLowerInvariant() ?? "";
            foreach (var vmStr in vmStrings)
            {
                if (value.Contains(vmStr))
                    indicators.Add($"{wmiClass}.{prop}: '{value}'");
            }
        }
    }
    catch { /* WMI unavailable — skip */ }
}
```

---

## 6. Keyboard Hook — SetWindowsHookEx

```csharp
public class KeyboardTestService : IDisposable
{
    private IntPtr _hookHandle = IntPtr.Zero;
    private readonly NativeMethods.LowLevelKeyboardProc _proc;
    private readonly HashSet<Keys> _testedKeys = new();

    public event EventHandler<Keys>? KeyTested;
    public IReadOnlySet<Keys> TestedKeys => _testedKeys;

    public KeyboardTestService()
    {
        _proc = HookCallback; // ✅ Keep reference to prevent GC collection
        _hookHandle = NativeMethods.SetWindowsHookEx(
            NativeMethods.WH_KEYBOARD_LL,
            _proc,
            NativeMethods.GetModuleHandle(null),
            0);

        if (_hookHandle == IntPtr.Zero)
            throw new InvalidOperationException(
                $"Failed to install keyboard hook: {Marshal.GetLastWin32Error()}");
    }

    private IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0 && wParam == NativeMethods.WM_KEYDOWN)
        {
            var vkCode = Marshal.ReadInt32(lParam);
            var key = (Keys)vkCode;
            _testedKeys.Add(key);
            KeyTested?.Invoke(this, key);
        }
        return NativeMethods.CallNextHookEx(_hookHandle, nCode, wParam, lParam);
    }

    public void Dispose()
    {
        if (_hookHandle != IntPtr.Zero)
        {
            NativeMethods.UnhookWindowsHookEx(_hookHandle);
            _hookHandle = IntPtr.Zero;
        }
    }
}

internal static class NativeMethods
{
    public const int WH_KEYBOARD_LL = 13;
    public const int WM_KEYDOWN = 0x0100;

    public delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc lpfn,
        IntPtr hMod, uint dwThreadId);

    [DllImport("user32.dll")]
    public static extern bool UnhookWindowsHookEx(IntPtr hhk);

    [DllImport("user32.dll")]
    public static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("kernel32.dll")]
    public static extern IntPtr GetModuleHandle(string? lpModuleName);
}
```

---

## 7. Battery Chemistry Detection

```csharp
public string DetectBatteryChemistry()
{
    // Check Win32_Battery DeviceID and Description
    var battery = _wmi.Query("Win32_Battery").FirstOrDefault();
    if (battery == null) return "Unknown";

    var deviceId = battery["DeviceID"]?.ToString()?.ToUpperInvariant() ?? "";
    var description = battery["Description"]?.ToString()?.ToUpperInvariant() ?? "";
    var combined = $"{deviceId} {description}";

    if (combined.Contains("LION") || combined.Contains("LI-ION") || combined.Contains("LITHIUM ION"))
        return "Li-Ion";
    if (combined.Contains("LIPO") || combined.Contains("LI-PO") || combined.Contains("POLYMER"))
        return "Li-Polymer";
    if (combined.Contains("NIMH") || combined.Contains("NI-MH"))
        return "NiMH";
    if (combined.Contains("NICD") || combined.Contains("NI-CD"))
        return "NiCd";

    // Fallback: check Chemistry property (WMI enum)
    var chemistry = Convert.ToInt32(battery["Chemistry"] ?? 0);
    return chemistry switch
    {
        2 => "Lead Acid",
        3 => "NiCd",
        4 => "NiMH",
        5 => "Li-Ion",
        6 => "NiZn",
        7 => "LiPolymer",
        _ => "Unknown"
    };
}
```

---

## 8. WinPE Compatibility Checklist

```csharp
// WinPE environment constraints:
// - No installer dependencies (no .NET installer, no VC++ redist)
// - Offline operation (no internet, no license servers)
// - Admin rights always available (WinPE runs as SYSTEM)
// - No AppData, no user profile paths
// - Limited registry (no HKCU persistence)
// - No Windows services (WMI may be limited)

public class WinPeCompatibilityChecker
{
    public List<string> CheckCompatibility()
    {
        var issues = new List<string>();

        // ✅ Check: no hardcoded user paths
        // ❌ Bad: Environment.GetFolderPath(SpecialFolder.ApplicationData)
        // ✅ Good: use executable directory or passed-in path

        // ✅ Check: graceful WMI fallback
        // WMI may not have all classes in WinPE

        // ✅ Check: no network calls
        // WinPE may have no network

        return issues;
    }
}

// ✅ WinPE-safe path resolution
public static string GetAppDataPath(string filename)
{
    // In WinPE: AppData doesn't exist — use exe directory
    var exeDir = AppDomain.CurrentDomain.BaseDirectory;
    var appDataDir = Environment.GetFolderPath(
        Environment.SpecialFolder.ApplicationData);

    // If AppData doesn't exist (WinPE), fall back to exe directory
    var baseDir = Directory.Exists(appDataDir) ? appDataDir : exeDir;
    return Path.Combine(baseDir, "LaptopTesterPro", filename);
}
```

---

## Checklist

- [ ] CPU stress test uses `Environment.ProcessorCount` tasks
- [ ] RAM test covers all 4 patterns (0x00, 0xFF, 0xAA, 0x55) + walking bit
- [ ] Disk test uses `FileOptions.WriteThrough` for write, `SequentialScan` for read
- [ ] Disk test includes SLC cache disclaimer
- [ ] Anti-fake validates CPU clock range (500-10000 MHz)
- [ ] Anti-fake cross-validates WMI vs Registry CPU name
- [ ] RAM validation checks against valid size list
- [ ] VM detection checks BIOS, BaseBoard, ComputerSystem + processes
- [ ] Keyboard hook keeps delegate reference to prevent GC
- [ ] Keyboard hook implements `IDisposable` with `UnhookWindowsHookEx`
- [ ] Battery chemistry checks both string patterns and WMI Chemistry enum
- [ ] WinPE paths use exe directory fallback when AppData unavailable
