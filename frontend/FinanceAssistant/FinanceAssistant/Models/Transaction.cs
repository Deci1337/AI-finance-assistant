using SQLite;

namespace FinanceAssistant.Models
{
    public enum TransactionType
    {
        Income = 0,
        Expense = 1
    }

    public enum ImportanceLevel
    {
        Low = 0,
        Medium = 1,
        High = 2,
        Critical = 3
    }

    [Table("Transactions")]
    public class Transaction
    {
        [PrimaryKey, AutoIncrement]
        public int Id { get; set; }
        
        public string Title { get; set; } = string.Empty;
        
        public decimal Amount { get; set; }
        
        public TransactionType Type { get; set; }
        
        public int CategoryId { get; set; }
        
        public ImportanceLevel Importance { get; set; } = ImportanceLevel.Medium;
        
        public DateTime Date { get; set; } = DateTime.Now;
        
        public string? Description { get; set; }

        [Ignore]
        public Category? Category { get; set; }
    }
}
