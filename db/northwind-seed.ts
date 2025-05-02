import { db } from "./index";
import * as northwind from "@shared/northwind-schema";
import { eq } from "drizzle-orm";

async function seedNorthwind() {
  try {
    console.log("Starting Northwind database seeding...");

    // Check if we already have data
    const existingCategories = await db.select({ count: { count: northwind.categories.categoryId } }).from(northwind.categories);
    
    if (existingCategories.length > 0 && existingCategories[0].count.count > 0) {
      console.log("Northwind data already exists. Skipping seeding.");
      return;
    }
    
    // Seed Categories
    const categories = [
      { categoryName: "Beverages", description: "Soft drinks, coffees, teas, beers, and ales" },
      { categoryName: "Condiments", description: "Sweet and savory sauces, relishes, spreads, and seasonings" },
      { categoryName: "Confections", description: "Desserts, candies, and sweet breads" },
      { categoryName: "Dairy Products", description: "Cheeses" },
      { categoryName: "Grains/Cereals", description: "Breads, crackers, pasta, and cereal" },
      { categoryName: "Meat/Poultry", description: "Prepared meats" },
      { categoryName: "Produce", description: "Dried fruit and bean curd" },
      { categoryName: "Seafood", description: "Seaweed and fish" }
    ];
    
    const insertedCategories = await db.insert(northwind.categories)
      .values(categories)
      .returning();
    
    console.log(`Inserted ${insertedCategories.length} categories`);
    
    // Seed Suppliers
    const suppliers = [
      { 
        companyName: "Exotic Liquids", 
        contactName: "Charlotte Cooper", 
        contactTitle: "Purchasing Manager",
        address: "49 Gilbert St.",
        city: "London",
        region: null,
        postalCode: "EC1 4SD",
        country: "UK",
        phone: "(171) 555-2222"
      },
      { 
        companyName: "New Orleans Cajun Delights", 
        contactName: "Shelley Burke", 
        contactTitle: "Order Administrator",
        address: "P.O. Box 78934",
        city: "New Orleans",
        region: "LA",
        postalCode: "70117",
        country: "USA",
        phone: "(100) 555-4822"
      },
      { 
        companyName: "Grandma Kelly's Homestead", 
        contactName: "Regina Murphy", 
        contactTitle: "Sales Representative",
        address: "707 Oxford Rd.",
        city: "Ann Arbor",
        region: "MI",
        postalCode: "48104",
        country: "USA",
        phone: "(313) 555-5735"
      },
      { 
        companyName: "Tokyo Traders", 
        contactName: "Yoshi Nagase", 
        contactTitle: "Marketing Manager",
        address: "9-8 Sekimai Musashino-shi",
        city: "Tokyo",
        region: null,
        postalCode: "100",
        country: "Japan",
        phone: "(03) 3555-5011"
      },
      { 
        companyName: "Cooperativa de Quesos 'Las Cabras'", 
        contactName: "Antonio del Valle Saavedra", 
        contactTitle: "Export Administrator",
        address: "Calle del Rosal 4",
        city: "Oviedo",
        region: "Asturias",
        postalCode: "33007",
        country: "Spain",
        phone: "(98) 598 76 54"
      }
    ];
    
    const insertedSuppliers = await db.insert(northwind.suppliers)
      .values(suppliers)
      .returning();
    
    console.log(`Inserted ${insertedSuppliers.length} suppliers`);
    
    // Seed Products
    const products = [
      {
        productName: "Chai",
        supplierId: insertedSuppliers[0].supplierId,
        categoryId: insertedCategories[0].categoryId,
        quantityPerUnit: "10 boxes x 20 bags",
        unitPrice: 18.00,
        unitsInStock: 39,
        unitsOnOrder: 0,
        reorderLevel: 10,
        discontinued: false
      },
      {
        productName: "Chang",
        supplierId: insertedSuppliers[0].supplierId,
        categoryId: insertedCategories[0].categoryId,
        quantityPerUnit: "24 - 12 oz bottles",
        unitPrice: 19.00,
        unitsInStock: 17,
        unitsOnOrder: 40,
        reorderLevel: 25,
        discontinued: false
      },
      {
        productName: "Aniseed Syrup",
        supplierId: insertedSuppliers[0].supplierId,
        categoryId: insertedCategories[1].categoryId,
        quantityPerUnit: "12 - 550 ml bottles",
        unitPrice: 10.00,
        unitsInStock: 13,
        unitsOnOrder: 70,
        reorderLevel: 25,
        discontinued: false
      },
      {
        productName: "Chef Anton's Cajun Seasoning",
        supplierId: insertedSuppliers[1].supplierId,
        categoryId: insertedCategories[1].categoryId,
        quantityPerUnit: "48 - 6 oz jars",
        unitPrice: 22.00,
        unitsInStock: 53,
        unitsOnOrder: 0,
        reorderLevel: 0,
        discontinued: false
      },
      {
        productName: "Queso Cabrales",
        supplierId: insertedSuppliers[4].supplierId,
        categoryId: insertedCategories[3].categoryId,
        quantityPerUnit: "1 kg pkg.",
        unitPrice: 21.00,
        unitsInStock: 22,
        unitsOnOrder: 30,
        reorderLevel: 30,
        discontinued: false
      },
      {
        productName: "Konbu",
        supplierId: insertedSuppliers[3].supplierId,
        categoryId: insertedCategories[7].categoryId,
        quantityPerUnit: "2 kg box",
        unitPrice: 6.00,
        unitsInStock: 24,
        unitsOnOrder: 0,
        reorderLevel: 5,
        discontinued: false
      },
      {
        productName: "Uncle Bob's Organic Dried Pears",
        supplierId: insertedSuppliers[2].supplierId,
        categoryId: insertedCategories[6].categoryId,
        quantityPerUnit: "12 - 1 lb pkgs.",
        unitPrice: 30.00,
        unitsInStock: 15,
        unitsOnOrder: 0,
        reorderLevel: 10,
        discontinued: false
      },
      {
        productName: "Ikura",
        supplierId: insertedSuppliers[3].supplierId,
        categoryId: insertedCategories[7].categoryId,
        quantityPerUnit: "12 - 200 ml jars",
        unitPrice: 31.00,
        unitsInStock: 31,
        unitsOnOrder: 0,
        reorderLevel: 0,
        discontinued: false
      }
    ];
    
    const insertedProducts = await db.insert(northwind.products)
      .values(products)
      .returning();
    
    console.log(`Inserted ${insertedProducts.length} products`);
    
    // Seed Customers
    const customers = [
      {
        customerId: "ALFKI",
        companyName: "Alfreds Futterkiste",
        contactName: "Maria Anders",
        contactTitle: "Sales Representative",
        address: "Obere Str. 57",
        city: "Berlin",
        region: null,
        postalCode: "12209",
        country: "Germany",
        phone: "030-0074321"
      },
      {
        customerId: "ANATR",
        companyName: "Ana Trujillo Emparedados y helados",
        contactName: "Ana Trujillo",
        contactTitle: "Owner",
        address: "Avda. de la Constitución 2222",
        city: "México D.F.",
        region: null,
        postalCode: "05021",
        country: "Mexico",
        phone: "(5) 555-4729"
      },
      {
        customerId: "ANTON",
        companyName: "Antonio Moreno Taquería",
        contactName: "Antonio Moreno",
        contactTitle: "Owner",
        address: "Mataderos 2312",
        city: "México D.F.",
        region: null,
        postalCode: "05023",
        country: "Mexico",
        phone: "(5) 555-3932"
      },
      {
        customerId: "AROUT",
        companyName: "Around the Horn",
        contactName: "Thomas Hardy",
        contactTitle: "Sales Representative",
        address: "120 Hanover Sq.",
        city: "London",
        region: null,
        postalCode: "WA1 1DP",
        country: "UK",
        phone: "(171) 555-7788"
      }
    ];
    
    await db.insert(northwind.customers)
      .values(customers)
      .returning();
    
    console.log(`Inserted ${customers.length} customers`);
    
    // Seed Employees
    const employees = [
      {
        lastName: "Davolio",
        firstName: "Nancy",
        title: "Sales Representative",
        titleOfCourtesy: "Ms.",
        birthDate: new Date("1968-12-08"),
        hireDate: new Date("2022-05-01"),
        address: "507 - 20th Ave. E. Apt. 2A",
        city: "Seattle",
        region: "WA",
        postalCode: "98122",
        country: "USA",
        homePhone: "(206) 555-9857",
        extension: "5467",
        notes: "Education includes a BA in psychology from Colorado State University. She also completed 'The Art of the Cold Call.' Nancy is a member of Toastmasters International."
      },
      {
        lastName: "Fuller",
        firstName: "Andrew",
        title: "Vice President, Sales",
        titleOfCourtesy: "Dr.",
        birthDate: new Date("1952-02-19"),
        hireDate: new Date("2022-08-14"),
        address: "908 W. Capital Way",
        city: "Tacoma",
        region: "WA",
        postalCode: "98401",
        country: "USA",
        homePhone: "(206) 555-9482",
        extension: "3457",
        notes: "Andrew received his BTS commercial and a Ph.D. in international marketing from the University of Dallas. He is fluent in French and Italian and reads German. He joined the company as a sales representative, was promoted to sales manager and was then named vice president of sales. Andrew is a member of the Sales Management Roundtable, the Seattle Chamber of Commerce, and the Pacific Rim Importers Association."
      }
    ];
    
    const insertedEmployees = await db.insert(northwind.employees)
      .values(employees)
      .returning();
    
    console.log(`Inserted ${insertedEmployees.length} employees`);
    
    // Update reportsTo for employees
    await db.update(northwind.employees)
      .set({ reportsTo: insertedEmployees[1].employeeId })
      .where(eq(northwind.employees.employeeId, insertedEmployees[0].employeeId));
    
    console.log("Updated employee reporting relationships");
    
    // Seed Shippers
    const shippers = [
      {
        companyName: "Speedy Express",
        phone: "(503) 555-9831"
      },
      {
        companyName: "United Package",
        phone: "(503) 555-3199"
      },
      {
        companyName: "Federal Shipping",
        phone: "(503) 555-9931"
      }
    ];
    
    const insertedShippers = await db.insert(northwind.shippers)
      .values(shippers)
      .returning();
    
    console.log(`Inserted ${insertedShippers.length} shippers`);
    
    // Seed Orders
    const orders = [
      {
        customerId: "ALFKI",
        employeeId: insertedEmployees[0].employeeId,
        orderDate: new Date("2022-07-04"),
        requiredDate: new Date("2022-07-16"),
        shippedDate: new Date("2022-07-10"),
        shipVia: insertedShippers[0].shipperId,
        freight: 32.38,
        shipName: "Alfreds Futterkiste",
        shipAddress: "Obere Str. 57",
        shipCity: "Berlin",
        shipRegion: null,
        shipPostalCode: "12209",
        shipCountry: "Germany"
      },
      {
        customerId: "ANATR",
        employeeId: insertedEmployees[0].employeeId,
        orderDate: new Date("2022-07-05"),
        requiredDate: new Date("2022-08-16"),
        shippedDate: new Date("2022-07-12"),
        shipVia: insertedShippers[1].shipperId,
        freight: 11.61,
        shipName: "Ana Trujillo Emparedados y helados",
        shipAddress: "Avda. de la Constitución 2222",
        shipCity: "México D.F.",
        shipRegion: null,
        shipPostalCode: "05021",
        shipCountry: "Mexico"
      },
      {
        customerId: "ANTON",
        employeeId: insertedEmployees[1].employeeId,
        orderDate: new Date("2022-07-08"),
        requiredDate: new Date("2022-08-05"),
        shippedDate: new Date("2022-07-15"),
        shipVia: insertedShippers[2].shipperId,
        freight: 65.83,
        shipName: "Antonio Moreno Taquería",
        shipAddress: "Mataderos 2312",
        shipCity: "México D.F.",
        shipRegion: null,
        shipPostalCode: "05023",
        shipCountry: "Mexico"
      }
    ];
    
    const insertedOrders = await db.insert(northwind.orders)
      .values(orders)
      .returning();
    
    console.log(`Inserted ${insertedOrders.length} orders`);
    
    // Seed Order Details
    const orderDetailsData = [
      {
        orderId: insertedOrders[0].orderId,
        productId: insertedProducts[0].productId,
        unitPrice: 18.00,
        quantity: 12,
        discount: 0.00
      },
      {
        orderId: insertedOrders[0].orderId,
        productId: insertedProducts[1].productId,
        unitPrice: 19.00,
        quantity: 10,
        discount: 0.00
      },
      {
        orderId: insertedOrders[1].orderId,
        productId: insertedProducts[2].productId,
        unitPrice: 10.00,
        quantity: 5,
        discount: 0.15
      },
      {
        orderId: insertedOrders[1].orderId,
        productId: insertedProducts[3].productId,
        unitPrice: 22.00,
        quantity: 9,
        discount: 0.05
      },
      {
        orderId: insertedOrders[2].orderId,
        productId: insertedProducts[4].productId,
        unitPrice: 21.00,
        quantity: 2,
        discount: 0.00
      },
      {
        orderId: insertedOrders[2].orderId,
        productId: insertedProducts[7].productId,
        unitPrice: 31.00,
        quantity: 8,
        discount: 0.10
      }
    ];
    
    for (const detail of orderDetailsData) {
      await db.insert(northwind.orderDetails)
        .values(detail);
    }
    
    console.log(`Inserted ${orderDetailsData.length} order details`);
    
    console.log("Northwind database seeding completed successfully!");
  } catch (error) {
    console.error("Error seeding Northwind database:", error);
  }
}

seedNorthwind();