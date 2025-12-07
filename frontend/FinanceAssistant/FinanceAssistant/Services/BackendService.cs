using System.Diagnostics;
using Microsoft.Maui.Storage;
using Microsoft.Maui.Devices;

namespace FinanceAssistant.Services
{
    public class BackendService
    {
        private Process? _backendProcess;
        private static BackendService? _instance;
        public static BackendService Instance => _instance ??= new BackendService();

        private string GetBackendPath()
        {
            // Для Android - используем путь к ресурсам приложения
            if (DeviceInfo.Platform == DevicePlatform.Android)
            {
                var androidPaths = new[]
                {
                    Path.Combine(FileSystem.AppDataDirectory, "backend"),
                    "/data/data/com.termux/files/home/AI-finance-assistant/backend",
                    "/data/data/com.termux/files/home/backend"
                };
                
                foreach (var path in androidPaths)
                {
                    if (Directory.Exists(path) && File.Exists(Path.Combine(path, "main.py")))
                    {
                        return path;
                    }
                }
            }
            
            // Для других платформ - путь к backend относительно приложения
            var appPath = AppDomain.CurrentDomain.BaseDirectory;
            
            var possiblePaths = new[]
            {
                Path.Combine(appPath, "..", "..", "..", "..", "..", "..", "backend"),
                Path.Combine(appPath, "..", "..", "..", "..", "backend"),
                Path.Combine(appPath, "backend"),
                Path.GetFullPath(Path.Combine(appPath, @"..\..\..\..\..\..\..\..\backend"))
            };

            foreach (var path in possiblePaths)
            {
                try
                {
                    var fullPath = Path.GetFullPath(path);
                    if (Directory.Exists(fullPath) && File.Exists(Path.Combine(fullPath, "main.py")))
                    {
                        return fullPath;
                    }
                }
                catch
                {
                    continue;
                }
            }

            return possiblePaths.FirstOrDefault() ?? appPath;
        }
        
        private string FindPythonExecutable()
        {
            var executables = new[]
            {
                "python3",
                "python",
                "/data/data/com.termux/files/usr/bin/python3",
                "/usr/bin/python3",
                "/usr/local/bin/python3"
            };
            
            foreach (var exe in executables)
            {
                try
                {
                    var process = Process.Start(new ProcessStartInfo
                    {
                        FileName = exe,
                        Arguments = "--version",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        CreateNoWindow = true
                    });
                    
                    if (process != null)
                    {
                        process.WaitForExit(1000);
                        if (process.ExitCode == 0)
                        {
                            return exe;
                        }
                        process.Dispose();
                    }
                }
                catch
                {
                    continue;
                }
            }
            
            return "python3"; // Fallback
        }

        public async Task<bool> StartBackendAsync()
        {
            try
            {
                // Для Android без Termux - не пытаемся запускать локально
                // Используем облачный сервер или локальный сервер на ПК
                if (DeviceInfo.Platform == DevicePlatform.Android)
                {
                    Debug.WriteLine("Android: Используйте облачный сервер или локальный сервер на ПК");
                    // Пытаемся найти работающий сервер в сети
                    return await TryFindServerInNetworkAsync();
                }
                
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
                    // Пытаемся найти сервер в сети
                    return await TryFindServerInNetworkAsync();
                }

                // Определяем исполняемый файл Python
                var pythonExe = FindPythonExecutable();
                
                // Запускаем Python процесс для Windows/iOS/macOS
                var startInfo = new ProcessStartInfo
                {
                    FileName = pythonExe,
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
                // Пытаемся найти сервер в сети как fallback
                return await TryFindServerInNetworkAsync();
            }
        }
        
        private async Task<bool> TryFindServerInNetworkAsync()
        {
            // Пытаемся найти работающий сервер в локальной сети
            // Это полезно если backend запущен на ПК в той же Wi-Fi сети
            var commonUrls = new[]
            {
                "http://127.0.0.1:8000",
                "http://localhost:8000",
                // Добавляем IP из настроек если есть
            };
            
            var customUrl = Preferences.Get("api_base_url", string.Empty);
            if (!string.IsNullOrEmpty(customUrl))
            {
                var urlsList = commonUrls.ToList();
                urlsList.Insert(0, customUrl);
                commonUrls = urlsList.ToArray();
            }
            
            foreach (var url in commonUrls)
            {
                try
                {
                    using var client = new HttpClient();
                    client.Timeout = TimeSpan.FromSeconds(1);
                    var response = await client.GetAsync($"{url}/health");
                    if (response.IsSuccessStatusCode)
                    {
                        Debug.WriteLine($"Found backend at: {url}");
                        // Сохраняем найденный URL для использования
                        Preferences.Set("api_base_url", url);
                        return true;
                    }
                }
                catch
                {
                    continue;
                }
            }
            
            return false;
        }

        public async Task<bool> IsBackendRunningAsync()
        {
            try
            {
                using var client = new HttpClient();
                client.Timeout = TimeSpan.FromSeconds(2);
                
                // Пробуем разные адреса в зависимости от платформы
                var urls = new[]
                {
                    "http://127.0.0.1:8000/health",
                    "http://localhost:8000/health"
                };
                
                foreach (var url in urls)
                {
                    try
                    {
                        var response = await client.GetAsync(url);
                        if (response.IsSuccessStatusCode)
                        {
                            return true;
                        }
                    }
                    catch
                    {
                        continue;
                    }
                }
                
                return false;
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

