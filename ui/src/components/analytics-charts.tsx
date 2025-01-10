import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  BarChart,
  Bar,
} from "recharts";
import type { Analytics } from "../types/analytics";

interface AnalyticsChartsProps {
  data: Analytics;
}

export function AnalyticsCharts({ data }: AnalyticsChartsProps) {
  console.log(data);
  return (
    <div className="grid gap-8 md:grid-cols-2">
      {/* Cumulative Words Chart */}
      <div className="space-y-2">
        <div className="space-y-1">
          <h2 className="text-base font-medium">
            Cumulative Words in Messages
          </h2>
          <p className="text-sm text-muted-foreground">
            Total word count over time
          </p>
        </div>
        <div className="h-[400px] w-full">
          <LineChart width={500} height={400} data={data.cumulative_words}>
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="hsl(var(--border))"
            />
            <XAxis
              dataKey="x"
              tickLine={false}
              axisLine={false}
              fontSize={12}
              tickFormatter={(value) => value.split(" ")[0]}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              fontSize={12}
              tickFormatter={(value) => `${value / 1000}k`}
            />
            <Line
              type="monotone"
              dataKey="y"
              stroke="hsl(var(--foreground))"
              strokeWidth={1.5}
              dot={false}
            />
          </LineChart>
        </div>
      </div>

      {/* New Chats Chart */}
      <div className="space-y-2">
        <div className="space-y-1">
          <h2 className="text-base font-medium">New Chats Created</h2>
          <p className="text-sm text-muted-foreground">
            Weekly chat creation activity
          </p>
        </div>
        <div className="h-[200px] w-full">
          <BarChart width={500} height={400} data={data.new_chats_per_week}>
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="hsl(var(--border))"
            />
            <XAxis
              dataKey="x"
              tickLine={false}
              axisLine={false}
              fontSize={12}
              tickFormatter={(value) => value.split(" ")[0]}
            />
            <YAxis tickLine={false} axisLine={false} fontSize={12} />
            <Bar dataKey="y" fill="rgb(231, 91, 87)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </div>
      </div>

      {/* Average Messages Chart */}
      <div className="space-y-2">
        <div className="space-y-1">
          <h2 className="text-base font-medium">Average Messages per Chat</h2>
          <p className="text-sm text-muted-foreground">
            Message density trends
          </p>
        </div>
        <div className="h-[400px] w-full">
          <LineChart width={500} height={400} data={data.messages_per_chat}>
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="hsl(var(--border))"
            />
            <XAxis
              dataKey="x"
              tickLine={false}
              axisLine={false}
              fontSize={12}
              tickFormatter={(value) => {
                const date = new Date(value);
                return date.toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                });
              }}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              fontSize={12}
              domain={[0, "auto"]}
              tickFormatter={(value) => `${value.toFixed(1)}`}
            />
            <Line
              type="monotone"
              dataKey="y"
              stroke="hsl(var(--foreground))"
              strokeWidth={1.5}
              dot={false}
            />
          </LineChart>
        </div>
      </div>

      {/* Messages per Week Chart */}
      <div className="space-y-2">
        <div className="space-y-1">
          <h2 className="text-base font-medium">Weekly Message Volume</h2>
          <p className="text-sm text-muted-foreground">
            Total messages sent per week
          </p>
        </div>
        <div className="h-[200px] w-full">
          <BarChart width={500} height={400} data={data.messages_per_week}>
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="hsl(var(--border))"
            />
            <XAxis
              dataKey="x"
              tickLine={false}
              axisLine={false}
              fontSize={12}
              tickFormatter={(value) => value.split(" ")[0]}
            />
            <YAxis tickLine={false} axisLine={false} fontSize={12} />
            <Bar dataKey="y" fill="rgb(231, 91, 87)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </div>
      </div>
    </div>
  );
}
