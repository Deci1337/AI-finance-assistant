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
    }
}
