using SQLite;

namespace FinanceAssistant.Models
{
    [Table("ChatMessages")]
    public class ChatMessage
    {
        [PrimaryKey, AutoIncrement]
        public int Id { get; set; }
        
        public string Message { get; set; } = string.Empty;
        
        public bool IsUser { get; set; } = true;
        
        public DateTime Timestamp { get; set; } = DateTime.Now;
    }
}

