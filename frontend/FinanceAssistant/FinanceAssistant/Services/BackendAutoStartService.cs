using System.Diagnostics;
using System.Runtime.InteropServices;

namespace FinanceAssistant.Services
{
    public class BackendAutoStartService
    {
        private Process? _backendProcess;
        private static readonly string BackendPath = GetBackendPath();
        
        public bool IsBackendRunning()
        {
            try
            {
                using var client = new HttpClient();
                client.Timeout = TimeSpan.FromSeconds(2);
                var response = client.GetAsync("http://127.0.0.1:8000/health").Result;
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }
        
        public async Task<bool> StartBackendAsync()
        {
            if (IsBackendRunning())
            {
                return true;
            }
            
            try
            {
                var pythonExecutable = FindPythonExecutable();
                if (string.IsNullOrEmpty(pythonExecutable))
                {
                    System.Diagnostics.Debug.WriteLine("Python не найден");
                    return false;
                }
                
                var startInfo = new ProcessStartInfo
                {
                    FileName = pythonExecutable,
                    Arguments = $"\"{Path.Combine(BackendPath, "main.py")}\"",
                    WorkingDirectory = BackendPath,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };
                
                // Для Android через Termux
                if (DeviceInfo.Platform == DevicePlatform.Android)
                {
                    return await StartBackendAndroidAsync();
                }
                
                _backendProcess = Process.Start(startInfo);
                
                // Ждем запуска сервера
                await Task.Delay(2000);
                
                // Проверяем что сервер запустился
                for (int i = 0; i < 10; i++)
                {
                    if (IsBackendRunning())
                    {
                        return true;
                    }
                    await Task.Delay(1000);
                }
                
                return false;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Ошибка запуска backend: {ex.Message}");
                return false;
            }
        }
        
        private async Task<bool> StartBackendAndroidAsync()
        {
            try
            {
                // Попытка запуска через Termux
                var termuxScript = $@"
cd {BackendPath}
python3 main.py &
";
                
                // Сохраняем скрипт во временный файл
                var scriptPath = Path.Combine(FileSystem.CacheDirectory, "start_backend.sh");
                await File.WriteAllTextAsync(scriptPath, termuxScript);
                
                // Запуск через Termux (требует установленного Termux)
                var startInfo = new ProcessStartInfo
                {
                    FileName = "termux-run",
                    Arguments = $"bash {scriptPath}",
                    UseShellExecute = false,
                    CreateNoWindow = true
                };
                
                _backendProcess = Process.Start(startInfo);
                await Task.Delay(3000);
                
                return IsBackendRunning();
            }
            catch
            {
                // Если Termux не установлен, пробуем напрямую
                return false;
            }
        }
        
        private static string FindPythonExecutable()
        {
            var possiblePaths = new[]
            {
                "python3",
                "python",
                "/usr/bin/python3",
                "/usr/local/bin/python3"
            };
            
            foreach (var path in possiblePaths)
            {
                try
                {
                    var process = Process.Start(new ProcessStartInfo
                    {
                        FileName = path,
                        Arguments = "--version",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        CreateNoWindow = true
                    });
                    
                    if (process != null)
                    {
                        process.WaitForExit();
                        if (process.ExitCode == 0)
                        {
                            return path;
                        }
                    }
                }
                catch
                {
                    continue;
                }
            }
            
            return string.Empty;
        }
        
        private static string GetBackendPath()
        {
            // Для Android - путь к ресурсам приложения
            if (DeviceInfo.Platform == DevicePlatform.Android)
            {
                // Backend должен быть включен в Assets приложения
                return Path.Combine(FileSystem.AppDataDirectory, "backend");
            }
            
            // Для других платформ - относительный путь
            var currentDir = AppContext.BaseDirectory;
            var backendPath = Path.Combine(currentDir, "..", "..", "..", "..", "backend");
            return Path.GetFullPath(backendPath);
        }
        
        public void StopBackend()
        {
            try
            {
                _backendProcess?.Kill();
                _backendProcess?.Dispose();
                _backendProcess = null;
            }
            catch
            {
                // Игнорируем ошибки при остановке
            }
        }
    }
}

