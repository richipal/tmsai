import { useState } from "react";
import Header from "@/components/layout/header";
import Sidebar from "@/components/layout/sidebar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Eye, EyeOff, Database } from "lucide-react";

// This is a simplified schema page that would typically fetch schema from the backend
export default function DatabaseSchema() {
  const [selectedConnectionId, setSelectedConnectionId] = useState<number>(1);
  const [expandedTables, setExpandedTables] = useState<string[]>([]);
  
  // Sample schema data - in a real app this would come from the API
  const sampleSchema = {
    tables: [
      {
        name: "customers",
        description: "Customer information",
        columns: [
          { name: "customer_id", type: "INTEGER", isPrimary: true, description: "Primary key" },
          { name: "company_name", type: "VARCHAR(40)", isPrimary: false, description: "Company name" },
          { name: "contact_name", type: "VARCHAR(30)", isPrimary: false, description: "Contact person" },
          { name: "contact_title", type: "VARCHAR(30)", isPrimary: false, description: "Contact's title" },
          { name: "address", type: "VARCHAR(60)", isPrimary: false, description: "Street address" },
          { name: "city", type: "VARCHAR(15)", isPrimary: false, description: "City" },
          { name: "region", type: "VARCHAR(15)", isPrimary: false, description: "State or province" },
          { name: "postal_code", type: "VARCHAR(10)", isPrimary: false, description: "Postal code" },
          { name: "country", type: "VARCHAR(15)", isPrimary: false, description: "Country" },
          { name: "phone", type: "VARCHAR(24)", isPrimary: false, description: "Phone number" },
          { name: "fax", type: "VARCHAR(24)", isPrimary: false, description: "Fax number" },
        ]
      },
      {
        name: "orders",
        description: "Customer orders",
        columns: [
          { name: "order_id", type: "INTEGER", isPrimary: true, description: "Primary key" },
          { name: "customer_id", type: "VARCHAR(5)", isPrimary: false, description: "Customer ID (FK)" },
          { name: "employee_id", type: "INTEGER", isPrimary: false, description: "Employee ID (FK)" },
          { name: "order_date", type: "DATETIME", isPrimary: false, description: "Date order was placed" },
          { name: "required_date", type: "DATETIME", isPrimary: false, description: "Date order is required" },
          { name: "shipped_date", type: "DATETIME", isPrimary: false, description: "Date order was shipped" },
          { name: "ship_via", type: "INTEGER", isPrimary: false, description: "Shipper ID (FK)" },
          { name: "freight", type: "MONEY", isPrimary: false, description: "Shipping cost" },
          { name: "ship_name", type: "VARCHAR(40)", isPrimary: false, description: "Name of recipient" },
          { name: "ship_address", type: "VARCHAR(60)", isPrimary: false, description: "Street address" },
          { name: "ship_city", type: "VARCHAR(15)", isPrimary: false, description: "City" },
          { name: "ship_region", type: "VARCHAR(15)", isPrimary: false, description: "State or province" },
          { name: "ship_postal_code", type: "VARCHAR(10)", isPrimary: false, description: "Postal code" },
          { name: "ship_country", type: "VARCHAR(15)", isPrimary: false, description: "Country" },
        ]
      },
      {
        name: "products",
        description: "Product information",
        columns: [
          { name: "product_id", type: "INTEGER", isPrimary: true, description: "Primary key" },
          { name: "product_name", type: "VARCHAR(40)", isPrimary: false, description: "Product name" },
          { name: "supplier_id", type: "INTEGER", isPrimary: false, description: "Supplier ID (FK)" },
          { name: "category_id", type: "INTEGER", isPrimary: false, description: "Category ID (FK)" },
          { name: "quantity_per_unit", type: "VARCHAR(20)", isPrimary: false, description: "Quantity per unit" },
          { name: "unit_price", type: "MONEY", isPrimary: false, description: "Unit price" },
          { name: "units_in_stock", type: "SMALLINT", isPrimary: false, description: "Units in stock" },
          { name: "units_on_order", type: "SMALLINT", isPrimary: false, description: "Units on order" },
          { name: "reorder_level", type: "SMALLINT", isPrimary: false, description: "Reorder level" },
          { name: "discontinued", type: "BIT", isPrimary: false, description: "Discontinued flag" },
        ]
      }
    ]
  };
  
  // Handle connection change
  const handleConnectionChange = (connectionId: number) => {
    setSelectedConnectionId(connectionId);
  };
  
  // Toggle table expansion
  const toggleTableExpansion = (tableName: string) => {
    if (expandedTables.includes(tableName)) {
      setExpandedTables(expandedTables.filter(name => name !== tableName));
    } else {
      setExpandedTables([...expandedTables, tableName]);
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
                  <CardTitle className="text-xl font-semibold">Database Schema</CardTitle>
                  <CardDescription>
                    Explore the tables and columns in your database
                  </CardDescription>
                </CardHeader>
                
                <CardContent>
                  <Tabs defaultValue="tables">
                    <TabsList className="mb-4">
                      <TabsTrigger value="tables">Tables</TabsTrigger>
                      <TabsTrigger value="relationships">Relationships</TabsTrigger>
                      <TabsTrigger value="views">Views</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="tables">
                      <div className="space-y-4">
                        {sampleSchema.tables.map(table => (
                          <Card key={table.name}>
                            <CardHeader className="py-3 px-4 cursor-pointer" onClick={() => toggleTableExpansion(table.name)}>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                  <Database className="h-5 w-5 text-primary-500" />
                                  <CardTitle className="text-base">{table.name}</CardTitle>
                                </div>
                                <Button variant="ghost" size="sm">
                                  {expandedTables.includes(table.name) ? (
                                    <EyeOff className="h-4 w-4" />
                                  ) : (
                                    <Eye className="h-4 w-4" />
                                  )}
                                </Button>
                              </div>
                              <CardDescription className="mt-1">
                                {table.description}
                              </CardDescription>
                            </CardHeader>
                            
                            {expandedTables.includes(table.name) && (
                              <CardContent className="pb-4">
                                <Table>
                                  <TableHeader>
                                    <TableRow>
                                      <TableHead className="w-[200px]">Column Name</TableHead>
                                      <TableHead className="w-[150px]">Data Type</TableHead>
                                      <TableHead>Description</TableHead>
                                      <TableHead className="w-[100px]">Key</TableHead>
                                    </TableRow>
                                  </TableHeader>
                                  <TableBody>
                                    {table.columns.map(column => (
                                      <TableRow key={column.name}>
                                        <TableCell className="font-medium">{column.name}</TableCell>
                                        <TableCell className="font-mono text-xs">{column.type}</TableCell>
                                        <TableCell>{column.description}</TableCell>
                                        <TableCell>
                                          {column.isPrimary && (
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                                              PK
                                            </span>
                                          )}
                                        </TableCell>
                                      </TableRow>
                                    ))}
                                  </TableBody>
                                </Table>
                              </CardContent>
                            )}
                          </Card>
                        ))}
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="relationships">
                      <div className="text-center py-10 text-gray-500">
                        Relationship diagram would be displayed here
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="views">
                      <div className="text-center py-10 text-gray-500">
                        No views found in this database
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
