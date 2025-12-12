using FinanceAssistant.Pages;
using Microsoft.Extensions.DependencyInjection;

namespace FinanceAssistant
{
    public partial class AppShell : Shell
    {
        public AppShell()
        {
            InitializeComponent();

            // Register routes with service resolver
            Routing.RegisterRoute("AddTransactionPage", typeof(AddTransactionPage));
            Routing.RegisterRoute("AIAssistantPage", typeof(AIAssistantPage));
            Routing.RegisterRoute("ProfilePage", typeof(ProfilePage));
            Routing.RegisterRoute("StatisticsPage", typeof(StatisticsPage));
            Routing.RegisterRoute("ChatPage", typeof(ChatPage)); // AI Transaction extraction chat
            Routing.RegisterRoute("SettingsPage", typeof(SettingsPage)); // Settings page
        }

        // Override to use DI for creating pages
        protected override void OnNavigating(ShellNavigatingEventArgs args)
        {
            base.OnNavigating(args);
        }
    }
}
