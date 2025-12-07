using FinanceAssistant.Data;
using FinanceAssistant.Models;
using FinanceAssistant.Services;
using Microsoft.Maui.Controls.Shapes;

namespace FinanceAssistant
{
    public partial class ChatPage : ContentPage
    {
        private readonly FinanceService _financeService;
        private readonly DatabaseService _databaseService;

        public ChatPage(FinanceService financeService, DatabaseService databaseService)
        {
            InitializeComponent();
            _financeService = financeService;
            _databaseService = databaseService;
            
            UpdateConnectionStatus();
            AddWelcomeMessage();
            _ = CheckServerConnectionAsync();
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();
            ScrollToBottom();
            UpdateConnectionStatus();
        }

        private void UpdateConnectionStatus()
        {
            ConnectionStatusLabel.Text = $"Сервер: {_financeService.GetApiBaseUrl()}";
        }

        private async Task CheckServerConnectionAsync()
        {
            var isAvailable = await _financeService.IsServerAvailableAsync();
            MainThread.BeginInvokeOnMainThread(() =>
            {
                if (isAvailable)
                {
                    ConnectionIndicator.Text = "OK";
                    ConnectionIndicator.TextColor = Color.FromArgb("#00D09E");
                }
                else
                {
                    ConnectionIndicator.Text = "Offline";
                    ConnectionIndicator.TextColor = Color.FromArgb("#FF6B6B");
                }
            });
        }

        private async void OnBackTapped(object? sender, TappedEventArgs e)
        {
            await Shell.Current.GoToAsync("..");
        }

        private async void OnTitleTapped(object? sender, TappedEventArgs e)
        {
            await ShowServerSettingsAsync();
        }

        private async void OnSettingsTapped(object? sender, TappedEventArgs e)
        {
            await ShowServerSettingsAsync();
        }

        private async Task ShowServerSettingsAsync()
        {
            string action = await DisplayActionSheet(
                "Настройки сервера", 
                "Отмена", 
                null, 
                "Ввести IP адрес", 
                "Использовать localhost (Windows)",
                "Использовать 10.0.2.2 (Android эмулятор)",
                "Как узнать IP компьютера?",
                "Проверить подключение"
            );

            if (action == "Ввести IP адрес")
            {
                string? ipAddress = await DisplayPromptAsync(
                    "IP адрес сервера", 
                    "Введите IP адрес компьютера с backend\n(например: 192.168.1.100)", 
                    "OK", 
                    "Отмена", 
                    placeholder: "192.168.1.100"
                );
                
                if (!string.IsNullOrWhiteSpace(ipAddress))
                {
                    var ip = ipAddress.Trim();
                    // Add http:// and port if not present
                    if (!ip.StartsWith("http"))
                    {
                        ip = $"http://{ip}";
                    }
                    if (!ip.Contains(":8000"))
                    {
                        ip = $"{ip}:8000";
                    }
                    
                    _financeService.SetApiBaseUrl(ip);
                    UpdateConnectionStatus();
                    await DisplayAlert("Готово", $"Адрес сервера установлен: {ip}", "OK");
                    await CheckServerConnectionAsync();
                }
            }
            else if (action == "Использовать localhost (Windows)")
            {
                _financeService.SetApiBaseUrl("http://localhost:8000");
                UpdateConnectionStatus();
                await CheckServerConnectionAsync();
            }
            else if (action == "Использовать 10.0.2.2 (Android эмулятор)")
            {
                _financeService.SetApiBaseUrl("http://10.0.2.2:8000");
                UpdateConnectionStatus();
                await CheckServerConnectionAsync();
            }
            else if (action == "Как узнать IP компьютера?")
            {
                await DisplayAlert("Как узнать IP",
                    "Windows:\n" +
                    "1. Откройте PowerShell\n" +
                    "2. Введите: ipconfig\n" +
                    "3. Найдите 'IPv4 Address' в секции Wi-Fi или Ethernet\n\n" +
                    "Пример: 192.168.1.100\n\n" +
                    "Важно:\n" +
                    "- Телефон и компьютер должны быть в одной Wi-Fi сети\n" +
                    "- Backend должен быть запущен на компьютере\n" +
                    "- Firewall должен разрешать порт 8000",
                    "OK"
                );
            }
            else if (action == "Проверить подключение")
            {
                var isAvailable = await _financeService.IsServerAvailableAsync();
                if (isAvailable)
                {
                    await DisplayAlert("Подключение", "Сервер доступен!", "OK");
                    ConnectionIndicator.Text = "OK";
                    ConnectionIndicator.TextColor = Color.FromArgb("#00D09E");
                }
                else
                {
                    await DisplayAlert("Ошибка", 
                        $"Не удалось подключиться к серверу:\n{_financeService.GetApiBaseUrl()}\n\n" +
                        "Проверьте:\n" +
                        "1. Backend запущен (python main.py)\n" +
                        "2. Правильный IP адрес\n" +
                        "3. Firewall не блокирует порт 8000",
                        "OK"
                    );
                    ConnectionIndicator.Text = "Offline";
                    ConnectionIndicator.TextColor = Color.FromArgb("#FF6B6B");
                }
            }
        }

        private void AddWelcomeMessage()
        {
            var messageView = CreateBotMessageView(
                "Привет! Я ваш финансовый помощник.\n\n" +
                "Расскажите мне о ваших тратах, и я автоматически добавлю их.\n\n" +
                "Примеры:\n" +
                "- Купил хлеб за 50 рублей\n" +
                "- Получил зарплату 85000\n" +
                "- Потратил 2000 на обед\n\n" +
                "Нажмите * чтобы настроить IP сервера"
            );
            MessagesContainer.Children.Add(messageView);
        }

        private async void OnSendMessage(object? sender, EventArgs e)
        {
            var message = MessageEntry.Text?.Trim();
            if (string.IsNullOrEmpty(message))
                return;

            MessageEntry.Text = string.Empty;
            MessageEntry.IsEnabled = false;

            AddUserMessage(message);
            ScrollToBottom();

            // Analyze friendliness in background
            _ = AnalyzeFriendlinessAsync(message);

            var loadingView = CreateLoadingMessageView();
            MessagesContainer.Children.Add(loadingView);
            ScrollToBottom();

            try
            {
                var result = await _financeService.ExtractTransactionsFromMessageAsync(message);

                MessagesContainer.Children.Remove(loadingView);

                if (result.Transactions != null && result.Transactions.Count > 0)
                {
                    var botResponse = CreateBotMessageView(result.Analysis ?? "Я извлек следующие транзакции:");
                    MessagesContainer.Children.Add(botResponse);
                    ScrollToBottom();

                    foreach (var extractedTransaction in result.Transactions)
                    {
                        if (extractedTransaction != null)
                        {
                            var transactionView = CreateTransactionPreviewView(extractedTransaction, result);
                            MessagesContainer.Children.Add(transactionView);
                            ScrollToBottom();
                        }
                    }

                    if (result.Warnings != null && result.Warnings.Count > 0)
                    {
                        var warningsView = CreateWarningMessageView(result.Warnings);
                        MessagesContainer.Children.Add(warningsView);
                        ScrollToBottom();
                    }
                }
                else
                {
                    var noTransactionsView = CreateBotMessageView(
                        result.Analysis ?? "Не удалось извлечь транзакции.\n\n" +
                        "Попробуйте указать сумму явно, например:\n" +
                        "'Потратил 500 рублей на еду'"
                    );
                    MessagesContainer.Children.Add(noTransactionsView);
                    ScrollToBottom();
                }
            }
            catch (Exception ex)
            {
                MessagesContainer.Children.Remove(loadingView);
                var errorView = CreateBotMessageView($"Ошибка: {ex.Message}\n\nНажмите * для настройки сервера");
                MessagesContainer.Children.Add(errorView);
                ScrollToBottom();
            }

            MessageEntry.IsEnabled = true;
        }

        private void AddUserMessage(string message)
        {
            var messageView = CreateUserMessageView(message);
            MessagesContainer.Children.Add(messageView);
        }

        private View CreateUserMessageView(string message)
        {
            var border = new Border
            {
                BackgroundColor = Color.FromArgb("#238636"),
                StrokeShape = new RoundRectangle { CornerRadius = 15 },
                Stroke = Brush.Transparent,
                Padding = new Thickness(15),
                HorizontalOptions = LayoutOptions.End,
                MaximumWidthRequest = 300
            };

            var label = new Label
            {
                Text = message,
                TextColor = Colors.White,
                FontSize = 14
            };

            border.Content = label;
            return border;
        }

        private View CreateBotMessageView(string message)
        {
            var border = new Border
            {
                BackgroundColor = Color.FromArgb("#161B22"),
                StrokeShape = new RoundRectangle { CornerRadius = 15 },
                Stroke = Brush.Transparent,
                Padding = new Thickness(15),
                HorizontalOptions = LayoutOptions.Start,
                MaximumWidthRequest = 300
            };

            var label = new Label
            {
                Text = message,
                TextColor = Color.FromArgb("#FFFFFF"),
                FontSize = 14
            };

            border.Content = label;
            return border;
        }

        private View CreateLoadingMessageView()
        {
            var border = new Border
            {
                BackgroundColor = Color.FromArgb("#161B22"),
                StrokeShape = new RoundRectangle { CornerRadius = 15 },
                Stroke = Brush.Transparent,
                Padding = new Thickness(15),
                HorizontalOptions = LayoutOptions.Start
            };

            var activityIndicator = new ActivityIndicator
            {
                IsRunning = true,
                Color = Color.FromArgb("#238636")
            };

            border.Content = activityIndicator;
            return border;
        }

        private View CreateTransactionPreviewView(ExtractedTransaction extractedTransaction, TransactionExtractionResult result)
        {
            var border = new Border
            {
                BackgroundColor = Color.FromArgb("#21262D"),
                StrokeShape = new RoundRectangle { CornerRadius = 15 },
                Stroke = Brush.Transparent,
                Padding = new Thickness(15),
                Margin = new Thickness(0, 5, 0, 5)
            };

            var stack = new VerticalStackLayout { Spacing = 10 };

            var grid = new Grid
            {
                ColumnDefinitions = new ColumnDefinitionCollection
                {
                    new ColumnDefinition(GridLength.Star),
                    new ColumnDefinition(GridLength.Auto)
                }
            };

            var titleLabel = new Label
            {
                Text = extractedTransaction.Title,
                TextColor = Color.FromArgb("#FFFFFF"),
                FontSize = 16,
                FontAttributes = FontAttributes.Bold
            };

            var amountLabel = new Label
            {
                Text = extractedTransaction.Amount.HasValue 
                    ? $"{(extractedTransaction.Type == "income" ? "+" : "-")}{FormatCurrency(extractedTransaction.Amount.Value)}"
                    : "Сумма не указана",
                TextColor = extractedTransaction.Type == "income" 
                    ? Color.FromArgb("#00D09E") 
                    : Color.FromArgb("#FF6B6B"),
                FontSize = 16,
                FontAttributes = FontAttributes.Bold
            };

            Grid.SetColumn(titleLabel, 0);
            Grid.SetColumn(amountLabel, 1);

            grid.Children.Add(titleLabel);
            grid.Children.Add(amountLabel);

            var categoryLabel = new Label
            {
                Text = $"{extractedTransaction.Category} - {extractedTransaction.Date}",
                TextColor = Color.FromArgb("#8B949E"),
                FontSize = 12
            };

            stack.Children.Add(grid);
            stack.Children.Add(categoryLabel);

            if (!string.IsNullOrEmpty(extractedTransaction.Description))
            {
                var descLabel = new Label
                {
                    Text = extractedTransaction.Description,
                    TextColor = Color.FromArgb("#8B949E"),
                    FontSize = 12
                };
                stack.Children.Add(descLabel);
            }

            var button = new Button
            {
                Text = "Добавить транзакцию",
                BackgroundColor = Color.FromArgb("#238636"),
                TextColor = Colors.White,
                FontSize = 14,
                Margin = new Thickness(0, 10, 0, 0)
            };

            button.Clicked += async (s, e) =>
            {
                await AddTransactionFromExtracted(extractedTransaction);
            };

            stack.Children.Add(button);

            border.Content = stack;
            return border;
        }

        private async Task AddTransactionFromExtracted(ExtractedTransaction extractedTransaction)
        {
            if (!extractedTransaction.Amount.HasValue)
            {
                await DisplayAlert("Ошибка", "Нельзя добавить транзакцию без суммы", "OK");
                return;
            }

            // Get or create category in database
            var transactionType = extractedTransaction.Type == "income" ? TransactionType.Income : TransactionType.Expense;
            var categoryName = MapCategory(extractedTransaction.Category);
            var category = await _databaseService.GetOrCreateCategoryAsync(categoryName, transactionType);

            var transaction = new Transaction
            {
                Title = extractedTransaction.Title,
                Amount = extractedTransaction.Amount.Value,
                Type = transactionType,
                CategoryId = category.Id,
                Date = DateTime.TryParse(extractedTransaction.Date, out var date) ? date : DateTime.Now,
                Description = extractedTransaction.Description
            };

            await _databaseService.SaveTransactionAsync(transaction);

            var successView = CreateBotMessageView($"Транзакция '{transaction.Title}' успешно добавлена!");
            MessagesContainer.Children.Add(successView);
            ScrollToBottom();

            await DisplayAlert("Успешно", "Транзакция добавлена", "OK");
        }

        private string MapCategory(string category)
        {
            return category.ToLower() switch
            {
                "food" => "Food",
                "transport" => "Transport",
                "entertainment" => "Entertainment",
                "health" => "Health",
                "shopping" => "Shopping",
                "housing" => "Housing",
                "work" => "Work",
                "freelance" => "Work",
                "bills" => "Bills",
                _ => "Other"
            };
        }

        private View CreateWarningMessageView(List<string> warnings)
        {
            var border = new Border
            {
                BackgroundColor = Color.FromArgb("#3D2117"),
                StrokeShape = new RoundRectangle { CornerRadius = 15 },
                Stroke = Brush.Transparent,
                Padding = new Thickness(15),
                HorizontalOptions = LayoutOptions.Start,
                MaximumWidthRequest = 300
            };

            var stack = new VerticalStackLayout { Spacing = 5 };

            var titleLabel = new Label
            {
                Text = "Предупреждения:",
                TextColor = Color.FromArgb("#FF6B6B"),
                FontSize = 14,
                FontAttributes = FontAttributes.Bold
            };

            stack.Children.Add(titleLabel);

            foreach (var warning in warnings)
            {
                var warningLabel = new Label
                {
                    Text = $"- {warning}",
                    TextColor = Color.FromArgb("#FF6B6B"),
                    FontSize = 12
                };
                stack.Children.Add(warningLabel);
            }

            border.Content = stack;
            return border;
        }

        private void ScrollToBottom()
        {
            MainThread.BeginInvokeOnMainThread(async () =>
            {
                await Task.Delay(100);
                await MessagesScrollView.ScrollToAsync(MessagesContainer, ScrollToPosition.End, false);
            });
        }

        private static string FormatCurrency(decimal amount)
        {
            return $"{amount:N0} RUB".Replace(",", " ");
        }

        /// <summary>
        /// Analyze friendliness of user message and update profile
        /// </summary>
        private async Task AnalyzeFriendlinessAsync(string message)
        {
            try
            {
                var result = await _financeService.AnalyzeFriendlinessAsync(message);
                if (result != null)
                {
                    var profile = await _databaseService.GetUserProfileAsync();
                    
                    // Update friendliness using weighted average
                    // New messages have more weight for recent behavior
                    int totalMessages = profile.MessagesAnalyzed + 1;
                    double weight = Math.Min(0.3, 1.0 / totalMessages); // Max 30% weight for new message
                    
                    profile.Friendliness = profile.Friendliness * (1 - weight) + result.FriendlinessScore * weight;
                    profile.MessagesAnalyzed = totalMessages;
                    
                    await _databaseService.SaveUserProfileAsync(profile);
                    
                    System.Diagnostics.Debug.WriteLine($"Friendliness updated: {result.FriendlinessScore} -> avg: {profile.Friendliness}");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error analyzing friendliness: {ex.Message}");
            }
        }
    }
}
