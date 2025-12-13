using System;

namespace FinanceAssistant.Services
{
    public class ThemeService
    {
        private const string ThemeKey = "AppTheme";
        
        public event EventHandler<bool>? ThemeChanged;
        
        public bool IsDarkTheme
        {
            get => Preferences.Get(ThemeKey, true); // Default to dark
            set
            {
                if (IsDarkTheme != value)
                {
                    Preferences.Set(ThemeKey, value);
                    ApplyTheme(value);
                    ThemeChanged?.Invoke(this, value);
                }
            }
        }
        
        public void Initialize()
        {
            ApplyTheme(IsDarkTheme);
        }
        
        public void ApplyTheme(bool isDark)
        {
            var app = Application.Current;
            if (app == null) return;
            
            app.UserAppTheme = isDark ? AppTheme.Dark : AppTheme.Light;
            
            var mergedDictionaries = app.Resources.MergedDictionaries;
            if (mergedDictionaries == null) return;

            if (isDark)
            {
                app.Resources["BackgroundDark"] = Color.FromArgb("#0D1117");
                app.Resources["BackgroundCard"] = Color.FromArgb("#161B22");
                app.Resources["BackgroundElevated"] = Color.FromArgb("#21262D");
                app.Resources["TextPrimary"] = Color.FromArgb("#FFFFFF");
                app.Resources["TextSecondary"] = Color.FromArgb("#8B949E");
                app.Resources["TextMuted"] = Color.FromArgb("#484F58");
            }
            else
            {
                app.Resources["BackgroundDark"] = Color.FromArgb("#F8F9FA");
                app.Resources["BackgroundCard"] = Color.FromArgb("#FFFFFF");
                app.Resources["BackgroundElevated"] = Color.FromArgb("#E9ECEF");
                app.Resources["TextPrimary"] = Color.FromArgb("#1A1A2E");
                app.Resources["TextSecondary"] = Color.FromArgb("#6C757D");
                app.Resources["TextMuted"] = Color.FromArgb("#ADB5BD");
            }
        }
        
        // Static helper methods to get theme colors for dynamically created UI elements
        public static Color GetBackgroundDark() => GetResourceColor("BackgroundDark", "#0D1117");
        public static Color GetBackgroundCard() => GetResourceColor("BackgroundCard", "#161B22");
        public static Color GetBackgroundElevated() => GetResourceColor("BackgroundElevated", "#21262D");
        public static Color GetTextPrimary() => GetResourceColor("TextPrimary", "#FFFFFF");
        public static Color GetTextSecondary() => GetResourceColor("TextSecondary", "#8B949E");
        public static Color GetTextMuted() => GetResourceColor("TextMuted", "#484F58");
        
        private static Color GetResourceColor(string key, string fallback)
        {
            if (Application.Current?.Resources.TryGetValue(key, out var value) == true && value is Color color)
            {
                return color;
            }
            return Color.FromArgb(fallback);
        }
    }
}

