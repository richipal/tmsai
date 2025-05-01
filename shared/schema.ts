import { pgTable, text, serial, integer, boolean, timestamp, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";
import { relations } from "drizzle-orm";

// User table
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  displayName: text("display_name"),
  email: text("email"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Database connections table
export const databaseConnections = pgTable("database_connections", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  description: text("description"),
  type: text("type").notNull(), // mysql, postgresql, etc.
  host: text("host").notNull(),
  port: integer("port").notNull(),
  username: text("username").notNull(),
  password: text("password").notNull(),
  database: text("database").notNull(),
  userId: integer("user_id").references(() => users.id),
  isActive: boolean("is_active").default(false),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Queries table
export const queries = pgTable("queries", {
  id: serial("id").primaryKey(),
  naturalLanguageQuery: text("natural_language_query").notNull(),
  sqlQuery: text("sql_query"),
  databaseConnectionId: integer("database_connection_id").references(() => databaseConnections.id),
  userId: integer("user_id").references(() => users.id),
  isSaved: boolean("is_saved").default(false),
  executionTime: integer("execution_time"), // in milliseconds
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Query results table
export const queryResults = pgTable("query_results", {
  id: serial("id").primaryKey(),
  queryId: integer("query_id").references(() => queries.id).notNull(),
  result: jsonb("result").notNull(), // Store JSON result data
  explanation: text("explanation"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Relation definitions
export const usersRelations = relations(users, ({ many }) => ({
  databaseConnections: many(databaseConnections),
  queries: many(queries),
}));

export const databaseConnectionsRelations = relations(databaseConnections, ({ one, many }) => ({
  user: one(users, {
    fields: [databaseConnections.userId],
    references: [users.id],
  }),
  queries: many(queries),
}));

export const queriesRelations = relations(queries, ({ one, many }) => ({
  user: one(users, {
    fields: [queries.userId],
    references: [users.id],
  }),
  databaseConnection: one(databaseConnections, {
    fields: [queries.databaseConnectionId],
    references: [databaseConnections.id],
  }),
  results: many(queryResults),
}));

export const queryResultsRelations = relations(queryResults, ({ one }) => ({
  query: one(queries, {
    fields: [queryResults.queryId],
    references: [queries.id],
  }),
}));

// Zod schemas for validation
export const insertUserSchema = createInsertSchema(users, {
  username: (schema) => schema.min(3, "Username must be at least 3 characters"),
  password: (schema) => schema.min(8, "Password must be at least 8 characters"),
  email: (schema) => schema.email("Please provide a valid email").optional(),
}).omit({ createdAt: true });

export const insertDatabaseConnectionSchema = createInsertSchema(databaseConnections, {
  name: (schema) => schema.min(1, "Name is required"),
  host: (schema) => schema.min(1, "Host is required"),
  username: (schema) => schema.min(1, "Username is required"),
  password: (schema) => schema.min(1, "Password is required"),
  database: (schema) => schema.min(1, "Database name is required"),
}).omit({ createdAt: true });

export const insertQuerySchema = createInsertSchema(queries, {
  naturalLanguageQuery: (schema) => schema.min(1, "Query is required"),
}).omit({ createdAt: true, executionTime: true });

export const insertQueryResultSchema = createInsertSchema(queryResults).omit({ createdAt: true });

// Types for our schemas
export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

export type InsertDatabaseConnection = z.infer<typeof insertDatabaseConnectionSchema>;
export type DatabaseConnection = typeof databaseConnections.$inferSelect;

export type InsertQuery = z.infer<typeof insertQuerySchema>;
export type Query = typeof queries.$inferSelect;

export type InsertQueryResult = z.infer<typeof insertQueryResultSchema>;
export type QueryResult = typeof queryResults.$inferSelect;
