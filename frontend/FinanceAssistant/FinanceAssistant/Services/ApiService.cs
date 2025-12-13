using System.Net.Http.Json;
using System.Net.NetworkInformation;
using System.Net.Sockets;

namespace FinanceAssistant.Services
{
    public class ChatRequest
    {
        public string message { get; set; } = string.Empty;
        public string? context { get; set; }
        public List<Dictionary<string, object>>? transactions { get; set; }
    }

    public class ChatResponse
    {
        public string response { get; set; } = string.Empty;
        public string timestamp { get; set; } = string.Empty;
    }

    public class ApiService
    {
        private readonly HttpClient _httpClient;
        private string _baseUrl;
        
        private static string? _customServerUrl;
        public static string? CustomServerUrl 
        { 
            get => _customServerUrl;
            set => _customServerUrl = value;
        }

        public ApiService()
        {
            var handler = new HttpClientHandler();
            handler.ServerCertificateCustomValidationCallback = (message, cert, chain, errors) => true;
            
            _httpClient = new HttpClient(handler);
            _httpClient.Timeout = TimeSpan.FromSeconds(60);
            
            _baseUrl = GetBaseUrl();
        }

        private string GetBaseUrl()
        {
            if (!string.IsNullOrEmpty(_customServerUrl))
                return _customServerUrl;

#if ANDROID
            return "http://192.168.43.1:8000"; // Типичный IP при раздаче с телефона
#elif WINDOWS
            return "http://localhost:8000";
#else
            return "http://localhost:8000";
#endif
        }

        public void SetServerUrl(string url)
        {
            _baseUrl = url;
            _customServerUrl = url;
        }

        public string GetCurrentServerUrl() => _baseUrl;

        public async Task<string> SendChatMessageAsync(
            string message,
            string? context = null,
            List<Dictionary<string, object>>? transactions = null
        )
        {
            try
            {
                var request = new ChatRequest
                {
                    message = message,
                    context = context,
                    transactions = transactions
                };

                var response = await _httpClient.PostAsJsonAsync($"{_baseUrl}/chat", request);
                
                if (response.IsSuccessStatusCode)
                {
                    var chatResponse = await response.Content.ReadFromJsonAsync<ChatResponse>();
                    return chatResponse?.response ?? "Не удалось получить ответ";
                }
                else
                {
                    return $"Ошибка сервера: {response.StatusCode}";
                }
            }
            catch (HttpRequestException ex)
            {
                return $"Нет подключения к серверу. Нажми на заголовок чтобы ввести IP.";
            }
            catch (TaskCanceledException)
            {
                return "Превышено время ожидания. Проверь подключение.";
            }
            catch (Exception ex)
            {
                return $"Ошибка: {ex.Message}";
            }
        }

        public async Task<bool> CheckHealthAsync()
        {
            try
            {
                using var client = new HttpClient();
                client.Timeout = TimeSpan.FromSeconds(3);
                var response = await client.GetAsync($"{_baseUrl}/health");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        public async Task<(bool success, string url)> FindWorkingServerAsync()
        {
            // IP адреса для поиска:
            // - Мобильный хотспот Android: 192.168.43.x
            // - Мобильный хотспот iOS: 172.20.10.x  
            // - Стандартные роутеры: 192.168.0.x, 192.168.1.x
            // - Android эмулятор: 10.0.2.2
            
            var urlsToTry = new List<string>
            {
                "http://localhost:8000",
                "http://127.0.0.1:8000",
                "http://10.0.2.2:8000",
            };

            // Добавляем IP для мобильного хотспота (192.168.43.x)
            for (int i = 1; i <= 20; i++)
            {
                urlsToTry.Add($"http://192.168.43.{i}:8000");
            }

            // iOS hotspot (172.20.10.x)
            for (int i = 1; i <= 15; i++)
            {
                urlsToTry.Add($"http://172.20.10.{i}:8000");
            }

            // Стандартные сети (расширенный диапазон)
            for (int i = 1; i <= 50; i++)
            {
                urlsToTry.Add($"http://192.168.1.{i}:8000");
                urlsToTry.Add($"http://192.168.0.{i}:8000");
                urlsToTry.Add($"http://192.168.2.{i}:8000");
            }

            foreach (var url in urlsToTry)
            {
                try
                {
                    using var client = new HttpClient();
                    client.Timeout = TimeSpan.FromMilliseconds(500); // Быстрый таймаут
                    var response = await client.GetAsync($"{url}/health");
                    if (response.IsSuccessStatusCode)
                    {
                        _baseUrl = url;
                        _customServerUrl = url;
                        return (true, url);
                    }
                }
                catch
                {
                    // Продолжаем поиск
                }
            }

            return (false, _baseUrl);
        }

        // Получить подсказку какой IP использовать
        public static string GetConnectionHint()
        {
            return @"Для подключения:

1. На ПК запусти: python main.py

2. На ПК узнай IP командой: ipconfig
   Ищи 'IPv4' в разделе Wi-Fi
   (обычно 192.168.43.xxx)

3. Введи: http://IP_АДРЕС:8000
   Пример: http://192.168.43.5:8000";
        }
    }
}
