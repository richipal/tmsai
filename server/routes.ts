import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { ensureFlaskService, startFlaskService, stopFlaskService } from "./vanna-service";
import { z } from "zod";
import { insertQuerySchema, insertDatabaseConnectionSchema } from "@shared/schema";
import fetch from "node-fetch";

// Flask service port
const FLASK_PORT = 8000;
const FLASK_BASE_URL = `http://localhost:${FLASK_PORT}`;

export async function registerRoutes(app: Express): Promise<Server> {
  console.log("Registering API routes...");
  
  // Start the Flask service when the server starts
  try {
    await startFlaskService();
    console.log("Flask service started successfully");
  } catch (error) {
    console.error("Failed to start Flask service:", error);
  }
  
  // Create HTTP server
  const httpServer = createServer(app);
  
  // Set up cleanup handler
  process.on('SIGINT', async () => {
    console.log('Shutting down gracefully...');
    await stopFlaskService();
    process.exit(0);
  });
  
  // API routes
  // --------------------------------------------------------
  
  // Database connections
  app.get('/api/connections', async (req, res) => {
    try {
      // In a real app, we would get the user ID from the session
      const userId = 1; // Demo user ID
      const connections = await storage.getDatabaseConnections(userId);
      res.json(connections);
    } catch (error) {
      console.error('Error fetching connections:', error);
      res.status(500).json({ message: 'Failed to fetch database connections' });
    }
  });
  
  app.post('/api/connections', async (req, res) => {
    try {
      const connectionData = insertDatabaseConnectionSchema.parse(req.body);
      const newConnection = await storage.insertDatabaseConnection(connectionData);
      res.status(201).json(newConnection);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ errors: error.errors });
      }
      console.error('Error creating connection:', error);
      res.status(500).json({ message: 'Failed to create database connection' });
    }
  });
  
  // Natural language queries
  app.post('/api/query', async (req, res) => {
    try {
      // Check if Flask service is running
      await ensureFlaskService();
      
      const { naturalLanguageQuery, databaseConnectionId } = req.body;
      
      if (!naturalLanguageQuery || !databaseConnectionId) {
        return res.status(400).json({ message: 'Query and database connection ID are required' });
      }
      
      // In a real app, get user ID from session
      const userId = 1; // Demo user ID
      
      // First, store the query in our database
      const queryData = {
        naturalLanguageQuery,
        databaseConnectionId,
        userId,
      };
      
      const validatedQuery = insertQuerySchema.parse(queryData);
      const savedQuery = await storage.insertQuery(validatedQuery);
      
      // Get database connection details
      const connection = await storage.getDatabaseConnectionById(databaseConnectionId);
      if (!connection) {
        return res.status(404).json({ message: 'Database connection not found' });
      }
      
      // Forward the request to the Flask service
      const flaskResponse = await fetch(`${FLASK_BASE_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: naturalLanguageQuery,
          connection: {
            type: connection.type,
            host: connection.host,
            port: connection.port,
            username: connection.username,
            password: connection.password,
            database: connection.database,
          }
        }),
      });
      
      if (!flaskResponse.ok) {
        const errorData = await flaskResponse.text();
        throw new Error(`Flask service error: ${errorData}`);
      }
      
      const result = await flaskResponse.json();
      
      // Update the query with the generated SQL
      await storage.updateQuery(savedQuery.id, {
        sqlQuery: result.sql,
        executionTime: result.execution_time,
      });
      
      // Store the query result
      if (result.data) {
        await storage.insertQueryResult({
          queryId: savedQuery.id,
          result: result.data,
          explanation: result.explanation,
        });
      }
      
      res.json(result);
    } catch (error) {
      console.error('Error processing query:', error);
      res.status(500).json({ message: 'Failed to process query', error: String(error) });
    }
  });
  
  // Query history
  app.get('/api/history', async (req, res) => {
    try {
      // In a real app, get user ID from session
      const userId = 1; // Demo user ID
      const queries = await storage.getQueriesByUserId(userId);
      res.json(queries);
    } catch (error) {
      console.error('Error fetching query history:', error);
      res.status(500).json({ message: 'Failed to fetch query history' });
    }
  });
  
  // Saved queries
  app.get('/api/saved-queries', async (req, res) => {
    try {
      // In a real app, get user ID from session
      const userId = 1; // Demo user ID
      const savedQueries = await storage.getSavedQueriesByUserId(userId);
      res.json(savedQueries);
    } catch (error) {
      console.error('Error fetching saved queries:', error);
      res.status(500).json({ message: 'Failed to fetch saved queries' });
    }
  });
  
  // Save a query
  app.post('/api/queries/:id/save', async (req, res) => {
    try {
      const queryId = parseInt(req.params.id, 10);
      if (isNaN(queryId)) {
        return res.status(400).json({ message: 'Invalid query ID' });
      }
      
      const updatedQuery = await storage.updateQuery(queryId, { isSaved: true });
      if (!updatedQuery) {
        return res.status(404).json({ message: 'Query not found' });
      }
      
      res.json(updatedQuery);
    } catch (error) {
      console.error('Error saving query:', error);
      res.status(500).json({ message: 'Failed to save query' });
    }
  });
  
  // Unsave a query
  app.post('/api/queries/:id/unsave', async (req, res) => {
    try {
      const queryId = parseInt(req.params.id, 10);
      if (isNaN(queryId)) {
        return res.status(400).json({ message: 'Invalid query ID' });
      }
      
      const updatedQuery = await storage.updateQuery(queryId, { isSaved: false });
      if (!updatedQuery) {
        return res.status(404).json({ message: 'Query not found' });
      }
      
      res.json(updatedQuery);
    } catch (error) {
      console.error('Error unsaving query:', error);
      res.status(500).json({ message: 'Failed to unsave query' });
    }
  });
  
  // Get query result
  app.get('/api/queries/:id/result', async (req, res) => {
    try {
      const queryId = parseInt(req.params.id, 10);
      if (isNaN(queryId)) {
        return res.status(400).json({ message: 'Invalid query ID' });
      }
      
      const query = await storage.getQueryById(queryId);
      if (!query) {
        return res.status(404).json({ message: 'Query not found' });
      }
      
      const result = await storage.getQueryResultByQueryId(queryId);
      if (!result) {
        return res.status(404).json({ message: 'Query result not found' });
      }
      
      res.json({
        query,
        result,
      });
    } catch (error) {
      console.error('Error fetching query result:', error);
      res.status(500).json({ message: 'Failed to fetch query result' });
    }
  });

  return httpServer;
}
