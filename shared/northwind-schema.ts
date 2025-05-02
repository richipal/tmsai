import { pgTable, text, serial, integer, boolean, timestamp, jsonb, decimal, date, foreignKey } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { relations } from "drizzle-orm";
import { z } from "zod";

// Categories table
export const categories = pgTable("categories", {
  categoryId: serial("category_id").primaryKey(),
  categoryName: text("category_name").notNull(),
  description: text("description"),
  picture: text("picture"),
});

// Customers table
export const customers = pgTable("customers", {
  customerId: text("customer_id").primaryKey(),
  companyName: text("company_name").notNull(),
  contactName: text("contact_name"),
  contactTitle: text("contact_title"),
  address: text("address"),
  city: text("city"),
  region: text("region"),
  postalCode: text("postal_code"),
  country: text("country"),
  phone: text("phone"),
  fax: text("fax"),
});

// Employees table
export const employees = pgTable("employees", {
  employeeId: serial("employee_id").primaryKey(),
  lastName: text("last_name").notNull(),
  firstName: text("first_name").notNull(),
  title: text("title"),
  titleOfCourtesy: text("title_of_courtesy"),
  birthDate: date("birth_date"),
  hireDate: date("hire_date"),
  address: text("address"),
  city: text("city"),
  region: text("region"),
  postalCode: text("postal_code"),
  country: text("country"),
  homePhone: text("home_phone"),
  extension: text("extension"),
  notes: text("notes"),
  reportsTo: integer("reports_to"),
  photoPath: text("photo_path"),
}, (table) => {
  return {
    reportsToFk: foreignKey({
      columns: [table.reportsTo],
      foreignColumns: [table.employeeId],
    }),
  };
});

// Suppliers table
export const suppliers = pgTable("suppliers", {
  supplierId: serial("supplier_id").primaryKey(),
  companyName: text("company_name").notNull(),
  contactName: text("contact_name"),
  contactTitle: text("contact_title"),
  address: text("address"),
  city: text("city"),
  region: text("region"),
  postalCode: text("postal_code"),
  country: text("country"),
  phone: text("phone"),
  fax: text("fax"),
  homePage: text("home_page"),
});

// Products table
export const products = pgTable("products", {
  productId: serial("product_id").primaryKey(),
  productName: text("product_name").notNull(),
  supplierId: integer("supplier_id").references(() => suppliers.supplierId),
  categoryId: integer("category_id").references(() => categories.categoryId),
  quantityPerUnit: text("quantity_per_unit"),
  unitPrice: decimal("unit_price", { precision: 10, scale: 2 }),
  unitsInStock: integer("units_in_stock"),
  unitsOnOrder: integer("units_on_order"),
  reorderLevel: integer("reorder_level"),
  discontinued: boolean("discontinued").notNull(),
});

// Shippers table
export const shippers = pgTable("shippers", {
  shipperId: serial("shipper_id").primaryKey(),
  companyName: text("company_name").notNull(),
  phone: text("phone"),
});

// Orders table
export const orders = pgTable("orders", {
  orderId: serial("order_id").primaryKey(),
  customerId: text("customer_id").references(() => customers.customerId),
  employeeId: integer("employee_id").references(() => employees.employeeId),
  orderDate: date("order_date"),
  requiredDate: date("required_date"),
  shippedDate: date("shipped_date"),
  shipVia: integer("ship_via").references(() => shippers.shipperId),
  freight: decimal("freight", { precision: 10, scale: 2 }),
  shipName: text("ship_name"),
  shipAddress: text("ship_address"),
  shipCity: text("ship_city"),
  shipRegion: text("ship_region"),
  shipPostalCode: text("ship_postal_code"),
  shipCountry: text("ship_country"),
});

// Order Details table
export const orderDetails = pgTable("order_details", {
  orderId: integer("order_id").references(() => orders.orderId),
  productId: integer("product_id").references(() => products.productId),
  unitPrice: decimal("unit_price", { precision: 10, scale: 2 }).notNull(),
  quantity: integer("quantity").notNull(),
  discount: decimal("discount", { precision: 4, scale: 2 }).notNull(),
}, (table) => {
  return {
    pk: primaryKey(table.orderId, table.productId)
  }
});

// Define relations
export const categoriesRelations = relations(categories, ({ many }) => ({
  products: many(products),
}));

export const customersRelations = relations(customers, ({ many }) => ({
  orders: many(orders),
}));

export const employeesRelations = relations(employees, ({ many, one }) => ({
  orders: many(orders),
  manager: one(employees, {
    fields: [employees.reportsTo],
    references: [employees.employeeId],
  }),
  directReports: many(employees, {
    relationName: "manager",
  }),
}));

export const suppliersRelations = relations(suppliers, ({ many }) => ({
  products: many(products),
}));

export const productsRelations = relations(products, ({ one, many }) => ({
  category: one(categories, {
    fields: [products.categoryId],
    references: [categories.categoryId],
  }),
  supplier: one(suppliers, {
    fields: [products.supplierId],
    references: [suppliers.supplierId],
  }),
  orderDetails: many(orderDetails),
}));

export const shippersRelations = relations(shippers, ({ many }) => ({
  orders: many(orders),
}));

export const ordersRelations = relations(orders, ({ one, many }) => ({
  customer: one(customers, {
    fields: [orders.customerId],
    references: [customers.customerId],
  }),
  employee: one(employees, {
    fields: [orders.employeeId],
    references: [employees.employeeId],
  }),
  shipper: one(shippers, {
    fields: [orders.shipVia],
    references: [shippers.shipperId],
  }),
  orderDetails: many(orderDetails),
}));

export const orderDetailsRelations = relations(orderDetails, ({ one }) => ({
  order: one(orders, {
    fields: [orderDetails.orderId],
    references: [orders.orderId],
  }),
  product: one(products, {
    fields: [orderDetails.productId],
    references: [products.productId],
  }),
}));

// Add missing primaryKey function
function primaryKey(...columns: any[]) {
  return {
    name: 'pk_' + columns.map(c => c.name).join('_'),
    columns
  };
}