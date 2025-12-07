using System.Text;
using System.Text.Json;
using Microsoft.Maui.Storage;

namespace FinanceAssistant.Services
{
    /// <summary>
    /// Service for communicating with the backend API for AI-powered transaction extraction
    /// </summary>
    public class FinanceService
    {
        private string _apiBaseUrl;

        public FinanceService()
        {
            _apiBaseUrl = GetDefaultApiUrl();
        }

        private static string GetDefaultApiUrl()
        {
            // Check saved preference first
            var savedUrl = Preferences.Get("api_base_url", string.Empty);
            if (!string.IsNullOrEmpty(savedUrl))
            {
                return savedUrl;
            }

            // For Android emulator
            if (DeviceInfo.Platform == DevicePlatform.Android && DeviceInfo.DeviceType == DeviceType.Virtual)
            {
                return "http://10.0.2.2:8000";
            }
            
            // Default - localhost
            return "http://localhost:8000";
        }

        /// <summary>
        /// Set the API base URL (for connecting to backend from different devices)
        /// </summary>
        public void SetApiBaseUrl(string url)
        {
            _apiBaseUrl = url.TrimEnd('/');
            Preferences.Set("api_base_url", _apiBaseUrl);
        }

        /// <summary>
        /// Get the current API base URL
        /// </summary>
        public string GetApiBaseUrl() => _apiBaseUrl;

        /// <summary>
        /// Extract transactions from a user message using the backend AI
        /// </summary>
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
                else
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    System.Diagnostics.Debug.WriteLine($"API Error: {response.StatusCode} - {errorContent}");
                }
            }
            catch (HttpRequestException ex)
            {
                System.Diagnostics.Debug.WriteLine($"HTTP Error: {ex.Message}");
                return new TransactionExtractionResult
                {
                    Transactions = new List<ExtractedTransaction>(),
                    Analysis = $"Не удалось подключиться к серверу ({_apiBaseUrl}). Убедитесь, что backend запущен.",
                    Questions = new List<string> { "Проверьте, что backend сервер запущен на порту 8000" }
                };
            }
            catch (TaskCanceledException)
            {
                return new TransactionExtractionResult
                {
                    Transactions = new List<ExtractedTransaction>(),
                    Analysis = "Превышено время ожидания ответа от сервера.",
                    Questions = new List<string> { "Попробуйте отправить сообщение еще раз" }
                };
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error extracting transactions: {ex.Message}");
            }

            return new TransactionExtractionResult
            {
                Transactions = new List<ExtractedTransaction>(),
                Analysis = "Не удалось обработать запрос. Попробуйте позже.",
                Questions = new List<string> { "Проверьте подключение к серверу" }
            };
        }

        /// <summary>
        /// Send a chat message to the AI assistant
        /// </summary>
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
                    Response = $"Ошибка подключения к серверу: {ex.Message}",
                    Timestamp = DateTime.Now.ToString("o")
                };
            }

            return new ChatResult
            {
                Response = "Не удалось получить ответ от ассистента.",
                Timestamp = DateTime.Now.ToString("o")
            };
        }

        /// <summary>
        /// Check if the backend server is available
        /// </summary>
        public async Task<bool> IsServerAvailableAsync()
        {
            try
            {
                using var httpClient = new HttpClient();
                httpClient.Timeout = TimeSpan.FromSeconds(5);
                var response = await httpClient.GetAsync($"{_apiBaseUrl}/health");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Analyze friendliness of a user message
        /// </summary>
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

    // DTOs for API responses
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
}
