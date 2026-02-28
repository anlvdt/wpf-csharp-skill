# XAML Best Practices

Chuẩn mực XAML cho WPF C# — styles, accessibility, animations, keyboard navigation.

## Quick Reference

| Topic | Rule |
|-------|------|
| Colors | Always ResourceDictionary, never hardcoded hex |
| Accessibility | `AutomationProperties.Name` on all icon-only controls |
| Keyboard nav | Use `Button` styled as card, not `Border` with click handler |
| Resources | `DynamicResource` for theme-switchable, `StaticResource` for fixed |
| Layout | `*` sizing in Grid, avoid fixed pixel widths |
| Large lists | `VirtualizingStackPanel` to prevent UI freeze |

---

## 1. ResourceDictionary — No Hardcoded Colors

```xml
<!-- ❌ WRONG: hardcoded hex everywhere -->
<Border Background="#A50064" />
<TextBlock Foreground="#1A1A2E" FontSize="14" />
<Button Background="#0078D4" />
```

```xml
<!-- ✅ CORRECT: define in Colors.xaml ResourceDictionary -->
<!-- Resources/Colors.xaml -->
<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
    <!-- Brand colors -->
    <Color x:Key="PrimaryColor">#0078D4</Color>
    <Color x:Key="AccentColor">#A50064</Color>
    <Color x:Key="BackgroundColor">#1A1A2E</Color>
    <Color x:Key="SurfaceColor">#16213E</Color>
    <Color x:Key="TextPrimaryColor">#FFFFFF</Color>
    <Color x:Key="TextSecondaryColor">#B0B0C0</Color>
    <Color x:Key="ErrorColor">#CF6679</Color>
    <Color x:Key="SuccessColor">#4CAF50</Color>
    <Color x:Key="WarningColor">#FF9800</Color>

    <!-- Brushes -->
    <SolidColorBrush x:Key="PrimaryBrush" Color="{StaticResource PrimaryColor}" />
    <SolidColorBrush x:Key="AccentBrush" Color="{StaticResource AccentColor}" />
    <SolidColorBrush x:Key="BackgroundBrush" Color="{StaticResource BackgroundColor}" />
    <SolidColorBrush x:Key="SurfaceBrush" Color="{StaticResource SurfaceColor}" />
    <SolidColorBrush x:Key="TextPrimaryBrush" Color="{StaticResource TextPrimaryColor}" />
    <SolidColorBrush x:Key="TextSecondaryBrush" Color="{StaticResource TextSecondaryColor}" />
    <SolidColorBrush x:Key="ErrorBrush" Color="{StaticResource ErrorColor}" />
    <SolidColorBrush x:Key="SuccessBrush" Color="{StaticResource SuccessColor}" />
</ResourceDictionary>
```

```xml
<!-- App.xaml — merge all resource dictionaries -->
<Application.Resources>
    <ResourceDictionary>
        <ResourceDictionary.MergedDictionaries>
            <ResourceDictionary Source="Resources/Colors.xaml" />
            <ResourceDictionary Source="Resources/Styles.xaml" />
            <ResourceDictionary Source="Resources/Templates.xaml" />
        </ResourceDictionary.MergedDictionaries>
    </ResourceDictionary>
</Application.Resources>
```

```xml
<!-- Usage in views -->
<Border Background="{StaticResource SurfaceBrush}" />
<TextBlock Foreground="{StaticResource TextPrimaryBrush}" />
<Button Background="{StaticResource PrimaryBrush}" />
```

---

## 2. Accessibility — AutomationProperties

```xml
<!-- ❌ WRONG: screen reader says "Button" — useless -->
<Button Margin="4">
    <Image Source="/Assets/settings.png" Width="20" Height="20" />
</Button>

<!-- ❌ WRONG: icon-only with no label -->
<Button Content="&#xE713;" FontFamily="Segoe MDL2 Assets" />
```

```xml
<!-- ✅ CORRECT: AutomationProperties.Name + ToolTip -->
<Button AutomationProperties.Name="Open Settings"
        ToolTip="Open Settings"
        Margin="4">
    <Image Source="/Assets/settings.png" Width="20" Height="20"
           AutomationProperties.HelpText="Settings icon" />
</Button>

<!-- ✅ CORRECT: icon font button -->
<Button Content="&#xE713;"
        FontFamily="Segoe MDL2 Assets"
        AutomationProperties.Name="Settings"
        ToolTip="Settings (Ctrl+,)" />

<!-- ✅ CORRECT: toggle button with state -->
<ToggleButton AutomationProperties.Name="Dark mode toggle"
              AutomationProperties.HelpText="Switch between light and dark theme"
              IsChecked="{Binding IsDarkMode}" />
```

---

## 3. Keyboard-Accessible Cards

```xml
<!-- ❌ WRONG: Border with mouse handler — not keyboard accessible -->
<Border Background="{StaticResource SurfaceBrush}"
        CornerRadius="8"
        Cursor="Hand"
        MouseLeftButtonUp="Card_Click">
    <TextBlock Text="Click me" Margin="16" />
</Border>
```

```xml
<!-- ✅ CORRECT: Button styled as card -->
<Button Style="{StaticResource CardButtonStyle}"
        Command="{Binding SelectItemCommand}"
        CommandParameter="{Binding}"
        AutomationProperties.Name="{Binding Title}">
    <TextBlock Text="{Binding Title}" Margin="16" />
</Button>
```

```xml
<!-- Styles.xaml — CardButtonStyle -->
<Style x:Key="CardButtonStyle" TargetType="Button">
    <Setter Property="Background" Value="{StaticResource SurfaceBrush}" />
    <Setter Property="BorderThickness" Value="0" />
    <Setter Property="Cursor" Value="Hand" />
    <Setter Property="FocusVisualStyle" Value="{StaticResource FocusVisualStyle}" />
    <Setter Property="Template">
        <Setter.Value>
            <ControlTemplate TargetType="Button">
                <Border Background="{TemplateBinding Background}"
                        CornerRadius="8"
                        BorderBrush="{TemplateBinding BorderBrush}"
                        BorderThickness="{TemplateBinding BorderThickness}">
                    <ContentPresenter Margin="{TemplateBinding Padding}" />
                </Border>
                <ControlTemplate.Triggers>
                    <Trigger Property="IsMouseOver" Value="True">
                        <Setter Property="Background" Value="{StaticResource SurfaceHoverBrush}" />
                    </Trigger>
                    <Trigger Property="IsPressed" Value="True">
                        <Setter Property="Background" Value="{StaticResource SurfacePressedBrush}" />
                    </Trigger>
                    <Trigger Property="IsFocused" Value="True">
                        <Setter Property="BorderBrush" Value="{StaticResource PrimaryBrush}" />
                        <Setter Property="BorderThickness" Value="2" />
                    </Trigger>
                </ControlTemplate.Triggers>
            </ControlTemplate>
        </Setter.Value>
    </Setter>
</Style>
```

---

## 4. DynamicResource vs StaticResource

```xml
<!-- StaticResource: resolved once at load time — use for fixed values -->
<TextBlock FontFamily="{StaticResource PrimaryFont}"
           FontSize="{StaticResource BodyFontSize}" />

<!-- DynamicResource: re-resolved when resource changes — use for themes -->
<Border Background="{DynamicResource SurfaceBrush}" />
<TextBlock Foreground="{DynamicResource TextPrimaryBrush}" />
<Button Style="{DynamicResource PrimaryButtonStyle}" />
```

```csharp
// Runtime theme switching — DynamicResource updates automatically
public void SwitchTheme(string theme)
{
    var dict = new ResourceDictionary
    {
        Source = new Uri($"Resources/Themes/{theme}.xaml", UriKind.Relative)
    };

    // Replace theme dictionary (index 0 = theme, index 1+ = fixed resources)
    Application.Current.Resources.MergedDictionaries[0] = dict;
    // All DynamicResource bindings update automatically — no restart needed
}
```

**Rule:** Use `DynamicResource` for anything that can change at runtime (theme colors, localized strings). Use `StaticResource` for fixed values (font sizes, icon paths, converters).

---

## 5. Grid Layout — Responsive with * Sizing

```xml
<!-- ❌ WRONG: fixed pixel widths break on different DPI/screen sizes -->
<Grid>
    <Grid.ColumnDefinitions>
        <ColumnDefinition Width="250" />
        <ColumnDefinition Width="750" />
    </Grid.ColumnDefinitions>
</Grid>
```

```xml
<!-- ✅ CORRECT: proportional * sizing -->
<Grid>
    <Grid.ColumnDefinitions>
        <ColumnDefinition Width="250" MinWidth="200" MaxWidth="350" />  <!-- sidebar: fixed range -->
        <ColumnDefinition Width="*" />                                   <!-- content: fills rest -->
    </Grid.ColumnDefinitions>
    <Grid.RowDefinitions>
        <RowDefinition Height="Auto" />   <!-- header: fits content -->
        <RowDefinition Height="*" />      <!-- body: fills space -->
        <RowDefinition Height="Auto" />   <!-- footer: fits content -->
    </Grid.RowDefinitions>
</Grid>

<!-- ✅ Equal columns -->
<Grid>
    <Grid.ColumnDefinitions>
        <ColumnDefinition Width="*" />
        <ColumnDefinition Width="*" />
        <ColumnDefinition Width="*" />
    </Grid.ColumnDefinitions>
</Grid>

<!-- ✅ 2:1 ratio -->
<Grid>
    <Grid.ColumnDefinitions>
        <ColumnDefinition Width="2*" />
        <ColumnDefinition Width="*" />
    </Grid.ColumnDefinitions>
</Grid>
```

---

## 6. WindowChrome — Custom TitleBar

```xml
<Window xmlns:shell="clr-namespace:System.Windows.Shell;assembly=PresentationFramework"
        WindowStyle="None"
        AllowsTransparency="False"
        ResizeMode="CanResizeWithGrip">

    <shell:WindowChrome.WindowChrome>
        <shell:WindowChrome CaptionHeight="40"
                            ResizeBorderThickness="6"
                            GlassFrameThickness="0"
                            UseAeroCaptionButtons="False" />
    </shell:WindowChrome.WindowChrome>

    <Grid>
        <Grid.RowDefinitions>
            <RowDefinition Height="40" />  <!-- TitleBar -->
            <RowDefinition Height="*" />   <!-- Content -->
        </Grid.RowDefinitions>

        <!-- Custom TitleBar -->
        <Grid Background="{StaticResource TitleBarBrush}"
              shell:WindowChrome.IsHitTestVisibleInChrome="True">
            <TextBlock Text="{Binding Title}"
                       VerticalAlignment="Center"
                       Margin="16,0"
                       Foreground="{StaticResource TextPrimaryBrush}" />

            <!-- Window control buttons -->
            <StackPanel Orientation="Horizontal"
                        HorizontalAlignment="Right">
                <Button Content="&#xE921;" FontFamily="Segoe MDL2 Assets"
                        AutomationProperties.Name="Minimize"
                        Click="MinimizeButton_Click"
                        Style="{StaticResource TitleBarButtonStyle}" />
                <Button Content="&#xE922;" FontFamily="Segoe MDL2 Assets"
                        AutomationProperties.Name="Maximize"
                        Click="MaximizeButton_Click"
                        Style="{StaticResource TitleBarButtonStyle}" />
                <Button Content="&#xE8BB;" FontFamily="Segoe MDL2 Assets"
                        AutomationProperties.Name="Close"
                        Click="CloseButton_Click"
                        Style="{StaticResource TitleBarCloseButtonStyle}" />
            </StackPanel>
        </Grid>

        <!-- Main content -->
        <ContentControl Grid.Row="1" Content="{Binding CurrentView}" />
    </Grid>
</Window>
```

---

## 7. VirtualizingStackPanel — Large Lists

```xml
<!-- ❌ WRONG: default ItemsControl renders ALL items — freezes UI with 1000+ items -->
<ItemsControl ItemsSource="{Binding LargeList}" />

<!-- ✅ CORRECT: ListBox/ListView with virtualization -->
<ListBox ItemsSource="{Binding LargeList}"
         VirtualizingPanel.IsVirtualizing="True"
         VirtualizingPanel.VirtualizationMode="Recycling"
         VirtualizingPanel.ScrollUnit="Item"
         ScrollViewer.IsDeferredScrollingEnabled="False">
    <ListBox.ItemsPanel>
        <ItemsPanelTemplate>
            <VirtualizingStackPanel />
        </ItemsPanelTemplate>
    </ListBox.ItemsPanel>
</ListBox>

<!-- ✅ For ItemsControl (no selection needed) -->
<ItemsControl ItemsSource="{Binding LargeList}"
              VirtualizingPanel.IsVirtualizing="True"
              VirtualizingPanel.VirtualizationMode="Recycling">
    <ItemsControl.ItemsPanel>
        <ItemsPanelTemplate>
            <VirtualizingStackPanel />
        </ItemsPanelTemplate>
    </ItemsControl.ItemsPanel>
    <ItemsControl.Template>
        <ControlTemplate>
            <ScrollViewer CanContentScroll="True">
                <ItemsPresenter />
            </ScrollViewer>
        </ControlTemplate>
    </ItemsControl.Template>
</ItemsControl>
```

---

## 8. View Transition Animations

```xml
<!-- Fade-in on view load -->
<UserControl.Triggers>
    <EventTrigger RoutedEvent="Loaded">
        <BeginStoryboard>
            <Storyboard>
                <DoubleAnimation Storyboard.TargetProperty="Opacity"
                                 From="0" To="1"
                                 Duration="0:0:0.25"
                                 EasingFunction="{StaticResource EaseOut}" />
                <ThicknessAnimation Storyboard.TargetProperty="Margin"
                                    From="0,20,0,0" To="0"
                                    Duration="0:0:0.25"
                                    EasingFunction="{StaticResource EaseOut}" />
            </Storyboard>
        </BeginStoryboard>
    </EventTrigger>
</UserControl.Triggers>
```

```xml
<!-- Shared easing functions in Styles.xaml -->
<CubicEase x:Key="EaseOut" EasingMode="EaseOut" />
<CubicEase x:Key="EaseIn" EasingMode="EaseIn" />
<CubicEase x:Key="EaseInOut" EasingMode="EaseInOut" />
```

```xml
<!-- VisualStateManager for state-based animations -->
<VisualStateManager.VisualStateGroups>
    <VisualStateGroup x:Name="LoadingStates">
        <VisualState x:Name="Loading">
            <Storyboard>
                <DoubleAnimation Storyboard.TargetName="LoadingOverlay"
                                 Storyboard.TargetProperty="Opacity"
                                 To="1" Duration="0:0:0.15" />
            </Storyboard>
        </VisualState>
        <VisualState x:Name="Loaded">
            <Storyboard>
                <DoubleAnimation Storyboard.TargetName="LoadingOverlay"
                                 Storyboard.TargetProperty="Opacity"
                                 To="0" Duration="0:0:0.15" />
            </Storyboard>
        </VisualState>
    </VisualStateGroup>
</VisualStateManager.VisualStateGroups>
```

---

## 9. Empty State Handling

```xml
<!-- ✅ Show empty state when list is empty -->
<Grid>
    <!-- Data list -->
    <ListBox ItemsSource="{Binding Results}"
             Visibility="{Binding Results.Count,
                 Converter={StaticResource CountToVisibility}}" />

    <!-- Empty state -->
    <StackPanel HorizontalAlignment="Center"
                VerticalAlignment="Center"
                Visibility="{Binding Results.Count,
                    Converter={StaticResource CountToCollapsed}}">
        <TextBlock Text="&#xE9CE;"
                   FontFamily="Segoe MDL2 Assets"
                   FontSize="48"
                   HorizontalAlignment="Center"
                   Foreground="{StaticResource TextSecondaryBrush}" />
        <TextBlock Text="No results yet"
                   Style="{StaticResource SubtitleStyle}"
                   HorizontalAlignment="Center"
                   Margin="0,8,0,0" />
        <TextBlock Text="Run a test to see results here"
                   Style="{StaticResource CaptionStyle}"
                   HorizontalAlignment="Center"
                   Foreground="{StaticResource TextSecondaryBrush}" />
        <Button Content="Run Test"
                Command="{Binding RunTestCommand}"
                Style="{StaticResource PrimaryButtonStyle}"
                Margin="0,16,0,0"
                HorizontalAlignment="Center"
                AutomationProperties.Name="Run test to populate results" />
    </StackPanel>
</Grid>
```

```csharp
// CountToVisibilityConverter
public class CountToVisibilityConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        => value is int count && count > 0 ? Visibility.Visible : Visibility.Collapsed;

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotImplementedException();
}
```

---

## Checklist

- [ ] All colors defined in `Colors.xaml` ResourceDictionary — no hardcoded hex
- [ ] All icon-only buttons have `AutomationProperties.Name`
- [ ] Interactive cards use `Button` with custom style, not `Border` + click handler
- [ ] Theme-switchable values use `DynamicResource`
- [ ] Grid uses `*` sizing, not fixed pixel widths
- [ ] Custom TitleBar uses `WindowChrome` with proper `CaptionHeight`
- [ ] Lists with 50+ items use `VirtualizingStackPanel`
- [ ] Views have fade-in animation on `Loaded` event
- [ ] Empty states handled with placeholder UI and action button
