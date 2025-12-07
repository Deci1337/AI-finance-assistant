using FinanceAssistant.Controls;
using FinanceAssistant.Data;
using FinanceAssistant.Models;

namespace FinanceAssistant.Pages
{
    public partial class StatisticsPage : ContentPage
    {
        private readonly DatabaseService _databaseService;
        private readonly RadarChartDrawable _radarChartDrawable;
        private readonly BarChartDrawable _barChartDrawable;
        private int _currentPeriod = 7;

        public StatisticsPage(DatabaseService databaseService)
        {
            InitializeComponent();
            _databaseService = databaseService;
            
            _radarChartDrawable = new RadarChartDrawable();
            _barChartDrawable = new BarChartDrawable();
            
            RadarChartView.Drawable = _radarChartDrawable;
            BarChartView.Drawable = _barChartDrawable;
        }

        protected override async void OnAppearing()
        {
            base.OnAppearing();
            await LoadDataAsync();
        }

        private async Task LoadDataAsync()
        {
            var (income, expense) = await _databaseService.GetStatsForPeriodAsync(_currentPeriod);
            var expenseStats = await _databaseService.GetCategoryStatsAsync(_currentPeriod, TransactionType.Expense);
            var incomeStats = await _databaseService.GetCategoryStatsAsync(_currentPeriod, TransactionType.Income);
            var barChartData = await _databaseService.GetBarChartDataAsync(_currentPeriod);

            // Update summary
            PeriodIncomeLabel.Text = FormatCurrency(income);
            PeriodExpenseLabel.Text = FormatCurrency(expense);

            // Update radar chart with both expense and income data
            _radarChartDrawable.ExpenseData = expenseStats;
            _radarChartDrawable.IncomeData = incomeStats;
            RadarChartView.Invalidate();

            // Update bar chart
            _barChartDrawable.Data = barChartData;
            BarChartView.Invalidate();

            // Update category legend
            UpdateCategoryLegend(expenseStats);

            // Update top expenses
            UpdateTopExpenses(expenseStats);
        }

        private void UpdateCategoryLegend(List<CategoryStats> stats)
        {
            CategoryLegend.Children.Clear();

            var total = stats.Sum(s => s.Amount);
            if (total == 0) return;

            foreach (var stat in stats.Take(5))
            {
                var percentage = (double)(stat.Amount / total) * 100;
                
                var grid = new Grid
                {
                    ColumnDefinitions = new ColumnDefinitionCollection
                    {
                        new ColumnDefinition(GridLength.Auto),
                        new ColumnDefinition(GridLength.Star),
                        new ColumnDefinition(GridLength.Auto)
                    }
                };

                var colorBox = new BoxView
                {
                    Color = Color.FromArgb(stat.ColorHex),
                    WidthRequest = 12,
                    HeightRequest = 12,
                    CornerRadius = 3,
                    VerticalOptions = LayoutOptions.Center
                };

                var nameLabel = new Label
                {
                    Text = stat.CategoryName,
                    TextColor = Color.FromArgb("#FFFFFF"),
                    FontSize = 14,
                    Margin = new Thickness(10, 0, 0, 0),
                    VerticalOptions = LayoutOptions.Center
                };

                var percentLabel = new Label
                {
                    Text = $"{percentage:F1}%",
                    TextColor = Color.FromArgb("#8B949E"),
                    FontSize = 14,
                    VerticalOptions = LayoutOptions.Center
                };

                Grid.SetColumn(colorBox, 0);
                Grid.SetColumn(nameLabel, 1);
                Grid.SetColumn(percentLabel, 2);

                grid.Children.Add(colorBox);
                grid.Children.Add(nameLabel);
                grid.Children.Add(percentLabel);

                CategoryLegend.Children.Add(grid);
            }
        }

        private void UpdateTopExpenses(List<CategoryStats> stats)
        {
            TopExpensesList.Children.Clear();

            if (stats.Count == 0)
            {
                var emptyLabel = new Label
                {
                    Text = "No expenses in this period",
                    TextColor = Color.FromArgb("#8B949E"),
                    FontSize = 14
                };
                TopExpensesList.Children.Add(emptyLabel);
                return;
            }

            foreach (var stat in stats.Take(5))
            {
                var border = new Border
                {
                    BackgroundColor = Color.FromArgb("#21262D"),
                    StrokeShape = new Microsoft.Maui.Controls.Shapes.RoundRectangle { CornerRadius = 12 },
                    Stroke = Brush.Transparent,
                    Padding = new Thickness(12)
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

                var iconBorder = new Border
                {
                    BackgroundColor = Color.FromArgb(stat.ColorHex).WithAlpha(0.2f),
                    StrokeShape = new Microsoft.Maui.Controls.Shapes.RoundRectangle { CornerRadius = 10 },
                    Stroke = Brush.Transparent,
                    HeightRequest = 36,
                    WidthRequest = 36,
                    VerticalOptions = LayoutOptions.Center
                };

                var iconLabel = new Label
                {
                    Text = stat.CategoryName.Length > 0 ? stat.CategoryName[0].ToString() : "?",
                    TextColor = Color.FromArgb(stat.ColorHex),
                    FontSize = 14,
                    FontAttributes = FontAttributes.Bold,
                    HorizontalOptions = LayoutOptions.Center,
                    VerticalOptions = LayoutOptions.Center
                };
                iconBorder.Content = iconLabel;

                var infoStack = new VerticalStackLayout
                {
                    Margin = new Thickness(10, 0, 0, 0),
                    VerticalOptions = LayoutOptions.Center
                };

                var nameLabel = new Label
                {
                    Text = stat.CategoryName,
                    TextColor = Color.FromArgb("#FFFFFF"),
                    FontSize = 14,
                    FontAttributes = FontAttributes.Bold
                };

                var countLabel = new Label
                {
                    Text = $"{stat.Count} transactions",
                    TextColor = Color.FromArgb("#8B949E"),
                    FontSize = 12
                };

                infoStack.Children.Add(nameLabel);
                infoStack.Children.Add(countLabel);

                var amountLabel = new Label
                {
                    Text = FormatCurrency(stat.Amount),
                    TextColor = Color.FromArgb("#FF6B6B"),
                    FontSize = 14,
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
                TopExpensesList.Children.Add(border);
            }
        }

        private async void OnPeriodTapped(object? sender, EventArgs e)
        {
            if (sender is Border border && border.GestureRecognizers[0] is TapGestureRecognizer tap)
            {
                if (int.TryParse(tap.CommandParameter?.ToString(), out int days))
                {
                    _currentPeriod = days;
                    UpdatePeriodUI();
                    await LoadDataAsync();
                }
            }
        }

        private void UpdatePeriodUI()
        {
            var inactiveColor = Colors.Transparent;
            var activeColor = Color.FromArgb("#00D09E");
            var inactiveTextColor = Color.FromArgb("#8B949E");
            var activeTextColor = Color.FromArgb("#0D1117");

            Period1Day.BackgroundColor = _currentPeriod == 1 ? activeColor : inactiveColor;
            Period7Days.BackgroundColor = _currentPeriod == 7 ? activeColor : inactiveColor;
            Period30Days.BackgroundColor = _currentPeriod == 30 ? activeColor : inactiveColor;
            Period365Days.BackgroundColor = _currentPeriod == 365 ? activeColor : inactiveColor;

            UpdatePeriodLabel(Period1Day, _currentPeriod == 1, activeTextColor, inactiveTextColor);
            UpdatePeriodLabel(Period7Days, _currentPeriod == 7, activeTextColor, inactiveTextColor);
            UpdatePeriodLabel(Period30Days, _currentPeriod == 30, activeTextColor, inactiveTextColor);
            UpdatePeriodLabel(Period365Days, _currentPeriod == 365, activeTextColor, inactiveTextColor);
        }

        private static void UpdatePeriodLabel(Border border, bool isActive, Color activeColor, Color inactiveColor)
        {
            if (border.Content is Label label)
            {
                label.TextColor = isActive ? activeColor : inactiveColor;
                label.FontAttributes = isActive ? FontAttributes.Bold : FontAttributes.None;
            }
        }

        private static string FormatCurrency(decimal amount)
        {
            return $"{amount:N0} RUB".Replace(",", " ");
        }

        private async void OnBackTapped(object? sender, EventArgs e)
        {
            await Shell.Current.GoToAsync("..");
        }
    }
}

