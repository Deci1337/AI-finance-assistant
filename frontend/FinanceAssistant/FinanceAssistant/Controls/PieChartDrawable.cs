using FinanceAssistant.Models;

namespace FinanceAssistant.Controls
{
    public class PieChartDrawable : IDrawable
    {
        public List<CategoryStats> Data { get; set; } = new();
        public Color BackgroundColor { get; set; } = Color.FromArgb("#161B22");

        public void Draw(ICanvas canvas, RectF dirtyRect)
        {
            if (Data == null || Data.Count == 0)
            {
                DrawEmptyState(canvas, dirtyRect);
                return;
            }

            var centerX = dirtyRect.Width / 2;
            var centerY = dirtyRect.Height / 2;
            var radius = Math.Min(centerX, centerY) - 20;
            var innerRadius = radius * 0.6f; // Donut chart

            var total = Data.Sum(d => d.Amount);
            if (total == 0)
            {
                DrawEmptyState(canvas, dirtyRect);
                return;
            }

            float startAngle = -90; // Start from top

            foreach (var item in Data)
            {
                item.Percentage = (double)(item.Amount / total) * 100;
                var sweepAngle = (float)(item.Percentage / 100 * 360);

                // Draw pie segment
                canvas.FillColor = Color.FromArgb(item.ColorHex);
                
                var path = new PathF();
                
                // Outer arc
                var startRad = startAngle * MathF.PI / 180;
                var endRad = (startAngle + sweepAngle) * MathF.PI / 180;
                
                path.MoveTo(
                    centerX + innerRadius * MathF.Cos(startRad),
                    centerY + innerRadius * MathF.Sin(startRad)
                );
                
                path.LineTo(
                    centerX + radius * MathF.Cos(startRad),
                    centerY + radius * MathF.Sin(startRad)
                );

                // Draw outer arc
                DrawArc(path, centerX, centerY, radius, startAngle, sweepAngle);
                
                path.LineTo(
                    centerX + innerRadius * MathF.Cos(endRad),
                    centerY + innerRadius * MathF.Sin(endRad)
                );

                // Draw inner arc (reverse)
                DrawArc(path, centerX, centerY, innerRadius, startAngle + sweepAngle, -sweepAngle);
                
                path.Close();
                canvas.FillPath(path);

                startAngle += sweepAngle;
            }

            // Draw center circle (background)
            canvas.FillColor = BackgroundColor;
            canvas.FillCircle(centerX, centerY, innerRadius - 5);

            // Draw total in center
            canvas.FontColor = Color.FromArgb("#FFFFFF");
            canvas.FontSize = 14;
            canvas.DrawString($"{total:N0}", centerX, centerY - 5, HorizontalAlignment.Center);
            canvas.FontSize = 10;
            canvas.FontColor = Color.FromArgb("#8B949E");
            canvas.DrawString("RUB", centerX, centerY + 12, HorizontalAlignment.Center);
        }

        private static void DrawArc(PathF path, float centerX, float centerY, float radius, float startAngle, float sweepAngle)
        {
            var segments = (int)Math.Ceiling(Math.Abs(sweepAngle) / 10);
            var angleStep = sweepAngle / segments;

            for (int i = 1; i <= segments; i++)
            {
                var angle = (startAngle + angleStep * i) * MathF.PI / 180;
                path.LineTo(
                    centerX + radius * MathF.Cos(angle),
                    centerY + radius * MathF.Sin(angle)
                );
            }
        }

        private void DrawEmptyState(ICanvas canvas, RectF rect)
        {
            var centerX = rect.Width / 2;
            var centerY = rect.Height / 2;
            var radius = Math.Min(centerX, centerY) - 20;

            canvas.StrokeColor = Color.FromArgb("#21262D");
            canvas.StrokeSize = 20;
            canvas.DrawCircle(centerX, centerY, radius - 10);

            canvas.FontColor = Color.FromArgb("#8B949E");
            canvas.FontSize = 14;
            canvas.DrawString("No data", centerX, centerY, HorizontalAlignment.Center);
        }
    }
}

