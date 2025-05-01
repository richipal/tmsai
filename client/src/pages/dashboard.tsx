import { useState, useEffect } from "react";
import Header from "@/components/layout/header";
import Sidebar from "@/components/layout/sidebar";
import QueryInput from "@/components/query/query-input";
import ExampleQueries from "@/components/query/example-queries";
import SqlDisplay from "@/components/query/sql-display";
import DataVisualization from "@/components/results/visualization";
import DataTable from "@/components/results/data-table";
import QueryExplanation from "@/components/results/query-explanation";
import { Card, CardContent } from "@/components/ui/card";
import { useNaturalLanguageQuery } from "@/hooks/use-query";
import { useQuery } from "@tanstack/react-query";
import { getDatabaseConnections } from "@/lib/flask-service";

const EXAMPLE_QUERIES = [
  "Show me the top 5 products by revenue",
  "Customer orders by country",
  "Monthly sales trend for 2023"
];

export default function Dashboard() {
  // Get database connections
  const { data: connections, isLoading: isLoadingConnections } = useQuery({
    queryKey: ['/api/connections'],
    queryFn: getDatabaseConnections,
  });
  
  // Use the first connection by default or 1 if we don't have connections yet
  const [selectedConnectionId, setSelectedConnectionId] = useState<number>(1);
  
  // Update connection ID when connections are loaded
  useEffect(() => {
    if (connections && connections.length > 0) {
      setSelectedConnectionId(connections[0].id);
    }
  }, [connections]);
  
  // Set up the query hook
  const {
    queryInput,
    setQueryInput,
    queryResult,
    isPending,
    handleExecuteQuery
  } = useNaturalLanguageQuery(selectedConnectionId);
  
  // Handle example query selection
  const handleExampleQuerySelect = (example: string) => {
    setQueryInput(example);
    // Use setTimeout to ensure state is updated before executing
    setTimeout(() => {
      // Directly call the execute function with the example
      handleExecuteQuery();
    }, 50);
  };
  
  // Handle connection change
  const handleConnectionChange = (connectionId: number) => {
    setSelectedConnectionId(connectionId);
  };
  
  return (
    <div className="flex flex-col h-screen">
      <Header 
        selectedConnectionId={selectedConnectionId}
        onConnectionChange={handleConnectionChange}
      />
      
      <main className="flex-1 overflow-hidden flex">
        <Sidebar />
        
        <div className="flex-1 flex flex-col overflow-hidden bg-gray-50">
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-6xl mx-auto">
              {/* Query Input Section */}
              <Card className="bg-white shadow sm:rounded-lg overflow-hidden mb-6">
                <CardContent className="px-4 py-5 sm:p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-4">
                    Ask Vanna in Natural Language
                  </h2>
                  
                  <QueryInput 
                    value={queryInput}
                    onChange={setQueryInput}
                    onExecute={handleExecuteQuery}
                    loading={isPending}
                  />
                  
                  <ExampleQueries 
                    examples={EXAMPLE_QUERIES}
                    onSelect={handleExampleQuerySelect}
                  />
                </CardContent>
              </Card>
              
              {/* Results Section - only show if we have results */}
              {queryResult && (
                <>
                  {/* SQL Query Display */}
                  <SqlDisplay sql={queryResult.sql} />
                  
                  {/* Data Visualization */}
                  {queryResult.data && queryResult.data.length > 0 && (
                    <DataVisualization
                      title="Query Results"
                      description={queryInput}
                      data={queryResult.data}
                      columns={queryResult.columns}
                    />
                  )}
                  
                  {/* Data Table */}
                  {queryResult.data && queryResult.data.length > 0 && (
                    <DataTable
                      data={queryResult.data}
                      columns={queryResult.columns}
                    />
                  )}
                  
                  {/* Query Explanation */}
                  {queryResult.explanation && (
                    <QueryExplanation explanation={queryResult.explanation} />
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
