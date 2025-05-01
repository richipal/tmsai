import { useState } from "react";
import Header from "@/components/layout/header";
import Sidebar from "@/components/layout/sidebar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Bookmark, Clock, ExternalLink } from "lucide-react";
import { useSavedQueries, useQueryActions } from "@/hooks/use-query";
import { Link } from "wouter";
import { formatDistanceToNow } from "date-fns";

export default function SavedQueries() {
  const [selectedConnectionId, setSelectedConnectionId] = useState<number>(1);
  const { savedQueries, isLoading } = useSavedQueries();
  const { unsaveQuery, isUnsaving } = useQueryActions();
  
  // Handle connection change
  const handleConnectionChange = (connectionId: number) => {
    setSelectedConnectionId(connectionId);
  };
  
  // Format date for display
  const formatDate = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch (e) {
      return dateString;
    }
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
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl font-semibold">Saved Queries</CardTitle>
                  <CardDescription>
                    Quickly access your bookmarked queries
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {isLoading ? (
                    <div className="flex items-center justify-center py-10">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                    </div>
                  ) : !savedQueries || savedQueries.length === 0 ? (
                    <div className="text-center py-10">
                      <p className="text-gray-500">No saved queries found</p>
                      <p className="text-sm text-gray-400 mt-2">
                        Save queries from your query history by clicking the bookmark icon
                      </p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-[50%]">Query</TableHead>
                            <TableHead>Date</TableHead>
                            <TableHead>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {savedQueries.map((query) => (
                            <TableRow key={query.id}>
                              <TableCell className="font-medium">
                                {query.naturalLanguageQuery}
                              </TableCell>
                              <TableCell className="text-sm text-gray-500">
                                <div className="flex items-center">
                                  <Clock className="h-4 w-4 mr-1 text-gray-400" />
                                  {formatDate(query.createdAt)}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex space-x-2">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="text-xs"
                                    onClick={() => unsaveQuery(query.id)}
                                    disabled={isUnsaving}
                                  >
                                    <Bookmark className="h-4 w-4 mr-1 fill-primary-500 text-primary-500" />
                                    Unsave
                                  </Button>
                                  
                                  <Link href={`/query-history/${query.id}`}>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="text-xs"
                                    >
                                      <ExternalLink className="h-4 w-4 mr-1 text-gray-400" />
                                      View
                                    </Button>
                                  </Link>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
