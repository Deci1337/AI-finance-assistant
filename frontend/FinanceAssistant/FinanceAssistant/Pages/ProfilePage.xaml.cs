using FinanceAssistant.Data;
using FinanceAssistant.Models;

namespace FinanceAssistant.Pages
{
    public partial class ProfilePage : ContentPage
    {
        private readonly DatabaseService _databaseService;
        private UserProfile? _profile;

        public ProfilePage(DatabaseService databaseService)
        {
            InitializeComponent();
            _databaseService = databaseService;
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
        }

        private void UpdateFriendlinessDisplay(double friendliness, int messagesAnalyzed)
        {
            // friendliness is from -1 (evil) to 1 (kind)
            // Convert to 0-1 range for positioning
            double normalizedValue = (friendliness + 1) / 2.0;
            
            // Update the indicator position
            // The progress bar width is approximately the parent width minus padding
            // We'll use a percentage-based margin
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
                    ? "Start chatting to measure your friendliness!" 
                    : $"Based on {messagesAnalyzed} message{(messagesAnalyzed == 1 ? "" : "s")}";
            });
        }

        private static string GetFriendlinessText(double friendliness)
        {
            return friendliness switch
            {
                < -0.7 => "Very Rude",
                < -0.4 => "Rude",
                < -0.1 => "Slightly Rude",
                < 0.1 => "Neutral",
                < 0.4 => "Friendly",
                < 0.7 => "Very Friendly",
                _ => "Super Kind!"
            };
        }

        private static Color GetFriendlinessColor(double friendliness)
        {
            return friendliness switch
            {
                < -0.4 => Color.FromArgb("#FF6B6B"), // Red
                < -0.1 => Color.FromArgb("#FFA07A"), // Light red
                < 0.1 => Color.FromArgb("#FFE66D"),  // Yellow
                < 0.4 => Color.FromArgb("#90EE90"),  // Light green
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
            await DisplayAlert("Success", "Profile saved!", "OK");
        }

        private async void OnBackTapped(object? sender, EventArgs e)
        {
            await Shell.Current.GoToAsync("..");
        }

        private async void OnGenerateTestDataTapped(object? sender, EventArgs e)
        {
            bool confirm = await DisplayAlert(
                "Generate Test Data",
                "This will add random transactions for November and December 2024. Continue?",
                "Yes", "Cancel");
            
            if (!confirm) return;
            
            try
            {
                int count = await _databaseService.SeedTestDataAsync();
                await DisplayAlert("Success", $"Added {count} test transactions!", "OK");
                await LoadProfileAsync();
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to generate data: {ex.Message}", "OK");
            }
        }

        private async void OnClearDataTapped(object? sender, EventArgs e)
        {
            bool confirm = await DisplayAlert(
                "Clear All Data",
                "This will delete ALL transactions. This cannot be undone. Continue?",
                "Delete All", "Cancel");
            
            if (!confirm) return;
            
            try
            {
                await _databaseService.ClearAllTransactionsAsync();
                await DisplayAlert("Success", "All transactions deleted!", "OK");
                await LoadProfileAsync();
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", $"Failed to clear data: {ex.Message}", "OK");
            }
        }
    }
}
