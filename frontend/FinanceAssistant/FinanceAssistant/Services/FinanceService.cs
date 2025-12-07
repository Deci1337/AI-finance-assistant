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
