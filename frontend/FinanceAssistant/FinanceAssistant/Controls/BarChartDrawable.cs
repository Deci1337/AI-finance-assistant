using FinanceAssistant.Models;

namespace FinanceAssistant.Controls
{
    public class BarChartDrawable : IDrawable
    {
        public List<BarChartData> Data { get; set; } = new();
        public Color IncomeColor { get; set; } = Color.FromArgb("#00D09E");
        public Color ExpenseColor { get; set; } = Color.FromArgb("#FF6B6B");
        public Color GridColor { get; set; } = Color.FromArgb("#21262D");
        public Color TextColor { get; set; } = Color.FromArgb("#8B949E");

        public void Draw(ICanvas canvas, RectF dirtyRect)
        {
            if (Data == null || Data.Count == 0)
            {
                DrawEmptyState(canvas, dirtyRect);
                return;
            }

            var padding = new Thickness(50, 20, 20, 40);
            var chartArea = new RectF(
                (float)padding.Left,
                (float)padding.Top,
                dirtyRect.Width - (float)(padding.Left + padding.Right),
                dirtyRect.Height - (float)(padding.Top + padding.Bottom)
            );

            var maxValue = Data.Max(d => Math.Max(d.Income, d.Expense));
            if (maxValue == 0) maxValue = 1;

            DrawGrid(canvas, chartArea, maxValue);
            DrawBars(canvas, chartArea, maxValue);
            DrawLabels(canvas, chartArea);
        }

        private void DrawGrid(ICanvas canvas, RectF chartArea, decimal maxValue)
        {
            canvas.StrokeColor = GridColor;
            canvas.StrokeSize = 1;

            // Horizontal grid lines
            for (int i = 0; i <= 4; i++)
            {
                float y = chartArea.Top + (chartArea.Height / 4) * i;
                canvas.DrawLine(chartArea.Left, y, chartArea.Right, y);

                // Y-axis labels
                var value = maxValue - (maxValue / 4) * i;
                canvas.FontColor = TextColor;
                canvas.FontSize = 10;
                canvas.DrawString(FormatValue(value), 5, y + 4, HorizontalAlignment.Left);
            }
        }

        private void DrawBars(ICanvas canvas, RectF chartArea, decimal maxValue)
        {
            var barGroupWidth = chartArea.Width / Data.Count;
            var barWidth = barGroupWidth * 0.35f;
            var gap = barGroupWidth * 0.05f;

            for (int i = 0; i < Data.Count; i++)
            {
                var item = Data[i];
                var groupX = chartArea.Left + barGroupWidth * i + barGroupWidth / 2;

                // Income bar
                var incomeHeight = (float)(item.Income / maxValue) * chartArea.Height;
                if (incomeHeight > 0)
                {
                    canvas.FillColor = IncomeColor;
                    var incomeRect = new RectF(
                        groupX - barWidth - gap / 2,
                        chartArea.Bottom - incomeHeight,
                        barWidth,
                        incomeHeight
                    );
                    canvas.FillRoundedRectangle(incomeRect, 4);
                }

                // Expense bar
                var expenseHeight = (float)(item.Expense / maxValue) * chartArea.Height;
                if (expenseHeight > 0)
                {
                    canvas.FillColor = ExpenseColor;
                    var expenseRect = new RectF(
                        groupX + gap / 2,
                        chartArea.Bottom - expenseHeight,
                        barWidth,
                        expenseHeight
                    );
                    canvas.FillRoundedRectangle(expenseRect, 4);
                }
            }
        }

        private void DrawLabels(ICanvas canvas, RectF chartArea)
        {
            var barGroupWidth = chartArea.Width / Data.Count;

            canvas.FontColor = TextColor;
            canvas.FontSize = 10;

            for (int i = 0; i < Data.Count; i++)
            {
                var groupX = chartArea.Left + barGroupWidth * i + barGroupWidth / 2;
                canvas.DrawString(Data[i].Label, groupX, chartArea.Bottom + 20, HorizontalAlignment.Center);
            }
        }

        private static string FormatValue(decimal value)
        {
            if (value >= 1000000)
                return $"{value / 1000000:F1}M";
            if (value >= 1000)
                return $"{value / 1000:F0}K";
            return $"{value:F0}";
        }

        private void DrawEmptyState(ICanvas canvas, RectF rect)
        {
            canvas.FontColor = TextColor;
            canvas.FontSize = 14;
            canvas.DrawString("No data for this period", rect.Center.X, rect.Center.Y, HorizontalAlignment.Center);
        }
    }
}

