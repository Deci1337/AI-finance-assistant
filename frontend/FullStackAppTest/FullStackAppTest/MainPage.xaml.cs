using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;

namespace FullStackAppTest
{
    public partial class MainPage : ContentPage
    {
        private readonly HttpClient _httpClient;

        // Общие настройки JSON, чтобы имена полей были camelCase (a, b, result)
        private static readonly JsonSerializerOptions JsonOptions = new()
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            PropertyNameCaseInsensitive = true
        };


        public MainPage()
        {
            InitializeComponent();
            
            // подлюкчение сервера (аккуратно с ссылкой)
            _httpClient = new HttpClient
            {
                BaseAddress = new Uri("http://localhost:8000")
            };
        }

        // ДТО, то, что отправляем в бэк
        private sealed class SumRequestDto
        {
            public double A { get; set; }
            public double B { get; set; }
        }

        // То, что получаем от Python: { "result": ... }
        private sealed class SumResponseDto
        {
            public double Result { get; set; }
        }

        private async void OnSumClicked(object sender, EventArgs e)
        {
            try
            {
                // Читаем текст из полей
                var aText = EntryA.Text;
                var bText = EntryB.Text;

                // Проверяем и конвертируем в double
                if (!double.TryParse(aText, out var a))
                {
                    await DisplayAlert("Ошибка", "Некорректное число A", "OK");
                    return;
                }

                if (!double.TryParse(bText, out var b))
                {
                    await DisplayAlert("Ошибка", "Некорректное число B", "OK");
                    return;
                }

                // Формируем объект запроса DTO
                var request = new SumRequestDto
                {
                    A = a,
                    B = b
                };

                // Отправляем POST на /math/sum с JSON
                using var response = await _httpClient.PostAsJsonAsync("/math/sum", request, JsonOptions);

                // Если код не 2xx — бросаем исключение
                response.EnsureSuccessStatusCode();

                // Десериализуем ответ в SumResponseDto
                var resultDto = await response.Content.ReadFromJsonAsync<SumResponseDto>(JsonOptions);

                if (resultDto is null)
                {
                    await DisplayAlert("Ошибка", "Пустой ответ от сервера", "OK");
                    return;
                }

                // Показываем результат
                ResultLabel.Text = $"Результат: {resultDto.Result}";
            }
            catch (HttpRequestException ex)
            {
                // Ошибки сети или backend не запущен
                await DisplayAlert("Сетевая ошибка", ex.Message, "OK");
            }
            catch (Exception ex)
            {
                // Любые другие ошибки
                await DisplayAlert("Ошибка", ex.Message, "OK");
            }
        }
    }
}
