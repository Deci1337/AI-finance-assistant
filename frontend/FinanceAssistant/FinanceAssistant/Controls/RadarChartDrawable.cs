using FinanceAssistant.Models;

namespace FinanceAssistant.Controls
{
    public class RadarChartDrawable : IDrawable
    {
        public List<CategoryStats> ExpenseData { get; set; } = new();
        public List<CategoryStats> IncomeData { get; set; } = new();

        private readonly Color _expenseColor = Color.FromArgb("#FF6B9D");  // Pink
        private readonly Color _incomeColor = Color.FromArgb("#7EB8DA");   // Light blue
        private readonly Color _gridColor = Color.FromArgb("#3D4450");
        private readonly Color _textColor = Color.FromArgb("#8B949E");

        public void Draw(ICanvas canvas, RectF dirtyRect)
        {
            var centerX = dirtyRect.Width / 2;
            var centerY = dirtyRect.Height / 2 + 15; // Offset down for legend
            var radius = Math.Min(centerX, centerY) - 35; // Reduced padding for larger chart

            // Get all unique categories
            var allCategories = ExpenseData.Select(e => e.CategoryName)
                .Union(IncomeData.Select(i => i.CategoryName))
                .Distinct()
                .Take(8) // Max 8 categories for readability
                .ToList();

            if (allCategories.Count < 3)
            {
                // Add default categories if not enough data
                var defaults = new[] { "Food", "Transport", "Shopping", "Entertainment", "Health", "Other" };
                allCategories = defaults.Take(6).ToList();
            }

            var categoryCount = allCategories.Count;
            var angleStep = 360f / categoryCount;

            // Find max value for scaling
            var maxExpense = ExpenseData.Any() ? ExpenseData.Max(e => e.Amount) : 1;
            var maxIncome = IncomeData.Any() ? IncomeData.Max(i => i.Amount) : 1;
            var maxValue = Math.Max(maxExpense, maxIncome);
            if (maxValue == 0) maxValue = 100;

            // Draw grid circles (5 levels)
            DrawGridCircles(canvas, centerX, centerY, radius, 5);

            // Draw grid lines (axes)
            DrawGridLines(canvas, centerX, centerY, radius, categoryCount, angleStep);

            // Draw category labels
            DrawCategoryLabels(canvas, centerX, centerY, radius, allCategories, angleStep);

            // Draw expense data polygon
            DrawDataPolygon(canvas, centerX, centerY, radius, ExpenseData, allCategories, maxValue, _expenseColor, angleStep);

            // Draw income data polygon  
            DrawDataPolygon(canvas, centerX, centerY, radius, IncomeData, allCategories, maxValue, _incomeColor, angleStep);

            // Draw data points
            DrawDataPoints(canvas, centerX, centerY, radius, ExpenseData, allCategories, maxValue, _expenseColor, angleStep);
            DrawDataPoints(canvas, centerX, centerY, radius, IncomeData, allCategories, maxValue, _incomeColor, angleStep);

            // Draw legend
            DrawLegend(canvas, dirtyRect);
        }

        private void DrawGridCircles(ICanvas canvas, float centerX, float centerY, float radius, int levels)
        {
            canvas.StrokeColor = _gridColor;
            canvas.StrokeSize = 1;

            for (int i = 1; i <= levels; i++)
            {
                var r = radius * i / levels;
                canvas.DrawEllipse(centerX - r, centerY - r, r * 2, r * 2);
            }
        }

        private void DrawGridLines(ICanvas canvas, float centerX, float centerY, float radius, int count, float angleStep)
        {
            canvas.StrokeColor = _gridColor;
            canvas.StrokeSize = 1;

            for (int i = 0; i < count; i++)
            {
                var angle = (angleStep * i - 90) * Math.PI / 180;
                var x = centerX + radius * (float)Math.Cos(angle);
                var y = centerY + radius * (float)Math.Sin(angle);
                canvas.DrawLine(centerX, centerY, x, y);
            }
        }

        private void DrawCategoryLabels(ICanvas canvas, float centerX, float centerY, float radius, List<string> categories, float angleStep)
        {
            canvas.FontColor = _textColor;
            canvas.FontSize = 11;

            for (int i = 0; i < categories.Count; i++)
            {
                var angle = (angleStep * i - 90) * Math.PI / 180;
                var labelRadius = radius + 25;
                var x = centerX + labelRadius * (float)Math.Cos(angle);
                var y = centerY + labelRadius * (float)Math.Sin(angle);

                var label = categories[i].Length > 10 ? categories[i].Substring(0, 10) + ".." : categories[i];
                
                // Adjust text position based on angle
                var hAlign = HorizontalAlignment.Center;
                if (Math.Cos(angle) > 0.3) hAlign = HorizontalAlignment.Left;
                else if (Math.Cos(angle) < -0.3) hAlign = HorizontalAlignment.Right;

                canvas.DrawString(label, x - 40, y - 8, 80, 20, hAlign, VerticalAlignment.Center);
            }
        }

        private void DrawDataPolygon(ICanvas canvas, float centerX, float centerY, float radius,
            List<CategoryStats> data, List<string> categories, decimal maxValue, Color color, float angleStep)
        {
            if (data.Count == 0) return;

            var path = new PathF();
            var points = new List<PointF>();

            for (int i = 0; i < categories.Count; i++)
            {
                var category = categories[i];
                var stat = data.FirstOrDefault(d => d.CategoryName == category);
                var value = stat?.Amount ?? 0;
                var normalizedValue = maxValue > 0 ? (float)(value / maxValue) : 0;
                
                // Minimum 10% for visibility
                normalizedValue = Math.Max(normalizedValue, 0.1f);
                
                var angle = (angleStep * i - 90) * Math.PI / 180;
                var r = radius * normalizedValue;
                var x = centerX + r * (float)Math.Cos(angle);
                var y = centerY + r * (float)Math.Sin(angle);
                points.Add(new PointF(x, y));
            }

            if (points.Count > 0)
            {
                path.MoveTo(points[0]);
                for (int i = 1; i < points.Count; i++)
                {
                    path.LineTo(points[i]);
                }
                path.Close();

                // Fill with transparency
                canvas.FillColor = color.WithAlpha(0.3f);
                canvas.FillPath(path);

                // Draw border
                canvas.StrokeColor = color;
                canvas.StrokeSize = 2;
                canvas.DrawPath(path);
            }
        }

        private void DrawDataPoints(ICanvas canvas, float centerX, float centerY, float radius,
            List<CategoryStats> data, List<string> categories, decimal maxValue, Color color, float angleStep)
        {
            if (data.Count == 0) return;

            for (int i = 0; i < categories.Count; i++)
            {
                var category = categories[i];
                var stat = data.FirstOrDefault(d => d.CategoryName == category);
                var value = stat?.Amount ?? 0;
                var normalizedValue = maxValue > 0 ? (float)(value / maxValue) : 0;
                normalizedValue = Math.Max(normalizedValue, 0.1f);

                var angle = (angleStep * i - 90) * Math.PI / 180;
                var r = radius * normalizedValue;
                var x = centerX + r * (float)Math.Cos(angle);
                var y = centerY + r * (float)Math.Sin(angle);

                // Draw point
                canvas.FillColor = color;
                canvas.FillCircle(x, y, 4);
                
                canvas.StrokeColor = Colors.White;
                canvas.StrokeSize = 1.5f;
                canvas.DrawCircle(x, y, 4);
            }
        }

        private void DrawLegend(ICanvas canvas, RectF dirtyRect)
        {
            var y = 15f;
            var boxSize = 12f;

            // Expense legend
            canvas.FillColor = _expenseColor;
            canvas.FillRoundedRectangle(15, y, boxSize, boxSize, 2);
            canvas.FontColor = _textColor;
            canvas.FontSize = 12;
            canvas.DrawString("Expenses", 32, y - 2, 100, 20, HorizontalAlignment.Left, VerticalAlignment.Top);

            // Income legend
            canvas.FillColor = _incomeColor;
            canvas.FillRoundedRectangle(110, y, boxSize, boxSize, 2);
            canvas.DrawString("Income", 127, y - 2, 100, 20, HorizontalAlignment.Left, VerticalAlignment.Top);
        }
    }
}



