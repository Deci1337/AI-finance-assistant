using SQLite;

namespace FinanceAssistant.Models
{
    [Table("Categories")]
    public class Category
    {
        [PrimaryKey, AutoIncrement]
        public int Id { get; set; }
        
        public string Name { get; set; } = string.Empty;
        
        public string Icon { get; set; } = "O";
        
        public string ColorHex { get; set; } = "#8B949E";
        
        public bool IsDefault { get; set; }
        
        public TransactionType Type { get; set; }
    }
}




