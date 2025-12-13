using FinanceAssistant.Models;

namespace FinanceAssistant.Controls
{
    public class FinanceChartDrawable : IDrawable
    {
        public List<ChartDataPoint> DataPoints { get; set; } = new();
        public Color LineColor { get; set; } = Color.FromArgb("#00D09E");
        public Color GradientStartColor { get; set; } = Color.FromArgb("#3300D09E");
        public Color GradientEndColor { get; set; } = Color.FromArgb("#0000D09E");
        public Color GridColor { get; set; } = Color.FromArgb("#21262D");
        public Color TextColor { get; set; } = Color.FromArgb("#8B949E");

        public void Draw(ICanvas canvas, RectF dirtyRect)
        {
            if (DataPoints == null || DataPoints.Count < 2)
            {
                DrawEmptyState(canvas, dirtyRect);
                return;
            }

            var padding = new Thickness(40, 20, 20, 40);
            var chartArea = new RectF(
                (float)padding.Left,
                (float)padding.Top,
                dirtyRect.Width - (float)(padding.Left + padding.Right),
                dirtyRect.Height - (float)(padding.Top + padding.Bottom)
            );

            DrawGrid(canvas, chartArea);
            DrawBalanceLine(canvas, chartArea);
            DrawLabels(canvas, chartArea, padding);
        }

        private void DrawEmptyState(ICanvas canvas, RectF rect)
        {
            canvas.FontColor = TextColor;
            canvas.FontSize = 14;
            canvas.DrawString("No data available", rect.Center.X, rect.Center.Y, HorizontalAlignment.Center);
        }

        private void DrawGrid(ICanvas canvas, RectF chartArea)
        {
            canvas.StrokeColor = GridColor;
            canvas.StrokeSize = 1;

            // Horizontal grid lines
            for (int i = 0; i <= 4; i++)
            {
                float y = chartArea.Top + (chartArea.Height / 4) * i;
                canvas.DrawLine(chartArea.Left, y, chartArea.Right, y);
            }
        }

        private void DrawBalanceLine(ICanvas canvas, RectF chartArea)
        {
            var balances = DataPoints.Select(d => d.Balance).ToList();
            var maxBalance = balances.Max();
            var minBalance = balances.Min();
            var range = maxBalance - minBalance;
            if (range == 0) range = 1;

            var points = new List<PointF>();
            for (int i = 0; i < DataPoints.Count; i++)
            {
                float x = chartArea.Left + (chartArea.Width / (DataPoints.Count - 1)) * i;
                float normalizedY = (float)((DataPoints[i].Balance - minBalance) / range);
                float y = chartArea.Bottom - (normalizedY * chartArea.Height);
                points.Add(new PointF(x, y));
            }

            // Draw gradient fill
            var path = new PathF();
            path.MoveTo(points[0].X, chartArea.Bottom);
            foreach (var point in points)
            {
                path.LineTo(point.X, point.Y);
            }
            path.LineTo(points[^1].X, chartArea.Bottom);
            path.Close();

            var gradientPaint = new LinearGradientPaint
            {
                StartPoint = new Point(0, 0),
                EndPoint = new Point(0, 1),
                GradientStops = new[]
                {
                    new PaintGradientStop(0, GradientStartColor),
                    new PaintGradientStop(1, GradientEndColor)
                }
            };
            canvas.SetFillPaint(gradientPaint, chartArea);
            canvas.FillPath(path);

            // Draw line
            canvas.StrokeColor = LineColor;
            canvas.StrokeSize = 3;
            canvas.StrokeLineCap = LineCap.Round;
            canvas.StrokeLineJoin = LineJoin.Round;

            var linePath = new PathF();
            linePath.MoveTo(points[0]);
            for (int i = 1; i < points.Count; i++)
            {
                linePath.LineTo(points[i]);
            }
            canvas.DrawPath(linePath);

            // Draw points
            canvas.FillColor = LineColor;
            foreach (var point in points)
            {
                canvas.FillCircle(point.X, point.Y, 5);
            }

            // Draw white center for points
            canvas.FillColor = Color.FromArgb("#161B22");
            foreach (var point in points)
            {
                canvas.FillCircle(point.X, point.Y, 2);
            }
        }

        private void DrawLabels(ICanvas canvas, RectF chartArea, Thickness padding)
        {
            canvas.FontColor = TextColor;
            canvas.FontSize = 10;

            // X-axis labels (dates)
            for (int i = 0; i < DataPoints.Count; i++)
            {
                float x = chartArea.Left + (chartArea.Width / (DataPoints.Count - 1)) * i;
                string label = DataPoints[i].Date.ToString("dd.MM");
                canvas.DrawString(label, x, chartArea.Bottom + 20, HorizontalAlignment.Center);
            }

            // Y-axis labels
            var balances = DataPoints.Select(d => d.Balance).ToList();
            var maxBalance = balances.Max();
            var minBalance = balances.Min();

            for (int i = 0; i <= 4; i++)
            {
                float y = chartArea.Top + (chartArea.Height / 4) * i;
                decimal value = maxBalance - ((maxBalance - minBalance) / 4) * i;
                string label = FormatCurrency(value);
                canvas.DrawString(label, 5, y + 4, HorizontalAlignment.Left);
            }
        }

        private static string FormatCurrency(decimal value)
        {
            if (Math.Abs(value) >= 1000)
                return $"{value / 1000:F0}K";
            return $"{value:F0}";
        }
    }
}





