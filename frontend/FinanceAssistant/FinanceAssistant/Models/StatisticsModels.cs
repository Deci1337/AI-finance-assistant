namespace FinanceAssistant.Models
{
    public class CategoryStats
    {
        public string CategoryName { get; set; } = string.Empty;
        public string ColorHex { get; set; } = "#8B949E";
        public decimal Amount { get; set; }
        public int Count { get; set; }
        public double Percentage { get; set; }
    }

    public class BarChartData
    {
        public string Label { get; set; } = string.Empty;
        public decimal Income { get; set; }
        public decimal Expense { get; set; }
    }
}





