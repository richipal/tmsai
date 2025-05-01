import { useState } from "react";
import Header from "@/components/layout/header";
import Sidebar from "@/components/layout/sidebar";
import { useTrainingData, useTrainModel } from "@/hooks/use-query";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { CodeBlock } from "@/components/ui/code-block";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { 
  Table, 
  TableBody, 
  TableCaption, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";

export default function TrainingData() {
  const { toast } = useToast();
  
  // Get database connections and selected ID from props
  const [selectedConnectionId] = useState<number>(1);
  
  // Get training data
  const { trainingData, isLoading } = useTrainingData();
  
  // Train model mutation
  const { trainModel, isTraining } = useTrainModel();
  
  // Form state for adding new training data
  const [newQuestionSql, setNewQuestionSql] = useState({
    question: "",
    sql: ""
  });
  
  const [newDocumentation, setNewDocumentation] = useState({
    table: "",
    description: ""
  });
  
  const [newDdl, setNewDdl] = useState("");
  
  // Handle form submissions
  const handleAddQuestionSql = () => {
    if (!newQuestionSql.question || !newQuestionSql.sql) {
      toast({
        title: "Error",
        description: "Please provide both a question and SQL",
        variant: "destructive"
      });
      return;
    }
    
    trainModel({
      question: newQuestionSql.question,
      sql: newQuestionSql.sql
    });
    
    toast({
      title: "Training data added",
      description: "Question-SQL pair has been added to the training data"
    });
    
    // Reset form
    setNewQuestionSql({ question: "", sql: "" });
  };
  
  const handleAddDocumentation = () => {
    if (!newDocumentation.table || !newDocumentation.description) {
      toast({
        title: "Error",
        description: "Please provide both a table name and description",
        variant: "destructive"
      });
      return;
    }
    
    trainModel({
      documentation: JSON.stringify(newDocumentation)
    });
    
    toast({
      title: "Documentation added",
      description: "Table documentation has been added to the training data"
    });
    
    // Reset form
    setNewDocumentation({ table: "", description: "" });
  };
  
  const handleAddDdl = () => {
    if (!newDdl) {
      toast({
        title: "Error",
        description: "Please provide DDL statement",
        variant: "destructive"
      });
      return;
    }
    
    trainModel({
      ddl: newDdl
    });
    
    toast({
      title: "DDL added",
      description: "DDL statement has been added to the training data"
    });
    
    // Reset form
    setNewDdl("");
  };
  
  return (
    <div className="flex flex-col h-screen">
      <Header 
        selectedConnectionId={selectedConnectionId}
        onConnectionChange={() => {}}
      />
      
      <main className="flex-1 overflow-hidden flex">
        <Sidebar />
        
        <div className="flex-1 flex flex-col overflow-hidden bg-gray-50">
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-6xl mx-auto">
              <h1 className="text-2xl font-bold mb-6">Training Data Management</h1>
              
              <Tabs defaultValue="question-sql">
                <TabsList className="mb-4 grid w-full grid-cols-3">
                  <TabsTrigger value="question-sql">Question-SQL Pairs</TabsTrigger>
                  <TabsTrigger value="documentation">Table Documentation</TabsTrigger>
                  <TabsTrigger value="ddl">DDL Statements</TabsTrigger>
                </TabsList>
                
                {/* Question-SQL Pairs Tab */}
                <TabsContent value="question-sql">
                  <Card>
                    <CardHeader>
                      <CardTitle>Question-SQL Pairs</CardTitle>
                      <CardDescription>
                        These pairs help Vanna learn how to translate natural language questions into SQL queries.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {isLoading ? (
                        <div className="space-y-4">
                          {Array(3).fill(0).map((_, i) => (
                            <div key={i} className="space-y-2">
                              <Skeleton className="h-6 w-full" />
                              <Skeleton className="h-24 w-full" />
                            </div>
                          ))}
                        </div>
                      ) : (
                        <>
                          <div className="mb-6">
                            <h3 className="text-lg font-medium mb-2">Add New Question-SQL Pair</h3>
                            <div className="space-y-4">
                              <div>
                                <label className="block text-sm font-medium mb-1">Question</label>
                                <Input 
                                  value={newQuestionSql.question}
                                  onChange={(e) => setNewQuestionSql({...newQuestionSql, question: e.target.value})}
                                  placeholder="e.g., How many orders were placed in each country?"
                                />
                              </div>
                              <div>
                                <label className="block text-sm font-medium mb-1">SQL Query</label>
                                <Textarea 
                                  value={newQuestionSql.sql}
                                  onChange={(e) => setNewQuestionSql({...newQuestionSql, sql: e.target.value})}
                                  placeholder="e.g., SELECT country, COUNT(*) as order_count FROM customers JOIN orders..."
                                  rows={5}
                                />
                              </div>
                              <Button onClick={handleAddQuestionSql} disabled={isTraining}>
                                {isTraining ? "Adding..." : "Add Pair"}
                              </Button>
                            </div>
                          </div>
                          
                          <h3 className="text-lg font-medium mb-2">Existing Question-SQL Pairs</h3>
                          <div className="space-y-4">
                            {trainingData?.question_sql_pairs?.map((pair, index) => (
                              <Card key={index}>
                                <CardContent className="pt-6">
                                  <h4 className="font-medium mb-2">{pair.question}</h4>
                                  <CodeBlock code={pair.sql} language="sql" showCopyButton />
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        </>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
                
                {/* Documentation Tab */}
                <TabsContent value="documentation">
                  <Card>
                    <CardHeader>
                      <CardTitle>Table Documentation</CardTitle>
                      <CardDescription>
                        Table documentation helps Vanna understand the purpose and content of each table.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {isLoading ? (
                        <Skeleton className="h-64 w-full" />
                      ) : (
                        <>
                          <div className="mb-6">
                            <h3 className="text-lg font-medium mb-2">Add New Table Documentation</h3>
                            <div className="space-y-4">
                              <div>
                                <label className="block text-sm font-medium mb-1">Table Name</label>
                                <Input 
                                  value={newDocumentation.table}
                                  onChange={(e) => setNewDocumentation({...newDocumentation, table: e.target.value})}
                                  placeholder="e.g., customers"
                                />
                              </div>
                              <div>
                                <label className="block text-sm font-medium mb-1">Description</label>
                                <Textarea 
                                  value={newDocumentation.description}
                                  onChange={(e) => setNewDocumentation({...newDocumentation, description: e.target.value})}
                                  placeholder="e.g., Contains all customer information including company name, contact details, and location"
                                  rows={3}
                                />
                              </div>
                              <Button onClick={handleAddDocumentation} disabled={isTraining}>
                                {isTraining ? "Adding..." : "Add Documentation"}
                              </Button>
                            </div>
                          </div>
                          
                          <h3 className="text-lg font-medium mb-2">Existing Table Documentation</h3>
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Table</TableHead>
                                <TableHead>Description</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {trainingData?.documentation?.map((doc, index) => (
                                <TableRow key={index}>
                                  <TableCell className="font-medium">{doc.table}</TableCell>
                                  <TableCell>{doc.description}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
                
                {/* DDL Tab */}
                <TabsContent value="ddl">
                  <Card>
                    <CardHeader>
                      <CardTitle>DDL Statements</CardTitle>
                      <CardDescription>
                        Data Definition Language (DDL) statements define the database schema.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {isLoading ? (
                        <Skeleton className="h-64 w-full" />
                      ) : (
                        <>
                          <div className="mb-6">
                            <h3 className="text-lg font-medium mb-2">Add New DDL Statement</h3>
                            <div className="space-y-4">
                              <Textarea 
                                value={newDdl}
                                onChange={(e) => setNewDdl(e.target.value)}
                                placeholder="e.g., CREATE TABLE customers (customer_id VARCHAR PRIMARY KEY, ...);"
                                rows={5}
                              />
                              <Button onClick={handleAddDdl} disabled={isTraining}>
                                {isTraining ? "Adding..." : "Add DDL"}
                              </Button>
                            </div>
                          </div>
                          
                          <h3 className="text-lg font-medium mb-2">Existing DDL Statements</h3>
                          <div className="space-y-4">
                            {trainingData?.ddl?.map((ddl, index) => (
                              <CodeBlock key={index} code={ddl} language="sql" showCopyButton />
                            ))}
                          </div>
                        </>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}