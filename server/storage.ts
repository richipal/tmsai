import { db } from "@db";
import { 
  users, 
  databaseConnections, 
  queries, 
  queryResults,
  InsertUser,
  InsertDatabaseConnection,
  InsertQuery,
  InsertQueryResult,
  User,
  DatabaseConnection,
  Query,
  QueryResult
} from "@shared/schema";
import { eq, desc, and } from "drizzle-orm";

// User operations
export const storage = {
  // User operations
  getUserById: async (id: number): Promise<User | undefined> => {
    const result = await db.select().from(users).where(eq(users.id, id));
    return result[0];
  },
  
  getUserByUsername: async (username: string): Promise<User | undefined> => {
    const result = await db.select().from(users).where(eq(users.username, username));
    return result[0];
  },
  
  insertUser: async (user: InsertUser): Promise<User> => {
    const [newUser] = await db.insert(users).values(user).returning();
    return newUser;
  },
  
  // Database connection operations
  getDatabaseConnections: async (userId: number): Promise<DatabaseConnection[]> => {
    return await db.select().from(databaseConnections)
      .where(eq(databaseConnections.userId, userId))
      .orderBy(databaseConnections.name);
  },
  
  getDatabaseConnectionById: async (id: number): Promise<DatabaseConnection | undefined> => {
    const result = await db.select().from(databaseConnections).where(eq(databaseConnections.id, id));
    return result[0];
  },
  
  insertDatabaseConnection: async (connection: InsertDatabaseConnection): Promise<DatabaseConnection> => {
    const [newConnection] = await db.insert(databaseConnections).values(connection).returning();
    return newConnection;
  },
  
  updateDatabaseConnection: async (id: number, connection: Partial<InsertDatabaseConnection>): Promise<DatabaseConnection | undefined> => {
    const [updatedConnection] = await db.update(databaseConnections)
      .set(connection)
      .where(eq(databaseConnections.id, id))
      .returning();
    return updatedConnection;
  },
  
  // Query operations
  getQueriesByUserId: async (userId: number, limit = 10): Promise<Query[]> => {
    return await db.select().from(queries)
      .where(eq(queries.userId, userId))
      .orderBy(desc(queries.createdAt))
      .limit(limit);
  },
  
  getSavedQueriesByUserId: async (userId: number): Promise<Query[]> => {
    return await db.select().from(queries)
      .where(and(
        eq(queries.userId, userId),
        eq(queries.isSaved, true)
      ))
      .orderBy(desc(queries.createdAt));
  },
  
  getQueryById: async (id: number): Promise<Query | undefined> => {
    const result = await db.select().from(queries).where(eq(queries.id, id));
    return result[0];
  },
  
  insertQuery: async (query: InsertQuery): Promise<Query> => {
    const [newQuery] = await db.insert(queries).values(query).returning();
    return newQuery;
  },
  
  updateQuery: async (id: number, query: Partial<InsertQuery>): Promise<Query | undefined> => {
    const [updatedQuery] = await db.update(queries)
      .set(query)
      .where(eq(queries.id, id))
      .returning();
    return updatedQuery;
  },
  
  // Query result operations
  getQueryResultByQueryId: async (queryId: number): Promise<QueryResult | undefined> => {
    const result = await db.select().from(queryResults).where(eq(queryResults.queryId, queryId));
    return result[0];
  },
  
  insertQueryResult: async (result: InsertQueryResult): Promise<QueryResult> => {
    const [newResult] = await db.insert(queryResults).values(result).returning();
    return newResult;
  },
};
