"use client"

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "@/components/ui/chart"

// Default data if no data is passed in
const defaultData = [
  {
    name: "Jan",
    total: 18000,
  },
  {
    name: "Feb",
    total: 22000,
  },
  {
    name: "Mar",
    total: 32000,
  },
  {
    name: "Apr",
    total: 28000,
  },
  {
    name: "May",
    total: 35000,
  },
  {
    name: "Jun",
    total: 42000,
  },
  {
    name: "Jul",
    total: 38000,
  },
  {
    name: "Aug",
    total: 45000,
  },
  {
    name: "Sep",
    total: 48000,
  },
  {
    name: "Oct",
    total: 52000,
  },
  {
    name: "Nov",
    total: 49000,
  },
  {
    name: "Dec",
    total: 58000,
  },
]

interface OverviewProps {
  salesData?: Array<{ month: string; revenue: number }>
}

export function Overview({ salesData = [] }: OverviewProps) {
  // Transform API data to match the chart format
  const chartData = salesData.length > 0
    ? salesData.map(item => ({
        name: item.month,
        total: item.revenue
      }))
    : defaultData

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={chartData}>
        <defs>
          <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ff5757" stopOpacity={0.9} />
            <stop offset="50%" stopColor="#c850c0" stopOpacity={0.8} />
            <stop offset="100%" stopColor="#9f4fe1" stopOpacity={0.7} />
          </linearGradient>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.1)" />
        <XAxis
          dataKey="name"
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
        />
        <YAxis
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
          tickFormatter={(value) => `$${value / 1000}k`}
        />
        <Tooltip
          formatter={(value: number) => [`$${value.toLocaleString()}`, "Revenue"]}
          labelFormatter={(label) => `Month: ${label}`}
          contentStyle={{
            backgroundColor: "rgba(30, 30, 35, 0.9)",
            borderRadius: "8px",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            color: "#fff",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.3)",
          }}
        />
        <Legend />
        <Bar dataKey="total" fill="url(#colorGradient)" radius={[4, 4, 0, 0]} name="Revenue" filter="url(#glow)" />
      </BarChart>
    </ResponsiveContainer>
  )
}
