import { useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useQuery } from "@tanstack/react-query";
import { getDatabaseConnections, DatabaseConnectionType } from "@/lib/flask-service";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Menu } from "lucide-react";
import { useMobile } from "@/hooks/use-mobile";

interface HeaderProps {
  selectedConnectionId: number;
  onConnectionChange: (connectionId: number) => void;
}

export default function Header({ selectedConnectionId, onConnectionChange }: HeaderProps) {
  const isMobile = useMobile();
  
  const { data: connections, isLoading } = useQuery({
    queryKey: ['/api/connections'],
    queryFn: getDatabaseConnections,
  });
  
  const handleConnectionChange = (value: string) => {
    onConnectionChange(parseInt(value, 10));
  };
  
  return (
    <header className="bg-white shadow-sm z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        {isMobile && (
          <Sheet>
            <SheetTrigger asChild>
              <button className="p-2 mr-3 text-gray-500 rounded-md hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500">
                <Menu className="h-6 w-6" />
                <span className="sr-only">Open menu</span>
              </button>
            </SheetTrigger>
            <SheetContent side="left" className="p-0">
              <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
                <div className="flex-shrink-0 flex items-center px-4">
                  <svg className="h-8 w-8 text-primary-600" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 4L4 8L12 12L20 8L12 4Z" fill="currentColor" />
                    <path d="M4 12L12 16L20 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M4 16L12 20L20 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <h1 className="ml-3 text-xl font-bold text-gray-900">Vanna AI</h1>
                </div>
                <nav className="mt-5 px-2 space-y-1">
                  <a href="/" className="group flex items-center px-2 py-2 text-base font-medium rounded-md bg-gray-100 text-gray-900">
                    <svg className="mr-4 h-6 w-6 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                    Dashboard
                  </a>
                  <a href="/query-history" className="group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900">
                    <svg className="mr-4 h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Query History
                  </a>
                  <a href="/saved-queries" className="group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900">
                    <svg className="mr-4 h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                    </svg>
                    Saved Queries
                  </a>
                  <a href="/database-schema" className="group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900">
                    <svg className="mr-4 h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                    </svg>
                    Database Schema
                  </a>
                  <a href="/settings" className="group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900">
                    <svg className="mr-4 h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Settings
                  </a>
                </nav>
              </div>
            </SheetContent>
          </Sheet>
        )}
        
        <div className="flex items-center space-x-3">
          <svg className="h-8 w-8 text-primary-600" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 4L4 8L12 12L20 8L12 4Z" fill="currentColor" />
            <path d="M4 12L12 16L20 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M4 16L12 20L20 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <h1 className="text-xl font-semibold text-gray-900">Vanna AI SQL Assistant</h1>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Select
              value={selectedConnectionId.toString()}
              onValueChange={handleConnectionChange}
              disabled={isLoading}
            >
              <SelectTrigger className="w-[220px]">
                <SelectValue placeholder="Select database" />
              </SelectTrigger>
              <SelectContent>
                {connections?.map((connection) => (
                  <SelectItem 
                    key={connection.id}
                    value={connection.id.toString()}
                  >
                    {connection.name} {connection.isActive ? "(connected)" : ""}
                  </SelectItem>
                ))}
                <SelectItem value="new">+ Connect New Database</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="relative ml-3">
            <button 
              type="button" 
              className="flex items-center max-w-xs text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500" 
              id="user-menu-button" 
              aria-expanded="false" 
              aria-haspopup="true"
            >
              <span className="sr-only">Open user menu</span>
              <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center text-white">
                <span>DU</span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
