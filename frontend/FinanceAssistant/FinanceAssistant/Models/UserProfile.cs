using SQLite;

namespace FinanceAssistant.Models
{
    [Table("UserProfile")]
    public class UserProfile
    {
        [PrimaryKey, AutoIncrement]
        public int Id { get; set; }
        
        public string Name { get; set; } = "User";
        
        public string AvatarInitial { get; set; } = "U";
        
        public string Currency { get; set; } = "RUB";
        
        public DateTime CreatedAt { get; set; } = DateTime.Now;
        
        /// <summary>
        /// Friendliness score from -1 (evil) to 1 (kind)
        /// Calculated by AI based on user messages
        /// </summary>
        public double Friendliness { get; set; } = 0.0;
        
        /// <summary>
        /// Total number of messages analyzed for friendliness
        /// </summary>
        public int MessagesAnalyzed { get; set; } = 0;
    }
}
