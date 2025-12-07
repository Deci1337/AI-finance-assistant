using FinanceAssistant.Models;
using System.Text;
using System.Text.Json;
using Microsoft.Maui.Storage;

namespace FinanceAssistant.Services
{
    public class FinanceService
    {
        private string _apiBaseUrl;

        public FinanceService()
        {
            _apiBaseUrl = GetApiBaseUrl();
        }

        private static string GetApiBaseUrl()
        {
            var savedUrl = Preferences.Get("api_base_url", string.Empty);
            if (!string.IsNullOrEmpty(savedUrl))
                return savedUrl;

            // Default for Android emulator
            if (DeviceInfo.Platform == DevicePlatform.Android && DeviceInfo.DeviceType == DeviceType.Virtual)
                return "http://10.0.2.2:8000";
            
            return "http://localhost:8000";
        }

        public string GetCurrentServerUrl() => _apiBaseUrl;

        public void RefreshApiUrl()
        {
            _apiBaseUrl = GetApiBaseUrl();
        }

        public void SetServerUrl(string url)
        {
            _apiBaseUrl = url;
            Preferences.Set("api_base_url", url);
        }

        public async Task<bool> CheckHealthAsync()
        {
            try
            {
                using var client = new HttpClient();
                client.Timeout = TimeSpan.FromSeconds(3);
                var response = await client.GetAsync($"{_apiBaseUrl}/health");
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

            // Стандартные сети
            for (int i = 1; i <= 10; i++)
            {
                urlsToTry.Add($"http://192.168.1.{i}:8000");
                urlsToTry.Add($"http://192.168.0.{i}:8000");
            }

            foreach (var url in urlsToTry)
            {
                try
                {
                    using var client = new HttpClient();
                    client.Timeout = TimeSpan.FromSeconds(2);
                    var response = await client.GetAsync($"{url}/health");
                    
                    if (response.IsSuccessStatusCode)
                    {
                        SetServerUrl(url);
                        return (true, url);
                    }
                }
                catch
                {
                    // Continue to next URL
                }
            }

            return (false, string.Empty);
        }

        public async Task<TransactionExtractionResult> ExtractTransactionsFromMessageAsync(string message, string? context = null)
        {
            try
            {
                using var httpClient = new HttpClient();
                httpClient.Timeout = TimeSpan.FromSeconds(30);

                var request = new
                {
                    user_message = message,
                    context = context
                };

                var json = JsonSerializer.Serialize(request);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await httpClient.PostAsync($"{_apiBaseUrl}/extract-transactions", content);
                
                if (response.IsSuccessStatusCode)
                {
                    var responseContent = await response.Content.ReadAsStringAsync();
                    var result = JsonSerializer.Deserialize<TransactionExtractionResult>(responseContent, new JsonSerializerOptions
                    {
                        PropertyNameCaseInsensitive = true
                    });
                    
                    if (result != null)
                    {
                        return result;
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error extracting transactions: {ex.Message}");
            }

            return new TransactionExtractionResult
            {
                Transactions = new List<ExtractedTransaction>(),
                Analysis = "Не удалось подключиться к серверу. Проверьте, что backend запущен.",
                Questions = new List<string> { "Проверьте подключение к серверу" }
            };
        }

        public async Task<ChatResult> SendChatMessageAsync(string message, string? context = null)
        {
            try
            {
                using var httpClient = new HttpClient();
                httpClient.Timeout = TimeSpan.FromSeconds(30);

                var request = new
                {
                    message = message,
                    context = context
                };

                var json = JsonSerializer.Serialize(request);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await httpClient.PostAsync($"{_apiBaseUrl}/chat", content);
                
                if (response.IsSuccessStatusCode)
                {
                    var responseContent = await response.Content.ReadAsStringAsync();
                    var result = JsonSerializer.Deserialize<ChatResult>(responseContent, new JsonSerializerOptions
                    {
                        PropertyNameCaseInsensitive = true
                    });
                    
                    if (result != null)
                    {
                        return result;
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error sending chat message: {ex.Message}");
                return new ChatResult
                {
                    Response = $"Ошибка подключения: {ex.Message}",
                    Timestamp = DateTime.Now.ToString("o")
                };
            }

            return new ChatResult
            {
                Response = "Не удалось получить ответ от сервера.",
                Timestamp = DateTime.Now.ToString("o")
            };
        }

        public async Task<FriendlinessResult?> AnalyzeFriendlinessAsync(string message)
        {
            try
            {
                using var httpClient = new HttpClient();
                httpClient.Timeout = TimeSpan.FromSeconds(10);

                var request = new { message = message };
                var json = JsonSerializer.Serialize(request);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await httpClient.PostAsync($"{_apiBaseUrl}/analyze-friendliness", content);
                
                if (response.IsSuccessStatusCode)
                {
                    var responseContent = await response.Content.ReadAsStringAsync();
                    var result = JsonSerializer.Deserialize<FriendlinessResult>(responseContent, new JsonSerializerOptions
                    {
                        PropertyNameCaseInsensitive = true
                    });
                    return result;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error analyzing friendliness: {ex.Message}");
            }
            return null;
        }

        public async Task<VoiceTranscriptionResult> TranscribeAudioAsync(Stream audioStream, string fileName = "audio.wav")
        {
            try
            {
                using var httpClient = new HttpClient();
                httpClient.Timeout = TimeSpan.FromSeconds(60);

                var content = new MultipartFormDataContent();
                var streamContent = new StreamContent(audioStream);
                streamContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("audio/wav");
                content.Add(streamContent, "audio", fileName);
                content.Add(new StringContent("wav"), "audio_format");

                var response = await httpClient.PostAsync($"{_apiBaseUrl}/transcribe-voice", content);
                
                if (response.IsSuccessStatusCode)
                {
                    var responseContent = await response.Content.ReadAsStringAsync();
                    var result = JsonSerializer.Deserialize<VoiceTranscriptionResult>(responseContent, new JsonSerializerOptions
                    {
                        PropertyNameCaseInsensitive = true
                    });
                    
                    if (result != null)
                    {
                        return result;
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error transcribing audio: {ex.Message}");
                return new VoiceTranscriptionResult
                {
                    Text = "",
                    Error = $"Ошибка транскрипции: {ex.Message}"
                };
            }

            return new VoiceTranscriptionResult
            {
                Text = "",
                Error = "Не удалось распознать речь. Проверьте подключение к серверу."
            };
        }
    }

    public class VoiceTranscriptionResult
    {
        public string Text { get; set; } = string.Empty;
        public string? Error { get; set; }
        public double Confidence { get; set; }
    }

    public class ChatResult
    {
        public string Response { get; set; } = string.Empty;
        public string Timestamp { get; set; } = string.Empty;
    }

    public class FriendlinessResult
    {
        public double FriendlinessScore { get; set; }
        public string Sentiment { get; set; } = string.Empty;
        public string Timestamp { get; set; } = string.Empty;
    }

    public class TransactionExtractionResult
    {
        public List<ExtractedTransaction> Transactions { get; set; } = new();
        public string? Analysis { get; set; }
        public List<string>? Questions { get; set; }
        public List<string>? Warnings { get; set; }
        public ExtractedInfo? ExtractedInfo { get; set; }
    }

    public class ExtractedTransaction
    {
        public string Type { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public decimal? Amount { get; set; }
        public string Category { get; set; } = string.Empty;
        public string Date { get; set; } = string.Empty;
        public string? Description { get; set; }
        public double Confidence { get; set; }
    }

    public class ExtractedInfo
    {
        public decimal TotalIncome { get; set; }
        public decimal TotalExpense { get; set; }
        public int TransactionsCount { get; set; }
    }
}
