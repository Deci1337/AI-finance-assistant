using SQLite;

namespace FinanceAssistant.Models
{
    [Table("Achievements")]
    public class Achievement
    {
        [PrimaryKey, AutoIncrement]
        public int Id { get; set; }
        
        /// <summary>
        /// Unique identifier for the achievement type
        /// </summary>
        public string AchievementId { get; set; } = string.Empty;
        
        /// <summary>
        /// Achievement name
        /// </summary>
        public string Name { get; set; } = string.Empty;
        
        /// <summary>
        /// Achievement description
        /// </summary>
        public string Description { get; set; } = string.Empty;
        
        /// <summary>
        /// Emoji for the achievement
        /// </summary>
        public string Emoji { get; set; } = string.Empty;
        
        /// <summary>
        /// Whether the achievement has been earned
        /// </summary>
        public bool IsEarned { get; set; } = false;
        
        /// <summary>
        /// Date when the achievement was earned
        /// </summary>
        public DateTime? EarnedAt { get; set; }
    }
    
    /// <summary>
    /// Static class with achievement definitions
    /// </summary>
    public static class AchievementDefinitions
    {
        public static readonly Achievement FirstAiMessage = new()
        {
            AchievementId = "first_ai_message",
            Name = "Первый контакт",
            Description = "Отправь первое сообщение AI-ассистенту",
            Emoji = "🤖"
        };
        
        public static readonly Achievement FirstExpense = new()
        {
            AchievementId = "first_expense",
            Name = "Первая трата",
            Description = "Запиши свою первую трату",
            Emoji = "💸"
        };
        
        public static readonly Achievement FirstIncome = new()
        {
            AchievementId = "first_income",
            Name = "Первый доход",
            Description = "Запиши свой первый доход",
            Emoji = "💰"
        };
        
        public static readonly Achievement First100K = new()
        {
            AchievementId = "first_100k",
            Name = "Сто тысяч!",
            Description = "Накопи 100 000 RUB на балансе",
            Emoji = "🏆"
        };
        
        public static readonly Achievement BigSpender = new()
        {
            AchievementId = "big_spender",
            Name = "Большая покупка",
            Description = "Сделай трату на 50 000 RUB или больше",
            Emoji = "🛍️"
        };
        
        public static List<Achievement> GetAllDefinitions()
        {
            return new List<Achievement>
            {
                FirstAiMessage,
                FirstExpense,
                FirstIncome,
                First100K,
                BigSpender
            };
        }
    }
}


