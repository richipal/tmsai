import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface DataTableProps {
  title?: string;
  description?: string;
  data: Record<string, any>[];
  columns: string[];
}

export default function DataTable({ 
  title = "Data Table", 
  description = "Raw query results", 
  data, 
  columns 
}: DataTableProps) {
  const [rowsPerPage, setRowsPerPage] = useState("10");
  const [currentPage, setCurrentPage] = useState(1);
  
  if (!data || data.length === 0) {
    return (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="text-center py-8">
          No data available to display
        </CardContent>
      </Card>
    );
  }
  
  const pageSize = parseInt(rowsPerPage, 10);
  const totalPages = Math.ceil(data.length / pageSize);
  const startIdx = (currentPage - 1) * pageSize;
  const endIdx = Math.min(startIdx + pageSize, data.length);
  const currentData = data.slice(startIdx, endIdx);
  
  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };
  
  return (
    <Card className="mb-6">
      <CardHeader className="px-6 py-5 flex justify-between items-center border-b border-gray-200">
        <div>
          <CardTitle className="text-lg text-gray-900">{title}</CardTitle>
          <CardDescription className="mt-1 text-sm text-gray-500">
            {description}
          </CardDescription>
        </div>
        <div>
          <Select value={rowsPerPage} onValueChange={setRowsPerPage}>
            <SelectTrigger className="mt-1 block pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md w-[180px]">
              <SelectValue placeholder="Rows per page" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">10 rows per page</SelectItem>
              <SelectItem value="25">25 rows per page</SelectItem>
              <SelectItem value="50">50 rows per page</SelectItem>
              <SelectItem value="100">100 rows per page</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      
      <div className="overflow-x-auto">
        <Table>
          <TableHeader className="bg-gray-50">
            <TableRow>
              {columns.map((column, index) => (
                <TableHead
                  key={index}
                  className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                    typeof data[0][column] === 'number' ? 'text-right' : 'text-left'
                  }`}
                >
                  {column}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody className="bg-white divide-y divide-gray-200">
            {currentData.map((row, rowIndex) => (
              <TableRow key={rowIndex}>
                {columns.map((column, columnIndex) => (
                  <TableCell
                    key={columnIndex}
                    className={`px-6 py-4 whitespace-nowrap text-sm ${
                      columnIndex === 0 
                        ? 'font-medium text-gray-900' 
                        : typeof row[column] === 'number' 
                          ? 'text-right text-gray-500' 
                          : 'text-gray-500'
                    }`}
                  >
                    {typeof row[column] === 'number' 
                      ? new Intl.NumberFormat('en-US', {
                          style: column.toLowerCase().includes('price') || column.toLowerCase().includes('revenue') ? 'currency' : 'decimal',
                          currency: 'USD',
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2
                        }).format(row[column])
                      : String(row[column])
                    }
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      
      <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
        <div className="flex-1 flex justify-between sm:hidden">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            Next
          </Button>
        </div>
        <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-gray-700">
              Showing <span className="font-medium">{startIdx + 1}</span> to{" "}
              <span className="font-medium">{endIdx}</span> of{" "}
              <span className="font-medium">{data.length}</span> results
            </p>
          </div>
          <div>
            <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
              <Button
                variant="outline"
                size="sm"
                className="relative inline-flex items-center px-2 py-2 rounded-l-md border text-sm font-medium"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
              >
                <span className="sr-only">Previous</span>
                <ChevronLeft className="h-5 w-5" />
              </Button>
              
              {/* Page numbers */}
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                // Logic to display up to 5 page numbers around the current page
                let pageNumber;
                if (totalPages <= 5) {
                  pageNumber = i + 1;
                } else if (currentPage <= 3) {
                  pageNumber = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNumber = totalPages - 4 + i;
                } else {
                  pageNumber = currentPage - 2 + i;
                }
                
                return (
                  <Button
                    key={i}
                    variant={pageNumber === currentPage ? "default" : "outline"}
                    size="sm"
                    className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                      pageNumber === currentPage 
                        ? "z-10 bg-primary-50 border-primary-500 text-primary-600" 
                        : "bg-white text-gray-500 hover:bg-gray-50"
                    }`}
                    onClick={() => handlePageChange(pageNumber)}
                  >
                    {pageNumber}
                  </Button>
                );
              })}
              
              <Button
                variant="outline"
                size="sm"
                className="relative inline-flex items-center px-2 py-2 rounded-r-md border text-sm font-medium"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                <span className="sr-only">Next</span>
                <ChevronRight className="h-5 w-5" />
              </Button>
            </nav>
          </div>
        </div>
      </div>
    </Card>
  );
}
