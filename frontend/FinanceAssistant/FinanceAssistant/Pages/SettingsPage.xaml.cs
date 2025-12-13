using FinanceAssistant.Data;
using FinanceAssistant.Services;

namespace FinanceAssistant.Pages
{
    public partial class SettingsPage : ContentPage
    {
        private readonly DatabaseService _databaseService;
        private readonly ThemeService _themeService;

        public SettingsPage(DatabaseService databaseService, ThemeService themeService)
        {
            InitializeComponent();
            _databaseService = databaseService;
            _themeService = themeService;
        }

        protected override void OnAppearing()
        {
            base.OnAppearing();
            UpdateThemeUI();
        }

        private void UpdateThemeUI()
        {
            bool isDark = _themeService.IsDarkTheme;
            ThemeStatusLabel.Text = isDark ? "Темная тема" : "Светлая тема";
            ThemeEmojiButton.Text = isDark ? "🌙" : "☀️";
        }

        private void OnThemeTapped(object? sender, EventArgs e)
        {
            bool newTheme = !_themeService.IsDarkTheme;
            _themeService.IsDarkTheme = newTheme;
            UpdateThemeUI();
        }

        private async void OnGenerateTestDataTapped(object? sender, EventArgs e)
        {
            bool confirm = await DisplayAlert(
                "Генерация тестовых данных",
                "Будут добавлены случайные транзакции за последние 60 дней. Продолжить?",
                "Да", "Отмена");
            
            if (!confirm) return;
            
            try
            {
                int count = await _databaseService.SeedTestDataAsync();
                await DisplayAlert("Успех", $"Добавлено {count} тестовых транзакций!", "ОК");
            }
            catch (Exception ex)
            {
                await DisplayAlert("Ошибка", $"Не удалось сгенерировать данные: {ex.Message}", "ОК");
            }
        }

        private async void OnClearDataTapped(object? sender, EventArgs e)
        {
            bool confirm = await DisplayAlert(
                "Очистить ВСЕ данные",
                "Будут удалены: транзакции, история чата, достижения. Профиль будет сброшен. Это действие нельзя отменить. Продолжить?",
                "Удалить все", "Отмена");
            
            if (!confirm) return;
            
            try
            {
                await _databaseService.ClearAllDataAsync();
                await DisplayAlert("Успех", "Все данные удалены!", "ОК");
            }
            catch (Exception ex)
            {
                await DisplayAlert("Ошибка", $"Не удалось очистить данные: {ex.Message}", "ОК");
            }
        }

        private async void OnBackTapped(object? sender, EventArgs e)
        {
            await Shell.Current.GoToAsync("..");
        }
    }
}


