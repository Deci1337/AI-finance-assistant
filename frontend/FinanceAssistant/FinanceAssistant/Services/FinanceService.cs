using FinanceAssistant.Models;
using System.Text;
using System.Text.Json;
using Microsoft.Maui.Storage;
using Microsoft.Maui.Media;

namespace FinanceAssistant.Services
{
    public class FinanceService
    {
        // Автоматическое определение API URL
        // Приоритет: 1) Настройки приложения, 2) localhost для эмулятора, 3) Автопоиск в сети
        private static string GetApiBaseUrl()
        {
            // Для Android эмулятора
            if (DeviceInfo.Platform == DevicePlatform.Android && DeviceInfo.DeviceType == DeviceType.Virtual)
            {
                return "http://10.0.2.2:8000";
            }
            
            // Для iOS симулятора
            if (DeviceInfo.Platform == DevicePlatform.iOS && DeviceInfo.DeviceType == DeviceType.Virtual)
            {
                return "http://localhost:8000";
            }
            
            // Для реальных устройств - используем сохраненный URL или облачный сервер
            var customUrl = Preferences.Get("api_base_url", string.Empty);
            if (!string.IsNullOrEmpty(customUrl))
            {
                return customUrl;
            }
            
            // Для Android реальных устройств - используем облачный сервер по умолчанию
            // Или можно настроить IP локального сервера на ПК
            if (DeviceInfo.Platform == DevicePlatform.Android)
            {
                // По умолчанию - облачный сервер (нужно настроить)
                // Или локальный сервер на ПК в той же Wi-Fi сети
                return "http://localhost:8000"; // Будет заменено на найденный сервер
            }
            
            // Для других платформ - localhost (backend запускается локально)
            return "http://localhost:8000";
        }
        
        private static readonly string API_BASE_URL = GetApiBaseUrl();
        
        // Stub data - will be replaced with backend API calls
