import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import NotFound from "@/pages/not-found";
import Dashboard from "@/pages/dashboard";
import QueryHistory from "@/pages/query-history";
import SavedQueries from "@/pages/saved-queries";
import DatabaseSchema from "@/pages/database-schema";
import Settings from "@/pages/settings";
import TrainingData from "@/pages/training-data";
import { useState, useEffect } from "react";

// Query Detail Page component - Simplified version for now
function QueryDetail({ params }: { params: { id: string } }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white shadow-md rounded-lg p-8 max-w-md">
        <h1 className="text-xl font-semibold mb-4">Query Details</h1>
        <p>Viewing query with ID: {params.id}</p>
        <p className="mt-4 text-sm text-gray-500">
          This page would show detailed information about a specific query.
        </p>
      </div>
    </div>
  );
}

function Router() {
  return (
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/query-history" component={QueryHistory} />
      <Route path="/query-history/:id" component={QueryDetail} />
      <Route path="/saved-queries" component={SavedQueries} />
      <Route path="/database-schema" component={DatabaseSchema} />
      <Route path="/training-data" component={TrainingData} />
      <Route path="/settings" component={Settings} />
      {/* Fallback to 404 */}
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  // Add meta tags for the document title and favicon
  useEffect(() => {
    document.title = "Vanna AI SQL Assistant";
    
    // Add Inter and Fira Mono fonts
    const fontLink = document.createElement("link");
    fontLink.href = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Mono&display=swap";
    fontLink.rel = "stylesheet";
    document.head.appendChild(fontLink);
    
    return () => {
      // Cleanup
      document.head.removeChild(fontLink);
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <Router />
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;
