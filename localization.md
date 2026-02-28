# Localization Patterns

Reference guide for multi-language support in LaptopTesterPro — runtime language switching, resource management, and localization rules.

## ResourceDictionary + .resx Setup

LaptopTesterPro uses a hybrid approach: `.resx` files for C# code access and `ResourceDictionary` XAML files for UI bindings.

### File Structure

```
src/
  Resources/
    Strings.resx          ← Default (English)
    Strings.vi.resx       ← Vietnamese
    Strings.ja.resx       ← Japanese
  Themes/
    Strings.en.xaml       ← XAML ResourceDictionary (English)
    Strings.vi.xaml       ← XAML ResourceDictionary (Vietnamese)
```

### .resx File Pattern

```xml
<!-- Resources/Strings.resx -->
<root>
  <data name="Test_CPU_Title" xml:space="preserve">
    <value>CPU Performance Test</value>
  </data>
  <data name="Test_Battery_Health" xml:space="preserve">
    <value>Battery Health</value>
  </data>
  <data name="Result_Pass" xml:space="preserve">
    <value>PASS</value>
  </data>
  <data name="Result_Fail" xml:space="preserve">
    <value>FAIL</value>
  </data>
  <data name="Error_AdminRequired" xml:space="preserve">
    <value>Administrator rights required for this test.</value>
  </data>
</root>
```

```xml
<!-- Resources/Strings.vi.resx -->
<root>
  <data name="Test_CPU_Title" xml:space="preserve">
    <value>Kiểm tra hiệu năng CPU</value>
  </data>
  <data name="Test_Battery_Health" xml:space="preserve">
    <value>Sức khỏe pin</value>
  </data>
  <data name="Result_Pass" xml:space="preserve">
    <value>ĐẠT</value>
  </data>
  <data name="Result_Fail" xml:space="preserve">
    <value>KHÔNG ĐẠT</value>
  </data>
  <data name="Error_AdminRequired" xml:space="preserve">
    <value>Cần quyền Administrator để chạy bài kiểm tra này.</value>
  </data>
</root>
```

### XAML ResourceDictionary

```xml
<!-- Themes/Strings.en.xaml -->
<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
                    xmlns:sys="clr-namespace:System;assembly=mscorlib">
    <sys:String x:Key="Test_CPU_Title">CPU Performance Test</sys:String>
    <sys:String x:Key="Test_Battery_Health">Battery Health</sys:String>
    <sys:String x:Key="Nav_Dashboard">Dashboard</sys:String>
    <sys:String x:Key="Nav_Results">Test Results</sys:String>
    <sys:String x:Key="Btn_StartTest">Start Test</sys:String>
    <sys:String x:Key="Btn_Cancel">Cancel</sys:String>
</ResourceDictionary>
```

## DynamicResource Binding

Always use `DynamicResource` for user-visible strings — enables runtime language switching without restart.

```xml
<!-- Views/CpuTestView.xaml -->
<StackPanel>
    <!-- ✅ DynamicResource — updates when language changes -->
    <TextBlock Text="{DynamicResource Test_CPU_Title}"
               Style="{StaticResource SectionHeaderStyle}" />

    <Button Content="{DynamicResource Btn_StartTest}"
            Command="{Binding StartTestCommand}"
            Style="{StaticResource PrimaryButtonStyle}" />

    <!-- ❌ StaticResource — does NOT update at runtime -->
    <!-- <TextBlock Text="{StaticResource Test_CPU_Title}" /> -->
</StackPanel>
```

### AutomationProperties for Accessibility

```xml
<Button Content="{DynamicResource Btn_StartTest}"
        AutomationProperties.Name="{DynamicResource Btn_StartTest}"
        AutomationProperties.HelpText="{DynamicResource Btn_StartTest_Help}"
        Command="{Binding StartTestCommand}" />
```

## ILocalizationService Pattern

All C# code must use `ILocalizationService` — never hardcode strings or access `.resx` directly:

```csharp
// Services/ILocalizationService.cs
public interface ILocalizationService
{
    string Get(string key);
    string Get(string key, params object[] args);
    void SetLanguage(string languageCode);
    string CurrentLanguage { get; }
    event EventHandler<string> LanguageChanged;
}

// Services/LocalizationService.cs
public class LocalizationService : ILocalizationService
{
    private ResourceManager _resourceManager;
    private CultureInfo _currentCulture;

    public string CurrentLanguage => _currentCulture.TwoLetterISOLanguageName;
    public event EventHandler<string>? LanguageChanged;

    public LocalizationService()
    {
        _currentCulture = CultureInfo.CurrentUICulture;
        _resourceManager = new ResourceManager(
            "LaptopTesterPro.Resources.Strings",
            Assembly.GetExecutingAssembly());
    }

    public string Get(string key)
    {
        return _resourceManager.GetString(key, _currentCulture) ?? $"[{key}]";
    }

    public string Get(string key, params object[] args)
    {
        var template = Get(key);
        return string.Format(template, args);
    }

    public void SetLanguage(string languageCode)
    {
        _currentCulture = new CultureInfo(languageCode);
        Thread.CurrentThread.CurrentUICulture = _currentCulture;

        // Update XAML ResourceDictionary
        UpdateXamlResources(languageCode);

        LanguageChanged?.Invoke(this, languageCode);
    }

    private void UpdateXamlResources(string languageCode)
    {
        var dict = Application.Current.Resources.MergedDictionaries;
        var stringDict = dict.FirstOrDefault(d =>
            d.Source?.OriginalString.Contains("Strings.") == true);

        if (stringDict != null)
            dict.Remove(stringDict);

        var newDict = new ResourceDictionary
        {
            Source = new Uri($"Themes/Strings.{languageCode}.xaml", UriKind.Relative)
        };
        dict.Add(newDict);
    }
}
```

### Usage in Services

```csharp
// Services/ReportService.cs
public class ReportService : IReportService
{
    private readonly ILocalizationService _loc;

    public ReportService(ILocalizationService loc) => _loc = loc;

    public string BuildSummary(TestSession session)
    {
        // ✅ Use ILocalizationService
        var passLabel = _loc.Get("Result_Pass");
        var failLabel = _loc.Get("Result_Fail");
        var title = _loc.Get("Report_Title", session.Date.ToString("yyyy-MM-dd"));

        return $"{title}\n{passLabel}: {session.PassCount} | {failLabel}: {session.FailCount}";
    }

    // ❌ Never hardcode
    // var label = "PASS"; // Wrong
    // var label = Resources.Strings.Result_Pass; // Wrong — bypasses ILocalizationService
}
```

## Runtime Language Switching (No Restart)

```csharp
// ViewModels/SettingsViewModel.cs
public partial class SettingsViewModel : ObservableObject
{
    private readonly ILocalizationService _loc;

    [ObservableProperty]
    private string _selectedLanguage = "en";

    public IReadOnlyList<LanguageOption> AvailableLanguages { get; } = new[]
    {
        new LanguageOption("en", "English"),
        new LanguageOption("vi", "Tiếng Việt"),
        new LanguageOption("ja", "日本語"),
    };

    partial void OnSelectedLanguageChanged(string value)
    {
        _loc.SetLanguage(value);
        // Save preference
        Properties.Settings.Default.Language = value;
        Properties.Settings.Default.Save();
    }
}
```

```xml
<!-- Views/SettingsView.xaml -->
<ComboBox ItemsSource="{Binding AvailableLanguages}"
          SelectedValue="{Binding SelectedLanguage}"
          SelectedValuePath="Code"
          DisplayMemberPath="DisplayName"
          AutomationProperties.Name="{DynamicResource Settings_Language}" />
```

### Persist Language on Startup

```csharp
// App.xaml.cs
protected override void OnStartup(StartupEventArgs e)
{
    base.OnStartup(e);

    var savedLang = Properties.Settings.Default.Language;
    if (!string.IsNullOrEmpty(savedLang))
    {
        var locService = _serviceProvider.GetRequiredService<ILocalizationService>();
        locService.SetLanguage(savedLang);
    }
}
```

## Technical Units — Do NOT Localize

These units are international standards and must remain unchanged in all languages:

| Category | Units (never translate) |
|----------|------------------------|
| Frequency | MHz, GHz |
| Storage | GB, MB, KB, TB |
| Speed | MB/s, GB/s |
| Energy | Wh, mWh |
| Time | ns, ms, s |
| Temperature | °C (always Celsius) |
| Sound | dB |
| Voltage | V, mV |
| Current | A, mA |

```csharp
// ✅ Correct — unit stays in English
var display = $"{_loc.Get("CPU_Speed")}: {clockSpeed} MHz";
var battery = $"{_loc.Get("Battery_Capacity")}: {capacity} Wh";

// ❌ Wrong — never localize units
var display = $"{_loc.Get("CPU_Speed")}: {clockSpeed} {_loc.Get("Unit_MHz")}";
```

## Multi-Language File Sync Requirement

When adding a new string key, it must be added to ALL language files simultaneously:

```csharp
// scripts/validate_localization.py (run in CI)
import os, xml.etree.ElementTree as ET

LANG_FILES = ["Strings.resx", "Strings.vi.resx", "Strings.ja.resx"]
RESOURCES_DIR = "src/Resources"

def get_keys(filepath):
    tree = ET.parse(filepath)
    return {d.get("name") for d in tree.findall(".//data")}

base_keys = get_keys(os.path.join(RESOURCES_DIR, LANG_FILES[0]))
for lang_file in LANG_FILES[1:]:
    lang_keys = get_keys(os.path.join(RESOURCES_DIR, lang_file))
    missing = base_keys - lang_keys
    if missing:
        print(f"MISSING in {lang_file}: {missing}")
        exit(1)

print("All language files in sync ✓")
```

### Adding New Strings Checklist

When adding a new UI string:
1. Add to `Strings.resx` (English baseline)
2. Add to `Strings.vi.resx` (Vietnamese)
3. Add to `Strings.ja.resx` (Japanese)
4. Add to all `Strings.{lang}.xaml` XAML dictionaries
5. Use `{DynamicResource Key}` in XAML
6. Use `_loc.Get("Key")` in C# code

## Anti-Patterns to Avoid

```csharp
// ❌ Hardcoded strings in services
return "Test passed successfully"; // Wrong

// ❌ Direct .resx access bypassing ILocalizationService
return Resources.Strings.Result_Pass; // Wrong

// ❌ StaticResource for user-visible text (won't update at runtime)
// <TextBlock Text="{StaticResource Btn_StartTest}" /> // Wrong

// ❌ Localizing technical units
var msg = $"{speed} {_loc.Get("Unit_MHz")}"; // Wrong — MHz is never translated

// ✅ Correct patterns
return _loc.Get("Test_Passed"); // Service injection
// <TextBlock Text="{DynamicResource Btn_StartTest}" /> // DynamicResource
var msg = $"{speed} MHz"; // Unit stays as-is
```

## Checklist

- [ ] All user-visible strings use `{DynamicResource}` in XAML
- [ ] All C# string access goes through `ILocalizationService.Get()`
- [ ] No hardcoded English strings in services or ViewModels
- [ ] Technical units (MHz, GB, Wh, dB) are NOT localized
- [ ] New string keys added to ALL language files simultaneously
- [ ] Language preference persisted and restored on startup
- [ ] Localization sync validation script runs in CI
- [ ] `AutomationProperties.Name` also uses `DynamicResource`
