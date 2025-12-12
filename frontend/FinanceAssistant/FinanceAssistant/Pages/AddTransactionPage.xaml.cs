using FinanceAssistant.Data;
using FinanceAssistant.Models;
using FinanceAssistant.Services;

namespace FinanceAssistant.Pages
{
    public partial class AddTransactionPage : ContentPage
    {
        private readonly DatabaseService _databaseService;
        private readonly AchievementService _achievementService;
        private TransactionType _currentType = TransactionType.Expense;
        private ImportanceLevel _currentImportance = ImportanceLevel.Medium;
        private Category? _selectedCategory;
        private List<Category> _categories = new();

        public AddTransactionPage(DatabaseService databaseService, AchievementService achievementService)
        {
            InitializeComponent();
            _databaseService = databaseService;
            _achievementService = achievementService;
        }

        protected override async void OnAppearing()
        {
            base.OnAppearing();
            await LoadCategoriesAsync();
        }

        private async Task LoadCategoriesAsync()
        {
            _categories = await _databaseService.GetCategoriesByTypeAsync(_currentType);
            UpdateCategoriesUI();
        }

        private void UpdateCategoriesUI()
        {
            CategoriesContainer.Children.Clear();

            foreach (var category in _categories)
            {
                var isSelected = _selectedCategory?.Id == category.Id;
                var categoryView = CreateCategoryChip(category, isSelected);
                CategoriesContainer.Children.Add(categoryView);
            }

            // Select first category if none selected
            if (_selectedCategory == null && _categories.Count > 0)
            {
                _selectedCategory = _categories[0];
                UpdateCategoriesUI();
            }
        }

        private View CreateCategoryChip(Category category, bool isSelected)
        {
            var bgColor = isSelected ? Color.FromArgb(category.ColorHex) : Color.FromArgb("#21262D");
            var textColor = isSelected ? Color.FromArgb("#0D1117") : Color.FromArgb("#8B949E");

            var border = new Border
            {
                BackgroundColor = bgColor,
                StrokeShape = new Microsoft.Maui.Controls.Shapes.RoundRectangle { CornerRadius = 20 },
                Stroke = Brush.Transparent,
                Padding = new Thickness(15, 10),
                Margin = new Thickness(0, 0, 10, 10)
            };

            var label = new Label
            {
                Text = category.Name,
                TextColor = textColor,
                FontSize = 14,
                FontAttributes = isSelected ? FontAttributes.Bold : FontAttributes.None
            };

            border.Content = label;

            var tapGesture = new TapGestureRecognizer();
            tapGesture.Tapped += (s, e) => OnCategorySelected(category);
            border.GestureRecognizers.Add(tapGesture);

            return border;
        }

        private void OnCategorySelected(Category category)
        {
            _selectedCategory = category;
            UpdateCategoriesUI();
        }

        private async void OnExpenseTabTapped(object? sender, EventArgs e)
        {
            if (_currentType == TransactionType.Expense)
                return;

            _currentType = TransactionType.Expense;
            ExpenseTab.BackgroundColor = Color.FromArgb("#FF6B6B");
            IncomeTab.BackgroundColor = Colors.Transparent;
            
            if (ExpenseTab.Content is Label expenseLabel)
                expenseLabel.TextColor = Color.FromArgb("#FFFFFF");
            IncomeTabLabel.TextColor = Color.FromArgb("#8B949E");

            _selectedCategory = null;
            await LoadCategoriesAsync();
        }

        private async void OnIncomeTabTapped(object? sender, EventArgs e)
        {
            if (_currentType == TransactionType.Income)
                return;

            _currentType = TransactionType.Income;
            IncomeTab.BackgroundColor = Color.FromArgb("#00D09E");
            ExpenseTab.BackgroundColor = Colors.Transparent;
            
            IncomeTabLabel.TextColor = Color.FromArgb("#0D1117");
            IncomeTabLabel.FontAttributes = FontAttributes.Bold;
            
            if (ExpenseTab.Content is Label expenseLabel)
                expenseLabel.TextColor = Color.FromArgb("#8B949E");

            _selectedCategory = null;
            await LoadCategoriesAsync();
        }

        private void OnImportanceTapped(object? sender, EventArgs e)
        {
            if (sender is Border border && border.GestureRecognizers[0] is TapGestureRecognizer tap)
            {
                if (int.TryParse(tap.CommandParameter?.ToString(), out int level))
                {
                    _currentImportance = (ImportanceLevel)level;
                    UpdateImportanceUI();
                }
            }
        }

        private void UpdateImportanceUI()
        {
            var inactiveColor = Color.FromArgb("#21262D");
            var activeColor = Color.FromArgb("#00D09E");
            var inactiveTextColor = Color.FromArgb("#8B949E");
            var activeTextColor = Color.FromArgb("#0D1117");

            ImportanceLow.BackgroundColor = _currentImportance == ImportanceLevel.Low ? activeColor : inactiveColor;
            ImportanceMedium.BackgroundColor = _currentImportance == ImportanceLevel.Medium ? activeColor : inactiveColor;
            ImportanceHigh.BackgroundColor = _currentImportance == ImportanceLevel.High ? activeColor : inactiveColor;
            ImportanceCritical.BackgroundColor = _currentImportance == ImportanceLevel.Critical ? activeColor : inactiveColor;

            UpdateImportanceLabel(ImportanceLow, _currentImportance == ImportanceLevel.Low, activeTextColor, inactiveTextColor);
            UpdateImportanceLabel(ImportanceMedium, _currentImportance == ImportanceLevel.Medium, activeTextColor, inactiveTextColor);
            UpdateImportanceLabel(ImportanceHigh, _currentImportance == ImportanceLevel.High, activeTextColor, inactiveTextColor);
            UpdateImportanceLabel(ImportanceCritical, _currentImportance == ImportanceLevel.Critical, activeTextColor, inactiveTextColor);
        }

        private static void UpdateImportanceLabel(Border border, bool isActive, Color activeColor, Color inactiveColor)
        {
            if (border.Content is VerticalStackLayout stack && stack.Children[0] is Label label)
            {
                label.TextColor = isActive ? activeColor : inactiveColor;
                label.FontAttributes = isActive ? FontAttributes.Bold : FontAttributes.None;
            }
        }

        private async void OnAddCategoryTapped(object? sender, EventArgs e)
        {
            string? name = await DisplayPromptAsync("Новая категория", "Введите название категории:", "Добавить", "Отмена");
            
            if (string.IsNullOrWhiteSpace(name))
                return;

            var newCategory = new Category
            {
                Name = name,
                Icon = name[0].ToString().ToUpper(),
                ColorHex = GetRandomCategoryColor(),
                IsDefault = false,
                Type = _currentType
            };

            await _databaseService.SaveCategoryAsync(newCategory);
            await LoadCategoriesAsync();
            
            _selectedCategory = _categories.FirstOrDefault(c => c.Name == name);
            UpdateCategoriesUI();
        }

        private static string GetRandomCategoryColor()
        {
            var colors = new[] { "#FF6B6B", "#4ECDC4", "#FFE66D", "#6C5CE7", "#FD79A8", "#A29BFE", "#74B9FF", "#00D09E" };
            return colors[Random.Shared.Next(colors.Length)];
        }

        private async void OnSaveTapped(object? sender, EventArgs e)
        {
            if (!decimal.TryParse(AmountEntry.Text, out decimal amount) || amount <= 0)
            {
                await DisplayAlert("Ошибка", "Введите корректную сумму", "ОК");
                return;
            }

            if (_selectedCategory == null)
            {
                await DisplayAlert("Ошибка", "Выберите категорию", "ОК");
                return;
            }

            var transaction = new Transaction
            {
                Title = string.IsNullOrWhiteSpace(TitleEntry.Text) ? _selectedCategory.Name : TitleEntry.Text,
                Amount = amount,
                Type = _currentType,
                CategoryId = _selectedCategory.Id,
                Importance = _currentImportance,
                Date = DateTime.Now
            };

            await _databaseService.SaveTransactionAsync(transaction);
            
            // Check for achievements
            await _achievementService.CheckTransactionAchievementsAsync(transaction);
            
            await Shell.Current.GoToAsync("..");
        }

        private async void OnBackTapped(object? sender, EventArgs e)
        {
            await Shell.Current.GoToAsync("..");
        }
    }
}

