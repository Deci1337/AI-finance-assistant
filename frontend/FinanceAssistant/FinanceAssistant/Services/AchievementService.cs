using FinanceAssistant.Data;
using FinanceAssistant.Models;

namespace FinanceAssistant.Services
{
    public class AchievementService
    {
        private readonly DatabaseService _database;
        
        // Event fired when an achievement is earned
        public event Action<Achievement>? AchievementEarned;
        
        // Queue of pending achievements to show
        private readonly Queue<Achievement> _pendingAchievements = new();
        
        public AchievementService(DatabaseService database)
        {
            _database = database;
        }
        
        /// <summary>
        /// Check if there are pending achievements to display
        /// </summary>
        public bool HasPendingAchievements => _pendingAchievements.Count > 0;
        
        /// <summary>
        /// Get the next pending achievement to display
        /// </summary>
        public Achievement? GetNextPendingAchievement()
        {
            return _pendingAchievements.Count > 0 ? _pendingAchievements.Dequeue() : null;
        }
        
        private void QueueAchievement(Achievement achievement)
        {
            _pendingAchievements.Enqueue(achievement);
            AchievementEarned?.Invoke(achievement);
        }

        /// <summary>
        /// Check and award "First AI Message" achievement
        /// </summary>
        public async Task CheckFirstAiMessageAsync()
        {
            var achievementId = AchievementDefinitions.FirstAiMessage.AchievementId;
            if (await _database.IsAchievementEarnedAsync(achievementId))
                return;

            if (await _database.EarnAchievementAsync(achievementId))
            {
                var achievement = await _database.GetAchievementByIdAsync(achievementId);
                if (achievement != null)
                    QueueAchievement(achievement);
            }
        }

        /// <summary>
        /// Check and award "First Expense" achievement
        /// </summary>
        public async Task CheckFirstExpenseAsync()
        {
            var achievementId = AchievementDefinitions.FirstExpense.AchievementId;
            if (await _database.IsAchievementEarnedAsync(achievementId))
                return;

            if (await _database.EarnAchievementAsync(achievementId))
            {
                var achievement = await _database.GetAchievementByIdAsync(achievementId);
                if (achievement != null)
                    QueueAchievement(achievement);
            }
        }

        /// <summary>
        /// Check and award "First Income" achievement
        /// </summary>
        public async Task CheckFirstIncomeAsync()
        {
            var achievementId = AchievementDefinitions.FirstIncome.AchievementId;
            if (await _database.IsAchievementEarnedAsync(achievementId))
                return;

            if (await _database.EarnAchievementAsync(achievementId))
            {
                var achievement = await _database.GetAchievementByIdAsync(achievementId);
                if (achievement != null)
                    QueueAchievement(achievement);
            }
        }

        /// <summary>
        /// Check and award "First 100K" achievement based on balance
        /// </summary>
        public async Task CheckFirst100KAsync()
        {
            var achievementId = AchievementDefinitions.First100K.AchievementId;
            if (await _database.IsAchievementEarnedAsync(achievementId))
                return;

            var balance = await _database.GetTotalBalanceAsync();
            if (balance >= 100000)
            {
                if (await _database.EarnAchievementAsync(achievementId))
                {
                    var achievement = await _database.GetAchievementByIdAsync(achievementId);
                    if (achievement != null)
                        QueueAchievement(achievement);
                }
            }
        }

        /// <summary>
        /// Check and award "Big Spender" achievement for expenses >= 50K
        /// </summary>
        public async Task CheckBigSpenderAsync(decimal expenseAmount)
        {
            var achievementId = AchievementDefinitions.BigSpender.AchievementId;
            if (await _database.IsAchievementEarnedAsync(achievementId))
                return;

            if (expenseAmount >= 50000)
            {
                if (await _database.EarnAchievementAsync(achievementId))
                {
                    var achievement = await _database.GetAchievementByIdAsync(achievementId);
                    if (achievement != null)
                        QueueAchievement(achievement);
                }
            }
        }

        /// <summary>
        /// Check all transaction-related achievements after adding a transaction
        /// </summary>
        public async Task CheckTransactionAchievementsAsync(Transaction transaction)
        {
            if (transaction.Type == TransactionType.Expense)
            {
                await CheckFirstExpenseAsync();
                await CheckBigSpenderAsync(transaction.Amount);
            }
            else if (transaction.Type == TransactionType.Income)
            {
                await CheckFirstIncomeAsync();
            }

            // Check balance-based achievements
            await CheckFirst100KAsync();
        }

        /// <summary>
        /// Get all achievements with their earned status
        /// </summary>
        public async Task<List<Achievement>> GetAllAchievementsAsync()
        {
            return await _database.GetAllAchievementsAsync();
        }

        /// <summary>
        /// Get only earned achievements
        /// </summary>
        public async Task<List<Achievement>> GetEarnedAchievementsAsync()
        {
            return await _database.GetEarnedAchievementsAsync();
        }
    }
}

