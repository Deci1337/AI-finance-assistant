using FinanceAssistant.Data;
using FinanceAssistant.Pages;
using FinanceAssistant.Services;
using Microsoft.Extensions.Logging;

namespace FinanceAssistant
{
    public static class MauiProgram
    {
        public static MauiApp CreateMauiApp()
        {
            var builder = MauiApp.CreateBuilder();
            builder
                .UseMauiApp<App>()
                .ConfigureFonts(fonts =>
                {
                    fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular");
                    fonts.AddFont("OpenSans-Semibold.ttf", "OpenSansSemibold");
                });

            // Register services
            builder.Services.AddSingleton<DatabaseService>();
            builder.Services.AddSingleton<FinanceService>(); // API service for backend

            // Register pages for DI
            builder.Services.AddTransient<MainPage>();
            builder.Services.AddTransient<AddTransactionPage>();
            builder.Services.AddTransient<AIAssistantPage>();
            builder.Services.AddTransient<ProfilePage>();
            builder.Services.AddTransient<StatisticsPage>();
            builder.Services.AddTransient<ChatPage>(); // AI Transaction extraction chat

#if DEBUG
            builder.Logging.AddDebug();
#endif

            return builder.Build();
        }
    }
}
