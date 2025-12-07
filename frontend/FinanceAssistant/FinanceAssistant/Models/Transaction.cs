namespace FinanceAssistant.Models
{
    public enum TransactionType
    {
        Income,
        Expense
    }

    public class Transaction
    {
        public int Id { get; set; }
        public string Title { get; set; } = string.Empty;
        public decimal Amount { get; set; }
        public TransactionType Type { get; set; }
        public string Category { get; set; } = string.Empty;
        public DateTime Date { get; set; }
        public string? Description { get; set; }
    }

    public class ChartDataPoint
    {
        public DateTime Date { get; set; }
        public decimal Income { get; set; }
        public decimal Expense { get; set; }
        public decimal Balance => Income - Expense;
    }

    public class UserProfile
    {
        public string Name { get; set; } = "User";
        public string AvatarUrl { get; set; } = string.Empty;
        public decimal TotalBalance { get; set; }
        public decimal MonthlyIncome { get; set; }
        public decimal MonthlyExpense { get; set; }
    }
}

