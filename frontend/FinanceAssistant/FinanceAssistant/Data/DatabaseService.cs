using SQLite;
using FinanceAssistant.Models;
using System.Linq;

namespace FinanceAssistant.Data
{
    public class DatabaseService
    {
        private SQLiteAsyncConnection? _database;
        private readonly string _dbPath;

        public DatabaseService()
        {
            _dbPath = Path.Combine(FileSystem.AppDataDirectory, "financeassistant.db3");
        }

        private async Task InitAsync()
        {
            if (_database != null)
                return;

            _database = new SQLiteAsyncConnection(_dbPath, SQLiteOpenFlags.ReadWrite | SQLiteOpenFlags.Create | SQLiteOpenFlags.SharedCache);
            
            await _database.CreateTableAsync<Transaction>();
            await _database.CreateTableAsync<Category>();
            await _database.CreateTableAsync<UserProfile>();
            await _database.CreateTableAsync<ChatMessage>();

            await SeedDefaultDataAsync();
        }

        private async Task SeedDefaultDataAsync()
        {
            var categories = await _database!.Table<Category>().CountAsync();
            if (categories == 0)
            {
                var defaultCategories = new List<Category>
                {
                    // Expense categories
                    new() { Name = "Food", Icon = "F", ColorHex = "#FF6B6B", IsDefault = true, Type = TransactionType.Expense },
                    new() { Name = "Transport", Icon = "T", ColorHex = "#4ECDC4", IsDefault = true, Type = TransactionType.Expense },
                    new() { Name = "Entertainment", Icon = "E", ColorHex = "#FFE66D", IsDefault = true, Type = TransactionType.Expense },
                    new() { Name = "Health", Icon = "H", ColorHex = "#6C5CE7", IsDefault = true, Type = TransactionType.Expense },
                    new() { Name = "Shopping", Icon = "S", ColorHex = "#FD79A8", IsDefault = true, Type = TransactionType.Expense },
                    new() { Name = "Bills", Icon = "B", ColorHex = "#A29BFE", IsDefault = true, Type = TransactionType.Expense },
                    new() { Name = "Education", Icon = "Ed", ColorHex = "#74B9FF", IsDefault = true, Type = TransactionType.Expense },
                    new() { Name = "Other", Icon = "O", ColorHex = "#8B949E", IsDefault = true, Type = TransactionType.Expense },
                    
                    // Income categories
                    new() { Name = "Salary", Icon = "W", ColorHex = "#00D09E", IsDefault = true, Type = TransactionType.Income },
                    new() { Name = "Freelance", Icon = "Fr", ColorHex = "#00B386", IsDefault = true, Type = TransactionType.Income },
                    new() { Name = "Investment", Icon = "I", ColorHex = "#33DBAF", IsDefault = true, Type = TransactionType.Income },
                    new() { Name = "Gift", Icon = "G", ColorHex = "#FFE66D", IsDefault = true, Type = TransactionType.Income },
                    new() { Name = "Other Income", Icon = "O", ColorHex = "#8B949E", IsDefault = true, Type = TransactionType.Income },
                };

                await _database.InsertAllAsync(defaultCategories);
            }

            var profiles = await _database.Table<UserProfile>().CountAsync();
            if (profiles == 0)
            {
                await _database.InsertAsync(new UserProfile { Name = "User", AvatarInitial = "U" });
            }
        }

        // Transaction operations
        public async Task<List<Transaction>> GetTransactionsAsync()
        {
            await InitAsync();
            var transactions = await _database!.Table<Transaction>().OrderByDescending(t => t.Date).ToListAsync();
            var categories = await GetCategoriesAsync();
            
            foreach (var t in transactions)
            {
                t.Category = categories.FirstOrDefault(c => c.Id == t.CategoryId);
            }
            
            return transactions;
        }

        public async Task<List<Transaction>> GetRecentTransactionsAsync(int count)
        {
            await InitAsync();
            var transactions = await _database!.Table<Transaction>()
                .OrderByDescending(t => t.Date)
                .Take(count)
                .ToListAsync();
            
            var categories = await GetCategoriesAsync();
            foreach (var t in transactions)
            {
                t.Category = categories.FirstOrDefault(c => c.Id == t.CategoryId);
            }
            
            return transactions;
        }

        public async Task<int> SaveTransactionAsync(Transaction transaction)
        {
            await InitAsync();
            if (transaction.Id != 0)
                return await _database!.UpdateAsync(transaction);
            return await _database!.InsertAsync(transaction);
        }

        public async Task<int> DeleteTransactionAsync(Transaction transaction)
        {
            await InitAsync();
            return await _database!.DeleteAsync(transaction);
        }

        // Category operations
        public async Task<List<Category>> GetCategoriesAsync()
        {
            await InitAsync();
            return await _database!.Table<Category>().ToListAsync();
        }

        public async Task<List<Category>> GetCategoriesByTypeAsync(TransactionType type)
        {
            await InitAsync();
            return await _database!.Table<Category>().Where(c => c.Type == type).ToListAsync();
        }

        public async Task<int> SaveCategoryAsync(Category category)
        {
            await InitAsync();
            if (category.Id != 0)
                return await _database!.UpdateAsync(category);
            return await _database!.InsertAsync(category);
        }

        public async Task<Category> GetOrCreateCategoryAsync(string name, TransactionType type)
        {
            await InitAsync();
            
            // Try to find existing category by name and type
            var existingCategory = await _database!.Table<Category>()
                .Where(c => c.Name == name && c.Type == type)
                .FirstOrDefaultAsync();
            
            if (existingCategory != null)
                return existingCategory;
            
            // If not found, try to find "Other" category for this type
            existingCategory = await _database.Table<Category>()
                .Where(c => c.Name.Contains("Other") && c.Type == type)
                .FirstOrDefaultAsync();
            
            if (existingCategory != null)
                return existingCategory;
            
            // Create new category
            var newCategory = new Category
            {
                Name = name,
                Icon = name.Length > 0 ? name[0].ToString().ToUpper() : "O",
                ColorHex = "#8B949E",
                IsDefault = false,
                Type = type
            };
            
            await _database.InsertAsync(newCategory);
            return newCategory;
        }

        // Profile operations
        public async Task<UserProfile> GetUserProfileAsync()
        {
            await InitAsync();
            var profile = await _database!.Table<UserProfile>().FirstOrDefaultAsync();
            return profile ?? new UserProfile();
        }

        public async Task<int> SaveUserProfileAsync(UserProfile profile)
        {
            await InitAsync();
            if (profile.Id != 0)
                return await _database!.UpdateAsync(profile);
            return await _database!.InsertAsync(profile);
        }

        // Statistics
        public async Task<decimal> GetTotalBalanceAsync()
        {
            await InitAsync();
            var transactions = await _database!.Table<Transaction>().ToListAsync();
            var income = transactions.Where(t => t.Type == TransactionType.Income).Sum(t => t.Amount);
            var expense = transactions.Where(t => t.Type == TransactionType.Expense).Sum(t => t.Amount);
            return income - expense;
        }

        public async Task<(decimal income, decimal expense)> GetMonthlyTotalsAsync()
        {
            await InitAsync();
            var startOfMonth = new DateTime(DateTime.Now.Year, DateTime.Now.Month, 1);
            var transactions = await _database!.Table<Transaction>()
                .Where(t => t.Date >= startOfMonth)
                .ToListAsync();
            
            var income = transactions.Where(t => t.Type == TransactionType.Income).Sum(t => t.Amount);
            var expense = transactions.Where(t => t.Type == TransactionType.Expense).Sum(t => t.Amount);
            return (income, expense);
        }

        public async Task<List<ChartDataPoint>> GetChartDataAsync(int days)
        {
            await InitAsync();
            var startDate = DateTime.Now.Date.AddDays(-(days - 1));
            var transactions = await _database!.Table<Transaction>()
                .Where(t => t.Date >= startDate)
                .ToListAsync();

            var data = new List<ChartDataPoint>();
            for (int i = 0; i < days; i++)
            {
                var date = startDate.AddDays(i);
                var dayTransactions = transactions.Where(t => t.Date.Date == date).ToList();
                
                data.Add(new ChartDataPoint
                {
                    Date = date,
                    Income = dayTransactions.Where(t => t.Type == TransactionType.Income).Sum(t => t.Amount),
                    Expense = dayTransactions.Where(t => t.Type == TransactionType.Expense).Sum(t => t.Amount)
                });
            }

            return data;
        }

        public async Task<(decimal totalEarned, decimal totalSpent)> GetTotalStatsAsync()
        {
            await InitAsync();
            var transactions = await _database!.Table<Transaction>().ToListAsync();
            var totalEarned = transactions.Where(t => t.Type == TransactionType.Income).Sum(t => t.Amount);
            var totalSpent = transactions.Where(t => t.Type == TransactionType.Expense).Sum(t => t.Amount);
            return (totalEarned, totalSpent);
        }

        public async Task<(decimal income, decimal expense)> GetStatsForPeriodAsync(int days)
        {
            await InitAsync();
            var startDate = DateTime.Now.Date.AddDays(-(days - 1));
            var transactions = await _database!.Table<Transaction>()
                .Where(t => t.Date >= startDate)
                .ToListAsync();

            var income = transactions.Where(t => t.Type == TransactionType.Income).Sum(t => t.Amount);
            var expense = transactions.Where(t => t.Type == TransactionType.Expense).Sum(t => t.Amount);
            return (income, expense);
        }

        public async Task<List<CategoryStats>> GetCategoryStatsAsync(int days, TransactionType type)
        {
            await InitAsync();
            var startDate = DateTime.Now.Date.AddDays(-(days - 1));
            var transactions = await _database!.Table<Transaction>()
                .Where(t => t.Date >= startDate && t.Type == type)
                .ToListAsync();

            var categories = await GetCategoriesAsync();
            var stats = new List<CategoryStats>();

            var grouped = transactions.GroupBy(t => t.CategoryId);
            foreach (var group in grouped)
            {
                var category = categories.FirstOrDefault(c => c.Id == group.Key);
                if (category != null)
                {
                    stats.Add(new CategoryStats
                    {
                        CategoryName = category.Name,
                        ColorHex = category.ColorHex,
                        Amount = group.Sum(t => t.Amount),
                        Count = group.Count()
                    });
                }
            }

            return stats.OrderByDescending(s => s.Amount).ToList();
        }

        public async Task<List<BarChartData>> GetBarChartDataAsync(int days)
        {
            await InitAsync();
            var startDate = DateTime.Now.Date.AddDays(-(days - 1));
            var transactions = await _database!.Table<Transaction>()
                .Where(t => t.Date >= startDate)
                .ToListAsync();

            var data = new List<BarChartData>();
            
            // Group by appropriate period
            if (days <= 7)
            {
                // Daily
                for (int i = 0; i < days; i++)
                {
                    var date = startDate.AddDays(i);
                    var dayTrans = transactions.Where(t => t.Date.Date == date).ToList();
                    data.Add(new BarChartData
                    {
                        Label = date.ToString("dd.MM"),
                        Income = dayTrans.Where(t => t.Type == TransactionType.Income).Sum(t => t.Amount),
                        Expense = dayTrans.Where(t => t.Type == TransactionType.Expense).Sum(t => t.Amount)
                    });
                }
            }
            else if (days <= 30)
            {
                // Weekly
                var weeks = (int)Math.Ceiling(days / 7.0);
                for (int i = 0; i < weeks; i++)
                {
                    var weekStart = startDate.AddDays(i * 7);
                    var weekEnd = weekStart.AddDays(7);
                    var weekTrans = transactions.Where(t => t.Date.Date >= weekStart && t.Date.Date < weekEnd).ToList();
                    data.Add(new BarChartData
                    {
                        Label = $"W{i + 1}",
                        Income = weekTrans.Where(t => t.Type == TransactionType.Income).Sum(t => t.Amount),
                        Expense = weekTrans.Where(t => t.Type == TransactionType.Expense).Sum(t => t.Amount)
                    });
                }
            }
            else
            {
                // Monthly
                var months = transactions.GroupBy(t => new { t.Date.Year, t.Date.Month });
                foreach (var month in months.OrderBy(m => m.Key.Year).ThenBy(m => m.Key.Month))
                {
                    data.Add(new BarChartData
                    {
                        Label = new DateTime(month.Key.Year, month.Key.Month, 1).ToString("MMM"),
                        Income = month.Where(t => t.Type == TransactionType.Income).Sum(t => t.Amount),
                        Expense = month.Where(t => t.Type == TransactionType.Expense).Sum(t => t.Amount)
                    });
                }
            }

            return data;
        }

        // Generate test data for the last 60 days (current month + previous month)
        public async Task<int> SeedTestDataAsync()
        {
            await InitAsync();
            var random = new Random();
            var categories = await GetCategoriesAsync();
            var expenseCategories = categories.Where(c => c.Type == TransactionType.Expense).ToList();
            var incomeCategories = categories.Where(c => c.Type == TransactionType.Income).ToList();
            
            if (expenseCategories.Count == 0 || incomeCategories.Count == 0)
            {
                return 0; // No categories available
            }
            
            var testTransactions = new List<Transaction>();
            var today = DateTime.Now.Date;
            
            // Expense templates with realistic amounts (RUB)
            var expenseTemplates = new (string title, int minAmount, int maxAmount, string category)[]
            {
                ("Groceries", 500, 3000, "Food"),
                ("Coffee", 150, 400, "Food"),
                ("Lunch", 300, 800, "Food"),
                ("Dinner", 500, 2000, "Food"),
                ("Metro", 50, 100, "Transport"),
                ("Taxi", 200, 800, "Transport"),
                ("Gas", 1500, 3000, "Transport"),
                ("Cinema", 400, 800, "Entertainment"),
                ("Subscription", 200, 600, "Entertainment"),
                ("Games", 500, 2000, "Entertainment"),
                ("Pharmacy", 300, 1500, "Health"),
                ("Doctor", 1000, 5000, "Health"),
                ("Clothes", 1500, 8000, "Shopping"),
                ("Electronics", 2000, 15000, "Shopping"),
                ("Utilities", 3000, 6000, "Bills"),
                ("Internet", 500, 1000, "Bills"),
                ("Phone", 300, 700, "Bills"),
                ("Course", 2000, 10000, "Education"),
                ("Books", 300, 1500, "Education"),
                ("Other expense", 200, 2000, "Other"),
            };
            
            // Income templates
            var incomeTemplates = new (string title, int minAmount, int maxAmount, string category)[]
            {
                ("Salary", 80000, 120000, "Salary"),
                ("Freelance project", 5000, 30000, "Freelance"),
                ("Dividends", 1000, 10000, "Investment"),
                ("Gift from family", 1000, 5000, "Gift"),
                ("Cashback", 200, 1000, "Other Income"),
            };
            
            // Generate data for the last 60 days
            for (int dayOffset = 0; dayOffset < 60; dayOffset++)
            {
                var transactionDate = today.AddDays(-dayOffset);
                
                // Add salary on 5th and 20th of each month
                if (transactionDate.Day == 5 || transactionDate.Day == 20)
                {
                    var salaryCategory = incomeCategories.FirstOrDefault(c => c.Name == "Salary") ?? incomeCategories[0];
                    testTransactions.Add(new Transaction
                    {
                        Title = "Salary",
                        Amount = random.Next(40000, 60000),
                        Type = TransactionType.Income,
                        CategoryId = salaryCategory.Id,
                        Date = transactionDate,
                        Importance = ImportanceLevel.High
                    });
                }
                
                // Add random income (10% chance per day)
                if (random.Next(100) < 10)
                {
                    var template = incomeTemplates[random.Next(1, incomeTemplates.Length)];
                    var cat = incomeCategories.FirstOrDefault(c => c.Name == template.category) ?? incomeCategories[0];
                    testTransactions.Add(new Transaction
                    {
                        Title = template.title,
                        Amount = random.Next(template.minAmount, template.maxAmount),
                        Type = TransactionType.Income,
                        CategoryId = cat.Id,
                        Date = transactionDate,
                        Importance = ImportanceLevel.Medium
                    });
                }
                
                // Add 1-4 expense transactions per day
                var dailyExpenses = random.Next(1, 5);
                for (int i = 0; i < dailyExpenses; i++)
                {
                    var template = expenseTemplates[random.Next(expenseTemplates.Length)];
                    var cat = expenseCategories.FirstOrDefault(c => c.Name == template.category) ?? expenseCategories[0];
                    testTransactions.Add(new Transaction
                    {
                        Title = template.title,
                        Amount = random.Next(template.minAmount, template.maxAmount),
                        Type = TransactionType.Expense,
                        CategoryId = cat.Id,
                        Date = transactionDate,
                        Importance = (ImportanceLevel)random.Next(0, 3)
                    });
                }
            }
            
            await _database!.InsertAllAsync(testTransactions);
            return testTransactions.Count;
        }

        // Clear all test data
        public async Task ClearAllTransactionsAsync()
        {
            await InitAsync();
            await _database!.DeleteAllAsync<Transaction>();
        }

        // Chat history operations
        public async Task SaveChatMessageAsync(string message, bool isUser)
        {
            await InitAsync();
            var chatMessage = new ChatMessage
            {
                Message = message,
                IsUser = isUser,
                Timestamp = DateTime.Now
            };
            await _database!.InsertAsync(chatMessage);
            
            // Keep only last 20 messages
            var allMessages = await _database.Table<ChatMessage>()
                .OrderByDescending(m => m.Timestamp)
                .ToListAsync();
            
            if (allMessages.Count > 20)
            {
                var messagesToDelete = allMessages.Skip(20).ToList();
                foreach (var msg in messagesToDelete)
                {
                    await _database.DeleteAsync(msg);
                }
            }
        }

        public async Task<List<ChatMessage>> GetChatHistoryAsync(int limit = 20)
        {
            await InitAsync();
            return await _database!.Table<ChatMessage>()
                .OrderByDescending(m => m.Timestamp)
                .Take(limit)
                .ToListAsync();
        }

        public async Task ClearChatHistoryAsync()
        {
            await InitAsync();
            await _database!.DeleteAllAsync<ChatMessage>();
        }
    }
}

