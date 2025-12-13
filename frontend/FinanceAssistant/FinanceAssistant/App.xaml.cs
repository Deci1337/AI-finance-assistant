using FinanceAssistant.Services;

namespace FinanceAssistant
{
    public partial class App : Application
    {
        private readonly ThemeService _themeService;
        private readonly FinanceService _financeService;
        
        public App(ThemeService themeService, FinanceService financeService)
        {
            InitializeComponent();
            _themeService = themeService;
            _financeService = financeService;
            
            // Initialize theme from preferences
            _themeService.Initialize();
            
            // Запускаем backend при старте приложения автоматически
            _ = StartBackendAsync();
            
            // Автоматически ищем сервер на Android
#if ANDROID
            _ = AutoFindServerAsync();
#endif
        }
        
        private async Task AutoFindServerAsync()
        {
            try
            {
                await Task.Delay(2000);
                
                var isHealthy = await _financeService.CheckHealthAsync();
                if (!isHealthy)
                {
                    var (found, url) = await _financeService.FindWorkingServerAsync();
                    if (found)
                    {
                        System.Diagnostics.Debug.WriteLine($"Auto-found server: {url}");
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Auto-find server error: {ex.Message}");
            }
        }

        private async Task StartBackendAsync()
        {
            try
            {
                // Небольшая задержка для инициализации приложения
                await Task.Delay(1000);
                
                var started = await BackendService.Instance.StartBackendAsync();
                System.Diagnostics.Debug.WriteLine($"Backend auto-start: {started}");
                
                if (!started)
                {
                    System.Diagnostics.Debug.WriteLine("Backend не запустился автоматически. Используйте внешний сервер или запустите вручную.");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Ошибка автозапуска backend: {ex.Message}");
            }
        }

        protected override Window CreateWindow(IActivationState? activationState)
        {
            var window = new Window(new AppShell());
            
            // Останавливаем backend при закрытии приложения
            window.Destroying += (s, e) =>
            {
#if WINDOWS
                BackendService.Instance.StopBackend();
#endif
            };
            
            return window;
        }
    }
}
