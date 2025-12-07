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
    }
}

