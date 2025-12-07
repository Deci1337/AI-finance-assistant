using System.Diagnostics;

namespace FinanceAssistant.Services
{
    public class BackendService
    {
        private Process? _backendProcess;
        private static BackendService? _instance;
        public static BackendService Instance => _instance ??= new BackendService();

        private string GetBackendPath()
        {
            // Путь к backend относительно приложения
            var appPath = AppDomain.CurrentDomain.BaseDirectory;
            
            // Ищем backend в разных местах
            var possiblePaths = new[]
            {
                Path.Combine(appPath, "..", "..", "..", "..", "..", "..", "backend"),
                Path.Combine(appPath, "..", "..", "..", "..", "backend"),
                Path.Combine(appPath, "backend"),
                Path.GetFullPath(Path.Combine(appPath, @"..\..\..\..\..\..\..\..\backend")),
                @"C:\Users\HONOR\Desktop\HSE finance\backend" // Fallback путь
            };

            foreach (var path in possiblePaths)
            {
                var fullPath = Path.GetFullPath(path);
                if (Directory.Exists(fullPath) && File.Exists(Path.Combine(fullPath, "main.py")))
                {
                    return fullPath;
                }
            }

            return possiblePaths.Last();
        }

        public async Task<bool> StartBackendAsync()
        {
            try
            {
                // Проверяем, не запущен ли уже backend
                if (await IsBackendRunningAsync())
                {
                    Debug.WriteLine("Backend already running");
                    return true;
                }

                var backendPath = GetBackendPath();
                var mainPyPath = Path.Combine(backendPath, "main.py");

                if (!File.Exists(mainPyPath))
                {
                    Debug.WriteLine($"main.py not found at: {mainPyPath}");
                    return false;
                }

                // Запускаем Python процесс
                var startInfo = new ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = $"\"{mainPyPath}\"",
                    WorkingDirectory = backendPath,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };

                _backendProcess = new Process { StartInfo = startInfo };
                _backendProcess.Start();

                // Даём серверу время запуститься
                await Task.Delay(2000);

                // Проверяем, запустился ли сервер
                var isRunning = await IsBackendRunningAsync();
                Debug.WriteLine($"Backend started: {isRunning}");
                return isRunning;
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Failed to start backend: {ex.Message}");
                return false;
            }
        }

        public async Task<bool> IsBackendRunningAsync()
        {
            try
            {
                using var client = new HttpClient();
                client.Timeout = TimeSpan.FromSeconds(2);
                var response = await client.GetAsync("http://localhost:8000/health");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        public void StopBackend()
        {
            try
            {
                if (_backendProcess != null && !_backendProcess.HasExited)
                {
                    _backendProcess.Kill();
                    _backendProcess.Dispose();
                    _backendProcess = null;
                    Debug.WriteLine("Backend stopped");
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Failed to stop backend: {ex.Message}");
            }
        }
    }
}

