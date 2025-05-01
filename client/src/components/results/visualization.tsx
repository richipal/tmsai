import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart2, PieChart, Table2, Download } from "lucide-react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

type ChartType = 'bar' | 'pie' | 'table';

interface DataVisualizationProps {
  title: string;
  description: string;
  data: Record<string, any>[];
  columns: string[];
}

export default function DataVisualization({ 
  title,
  description,
  data,
  columns,
}: DataVisualizationProps) {
  const [chartType, setChartType] = useState<ChartType>('bar');
  
  if (!data || data.length === 0) {
    return (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="text-center py-8">
          No data available to visualize
        </CardContent>
      </Card>
    );
  }
  
  // For simplicity, assume the first column is the category and second is the value
  const firstColumnName = columns[0];
  const secondColumnName = columns[1];
  
  // Prepare chart data
  const labels = data.map(item => String(item[firstColumnName]));
  const values = data.map(item => Number(item[secondColumnName]));
  
  // Chart colors
  const backgroundColors = [
    'rgba(59, 130, 246, 0.8)',
    'rgba(16, 185, 129, 0.8)',
    'rgba(99, 102, 241, 0.8)',
    'rgba(239, 68, 68, 0.8)',
    'rgba(249, 115, 22, 0.8)',
    'rgba(217, 70, 239, 0.8)',
  ];
  
  const chartData = {
    labels,
    datasets: [
      {
        label: secondColumnName,
        data: values,
        backgroundColor: backgroundColors,
        borderColor: backgroundColors.map(color => color.replace('0.8', '1')),
        borderWidth: 1,
      },
    ],
  };
  
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
    },
  };
  
  // Function to export data as CSV
  const handleExport = () => {
    // Convert data to CSV
    const header = columns.join(',');
    const rows = data.map(row => 
      columns.map(col => {
        const value = row[col];
        // Handle values with commas
        return typeof value === 'string' && value.includes(',') 
          ? `"${value}"` 
          : value;
      }).join(',')
    );
    const csv = [header, ...rows].join('\n');
    
    // Create a blob and download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `query_result_${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  return (
    <Card className="mb-6">
      <CardHeader className="flex flex-row items-center justify-between px-6 py-5 border-b border-gray-200">
        <div>
          <CardTitle className="text-lg text-gray-900">{title}</CardTitle>
          <CardDescription className="mt-1 text-sm text-gray-500">
            {description}
          </CardDescription>
        </div>
        <div className="flex space-x-2">
          <div className="inline-flex rounded-md shadow-sm" role="group">
            <Button
              type="button"
              variant={chartType === 'table' ? 'default' : 'outline'}
              size="sm"
              className={`rounded-l-md text-xs ${chartType === 'table' ? 'text-white' : 'text-gray-700'}`}
              onClick={() => setChartType('table')}
            >
              <Table2 className="h-3.5 w-3.5 mr-1" />
              Table
            </Button>
            <Button
              type="button"
              variant={chartType === 'bar' ? 'default' : 'outline'}
              size="sm"
              className={`text-xs ${chartType === 'bar' ? 'text-white' : 'text-gray-700'}`}
              onClick={() => setChartType('bar')}
            >
              <BarChart2 className="h-3.5 w-3.5 mr-1" />
              Bar
            </Button>
            <Button
              type="button"
              variant={chartType === 'pie' ? 'default' : 'outline'}
              size="sm"
              className={`rounded-r-md text-xs ${chartType === 'pie' ? 'text-white' : 'text-gray-700'}`}
              onClick={() => setChartType('pie')}
            >
              <PieChart className="h-3.5 w-3.5 mr-1" />
              Pie
            </Button>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="text-xs"
            onClick={handleExport}
          >
            <Download className="h-3.5 w-3.5 mr-1" />
            Export
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="px-4 py-5 sm:p-6 overflow-hidden">
        <div className="h-80 w-full">
          {chartType === 'bar' && (
            <Bar options={chartOptions} data={chartData} className="h-full" />
          )}
          {chartType === 'pie' && (
            <Pie options={chartOptions} data={chartData} className="h-full" />
          )}
          {chartType === 'table' && (
            <div className="overflow-x-auto">
              {/* Will be implemented in data-table.tsx component */}
              <p className="text-center py-10">
                Table view is handled by the DataTable component
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
