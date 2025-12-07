using FinanceAssistant.Services;

namespace FinanceAssistant
{
    public partial class App : Application
    {
        public App()
        {
            InitializeComponent();
            
            // Запускаем backend при старте приложения (только на Windows)
#if WINDOWS
            _ = StartBackendAsync();
#endif
        }

        private async Task StartBackendAsync()
        {
            var started = await BackendService.Instance.StartBackendAsync();
            System.Diagnostics.Debug.WriteLine($"Backend auto-start: {started}");
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
