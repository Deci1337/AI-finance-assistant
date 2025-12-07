using FinanceAssistant.Data;
using FinanceAssistant.Models;
using FinanceAssistant.Services;
using Microsoft.Maui.Controls.Shapes;
using System.Text.RegularExpressions;
using Microsoft.Maui.Media;

namespace FinanceAssistant
{
    public partial class ChatPage : ContentPage
    {
        private readonly FinanceService _financeService;
        private readonly DatabaseService _databaseService;
        private bool _isRecording = false;
        private string? _currentAudioPath = null;

        public ChatPage(FinanceService financeService, DatabaseService databaseService)
        {
            InitializeComponent();
            _financeService = financeService;
            _databaseService = databaseService;
            
            AddWelcomeMessage();
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();
            ScrollToBottom();
        }

        private async void OnBackTapped(object? sender, EventArgs e)
        {
            await Shell.Current.GoToAsync("..");
        }

        private async void OnTitleTapped(object? sender, EventArgs e)
        {
            await ShowServerSettingsAsync();
        }

        private async void OnSettingsTapped(object? sender, EventArgs e)
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
                "Как узнать IP компьютера?"
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
                    if (!ip.StartsWith("http"))
                        ip = $"http://{ip}";
                    if (!ip.Contains(":8000"))
                        ip = $"{ip}:8000";
                    
                    Preferences.Set("api_base_url", ip);
                    await DisplayAlert("Готово", $"Адрес сервера: {ip}\n\nПерезапустите чат для применения.", "OK");
                }
            }
            else if (action == "Использовать localhost (Windows)")
            {
                Preferences.Set("api_base_url", "http://localhost:8000");
                await DisplayAlert("Готово", "Установлен localhost:8000", "OK");
            }
            else if (action == "Использовать 10.0.2.2 (Android эмулятор)")
            {
                Preferences.Set("api_base_url", "http://10.0.2.2:8000");
                await DisplayAlert("Готово", "Установлен 10.0.2.2:8000", "OK");
            }
            else if (action == "Как узнать IP компьютера?")
            {
                await DisplayAlert("Как узнать IP",
                    "Windows:\n" +
                    "1. Откройте PowerShell\n" +
                    "2. Введите: ipconfig\n" +
                    "3. Найдите 'IPv4 Address'\n\n" +
                    "Пример: 192.168.1.100\n\n" +
                    "Важно:\n" +
                    "- Телефон и ПК в одной Wi-Fi сети\n" +
                    "- Backend запущен (python main.py)",
                    "OK"
                );
            }
        }

        private void AddWelcomeMessage()
        {
            var messageView = CreateBotMessageView(
                "Привет! Я ваш финансовый помощник.\n\n" +
                "Вы можете:\n" +
                "- Задавать любые вопросы о финансах\n" +
                "- Добавлять транзакции голосом\n\n" +
                "Примеры транзакций:\n" +
                "- Купил хлеб за 50 рублей\n" +
                "- Получил зарплату 85000\n\n" +
                "Примеры вопросов:\n" +
                "- Как экономить деньги?\n" +
                "- Что такое инвестиции?"
            );
            MessagesContainer.Children.Add(messageView);
        }

        private bool IsTransactionMessage(string message)
        {
            var messageLower = message.ToLower();
            
            var transactionKeywords = new[]
            {
                "потратил", "потратила", "потратили",
                "купил", "купила", "купили", "купить",
                "заплатил", "заплатила", "заплатили",
                "трата", "траты", "расход", "расходы",
                "получил", "получила", "получили",
                "заработал", "заработала", "заработали",
                "доход", "зарплата", "зарплату", "прибыль",
                "добавь", "добавить", "запиши", "записать", "внеси"
            };
            
            bool hasTransactionKeyword = transactionKeywords.Any(k => messageLower.Contains(k));
            
            var amountPatterns = new[]
            {
                @"\d+\s*(рубл|rub|р\.|руб)",
                @"\d+\s*(тысяч|тыс|к)",
                @"\d+\s*(доллар|usd|\$|бакс)",
                @"\d+\s*(евро|eur)"
            };
            
            bool hasAmount = amountPatterns.Any(p => 
                Regex.IsMatch(messageLower, p, RegexOptions.IgnoreCase));
            
            return hasTransactionKeyword || hasAmount;
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
                if (IsTransactionMessage(message))
                {
                    // Handle as transaction
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
                else
                {
                    // Handle as general chat
                    var chatResult = await _financeService.SendChatMessageAsync(message);
                    MessagesContainer.Children.Remove(loadingView);

                    var botResponse = CreateBotMessageView(chatResult.Response);
                    MessagesContainer.Children.Add(botResponse);
                    ScrollToBottom();
                }
            }
            catch (Exception ex)
            {
                MessagesContainer.Children.Remove(loadingView);
                var errorView = CreateBotMessageView($"Произошла ошибка: {ex.Message}");
                MessagesContainer.Children.Add(errorView);
                ScrollToBottom();
            }

            MessageEntry.IsEnabled = true;
        }

        private async Task AnalyzeFriendlinessAsync(string message)
        {
            try
            {
                var result = await _financeService.AnalyzeFriendlinessAsync(message);
                if (result != null)
                {
                    var profile = await _databaseService.GetUserProfileAsync();
                    
                    // Update friendliness using weighted average
                    int totalMessages = profile.MessagesAnalyzed + 1;
                    double weight = Math.Min(0.3, 1.0 / totalMessages);
                    
                    profile.Friendliness = profile.Friendliness * (1 - weight) + result.FriendlinessScore * weight;
                    profile.MessagesAnalyzed = totalMessages;
                    
                    await _databaseService.SaveUserProfileAsync(profile);
                    
                    System.Diagnostics.Debug.WriteLine($"Friendliness updated: {result.FriendlinessScore:F2} -> avg: {profile.Friendliness:F2}");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error analyzing friendliness: {ex.Message}");
            }
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

        private View CreateTransactionPreviewView(FinanceAssistant.Services.ExtractedTransaction extractedTransaction, FinanceAssistant.Services.TransactionExtractionResult result)
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
                Text = $"{extractedTransaction.Category} • {extractedTransaction.Date}",
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

        private async Task AddTransactionFromExtracted(FinanceAssistant.Services.ExtractedTransaction extractedTransaction)
        {
            if (!extractedTransaction.Amount.HasValue)
            {
                await DisplayAlert("Ошибка", "Нельзя добавить транзакцию без суммы", "ОК");
                return;
            }

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

            await DisplayAlert("Успешно", "Транзакция добавлена", "ОК");
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
                    Text = $"• {warning}",
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

        private async void OnMicrophoneTapped(object? sender, EventArgs e)
        {
            if (_isRecording)
            {
                // Второе нажатие - пытаемся остановить запись
                // MediaPicker управляет записью через системный диалог,
                // поэтому просто показываем подсказку
                return;
            }

            try
            {
                var status = await Permissions.RequestAsync<Permissions.Microphone>();
                if (status != PermissionStatus.Granted)
                {
                    await DisplayAlert("Ошибка", "Необходимо разрешение на использование микрофона", "OK");
                    return;
                }

                _isRecording = true;
                MicrophoneIcon.Text = "⏹";
                // TODO: Audio recording requires platform-specific implementation
                // CaptureAudioAsync is not available in MAUI's MediaPicker
                var notImplementedMessage = CreateBotMessageView("Голосовой ввод пока недоступен. Введите текст вручную.");
                MessagesContainer.Children.Add(notImplementedMessage);
                ScrollToBottom();
                
                _isRecording = false;
                MicrophoneIcon.Text = "🎤";
                MicrophoneButton.BackgroundColor = Color.FromArgb("#21262D");
            }
            catch (Exception ex)
            {
                _isRecording = false;
                MicrophoneIcon.Text = "🎤";
                MicrophoneButton.BackgroundColor = Color.FromArgb("#21262D");
                
                var errorMessage = CreateBotMessageView($"❌ Ошибка записи: {ex.Message}");
                MessagesContainer.Children.Add(errorMessage);
                ScrollToBottom();
            }
        }

        private async Task ProcessAudioRecordingAsync(FileResult recording)
        {
            try
            {
                var statusMessage = CreateBotMessageView("🔄 Обработка аудио...");
                MessagesContainer.Children.Add(statusMessage);
                ScrollToBottom();

                // Читаем аудио файл
                using var audioStream = await recording.OpenReadAsync();
                var transcriptionResult = await _financeService.TranscribeAudioAsync(audioStream, recording.FileName ?? "audio.wav");

                // Удаляем статусное сообщение
                MessagesContainer.Children.Remove(statusMessage);

                if (!string.IsNullOrEmpty(transcriptionResult.Error))
                {
                    var errorMessage = CreateBotMessageView($"❌ Ошибка: {transcriptionResult.Error}");
                    MessagesContainer.Children.Add(errorMessage);
                    ScrollToBottom();
                    return;
                }

                if (string.IsNullOrWhiteSpace(transcriptionResult.Text))
                {
                    var errorMessage = CreateBotMessageView("❌ Не удалось распознать речь. Попробуйте еще раз.");
                    MessagesContainer.Children.Add(errorMessage);
                    ScrollToBottom();
                    return;
                }

                // Показываем распознанный текст как сообщение пользователя
                AddUserMessage(transcriptionResult.Text);
                ScrollToBottom();

                // Обрабатываем распознанный текст как обычное сообщение
                await ProcessMessageAsync(transcriptionResult.Text);
            }
            catch (Exception ex)
            {
                var errorMessage = CreateBotMessageView($"❌ Ошибка обработки аудио: {ex.Message}");
                MessagesContainer.Children.Add(errorMessage);
                ScrollToBottom();
            }
        }

        private async Task ProcessMessageAsync(string message)
        {
            MessageEntry.IsEnabled = false;

            // Analyze friendliness in background
            _ = AnalyzeFriendlinessAsync(message);

            var loadingView = CreateLoadingMessageView();
            MessagesContainer.Children.Add(loadingView);
            ScrollToBottom();

            try
            {
                if (IsTransactionMessage(message))
                {
                    // Handle as transaction
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
                else
                {
                    // Handle as general chat
                    var chatResult = await _financeService.SendChatMessageAsync(message);
                    MessagesContainer.Children.Remove(loadingView);

                    var botResponse = CreateBotMessageView(chatResult.Response);
                    MessagesContainer.Children.Add(botResponse);
                    ScrollToBottom();
                }
            }
            catch (Exception ex)
            {
                MessagesContainer.Children.Remove(loadingView);
                var errorView = CreateBotMessageView($"Произошла ошибка: {ex.Message}");
                MessagesContainer.Children.Add(errorView);
                ScrollToBottom();
            }

            MessageEntry.IsEnabled = true;
        }
    }
}

