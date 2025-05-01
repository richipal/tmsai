import { apiRequest } from "./queryClient";

export type DatabaseConnectionType = {
  id: number;
  name: string;
  description?: string;
  type: string;
  host: string;
  port: number;
  username: string;
  password: string;
  database: string;
  isActive: boolean;
};

export type QueryResultData = {
  sql: string;
  data: Record<string, any>[];
  columns: string[];
  explanation: string;
  execution_time: number;
};

export type QueryHistoryItem = {
  id: number;
  naturalLanguageQuery: string;
  sqlQuery?: string;
  executionTime?: number;
  createdAt: string;
  isSaved: boolean;
};

/**
 * Get all database connections for the current user
 */
export async function getDatabaseConnections(): Promise<DatabaseConnectionType[]> {
  const response = await fetch('/api/connections', {
    credentials: 'include',
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch connections: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Create a new database connection
 */
export async function createDatabaseConnection(connection: Omit<DatabaseConnectionType, 'id' | 'isActive'>): Promise<DatabaseConnectionType> {
  const response = await apiRequest('POST', '/api/connections', connection);
  return await response.json();
}

/**
 * Execute a natural language query
 */
export async function executeQuery(naturalLanguageQuery: string, databaseConnectionId: number): Promise<QueryResultData> {
  const response = await apiRequest('POST', '/api/query', {
    naturalLanguageQuery,
    databaseConnectionId,
  });
  
  return await response.json();
}

/**
 * Get query history for the current user
 */
export async function getQueryHistory(): Promise<QueryHistoryItem[]> {
  const response = await fetch('/api/history', {
    credentials: 'include',
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch query history: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Get saved queries for the current user
 */
export async function getSavedQueries(): Promise<QueryHistoryItem[]> {
  const response = await fetch('/api/saved-queries', {
    credentials: 'include',
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch saved queries: ${response.statusText}`);
  }
  
  return await response.json();
}

/**
 * Save a query
 */
export async function saveQuery(queryId: number): Promise<QueryHistoryItem> {
  const response = await apiRequest('POST', `/api/queries/${queryId}/save`, {});
  return await response.json();
}

/**
 * Unsave a query
 */
export async function unsaveQuery(queryId: number): Promise<QueryHistoryItem> {
  const response = await apiRequest('POST', `/api/queries/${queryId}/unsave`, {});
  return await response.json();
}

/**
 * Get a specific query result
 */
export async function getQueryResult(queryId: number): Promise<{query: QueryHistoryItem, result: {result: Record<string, any>[], explanation: string}}> {
  const response = await fetch(`/api/queries/${queryId}/result`, {
    credentials: 'include',
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch query result: ${response.statusText}`);
  }
  
  return await response.json();
}
