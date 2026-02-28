# Testing Patterns

TDD, xUnit + Moq + FluentAssertions, ISO 25010 quality mapping cho WPF C# applications.

## Quick Reference

| Tool | Purpose | NuGet |
|------|---------|-------|
| xUnit | Test framework | `xunit`, `xunit.runner.visualstudio` |
| Moq | Mocking | `Moq` |
| FluentAssertions | Readable assertions | `FluentAssertions` |
| FsCheck | Property-based testing | `FsCheck.Xunit` |
| Coverlet | Code coverage | `coverlet.collector` |

---

## 1. Project Setup

```xml
<!-- LaptopTesterPro.Tests.csproj -->
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0-windows</TargetFramework>
    <IsPackable>false</IsPackable>
    <IsTestProject>true</IsTestProject>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="xunit" Version="2.*" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.*" />
    <PackageReference Include="Moq" Version="4.*" />
    <PackageReference Include="FluentAssertions" Version="6.*" />
    <PackageReference Include="FsCheck.Xunit" Version="2.*" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.*" />
    <PackageReference Include="coverlet.collector" Version="6.*" />
  </ItemGroup>
  <ItemGroup>
    <ProjectReference Include="..\LaptopTesterPro.Core\LaptopTesterPro.Core.csproj" />
  </ItemGroup>
</Project>
```

---

## 2. Unit Test vs Integration Test

```csharp
// ✅ Unit Test — mocked dependencies, deterministic, fast (<10ms)
[Trait("Category", "Unit")]
public class BatteryHealthServiceTests
{
    [Fact]
    public void GetHealth_GoodBattery_Returns90Percent()
    {
        // Arrange
        var wmi = new Mock<IWmiService>();
        wmi.Setup(w => w.Query("BatteryFullChargedCapacity", @"root\wmi", null))
           .Returns([new() { ["FullChargedCapacity"] = 90000u }]);
        wmi.Setup(w => w.Query("BatteryStaticData", @"root\wmi", null))
           .Returns([new() { ["DesignedCapacity"] = 100000u }]);

        var svc = new BatteryHealthService(wmi.Object);

        // Act
        var result = svc.GetHealth();

        // Assert
        result.HealthPercent.Should().BeApproximately(90.0, 0.1);
        result.IsHealthy.Should().BeTrue();
        result.Status.Should().Be("Good");
    }
}

// ✅ Integration Test — real WMI/hardware, environment-dependent, slow
[Trait("Category", "Integration")]
public class HardwareDetectionIntegrationTests
{
    [Fact]
    public void GetCpuInfo_RealHardware_ReturnsValidData()
    {
        var wmi = new WindowsWmiService(); // real WMI
        var svc = new HardwareService(wmi);

        var cpu = svc.GetCpuInfo();

        cpu.Should().NotBeNull();
        cpu.Cores.Should().BeGreaterThan(0);
        cpu.MaxClockSpeedMhz.Should().BeInRange(500, 10000);
    }
}
```

```bash
# Run only unit tests in CI (fast, no hardware needed)
dotnet test --filter "Category=Unit"

# Run all tests including integration (requires real hardware)
dotnet test --filter "Category=Unit|Category=Integration"
```

---

## 3. TDD Pattern — BatteryLifePrediction Style

```csharp
// ✅ Pure business logic — fully testable with mocks
public class BatteryHealthService
{
    private readonly IWmiService _wmi;

    public BatteryHealthService(IWmiService wmi) => _wmi = wmi;

    public BatteryHealthResult GetHealth()
    {
        var fullChargeData = _wmi.Query("BatteryFullChargedCapacity", @"root\wmi")
            .FirstOrDefault();
        var staticData = _wmi.Query("BatteryStaticData", @"root\wmi")
            .FirstOrDefault();

        uint fullCharge = Convert.ToUInt32(fullChargeData?["FullChargedCapacity"] ?? 0u);
        uint designCap = Convert.ToUInt32(staticData?["DesignedCapacity"] ?? 0u);

        if (designCap == 0)
            return new BatteryHealthResult { HealthPercent = 0, Status = "Unknown" };

        double health = Math.Round((double)fullCharge / designCap * 100, 1);
        return new BatteryHealthResult
        {
            HealthPercent = health,
            IsHealthy = health >= 80,
            Status = health switch { >= 80 => "Good", >= 60 => "Fair", >= 40 => "Weak", _ => "Replace" }
        };
    }
}

// Full test suite: happy path + edge cases + error scenarios
[Trait("Category", "Unit")]
public class BatteryHealthServiceTests
{
    private static Mock<IWmiService> MockWmi(uint fullCharge, uint designCap)
    {
        var wmi = new Mock<IWmiService>();
        wmi.Setup(w => w.Query("BatteryFullChargedCapacity", @"root\wmi", null))
           .Returns([new() { ["FullChargedCapacity"] = fullCharge }]);
        wmi.Setup(w => w.Query("BatteryStaticData", @"root\wmi", null))
           .Returns([new() { ["DesignedCapacity"] = designCap }]);
        return wmi;
    }

    // Happy path
    [Fact]
    public void GetHealth_90PercentBattery_ReturnsGoodStatus()
    {
        var result = new BatteryHealthService(MockWmi(90000u, 100000u).Object).GetHealth();
        result.HealthPercent.Should().BeApproximately(90.0, 0.1);
        result.Status.Should().Be("Good");
        result.IsHealthy.Should().BeTrue();
    }

    // Edge cases
    [Theory]
    [InlineData(0u, 0u, 0.0, "Unknown")]      // division by zero
    [InlineData(0u, 100000u, 0.0, "Replace")] // dead battery
    [InlineData(100000u, 100000u, 100.0, "Good")] // perfect battery
    [InlineData(79999u, 100000u, 80.0, "Good")]   // boundary: exactly 80%
    public void GetHealth_EdgeCases_ReturnsExpected(
        uint fullCharge, uint designCap, double expectedPercent, string expectedStatus)
    {
        var result = new BatteryHealthService(MockWmi(fullCharge, designCap).Object).GetHealth();
        result.HealthPercent.Should().BeApproximately(expectedPercent, 0.1);
        result.Status.Should().Be(expectedStatus);
    }

    // Error scenario: WMI returns no data
    [Fact]
    public void GetHealth_WmiReturnsEmpty_ReturnsZeroNotThrow()
    {
        var wmi = new Mock<IWmiService>();
        wmi.Setup(w => w.Query(It.IsAny<string>(), It.IsAny<string>(), null))
           .Returns([]);

        var act = () => new BatteryHealthService(wmi.Object).GetHealth();

        act.Should().NotThrow();
        act().HealthPercent.Should().Be(0);
    }
}
```

---

## 4. Moq Patterns

```csharp
// Mock IWmiService
var wmi = new Mock<IWmiService>();

// Setup specific query
wmi.Setup(w => w.Query("Win32_Processor", null, null))
   .Returns([new() { ["Name"] = "Intel Core i7-1165G7", ["NumberOfCores"] = 4 }]);

// Setup with any namespace
wmi.Setup(w => w.Query("Win32_Processor", It.IsAny<string>(), null))
   .Returns([new() { ["Name"] = "Intel Core i7" }]);

// Setup to throw exception (test error handling)
wmi.Setup(w => w.Query("Win32_Battery", null, null))
   .Throws<ManagementException>();

// Verify call was made
wmi.Verify(w => w.Query("Win32_Processor", null, null), Times.Once);

// Mock IHardwareService
var hardware = new Mock<IHardwareService>();
hardware.Setup(h => h.GetCpuTemperatureAsync())
        .ReturnsAsync(45.5);
hardware.Setup(h => h.GetCpuTemperatureAsync())
        .ThrowsAsync(new InvalidOperationException("Sensor unavailable"));
```

---

## 5. Async Test Methods

```csharp
[Trait("Category", "Unit")]
public class CpuStressServiceTests
{
    [Fact]
    public async Task RunAsync_CancelledImmediately_CompletesWithoutError()
    {
        var tempService = new Mock<ITemperatureService>();
        tempService.Setup(t => t.GetCpuTemperatureAsync())
                   .ReturnsAsync(45.0);

        var svc = new CpuStressService(tempService.Object);
        using var cts = new CancellationTokenSource();
        cts.Cancel(); // cancel immediately

        var act = async () => await svc.RunAsync(30, null, cts.Token);

        await act.Should().NotThrowAsync();
    }

    [Fact]
    public async Task RunAsync_ShortDuration_ReportsProgress()
    {
        var tempService = new Mock<ITemperatureService>();
        tempService.Setup(t => t.GetCpuTemperatureAsync()).ReturnsAsync(50.0);

        var svc = new CpuStressService(tempService.Object);
        var progressReports = new List<CpuStressProgress>();
        var progress = new Progress<CpuStressProgress>(p => progressReports.Add(p));

        await svc.RunAsync(1, progress, CancellationToken.None); // 1 second

        progressReports.Should().NotBeEmpty();
        progressReports.Last().PercentComplete.Should().Be(100);
    }
}
```

---

## 6. Test Coverage Targets

| Component | Target | Rationale |
|-----------|--------|-----------|
| Business logic services | 80% | Core value — must be reliable |
| Critical calculations (battery health, SMART score) | 100% | Safety-critical — zero tolerance |
| ViewModels | 60% | Commands and state logic |
| Views/XAML | 0% | UI layout — not unit testable |
| WMI/hardware services | 40% | Integration tests cover the rest |

```bash
# Generate coverage report
dotnet test --collect:"XPlat Code Coverage"
reportgenerator -reports:"**/coverage.cobertura.xml" -targetdir:"coverage-report" -reporttypes:Html
```

---

## 7. ISO/IEC 25010 Quality Mapping

| Characteristic | WPF Implementation |
|---------------|-------------------|
| **Functional Suitability** | Unit tests for business logic, SMART scoring accuracy, battery formula correctness |
| **Reliability** | `async void` try/catch, graceful WMI fallbacks, IDisposable cleanup |
| **Performance Efficiency** | VirtualizingStackPanel, WMI caching, median benchmark measurements |
| **Usability** | AutomationProperties, keyboard navigation, localization completeness |
| **Security** | Admin rights detection, no hardcoded secrets, input validation |
| **Maintainability** | MVVM separation, interface-first design, DI, no service duplication |
| **Portability** | WinPE compatibility, no hardcoded paths, Registry-based detection |

---

## 8. Scoring Consistency Pattern

```csharp
// ✅ Ensure QuickTest verdict = Full Report verdict for same hardware state
[Trait("Category", "Unit")]
public class ScoringConsistencyTests
{
    [Fact]
    public void QuickTestScore_MatchesFullReportVerdict_ForSameHardwareState()
    {
        var wmi = new Mock<IWmiService>();
        // Setup same hardware state for both paths
        SetupHealthyBattery(wmi);

        var quickTestScore = new QuickTestScoreEngine(wmi.Object).Calculate();
        var fullReportVerdict = new FullReportEngine(wmi.Object).GetVerdict();

        // Both should agree: healthy battery = Pass
        quickTestScore.BatteryVerdict.Should().Be(fullReportVerdict.BatteryVerdict);
    }

    private static void SetupHealthyBattery(Mock<IWmiService> wmi)
    {
        wmi.Setup(w => w.Query("BatteryFullChargedCapacity", @"root\wmi", null))
           .Returns([new() { ["FullChargedCapacity"] = 90000u }]);
        wmi.Setup(w => w.Query("BatteryStaticData", @"root\wmi", null))
           .Returns([new() { ["DesignedCapacity"] = 100000u }]);
    }
}
```

---

## 9. Test Reliability Matrix

| Component | Reliability | Reason |
|-----------|-------------|--------|
| Battery health calculation | High | Pure math, fully mockable |
| SMART score calculation | High | Pure math, fully mockable |
| Anti-fake validation | High | Logic-based, mockable WMI |
| CPU stress test | Medium | Timing-dependent |
| Disk speed test | Medium | Hardware/OS cache dependent |
| WMI queries | Low | Real hardware required |
| Temperature sensors | Low | LibreHardwareMonitor required |

---

## 10. CI/CD Test Strategy

```yaml
# .github/workflows/ci.yml
- name: Run unit tests
  run: dotnet test --filter "Category=Unit" --logger trx --results-directory TestResults

- name: Run integration tests (nightly only)
  if: github.event_name == 'schedule'
  run: dotnet test --filter "Category=Integration"
```

```bash
# Local development
dotnet test --filter "Category=Unit" --no-build  # fast feedback
dotnet test                                        # all tests
dotnet test --filter "FullyQualifiedName~Battery" # specific class
```

---

## Checklist

- [ ] Test project references `xunit`, `Moq`, `FluentAssertions`
- [ ] Unit tests tagged `[Trait("Category", "Unit")]`
- [ ] Integration tests tagged `[Trait("Category", "Integration")]`
- [ ] Critical calculations (battery health, SMART) have 100% coverage
- [ ] Async tests use `async Task` not `async void`
- [ ] Moq setups use specific parameters, not `It.IsAny` everywhere
- [ ] Edge cases covered: zero values, null WMI returns, cancelled operations
- [ ] Scoring consistency verified: QuickTest = Full Report for same state
