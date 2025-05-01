import { useState } from "react";
import Header from "@/components/layout/header";
import Sidebar from "@/components/layout/sidebar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { useQuery } from "@tanstack/react-query";
import { getDatabaseConnections } from "@/lib/flask-service";
import { Key } from "lucide-react";

export default function Settings() {
  const [selectedConnectionId, setSelectedConnectionId] = useState<number>(1);
  const { toast } = useToast();
  const [apiKey, setApiKey] = useState("");
  
  // Get connections
  const { data: connections } = useQuery({
    queryKey: ['/api/connections'],
    queryFn: getDatabaseConnections,
  });
  
  // Handle connection change
  const handleConnectionChange = (connectionId: number) => {
    setSelectedConnectionId(connectionId);
  };
  
  const saveApiKey = () => {
    // In a real app, this would be saved to the server
    toast({
      title: "API Key Saved",
      description: "Your Vanna AI API key has been saved successfully.",
    });
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
            <div className="max-w-6xl mx-auto space-y-6">
              {/* API Key Settings */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl font-semibold">API Keys</CardTitle>
                  <CardDescription>
                    Configure your API keys for external services
                  </CardDescription>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  <div className="grid gap-3">
                    <div className="flex items-center space-x-2">
                      <Key className="h-5 w-5 text-gray-500" />
                      <Label htmlFor="vanna-api-key">Vanna AI API Key</Label>
                    </div>
                    <Input
                      id="vanna-api-key"
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Enter your Vanna AI API key"
                    />
                    <p className="text-sm text-gray-500">
                      Get your API key from the <a href="https://vanna.ai" className="text-primary-600 hover:underline" target="_blank" rel="noopener noreferrer">Vanna AI dashboard</a>
                    </p>
                  </div>
                </CardContent>
                
                <CardFooter className="flex justify-end">
                  <Button onClick={saveApiKey} disabled={!apiKey.trim()}>
                    Save API Key
                  </Button>
                </CardFooter>
              </Card>
              
              {/* Database Connections */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl font-semibold">Database Connections</CardTitle>
                  <CardDescription>
                    Manage your database connections
                  </CardDescription>
                </CardHeader>
                
                <CardContent>
                  <div className="space-y-6">
                    {/* Connection List */}
                    <div className="rounded-lg border overflow-hidden">
                      <div className="bg-gray-50 px-4 py-3 border-b">
                        <h3 className="text-sm font-medium text-gray-700">Existing Connections</h3>
                      </div>
                      
                      <div className="divide-y">
                        {connections?.map((connection) => (
                          <div key={connection.id} className="px-4 py-3 flex justify-between items-center">
                            <div>
                              <div className="font-medium">{connection.name}</div>
                              <div className="text-sm text-gray-500">
                                {connection.type} • {connection.host}:{connection.port} • {connection.database}
                              </div>
                            </div>
                            <div className="flex space-x-2">
                              <Button variant="outline" size="sm">Edit</Button>
                              <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">Delete</Button>
                            </div>
                          </div>
                        ))}
                        
                        {!connections?.length && (
                          <div className="px-4 py-6 text-center text-gray-500">
                            No connections found
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* New Connection Form */}
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 mb-3">Add New Connection</h3>
                      
                      <div className="grid gap-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="connection-name">Connection Name</Label>
                            <Input id="connection-name" placeholder="My Database" />
                          </div>
                          
                          <div className="space-y-2">
                            <Label htmlFor="connection-type">Database Type</Label>
                            <Select defaultValue="mysql">
                              <SelectTrigger id="connection-type">
                                <SelectValue placeholder="Select database type" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="mysql">MySQL</SelectItem>
                                <SelectItem value="postgresql">PostgreSQL</SelectItem>
                                <SelectItem value="sqlserver">SQL Server</SelectItem>
                                <SelectItem value="oracle">Oracle</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="host">Host</Label>
                            <Input id="host" placeholder="localhost or 127.0.0.1" />
                          </div>
                          
                          <div className="space-y-2">
                            <Label htmlFor="port">Port</Label>
                            <Input id="port" placeholder="3306" />
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <Label htmlFor="database">Database Name</Label>
                          <Input id="database" placeholder="my_database" />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="username">Username</Label>
                            <Input id="username" placeholder="root" />
                          </div>
                          
                          <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <Input id="password" type="password" placeholder="••••••••" />
                          </div>
                        </div>
                        
                        <div className="flex justify-end">
                          <Button>Add Connection</Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
