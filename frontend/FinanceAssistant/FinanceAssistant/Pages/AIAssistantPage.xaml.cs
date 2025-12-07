using FinanceAssistant.Data;
using FinanceAssistant.Services;

namespace FinanceAssistant.Pages
{
    public partial class AIAssistantPage : ContentPage
    {
        private readonly ApiService _apiService;
        private readonly DatabaseService _databaseService;
        private bool _isWaitingForResponse;

        public AIAssistantPage(DatabaseService databaseService)
        {
            InitializeComponent();
            _databaseService = databaseService;
            _apiService = new ApiService();
        }

        protected override async void OnAppearing()
        {
            base.OnAppearing();
            await CheckAndConnectToServerAsync();
        }

        private async Task CheckAndConnectToServerAsync()
        {
            // Проверяем текущее подключение
            var isHealthy = await _apiService.CheckHealthAsync();
            
            if (!isHealthy)
            {
                AddSystemMessage("Поиск сервера...");
                
                // Пробуем найти работающий сервер
                var (found, url) = await _apiService.FindWorkingServerAsync();
                
                if (found)
                {
                    AddSystemMessage($"Подключено: {url}");
                    AddWelcomeMessage();
                }
                else
                {
                    AddSystemMessage("Сервер не найден!");
                    AddSystemMessage("Нажми на 'AI Assistant' вверху для настройки");
                }
            }
            else
            {
                AddSystemMessage($"Подключено: {_apiService.GetCurrentServerUrl()}");
                AddWelcomeMessage();
            }
        }

        private async void OnBackTapped(object? sender, EventArgs e)
        {
            await Shell.Current.GoToAsync("..");
        }

        private async void OnHeaderTapped(object? sender, EventArgs e)
        {
            var action = await DisplayActionSheet(
                "Настройки сервера",
                "Отмена",
                null,
                "Ввести IP адрес",
                "Как узнать IP?",
                "Поиск сервера"
            );

            switch (action)
            {
                case "Ввести IP адрес":
                    var currentUrl = _apiService.GetCurrentServerUrl();
                    var result = await DisplayPromptAsync(
                        "IP адрес сервера",
                        "Введи адрес (на ПК: ipconfig)",
                        initialValue: currentUrl,
                        placeholder: "http://192.168.43.5:8000"
                    );

                    if (!string.IsNullOrEmpty(result))
                    {
                        // Добавляем http:// если не указан
                        if (!result.StartsWith("http"))
                            result = "http://" + result;
                        // Добавляем порт если не указан
                        if (!result.Contains(":8000"))
                            result = result.TrimEnd('/') + ":8000";
                            
                        _apiService.SetServerUrl(result);
                        MessagesContainer.Children.Clear();
                        await CheckAndConnectToServerAsync();
                    }
                    break;

                case "Как узнать IP?":
                    await DisplayAlert("Инструкция", ApiService.GetConnectionHint(), "OK");
                    break;

                case "Поиск сервера":
                    MessagesContainer.Children.Clear();
                    await CheckAndConnectToServerAsync();
                    break;
            }
        }

        private void AddWelcomeMessage()
        {
            var border = new Border
            {
                BackgroundColor = Color.FromArgb("#161B22"),
                StrokeShape = new Microsoft.Maui.Controls.Shapes.RoundRectangle { CornerRadius = new CornerRadius(15, 15, 15, 0) },
                Stroke = Brush.Transparent,
                Padding = new Thickness(15),
                HorizontalOptions = LayoutOptions.Start,
                MaximumWidthRequest = 300
            };

            var stack = new VerticalStackLayout { Spacing = 5 };

            var nameLabel = new Label
            {
                Text = "AI Assistant",
                TextColor = Color.FromArgb("#00D09E"),
                FontSize = 12,
                FontAttributes = FontAttributes.Bold
            };

            var messageLabel = new Label
            {
                Text = "Привет! Я твой финансовый ассистент. Могу помочь с анализом расходов, дать советы по бюджету и ответить на вопросы о финансах.",
                TextColor = Color.FromArgb("#FFFFFF"),
                FontSize = 14,
                LineBreakMode = LineBreakMode.WordWrap
            };

            stack.Children.Add(nameLabel);
            stack.Children.Add(messageLabel);
            border.Content = stack;

            MessagesContainer.Children.Add(border);
        }

        private void OnSendMessage(object? sender, EventArgs e)
        {
            _ = SendMessageAsync();
        }

        private void OnSendTapped(object? sender, EventArgs e)
        {
            _ = SendMessageAsync();
        }

        private async Task SendMessageAsync()
        {
            var message = MessageEntry.Text?.Trim();
            if (string.IsNullOrEmpty(message) || _isWaitingForResponse)
                return;

            _isWaitingForResponse = true;

            // Добавляем сообщение пользователя
            AddUserMessage(message);
            MessageEntry.Text = string.Empty;

            // Показываем индикатор загрузки
            AddTypingIndicator();

            try
            {
                // Получаем контекст финансов пользователя
                var context = await GetFinancialContextAsync();
                
                // Отправляем запрос в API
                var response = await _apiService.SendChatMessageAsync(message, context);
                
                // Убираем индикатор и показываем ответ
                RemoveTypingIndicator();
                AddAIMessage(response);
            }
            catch (Exception ex)
            {
                RemoveTypingIndicator();
                AddAIMessage($"Ошибка: {ex.Message}");
            }
            finally
            {
                _isWaitingForResponse = false;
            }
        }

        private async Task<string> GetFinancialContextAsync()
        {
            try
            {
                var balance = await _databaseService.GetTotalBalanceAsync();
                var (income, expense) = await _databaseService.GetMonthlyTotalsAsync();
                var transactions = await _databaseService.GetRecentTransactionsAsync(5);
                
                var recentTransStr = string.Join(", ", transactions.Select(t => 
                    $"{t.Title}: {(t.Type == Models.TransactionType.Income ? "+" : "-")}{t.Amount} RUB"));

                return $"Баланс: {balance} RUB. Доход за месяц: {income} RUB. Расходы за месяц: {expense} RUB. Последние операции: {recentTransStr}";
            }
            catch
            {
                return string.Empty;
            }
        }

        private void AddUserMessage(string message)
        {
            var border = new Border
            {
                BackgroundColor = Color.FromArgb("#00D09E"),
                StrokeShape = new Microsoft.Maui.Controls.Shapes.RoundRectangle { CornerRadius = new CornerRadius(15, 15, 0, 15) },
                Stroke = Brush.Transparent,
                Padding = new Thickness(15),
                HorizontalOptions = LayoutOptions.End,
                MaximumWidthRequest = 300
            };

            var label = new Label
            {
                Text = message,
                TextColor = Color.FromArgb("#0D1117"),
                FontSize = 14,
                LineBreakMode = LineBreakMode.WordWrap
            };

            border.Content = label;
            MessagesContainer.Children.Add(border);
            ScrollToBottom();
        }

        private void AddAIMessage(string message)
        {
            var border = new Border
            {
                BackgroundColor = Color.FromArgb("#161B22"),
                StrokeShape = new Microsoft.Maui.Controls.Shapes.RoundRectangle { CornerRadius = new CornerRadius(15, 15, 15, 0) },
                Stroke = Brush.Transparent,
                Padding = new Thickness(15),
                HorizontalOptions = LayoutOptions.Start,
                MaximumWidthRequest = 300
            };

            var stack = new VerticalStackLayout { Spacing = 5 };
            
            var nameLabel = new Label
            {
                Text = "AI Assistant",
                TextColor = Color.FromArgb("#00D09E"),
                FontSize = 12,
                FontAttributes = FontAttributes.Bold
            };

            var messageLabel = new Label
            {
                Text = message,
                TextColor = Color.FromArgb("#FFFFFF"),
                FontSize = 14,
                LineBreakMode = LineBreakMode.WordWrap
            };

            stack.Children.Add(nameLabel);
            stack.Children.Add(messageLabel);
            border.Content = stack;
            
            MessagesContainer.Children.Add(border);
            ScrollToBottom();
        }

        private void AddSystemMessage(string message)
        {
            var label = new Label
            {
                Text = message,
                TextColor = Color.FromArgb("#8B949E"),
                FontSize = 12,
                HorizontalOptions = LayoutOptions.Center,
                HorizontalTextAlignment = TextAlignment.Center,
                Margin = new Thickness(0, 5)
            };
            MessagesContainer.Children.Add(label);
            ScrollToBottom();
        }

        private Border? _typingIndicator;

        private void AddTypingIndicator()
        {
            _typingIndicator = new Border
            {
                BackgroundColor = Color.FromArgb("#161B22"),
                StrokeShape = new Microsoft.Maui.Controls.Shapes.RoundRectangle { CornerRadius = new CornerRadius(15, 15, 15, 0) },
                Stroke = Brush.Transparent,
                Padding = new Thickness(15),
                HorizontalOptions = LayoutOptions.Start,
                MaximumWidthRequest = 100
            };

            var label = new Label
            {
                Text = "...",
                TextColor = Color.FromArgb("#8B949E"),
                FontSize = 14
            };

            _typingIndicator.Content = label;
            MessagesContainer.Children.Add(_typingIndicator);
            ScrollToBottom();
        }

        private void RemoveTypingIndicator()
        {
            if (_typingIndicator != null)
            {
                MessagesContainer.Children.Remove(_typingIndicator);
                _typingIndicator = null;
            }
        }

        private async void ScrollToBottom()
        {
            await Task.Delay(50);
            await ChatScrollView.ScrollToAsync(0, MessagesContainer.Height, true);
        }
    }
}
