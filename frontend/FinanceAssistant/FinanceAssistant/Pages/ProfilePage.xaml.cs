using FinanceAssistant.Data;
using FinanceAssistant.Models;
using FinanceAssistant.Services;

namespace FinanceAssistant.Pages
{
    public partial class ProfilePage : ContentPage
    {
        private readonly DatabaseService _databaseService;
        private readonly AchievementService _achievementService;
        private UserProfile? _profile;

        public ProfilePage(DatabaseService databaseService, AchievementService achievementService)
        {
            InitializeComponent();
            _databaseService = databaseService;
            _achievementService = achievementService;
        }

        protected override async void OnAppearing()
        {
            base.OnAppearing();
            await LoadProfileAsync();
        }

        private async Task LoadProfileAsync()
        {
            _profile = await _databaseService.GetUserProfileAsync();
            var transactions = await _databaseService.GetTransactionsAsync();
            var categories = await _databaseService.GetCategoriesAsync();
            var (totalEarned, totalSpent) = await _databaseService.GetTotalStatsAsync();
            var balance = await _databaseService.GetTotalBalanceAsync();

            // Profile info
            NicknameEntry.Text = _profile.Name;
            UserNameDisplay.Text = _profile.Name;
            AvatarLabel.Text = _profile.AvatarInitial;

            // Total stats
            TotalEarnedLabel.Text = FormatCurrency(totalEarned);
            TotalSpentLabel.Text = FormatCurrency(totalSpent);
            BalanceLabel.Text = FormatCurrency(balance);

            // Account info
            TotalTransactionsLabel.Text = transactions.Count.ToString();
            TotalCategoriesLabel.Text = categories.Count.ToString();
            MemberSinceLabel.Text = _profile.CreatedAt.ToString("dd MMM yyyy");

            // Friendliness
            UpdateFriendlinessDisplay(_profile.Friendliness, _profile.MessagesAnalyzed);

            // Achievements
            await LoadAchievementsAsync();
        }

        private async Task LoadAchievementsAsync()
        {
            var achievements = await _achievementService.GetAllAchievementsAsync();
            var earnedCount = achievements.Count(a => a.IsEarned);
            
            AchievementsCountLabel.Text = $"{earnedCount}/{achievements.Count}";
            AchievementsContainer.Children.Clear();

            foreach (var achievement in achievements)
            {
                var achievementView = CreateAchievementView(achievement);
                AchievementsContainer.Children.Add(achievementView);
            }
        }

        private View CreateAchievementView(Achievement achievement)
        {
            var isEarned = achievement.IsEarned;
            
            var container = new Border
            {
                BackgroundColor = isEarned 
                    ? Color.FromArgb("#2D4A3E")  // Darker green for earned
                    : Color.FromArgb("#2A2F3A"), // Gray for locked
                StrokeShape = new Microsoft.Maui.Controls.Shapes.RoundRectangle { CornerRadius = 15 },
                Stroke = isEarned 
                    ? Color.FromArgb("#00D09E")
                    : Colors.Transparent,
                StrokeThickness = isEarned ? 2 : 0,
                Padding = new Thickness(12),
                Margin = new Thickness(4),
                WidthRequest = 72,
                HeightRequest = 72
            };

            var stack = new VerticalStackLayout
            {
                Spacing = 4,
                HorizontalOptions = LayoutOptions.Center,
                VerticalOptions = LayoutOptions.Center
            };

            var emojiLabel = new Label
            {
                Text = isEarned ? achievement.Emoji : "?",
                FontSize = 28,
                HorizontalOptions = LayoutOptions.Center,
                Opacity = isEarned ? 1.0 : 0.4
            };

            stack.Children.Add(emojiLabel);
            container.Content = stack;

            // Add tap gesture for showing achievement details
            var tapGesture = new TapGestureRecognizer();
            tapGesture.Tapped += async (s, e) => await ShowAchievementDetailsAsync(achievement);
            container.GestureRecognizers.Add(tapGesture);

            return container;
        }

        private async Task ShowAchievementDetailsAsync(Achievement achievement)
        {
            var status = achievement.IsEarned 
                ? $"Получено: {achievement.EarnedAt?.ToString("dd MMM yyyy HH:mm")}"
                : "Еще не получено";
            
            await DisplayAlert(
                $"{achievement.Emoji} {achievement.Name}",
                $"{achievement.Description}\n\n{status}",
                "ОК");
        }

        private void UpdateFriendlinessDisplay(double friendliness, int messagesAnalyzed)
        {
            // friendliness is from 0 (evil) to 1 (kind)
            // Clamp to valid range
            double normalizedValue = Math.Clamp(friendliness, 0, 1);
            
            // Update the indicator position
            MainThread.BeginInvokeOnMainThread(() =>
            {
                // Get the parent width (approximate)
                double barWidth = this.Width - 80; // Account for padding
                if (barWidth <= 0) barWidth = 300; // Default if not measured yet
                
                double indicatorPosition = normalizedValue * (barWidth - 16); // 16 is indicator width
                FriendlinessIndicator.Margin = new Thickness(indicatorPosition, 0, 0, 0);
                
                // Update the text label
                FriendlinessValueLabel.Text = GetFriendlinessText(friendliness);
                FriendlinessValueLabel.TextColor = GetFriendlinessColor(friendliness);
                
                // Update messages count
                MessagesAnalyzedLabel.Text = messagesAnalyzed == 0 
                    ? "Начни общаться, чтобы измерить дружелюбность!" 
                    : $"На основе {messagesAnalyzed} сообщений";
            });
        }

        private static string GetFriendlinessText(double friendliness)
        {
            // friendliness: 0.0 = very rude, 0.5 = neutral, 1.0 = very kind
            return friendliness switch
            {
                < 0.2 => "Очень грубый",
                < 0.35 => "Грубый",
                < 0.45 => "Немного грубый",
                < 0.55 => "Нейтрально",
                < 0.65 => "Дружелюбный",
                < 0.8 => "Очень дружелюбный",
                _ => "Супер добрый!"
            };
        }

        private static Color GetFriendlinessColor(double friendliness)
        {
            // friendliness: 0.0 = very rude, 0.5 = neutral, 1.0 = very kind
            return friendliness switch
            {
                < 0.3 => Color.FromArgb("#FF6B6B"), // Red
                < 0.45 => Color.FromArgb("#FFA07A"), // Light red
                < 0.55 => Color.FromArgb("#FFE66D"),  // Yellow
                < 0.7 => Color.FromArgb("#90EE90"),  // Light green
                _ => Color.FromArgb("#00D09E")       // Green
            };
        }

        private static string FormatCurrency(decimal amount)
        {
            return $"{amount:N0} RUB".Replace(",", " ");
        }

        private void OnNicknameChanged(object? sender, TextChangedEventArgs e)
        {
            var name = e.NewTextValue ?? "U";
            UserNameDisplay.Text = name;
            AvatarLabel.Text = name.Length > 0 ? name[0].ToString().ToUpper() : "U";
        }

        private async void OnSaveTapped(object? sender, EventArgs e)
        {
            if (_profile == null)
                return;

            _profile.Name = NicknameEntry.Text ?? "User";
            _profile.AvatarInitial = _profile.Name.Length > 0 ? _profile.Name[0].ToString().ToUpper() : "U";

            await _databaseService.SaveUserProfileAsync(_profile);
            await DisplayAlert("Успех", "Профиль сохранен!", "ОК");
        }

        private async void OnBackTapped(object? sender, EventArgs e)
        {
            await Shell.Current.GoToAsync("..");
        }

        private async void OnSettingsTapped(object? sender, EventArgs e)
        {
            await Shell.Current.GoToAsync("SettingsPage");
        }
    }
}
