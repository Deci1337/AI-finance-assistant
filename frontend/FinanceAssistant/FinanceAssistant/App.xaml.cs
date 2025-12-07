using FinanceAssistant.Services;

namespace FinanceAssistant
{
    public partial class App : Application
    {
        public App()
        {
            InitializeComponent();
            
            // Запускаем backend при старте приложения автоматически
            _ = StartBackendAsync();
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
