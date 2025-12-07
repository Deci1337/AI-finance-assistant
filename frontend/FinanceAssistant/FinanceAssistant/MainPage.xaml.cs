using FinanceAssistant.Controls;
using FinanceAssistant.Data;
using FinanceAssistant.Models;
using Microsoft.Maui.Controls.Shapes;

namespace FinanceAssistant
{
    public partial class MainPage : ContentPage
    {
        private readonly DatabaseService _databaseService;
        private readonly FinanceChartDrawable _chartDrawable;

        public MainPage(DatabaseService databaseService)
        {
            InitializeComponent();
            _databaseService = databaseService;
            _chartDrawable = new FinanceChartDrawable();
            ChartView.Drawable = _chartDrawable;
        }

        protected override async void OnAppearing()
        {
            base.OnAppearing();
            await LoadDataAsync();
        }

        private async Task LoadDataAsync()
        {
            var profile = await _databaseService.GetUserProfileAsync();
            var transactions = await _databaseService.GetRecentTransactionsAsync(5);
            var chartData = await _databaseService.GetChartDataAsync(7);
            var balance = await _databaseService.GetTotalBalanceAsync();
            var (monthlyIncome, monthlyExpense) = await _databaseService.GetMonthlyTotalsAsync();

            // Update profile
            UserNameLabel.Text = profile.Name;
            BalanceLabel.Text = FormatCurrency(balance);
            IncomeLabel.Text = $"+{FormatCurrency(monthlyIncome)}";
            ExpenseLabel.Text = $"-{FormatCurrency(monthlyExpense)}";

            // Update chart
            _chartDrawable.DataPoints = chartData;
            ChartView.Invalidate();

            // Update transactions
            UpdateTransactionsList(transactions);
        }

        private void UpdateTransactionsList(List<Transaction> transactions)
        {
            TransactionsContainer.Children.Clear();

            if (transactions.Count == 0)
            {
                var emptyLabel = new Label
                {
                    Text = "No transactions yet. Tap + to add one!",
                    TextColor = Color.FromArgb("#8B949E"),
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
                BackgroundColor = Color.FromArgb("#161B22"),
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
                TextColor = Color.FromArgb("#FFFFFF"),
                FontSize = 16,
                FontAttributes = FontAttributes.Bold
            };

            var categoryName = transaction.Category?.Name ?? "Other";
            var importanceText = GetImportanceText(transaction.Importance);
            var categoryLabel = new Label
            {
                Text = $"{categoryName} - {importanceText} - {transaction.Date:dd MMM}",
                TextColor = Color.FromArgb("#8B949E"),
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
                ImportanceLevel.Low => "Low",
                ImportanceLevel.Medium => "Med",
                ImportanceLevel.High => "High",
                ImportanceLevel.Critical => "Crit",
                _ => "Med"
            };
        }

        private static string GetCategoryIcon(string title)
        {
            return title.Length > 0 ? title[0].ToString().ToUpper() : "O";
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
