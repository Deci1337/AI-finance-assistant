using FinanceAssistant.Controls;
using FinanceAssistant.Data;
using FinanceAssistant.Models;
using FinanceAssistant.Services;
using Microsoft.Maui.Controls.Shapes;

namespace FinanceAssistant
{
    public partial class MainPage : ContentPage
    {
        private readonly DatabaseService _databaseService;
        private readonly FinanceService _financeService;
        private readonly AchievementService _achievementService;
        private readonly FinanceChartDrawable _chartDrawable;

        public MainPage(DatabaseService databaseService, FinanceService financeService, AchievementService achievementService)
        {
            InitializeComponent();
            _databaseService = databaseService;
            _financeService = financeService;
            _achievementService = achievementService;
            _chartDrawable = new FinanceChartDrawable();
            ChartView.Drawable = _chartDrawable;
        }

        protected override async void OnAppearing()
        {
            base.OnAppearing();
            await LoadDataAsync();
            
            // Show any pending achievements
            await ShowPendingAchievementsAsync();
        }
        
        private async Task ShowPendingAchievementsAsync()
        {
            while (_achievementService.HasPendingAchievements)
            {
                var achievement = _achievementService.GetNextPendingAchievement();
                if (achievement != null)
                {
                    await ShowAchievementNotificationAsync(achievement);
                }
            }
        }
        
        private async Task ShowAchievementNotificationAsync(Achievement achievement)
        {
            // Create notification popup
            var notification = new Border
            {
                BackgroundColor = Color.FromArgb("#1F2937"),
                StrokeShape = new RoundRectangle { CornerRadius = 20 },
                Stroke = Color.FromArgb("#00D09E"),
                StrokeThickness = 2,
                Padding = new Thickness(20, 15),
                HorizontalOptions = LayoutOptions.Center,
                VerticalOptions = LayoutOptions.End,
                Margin = new Thickness(20, 0, 20, 120),
                TranslationY = 200,
                Opacity = 0,
                ZIndex = 999
            };

            notification.Shadow = new Shadow
            {
                Brush = Color.FromArgb("#00D09E"),
                Offset = new Point(0, 0),
                Radius = 20,
                Opacity = 0.6f
            };

            var content = new HorizontalStackLayout
            {
                Spacing = 15,
                HorizontalOptions = LayoutOptions.Center
            };

            var emoji = new Label
            {
                Text = achievement.Emoji,
                FontSize = 36,
                VerticalOptions = LayoutOptions.Center
            };

            var textStack = new VerticalStackLayout
            {
                Spacing = 2,
                VerticalOptions = LayoutOptions.Center
            };

            textStack.Children.Add(new Label
            {
                Text = "Достижение получено!",
                FontSize = 12,
                TextColor = Color.FromArgb("#00D09E"),
                FontAttributes = FontAttributes.Bold
            });

            textStack.Children.Add(new Label
            {
                Text = achievement.Name,
                FontSize = 18,
                TextColor = Colors.White,
                FontAttributes = FontAttributes.Bold
            });

            textStack.Children.Add(new Label
            {
                Text = achievement.Description,
                FontSize = 12,
                TextColor = Color.FromArgb("#9CA3AF")
            });
            
            content.Children.Add(emoji);
            content.Children.Add(textStack);
            notification.Content = content;

            // Add to page
            if (Content is Grid grid)
            {
                grid.Children.Add(notification);
                Grid.SetRowSpan(notification, 99);
            }

            // Animate in
            await Task.WhenAll(
                notification.TranslateTo(0, 0, 400, Easing.SpringOut),
                notification.FadeTo(1, 300)
            );

            // Wait
            await Task.Delay(3500);

            // Animate out
            await Task.WhenAll(
                notification.TranslateTo(0, 200, 300, Easing.CubicIn),
                notification.FadeTo(0, 300)
            );

            // Remove
            if (Content is Grid g)
            {
                g.Children.Remove(notification);
            }
        }

        private async Task LoadDataAsync()
        {
            var profile = await _databaseService.GetUserProfileAsync();
            var transactions = await _databaseService.GetRecentTransactionsAsync(5);
            var chartData = await _databaseService.GetChartDataAsync(7);
            var (totalIncome, totalExpense) = await _databaseService.GetTotalStatsAsync();
            var balance = totalIncome - totalExpense;

            // Update profile
            UserNameLabel.Text = profile.Name;
            BalanceLabel.Text = FormatCurrency(balance);
            IncomeLabel.Text = $"+{FormatCurrency(totalIncome)}";
            ExpenseLabel.Text = $"-{FormatCurrency(totalExpense)}";

            // Update chart
            _chartDrawable.DataPoints = chartData;
            ChartView.Invalidate();

            // Update transactions
            UpdateTransactionsList(transactions);

            // Load AI insights
            await LoadInsightsAsync(transactions);
        }

        private async Task LoadInsightsAsync(List<Transaction> recentTransactions)
        {
            try
            {
                // Получаем все транзакции текущего месяца для анализа
                var allTransactions = await _databaseService.GetTransactionsAsync();
                var currentMonthTransactions = allTransactions
                    .Where(t => t.Date.Month == DateTime.Now.Month && t.Date.Year == DateTime.Now.Year)
                    .ToList();

                if (currentMonthTransactions.Count < 3)
                {
                    InsightsWidget.IsVisible = false;
                    return;
                }

                // Преобразуем транзакции в формат для API
                var transactionsData = currentMonthTransactions.Select(t => new Dictionary<string, object>
                {
                    { "title", t.Title },
                    { "amount", (double)t.Amount },
                    { "category", t.Category?.Name ?? "Other" },
                    { "date", t.Date.ToString("yyyy-MM-dd") },
                    { "importance", t.Importance.ToString().ToLower() },
                    { "type", t.Type == TransactionType.Expense ? "expense" : "income" }
                }).ToList();

                var currentMonth = DateTime.Now.ToString("yyyy-MM");
                var insight = await _financeService.GetInsightsAsync(transactionsData, currentMonth);

                if (insight != null && !string.IsNullOrEmpty(insight.Insight))
                {
                    InsightsWidget.IsVisible = true;
                    InsightText.Text = insight.Insight;
                    
                    // Добавляем аналитику
                    await UpdateInsightAnalyticsAsync(insight, currentMonthTransactions);
                }
                else
                {
                    InsightsWidget.IsVisible = false;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading insights: {ex.Message}");
                InsightsWidget.IsVisible = false;
            }
        }

        private void UpdateTransactionsList(List<Transaction> transactions)
        {
            TransactionsContainer.Children.Clear();

            if (transactions.Count == 0)
            {
                var emptyLabel = new Label
                {
                    Text = "Пока нет транзакций. Нажми + чтобы добавить!",
                    TextColor = ThemeService.GetTextSecondary(),
                    FontSize = 14,
                    HorizontalOptions = LayoutOptions.Center,
                    Margin = new Thickness(0, 20)
                };
                TransactionsContainer.Children.Add(emptyLabel);
                return;
            }

            foreach (var transaction in transactions)
            {
                var transactionView = CreateTransactionView(transaction);
                TransactionsContainer.Children.Add(transactionView);
            }
        }

        private View CreateTransactionView(Transaction transaction)
        {
            var isIncome = transaction.Type == TransactionType.Income;
            var amountColor = isIncome ? Color.FromArgb("#00D09E") : Color.FromArgb("#FF6B6B");
            var amountPrefix = isIncome ? "+" : "-";
            var iconText = transaction.Category?.Icon ?? GetCategoryIcon(transaction.Title);
            var categoryColor = transaction.Category?.ColorHex ?? "#8B949E";

            var border = new Border
            {
                BackgroundColor = ThemeService.GetBackgroundCard(),
                StrokeShape = new RoundRectangle { CornerRadius = 15 },
                Stroke = Brush.Transparent,
                Padding = new Thickness(15)
            };

            var grid = new Grid
            {
                ColumnDefinitions = new ColumnDefinitionCollection
                {
                    new ColumnDefinition(GridLength.Auto),
                    new ColumnDefinition(GridLength.Star),
                    new ColumnDefinition(GridLength.Auto)
                }
            };

            // Category icon
            var iconBorder = new Border
            {
                BackgroundColor = Color.FromArgb(categoryColor).WithAlpha(0.2f),
                StrokeShape = new RoundRectangle { CornerRadius = 12 },
                Stroke = Brush.Transparent,
                HeightRequest = 44,
                WidthRequest = 44,
                VerticalOptions = LayoutOptions.Center
            };

            var iconLabel = new Label
            {
                Text = iconText,
                TextColor = Color.FromArgb(categoryColor),
                FontSize = 16,
                FontAttributes = FontAttributes.Bold,
                HorizontalOptions = LayoutOptions.Center,
                VerticalOptions = LayoutOptions.Center
            };
            iconBorder.Content = iconLabel;

            // Transaction info
            var infoStack = new VerticalStackLayout
            {
                Margin = new Thickness(12, 0, 0, 0),
                VerticalOptions = LayoutOptions.Center
            };

            var titleLabel = new Label
            {
                Text = transaction.Title,
                TextColor = ThemeService.GetTextPrimary(),
                FontSize = 16,
                FontAttributes = FontAttributes.Bold
            };

            var categoryName = transaction.Category?.Name ?? "Other";
            var importanceText = GetImportanceText(transaction.Importance);
            var categoryLabel = new Label
            {
                Text = $"{categoryName} - {importanceText} - {transaction.Date:dd MMM}",
                TextColor = ThemeService.GetTextSecondary(),
                FontSize = 12
            };

            infoStack.Children.Add(titleLabel);
            infoStack.Children.Add(categoryLabel);

            // Amount
            var amountLabel = new Label
            {
                Text = $"{amountPrefix}{FormatCurrency(transaction.Amount)}",
                TextColor = amountColor,
                FontSize = 16,
                FontAttributes = FontAttributes.Bold,
                VerticalOptions = LayoutOptions.Center
            };

            Grid.SetColumn(iconBorder, 0);
            Grid.SetColumn(infoStack, 1);
            Grid.SetColumn(amountLabel, 2);

            grid.Children.Add(iconBorder);
            grid.Children.Add(infoStack);
            grid.Children.Add(amountLabel);

            border.Content = grid;
            return border;
        }

        private static string GetImportanceText(ImportanceLevel importance)
        {
            return importance switch
            {
                ImportanceLevel.Low => "Низк",
                ImportanceLevel.Medium => "Сред",
                ImportanceLevel.High => "Выс",
                ImportanceLevel.Critical => "Крит",
                _ => "Сред"
            };
        }

        private static string GetCategoryIcon(string title)
        {
            return title.Length > 0 ? title[0].ToString().ToUpper() : "O";
        }

        private async Task UpdateInsightAnalyticsAsync(Services.InsightResult insight, List<Transaction> transactions)
        {
            var analyticsContainer = this.FindByName<VerticalStackLayout>("AnalyticsContainer");
            if (analyticsContainer == null) return;
            
            analyticsContainer.Children.Clear();
            
            if (string.IsNullOrEmpty(insight.Category)) return;
            
            // Фильтруем транзакции по категории
            var categoryTransactions = transactions
                .Where(t => t.Category?.Name == insight.Category && t.Type == TransactionType.Expense)
                .ToList();
            
            // Статистика по категории
            var totalAmount = categoryTransactions.Sum(t => t.Amount);
            var transactionCount = categoryTransactions.Count;
            var lowImportanceCount = categoryTransactions.Count(t => t.Importance == ImportanceLevel.Low);
            
            // Сравнение с предыдущим месяцем
            var previousMonth = DateTime.Now.AddMonths(-1);
            var previousMonthTransactions = await _databaseService.GetTransactionsAsync();
            var previousMonthCategoryTransactions = previousMonthTransactions
                .Where(t => t.Date.Month == previousMonth.Month && 
                           t.Date.Year == previousMonth.Year &&
                           t.Category?.Name == insight.Category &&
                           t.Type == TransactionType.Expense)
                .ToList();
            var previousMonthAmount = previousMonthCategoryTransactions.Sum(t => t.Amount);
            
            // Процент от общих расходов
            var currentMonthExpenses = transactions
                .Where(t => t.Type == TransactionType.Expense)
                .Sum(t => t.Amount);
            var percentOfTotal = currentMonthExpenses > 0 
                ? (totalAmount / currentMonthExpenses * 100) 
                : 0;
            
            // Основная статистика
            var statsGrid = new Grid
            {
                ColumnDefinitions = new ColumnDefinitionCollection
                {
                    new ColumnDefinition(GridLength.Star),
                    new ColumnDefinition(GridLength.Star)
                },
                RowDefinitions = new RowDefinitionCollection
                {
                    new RowDefinition(GridLength.Auto),
                    new RowDefinition(GridLength.Auto)
                }
            };
            
            // Сумма
            var amountLabel = new Label
            {
                Text = $"Всего: {FormatCurrency(totalAmount)}",
                TextColor = Color.FromArgb("#FFFFFF"),
                FontSize = 16,
                FontAttributes = FontAttributes.Bold
            };
            Grid.SetRow(amountLabel, 0);
            Grid.SetColumn(amountLabel, 0);
            
            // Количество покупок
            var countLabel = new Label
            {
                Text = $"Покупок: {transactionCount}",
                TextColor = Color.FromArgb("#8B949E"),
                FontSize = 14
            };
            Grid.SetRow(countLabel, 1);
            Grid.SetColumn(countLabel, 0);
            
            // Процент от общих расходов
            var percentLabel = new Label
            {
                Text = $"{percentOfTotal:F1}% от расходов",
                TextColor = Color.FromArgb("#FF6B6B"),
                FontSize = 16,
                FontAttributes = FontAttributes.Bold,
                HorizontalOptions = LayoutOptions.End
            };
            Grid.SetRow(percentLabel, 0);
            Grid.SetColumn(percentLabel, 1);
            
            // Необязательные покупки
            var lowImportanceLabel = new Label
            {
                Text = $"Необязательных: {lowImportanceCount} ({insight.LowImportancePercent ?? 0:F1}%)",
                TextColor = Color.FromArgb("#8B949E"),
                FontSize = 14,
                HorizontalOptions = LayoutOptions.End
            };
            Grid.SetRow(lowImportanceLabel, 1);
            Grid.SetColumn(lowImportanceLabel, 1);
            
            statsGrid.Children.Add(amountLabel);
            statsGrid.Children.Add(countLabel);
            statsGrid.Children.Add(percentLabel);
            statsGrid.Children.Add(lowImportanceLabel);
            
            analyticsContainer.Children.Add(statsGrid);
            
            // Сравнение с предыдущим месяцем
            if (previousMonthAmount > 0)
            {
                var comparison = totalAmount - previousMonthAmount;
                var comparisonPercent = (comparison / previousMonthAmount * 100);
                var comparisonColor = comparison > 0 ? Color.FromArgb("#FF6B6B") : Color.FromArgb("#00D09E");
                var comparisonText = comparison > 0 ? "больше" : "меньше";
                
                var comparisonLabel = new Label
                {
                    Text = $"По сравнению с прошлым месяцем: {FormatCurrency(Math.Abs(comparison))} {comparisonText} ({Math.Abs(comparisonPercent):F1}%)",
                    TextColor = comparisonColor,
                    FontSize = 13,
                    Margin = new Thickness(0, 10, 0, 0)
                };
                analyticsContainer.Children.Add(comparisonLabel);
            }
        }

        private static string FormatCurrency(decimal amount)
        {
            return $"{amount:N0} RUB".Replace(",", " ");
        }

        private async void OnProfileTapped(object? sender, EventArgs e)
        {
            await Shell.Current.GoToAsync("ProfilePage");
        }

        private async void OnChatTapped(object? sender, EventArgs e)
        {
            // Navigate to ChatPage (new AI extraction chat)
            await Shell.Current.GoToAsync("ChatPage");
        }

        private async void OnAddTransactionTapped(object? sender, EventArgs e)
        {
            await Shell.Current.GoToAsync("AddTransactionPage");
        }

        private async void OnStatsTapped(object? sender, EventArgs e)
        {
            await Shell.Current.GoToAsync("StatisticsPage");
        }

        private async void OnSeeAllTapped(object? sender, EventArgs e)
        {
            await DisplayAlert("Все транзакции", "Полная история транзакций будет доступна в ближайшее время", "ОК");
        }
    }
}
