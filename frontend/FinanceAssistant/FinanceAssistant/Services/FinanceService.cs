using FinanceAssistant.Models;

namespace FinanceAssistant.Services
{
    public class FinanceService
    {
        // Stub data - will be replaced with backend API calls
        private readonly List<Transaction> _transactions;
        private readonly UserProfile _userProfile;

        public FinanceService()
        {
            _userProfile = new UserProfile
            {
                Name = "Alex",
                TotalBalance = 125430.50m,
                MonthlyIncome = 85000m,
                MonthlyExpense = 42350m
            };

            _transactions = GenerateStubTransactions();
        }

        private List<Transaction> GenerateStubTransactions()
        {
            return new List<Transaction>
            {
                new() { Id = 1, Title = "Salary", Amount = 85000, Type = TransactionType.Income, Category = "Work", Date = DateTime.Now.AddDays(-1) },
                new() { Id = 2, Title = "Groceries", Amount = 3500, Type = TransactionType.Expense, Category = "Food", Date = DateTime.Now.AddDays(-1) },
                new() { Id = 3, Title = "Netflix", Amount = 799, Type = TransactionType.Expense, Category = "Entertainment", Date = DateTime.Now.AddDays(-2) },
                new() { Id = 4, Title = "Freelance", Amount = 15000, Type = TransactionType.Income, Category = "Work", Date = DateTime.Now.AddDays(-3) },
                new() { Id = 5, Title = "Restaurant", Amount = 2800, Type = TransactionType.Expense, Category = "Food", Date = DateTime.Now.AddDays(-3) },
                new() { Id = 6, Title = "Transport", Amount = 1500, Type = TransactionType.Expense, Category = "Transport", Date = DateTime.Now.AddDays(-4) },
                new() { Id = 7, Title = "Gym", Amount = 3000, Type = TransactionType.Expense, Category = "Health", Date = DateTime.Now.AddDays(-5) },
                new() { Id = 8, Title = "Bonus", Amount = 10000, Type = TransactionType.Income, Category = "Work", Date = DateTime.Now.AddDays(-7) },
            };
        }

        public Task<UserProfile> GetUserProfileAsync()
        {
            return Task.FromResult(_userProfile);
        }

        public Task<List<Transaction>> GetRecentTransactionsAsync(int count = 10)
        {
            return Task.FromResult(_transactions.OrderByDescending(t => t.Date).Take(count).ToList());
        }

        public Task<List<ChartDataPoint>> GetChartDataAsync(int days = 7)
        {
            var data = new List<ChartDataPoint>();
            var random = new Random(42); // Fixed seed for consistent stub data

            for (int i = days - 1; i >= 0; i--)
            {
                var date = DateTime.Now.AddDays(-i).Date;
                data.Add(new ChartDataPoint
                {
                    Date = date,
                    Income = random.Next(5000, 20000),
                    Expense = random.Next(2000, 10000)
                });
            }

            return Task.FromResult(data);
        }

        public Task AddTransactionAsync(Transaction transaction)
        {
            transaction.Id = _transactions.Count + 1;
            transaction.Date = DateTime.Now;
            _transactions.Add(transaction);
            
            if (transaction.Type == TransactionType.Income)
            {
                _userProfile.TotalBalance += transaction.Amount;
                _userProfile.MonthlyIncome += transaction.Amount;
            }
            else
            {
                _userProfile.TotalBalance -= transaction.Amount;
                _userProfile.MonthlyExpense += transaction.Amount;
            }

            return Task.CompletedTask;
        }
    }
}

