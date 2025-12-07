namespace FinanceAssistant.Models
{
    public class ChartDataPoint
    {
        public DateTime Date { get; set; }
        public decimal Income { get; set; }
        public decimal Expense { get; set; }
        public decimal Balance => Income - Expense;
    }
}

