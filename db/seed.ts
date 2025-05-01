import { db } from "./index";
import * as schema from "@shared/schema";
import { eq } from "drizzle-orm";

async function seed() {
  try {
    // Check if we already have a default user
    const existingUsers = await db.select().from(schema.users).where(eq(schema.users.username, "demo"));
    
    // Only create a user if none exists
    if (existingUsers.length === 0) {
      // Add a demo user
      const [user] = await db.insert(schema.users).values({
        username: "demo",
        password: "password123", // In a real app, this would be hashed
        displayName: "Demo User",
        email: "demo@example.com",
      }).returning();
      
      console.log("Created demo user:", user);
      
      // Add a sample database connection
      const [connection] = await db.insert(schema.databaseConnections).values({
        name: "northwind_db",
        description: "Sample Northwind database",
        type: "mysql",
        host: "localhost",
        port: 3306,
        username: "root",
        password: "password",
        database: "northwind",
        userId: user.id,
        isActive: true,
      }).returning();
      
      console.log("Created database connection:", connection);
      
      // Add some example queries
      const exampleQueries = [
        "Show me the top 5 products by revenue",
        "Customer orders by country",
        "Monthly sales trend for 2023",
        "Top selling products in Q2",
        "Employee performance metrics"
      ];
      
      for (const queryText of exampleQueries) {
        const [query] = await db.insert(schema.queries).values({
          naturalLanguageQuery: queryText,
          userId: user.id,
          databaseConnectionId: connection.id,
          isSaved: Math.random() > 0.5, // Randomly save some queries
        }).returning();
        
        console.log("Created example query:", query);
      }
    } else {
      console.log("Database already seeded. Skipping...");
    }
  } catch (error) {
    console.error("Error seeding database:", error);
  }
}

seed();
