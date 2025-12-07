using FinanceAssistant.Models;
using FinanceAssistant.Services;
using Microsoft.Maui.Controls.Shapes;
using Microsoft.Maui.Media;

namespace FinanceAssistant
{
    public partial class ChatPage : ContentPage
    {
        private readonly FinanceService _financeService;
        private bool _isRecording = false;

        public ChatPage()
        {
            InitializeComponent();
            _financeService = new FinanceService();
            
            AddWelcomeMessage();
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();
            ScrollToBottom();
        }

        private void AddWelcomeMessage()
        {
            var messageView = CreateBotMessageView(
                "Привет! Я ваш финансовый помощник. " +
                "Просто расскажите мне о ваших доходах и расходах, и я автоматически добавлю их в ваш список транзакций.\n\n" +
                "Примеры:\n" +
                "• Купил хлеб за 50 рублей и молоко за 80 рублей\n" +
                "• Получил зарплату 85000 рублей\n" +
                "• Вчера потратил 2000 на обед в ресторане"
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
                        "Не удалось извлечь транзакции из вашего сообщения. " +
                        "Попробуйте указать сумму и тип транзакции более явно.\n\n" +
                        (result.Questions != null && result.Questions.Count > 0 
                            ? string.Join("\n", result.Questions.Select(q => $"• {q}"))
                            : "")
                    );
                    MessagesContainer.Children.Add(noTransactionsView);
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

        private View CreateTransactionPreviewView(FinanceAssistant.Services.ExtractedTransaction extractedTransaction, object result)
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

            var transaction = new Transaction
            {
                Title = extractedTransaction.Title,
                Amount = extractedTransaction.Amount.Value,
                Type = extractedTransaction.Type == "income" ? TransactionType.Income : TransactionType.Expense,
                Category = MapCategory(extractedTransaction.Category),
                Date = DateTime.TryParse(extractedTransaction.Date, out var date) ? date : DateTime.Now,
                Description = extractedTransaction.Description
            };

            await _financeService.AddTransactionAsync(transaction);

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
                await StopRecording();
            }
            else
            {
                await StartRecording();
            }
        }

        private async Task StartRecording()
        {
            try
            {
                var status = await Permissions.RequestAsync<Permissions.Microphone>();
                if (status != PermissionStatus.Granted)
                {
                    await DisplayAlert("Ошибка", "Необходимо разрешение на использование микрофона", "ОК");
                    return;
                }

                _isRecording = true;
                MicrophoneIcon.Text = "⏹";
                MicrophoneIcon.TextColor = Color.FromArgb("#FF6B6B");

                var recordingView = CreateBotMessageView("Запись начата... Говорите.");
                MessagesContainer.Children.Add(recordingView);
                ScrollToBottom();

                var audioFile = await MediaPicker.CaptureAudioAsync();
                
                if (audioFile != null)
                {
                    await ProcessAudioFile(audioFile);
                }
                else
                {
                    var cancelView = CreateBotMessageView("Запись отменена");
                    MessagesContainer.Children.Add(cancelView);
                    ScrollToBottom();
                }
            }
            catch (Exception ex)
            {
                var errorView = CreateBotMessageView($"Ошибка при записи: {ex.Message}");
                MessagesContainer.Children.Add(errorView);
                ScrollToBottom();
            }
            finally
            {
                _isRecording = false;
                MicrophoneIcon.Text = "🎤";
                MicrophoneIcon.TextColor = Color.FromArgb("#FFFFFF");
            }
        }

        private async Task StopRecording()
        {
            _isRecording = false;
            MicrophoneIcon.Text = "🎤";
            MicrophoneIcon.TextColor = Color.FromArgb("#FFFFFF");
        }

        private async Task ProcessAudioFile(FileResult audioFile)
        {
            try
            {
                var loadingView = CreateLoadingMessageView();
                MessagesContainer.Children.Add(loadingView);
                ScrollToBottom();

                var result = await _financeService.TranscribeAndExtractAsync(audioFile);

                MessagesContainer.Children.Remove(loadingView);

                if (result.Success && !string.IsNullOrEmpty(result.Transcription))
                {
                    AddUserMessage($"[Голосовое сообщение]");
                    
                    var transcriptionView = CreateBotMessageView($"Распознано: {result.Transcription}");
                    MessagesContainer.Children.Add(transcriptionView);
                    ScrollToBottom();

                    if (result.Transactions != null && result.Transactions.Count > 0)
                    {
                        var botResponse = CreateBotMessageView(result.Analysis ?? "Я извлек следующие транзакции:");
                        MessagesContainer.Children.Add(botResponse);
                        ScrollToBottom();

                        foreach (var extractedTransaction in result.Transactions)
                        {
                            if (extractedTransaction != null)
                            {
                                var transactionView = CreateTransactionPreviewView(extractedTransaction, new { });
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
                            "Не удалось извлечь транзакции из вашего сообщения. " +
                            "Попробуйте указать сумму и тип транзакции более явно."
                        );
                        MessagesContainer.Children.Add(noTransactionsView);
                        ScrollToBottom();
                    }
                }
                else
                {
                    var errorView = CreateBotMessageView(
                        result.Error ?? "Не удалось распознать речь. Попробуйте еще раз."
                    );
                    MessagesContainer.Children.Add(errorView);
                    ScrollToBottom();
                }
            }
            catch (Exception ex)
            {
                var errorView = CreateBotMessageView($"Ошибка при обработке аудио: {ex.Message}");
                MessagesContainer.Children.Add(errorView);
                ScrollToBottom();
            }
        }
    }
}

