using FinanceAssistant.Controls;
using FinanceAssistant.Models;
using FinanceAssistant.Services;
using Microsoft.Maui.Controls.Shapes;

namespace FinanceAssistant
{
    public partial class MainPage : ContentPage
    {
        private readonly FinanceService _financeService;
        private readonly FinanceChartDrawable _chartDrawable;

        public MainPage()
        {
            InitializeComponent();
            _financeService = new FinanceService();
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
            var profile = await _financeService.GetUserProfileAsync();
            var transactions = await _financeService.GetRecentTransactionsAsync(5);
            var chartData = await _financeService.GetChartDataAsync(7);

            // Update profile
            UserNameLabel.Text = profile.Name;
            BalanceLabel.Text = FormatCurrency(profile.TotalBalance);
            IncomeLabel.Text = $"+{FormatCurrency(profile.MonthlyIncome)}";
            ExpenseLabel.Text = $"-{FormatCurrency(profile.MonthlyExpense)}";

            // Update chart
            _chartDrawable.DataPoints = chartData;
            ChartView.Invalidate();

            // Update transactions
            UpdateTransactionsList(transactions);
        }

        private void UpdateTransactionsList(List<Transaction> transactions)
        {
            TransactionsContainer.Children.Clear();

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
            var iconText = GetCategoryIcon(transaction.Category);

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
                BackgroundColor = Color.FromArgb("#21262D"),
                StrokeShape = new RoundRectangle { CornerRadius = 12 },
                Stroke = Brush.Transparent,
                HeightRequest = 44,
                WidthRequest = 44,
                VerticalOptions = LayoutOptions.Center
            };

            var iconLabel = new Label
            {
                Text = iconText,
                TextColor = Color.FromArgb("#8B949E"),
                FontSize = 18,
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

            var categoryLabel = new Label
            {
                Text = $"{transaction.Category} - {transaction.Date:dd MMM}",
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

        private static string GetCategoryIcon(string category)
        {
            return category.ToLower() switch
            {
                "food" => "F",
                "transport" => "T",
                "entertainment" => "E",
                "health" => "H",
                "work" => "W",
                "shopping" => "S",
                _ => "O"
            };
        }

        private static string FormatCurrency(decimal amount)
        {
            return $"{amount:N0} RUB".Replace(",", " ");
        }

        private async void OnProfileTapped(object? sender, EventArgs e)
        {
            await DisplayAlert("Профиль", "Настройки профиля будут доступны в ближайшее время", "ОК");
        }

        private async void OnChatTapped(object? sender, EventArgs e)
        {
            var chatPage = new ChatPage();
            await Navigation.PushAsync(chatPage);
        }

        private async void OnAddTransactionTapped(object? sender, EventArgs e)
        {
            string action = await DisplayActionSheet("Добавить транзакцию", "Отмена", null, "Доход", "Расход");
            
            if (action == "Отмена" || string.IsNullOrEmpty(action))
                return;

            string? title = await DisplayPromptAsync("Транзакция", "Введите название:", "ОК", "Отмена");
            if (string.IsNullOrEmpty(title))
                return;

            string? amountStr = await DisplayPromptAsync("Сумма", "Введите сумму:", "ОК", "Отмена", keyboard: Keyboard.Numeric);
            if (string.IsNullOrEmpty(amountStr) || !decimal.TryParse(amountStr, out decimal amount))
                return;

            string? category = await DisplayPromptAsync("Категория", "Введите категорию:", "ОК", "Отмена", initialValue: "Другое");
            
            var transaction = new Transaction
            {
                Title = title,
                Amount = amount,
                Type = action == "Доход" ? TransactionType.Income : TransactionType.Expense,
                Category = category ?? "Другое"
            };

            await _financeService.AddTransactionAsync(transaction);
            await LoadDataAsync();

            string actionText = action == "Доход" ? "Доход" : "Расход";
            await DisplayAlert("Успешно", $"{actionText} добавлен успешно!", "ОК");
        }

        private async void OnStatsTapped(object? sender, EventArgs e)
        {
            await DisplayAlert("Статистика", "Детальная статистика будет доступна в ближайшее время", "ОК");
        }

        private async void OnSeeAllTapped(object? sender, EventArgs e)
        {
            await DisplayAlert("Все транзакции", "Полная история транзакций будет доступна в ближайшее время", "ОК");
        }
    }
}
