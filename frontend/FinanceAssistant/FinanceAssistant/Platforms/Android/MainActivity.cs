using Android.App;
using Android.Content.PM;
using Android.OS;
using AndroidX.Core.View;
using MauiApp = Microsoft.Maui.Controls.Application;

namespace FinanceAssistant
{
    [Activity(Theme = "@style/Maui.SplashTheme", MainLauncher = true, LaunchMode = LaunchMode.SingleTop, ConfigurationChanges = ConfigChanges.ScreenSize | ConfigChanges.Orientation | ConfigChanges.UiMode | ConfigChanges.ScreenLayout | ConfigChanges.SmallestScreenSize | ConfigChanges.Density)]
    public class MainActivity : MauiAppCompatActivity
    {
        protected override void OnCreate(Bundle? savedInstanceState)
        {
            base.OnCreate(savedInstanceState);
            UpdateSystemBarsTheme();
            
            if (MauiApp.Current != null)
            {
                MauiApp.Current.RequestedThemeChanged += OnRequestedThemeChanged;
            }
        }

        protected override void OnDestroy()
        {
            if (MauiApp.Current != null)
            {
                MauiApp.Current.RequestedThemeChanged -= OnRequestedThemeChanged;
            }
            base.OnDestroy();
        }

        protected override void OnResume()
        {
            base.OnResume();
            UpdateSystemBarsTheme();
        }

        public override void OnConfigurationChanged(Android.Content.Res.Configuration newConfig)
        {
            base.OnConfigurationChanged(newConfig);
            UpdateSystemBarsTheme();
        }

        private void OnRequestedThemeChanged(object? sender, AppThemeChangedEventArgs e)
        {
            UpdateSystemBarsTheme();
        }

        public void UpdateSystemBarsTheme()
        {
            var window = Window;
            if (window == null) return;

            var windowInsetsController = WindowCompat.GetInsetsController(window, window.DecorView);
            if (windowInsetsController == null) return;

            var isDarkTheme = MauiApp.Current?.UserAppTheme == AppTheme.Dark || 
                             (MauiApp.Current?.UserAppTheme == AppTheme.Unspecified && 
                              MauiApp.Current?.RequestedTheme == AppTheme.Dark);
            
            var backgroundColor = isDarkTheme ? Android.Graphics.Color.ParseColor("#0D1117") : Android.Graphics.Color.ParseColor("#F8F9FA");
            
            window.SetNavigationBarColor(backgroundColor);
            window.SetStatusBarColor(backgroundColor);
            
            windowInsetsController.AppearanceLightNavigationBars = !isDarkTheme;
            windowInsetsController.AppearanceLightStatusBars = !isDarkTheme;
            
            WindowCompat.SetDecorFitsSystemWindows(window, true);
            windowInsetsController.Show(WindowInsetsCompat.Type.NavigationBars());
            windowInsetsController.Show(WindowInsetsCompat.Type.StatusBars());
        }
    }
}
