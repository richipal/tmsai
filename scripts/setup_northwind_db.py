"""
Script to set up the Northwind database tables and sample data
"""
import os
import psycopg
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get database connection from environment variables
DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    logger.error("DATABASE_URL environment variable not set")
    exit(1)

# Northwind tables creation SQL
TABLES_SQL = """
-- Create Categories table
CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(15) NOT NULL,
    description TEXT,
    picture BYTEA
);

-- Create Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id CHAR(5) PRIMARY KEY,
    company_name VARCHAR(40) NOT NULL,
    contact_name VARCHAR(30),
    contact_title VARCHAR(30),
    address VARCHAR(60),
    city VARCHAR(15),
    region VARCHAR(15),
    postal_code VARCHAR(10),
    country VARCHAR(15),
    phone VARCHAR(24),
    fax VARCHAR(24)
);

-- Create Employees table
CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    last_name VARCHAR(20) NOT NULL,
    first_name VARCHAR(10) NOT NULL,
    title VARCHAR(30),
    title_of_courtesy VARCHAR(25),
    birth_date DATE,
    hire_date DATE,
    address VARCHAR(60),
    city VARCHAR(15),
    region VARCHAR(15),
    postal_code VARCHAR(10),
    country VARCHAR(15),
    home_phone VARCHAR(24),
    extension VARCHAR(4),
    photo BYTEA,
    notes TEXT,
    reports_to INTEGER REFERENCES employees(employee_id),
    photo_path VARCHAR(255)
);

-- Create Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id SERIAL PRIMARY KEY,
    company_name VARCHAR(40) NOT NULL,
    contact_name VARCHAR(30),
    contact_title VARCHAR(30),
    address VARCHAR(60),
    city VARCHAR(15),
    region VARCHAR(15),
    postal_code VARCHAR(10),
    country VARCHAR(15),
    phone VARCHAR(24),
    fax VARCHAR(24),
    homepage TEXT
);

-- Create Products table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(40) NOT NULL,
    supplier_id INTEGER REFERENCES suppliers(supplier_id),
    category_id INTEGER REFERENCES categories(category_id),
    quantity_per_unit VARCHAR(20),
    unit_price DECIMAL(10, 2),
    units_in_stock SMALLINT,
    units_on_order SMALLINT,
    reorder_level SMALLINT,
    discontinued BOOLEAN NOT NULL
);

-- Create Shippers table
CREATE TABLE IF NOT EXISTS shippers (
    shipper_id SERIAL PRIMARY KEY,
    company_name VARCHAR(40) NOT NULL,
    phone VARCHAR(24)
);

-- Create Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id CHAR(5) REFERENCES customers(customer_id),
    employee_id INTEGER REFERENCES employees(employee_id),
    order_date DATE,
    required_date DATE,
    shipped_date DATE,
    ship_via INTEGER REFERENCES shippers(shipper_id),
    freight DECIMAL(10, 2),
    ship_name VARCHAR(40),
    ship_address VARCHAR(60),
    ship_city VARCHAR(15),
    ship_region VARCHAR(15),
    ship_postal_code VARCHAR(10),
    ship_country VARCHAR(15)
);

-- Create Order Details table
CREATE TABLE IF NOT EXISTS order_details (
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    unit_price DECIMAL(10, 2) NOT NULL,
    quantity SMALLINT NOT NULL,
    discount REAL NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
"""

# Sample data
SAMPLE_DATA = {
    "categories": [
        {"category_id": 1, "category_name": "Beverages", "description": "Soft drinks, coffees, teas, beers, and ales"},
        {"category_id": 2, "category_name": "Condiments", "description": "Sweet and savory sauces, relishes, spreads, and seasonings"},
        {"category_id": 3, "category_name": "Confections", "description": "Desserts, candies, and sweet breads"},
        {"category_id": 4, "category_name": "Dairy Products", "description": "Cheeses and milk products"},
        {"category_id": 5, "category_name": "Grains/Cereals", "description": "Breads, crackers, pasta, and cereal"},
        {"category_id": 6, "category_name": "Meat/Poultry", "description": "Prepared meats"},
        {"category_id": 7, "category_name": "Produce", "description": "Dried fruit and bean curd"},
        {"category_id": 8, "category_name": "Seafood", "description": "Seaweed and fish"}
    ],
    "suppliers": [
        {"supplier_id": 1, "company_name": "Exotic Liquids", "contact_name": "Charlotte Cooper", "contact_title": "Purchasing Manager", "address": "49 Gilbert St.", "city": "London", "region": None, "postal_code": "EC1 4SD", "country": "UK", "phone": "(171) 555-2222"},
        {"supplier_id": 2, "company_name": "New Orleans Cajun Delights", "contact_name": "Shelley Burke", "contact_title": "Order Administrator", "address": "P.O. Box 78934", "city": "New Orleans", "region": "LA", "postal_code": "70117", "country": "USA", "phone": "(100) 555-4822"},
        {"supplier_id": 3, "company_name": "Grandma Kelly's Homestead", "contact_name": "Regina Murphy", "contact_title": "Sales Representative", "address": "707 Oxford Rd.", "city": "Ann Arbor", "region": "MI", "postal_code": "48104", "country": "USA", "phone": "(313) 555-5735"}
    ],
    "products": [
        {"product_id": 1, "product_name": "Chai", "supplier_id": 1, "category_id": 1, "quantity_per_unit": "10 boxes x 20 bags", "unit_price": 18.00, "units_in_stock": 39, "units_on_order": 0, "reorder_level": 10, "discontinued": False},
        {"product_id": 2, "product_name": "Chang", "supplier_id": 1, "category_id": 1, "quantity_per_unit": "24 - 12 oz bottles", "unit_price": 19.00, "units_in_stock": 17, "units_on_order": 40, "reorder_level": 25, "discontinued": False},
        {"product_id": 3, "product_name": "Aniseed Syrup", "supplier_id": 1, "category_id": 2, "quantity_per_unit": "12 - 550 ml bottles", "unit_price": 10.00, "units_in_stock": 13, "units_on_order": 70, "reorder_level": 25, "discontinued": False},
        {"product_id": 4, "product_name": "Chef Anton's Cajun Seasoning", "supplier_id": 2, "category_id": 2, "quantity_per_unit": "48 - 6 oz jars", "unit_price": 22.00, "units_in_stock": 53, "units_on_order": 0, "reorder_level": 0, "discontinued": False}
    ],
    "customers": [
        {"customer_id": "ALFKI", "company_name": "Alfreds Futterkiste", "contact_name": "Maria Anders", "contact_title": "Sales Representative", "address": "Obere Str. 57", "city": "Berlin", "region": None, "postal_code": "12209", "country": "Germany", "phone": "030-0074321"},
        {"customer_id": "ANATR", "company_name": "Ana Trujillo Emparedados y helados", "contact_name": "Ana Trujillo", "contact_title": "Owner", "address": "Avda. de la Constitución 2222", "city": "México D.F.", "region": None, "postal_code": "05021", "country": "Mexico", "phone": "(5) 555-4729"},
        {"customer_id": "ANTON", "company_name": "Antonio Moreno Taquería", "contact_name": "Antonio Moreno", "contact_title": "Owner", "address": "Mataderos 2312", "city": "México D.F.", "region": None, "postal_code": "05023", "country": "Mexico", "phone": "(5) 555-3932"}
    ],
    "employees": [
        {"employee_id": 1, "last_name": "Davolio", "first_name": "Nancy", "title": "Sales Representative", "title_of_courtesy": "Ms.", "birth_date": "1968-12-08", "hire_date": "1992-05-01", "address": "507 - 20th Ave. E. Apt. 2A", "city": "Seattle", "region": "WA", "postal_code": "98122", "country": "USA", "home_phone": "(206) 555-9857", "extension": "5467", "reports_to": None, "notes": "Education includes a BA in psychology from Colorado State University. She also completed 'The Art of the Cold Call.' Nancy is a member of Toastmasters International."},
        {"employee_id": 2, "last_name": "Fuller", "first_name": "Andrew", "title": "Vice President, Sales", "title_of_courtesy": "Dr.", "birth_date": "1952-02-19", "hire_date": "1992-08-14", "address": "908 W. Capital Way", "city": "Tacoma", "region": "WA", "postal_code": "98401", "country": "USA", "home_phone": "(206) 555-9482", "extension": "3457", "reports_to": None, "notes": "Andrew received his BTS commercial and a Ph.D. in international marketing from the University of Dallas. He is fluent in French and Italian and reads German. He joined the company as a sales representative, was promoted to sales manager and was then named vice president of sales. Andrew is a member of the Sales Management Roundtable, the Seattle Chamber of Commerce, and the Pacific Rim Importers Association."},
        {"employee_id": 3, "last_name": "Leverling", "first_name": "Janet", "title": "Sales Representative", "title_of_courtesy": "Ms.", "birth_date": "1963-08-30", "hire_date": "1992-04-01", "address": "722 Moss Bay Blvd.", "city": "Kirkland", "region": "WA", "postal_code": "98033", "country": "USA", "home_phone": "(206) 555-3412", "extension": "3355", "reports_to": 2, "notes": "Janet has a BS degree in chemistry from Boston College. She has also completed a certificate program in food retailing management. Janet was hired as a sales associate and was promoted to sales representative."}
    ],
    "shippers": [
        {"shipper_id": 1, "company_name": "Speedy Express", "phone": "(503) 555-9831"},
        {"shipper_id": 2, "company_name": "United Package", "phone": "(503) 555-3199"},
        {"shipper_id": 3, "company_name": "Federal Shipping", "phone": "(503) 555-9931"}
    ],
    "orders": [
        {"order_id": 10248, "customer_id": "ALFKI", "employee_id": 1, "order_date": "2022-07-04", "required_date": "2022-08-01", "shipped_date": "2022-07-16", "ship_via": 3, "freight": 32.38, "ship_name": "Alfreds Futterkiste", "ship_address": "Obere Str. 57", "ship_city": "Berlin", "ship_region": None, "ship_postal_code": "12209", "ship_country": "Germany"},
        {"order_id": 10249, "customer_id": "ANATR", "employee_id": 1, "order_date": "2022-07-05", "required_date": "2022-08-16", "shipped_date": "2022-07-10", "ship_via": 1, "freight": 11.61, "ship_name": "Ana Trujillo Emparedados y helados", "ship_address": "Avda. de la Constitución 2222", "ship_city": "México D.F.", "ship_region": None, "ship_postal_code": "05021", "ship_country": "Mexico"},
        {"order_id": 10250, "customer_id": "ANTON", "employee_id": 2, "order_date": "2022-07-08", "required_date": "2022-08-05", "shipped_date": "2022-07-12", "ship_via": 2, "freight": 65.83, "ship_name": "Antonio Moreno Taquería", "ship_address": "Mataderos 2312", "ship_city": "México D.F.", "ship_region": None, "ship_postal_code": "05023", "ship_country": "Mexico"}
    ],
    "order_details": [
        {"order_id": 10248, "product_id": 1, "unit_price": 18.00, "quantity": 12, "discount": 0.00},
        {"order_id": 10248, "product_id": 2, "unit_price": 19.00, "quantity": 10, "discount": 0.00},
        {"order_id": 10249, "product_id": 3, "unit_price": 10.00, "quantity": 5, "discount": 0.00},
        {"order_id": 10250, "product_id": 4, "unit_price": 22.00, "quantity": 15, "discount": 0.15}
    ]
}

def parse_date(date_str):
    """Parse a date string into a Python date object"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        logger.warning(f"Invalid date format: {date_str}")
        return None

def create_tables(connection):
    """Create the Northwind database tables"""
    logger.info("Creating tables...")
    with connection.cursor() as cursor:
        cursor.execute(TABLES_SQL)
    connection.commit()
    logger.info("Tables created successfully")

def insert_sample_data(connection):
    """Insert sample data into the Northwind database"""
    logger.info("Inserting sample data...")
    
    # Insert categories
    with connection.cursor() as cursor:
        for category in SAMPLE_DATA["categories"]:
            # Check if record already exists to avoid duplicates
            cursor.execute("SELECT count(*) FROM categories WHERE category_id = %s", 
                           (category["category_id"],))
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO categories (category_id, category_name, description) VALUES (%s, %s, %s)",
                    (category["category_id"], category["category_name"], category["description"])
                )
    connection.commit()
    logger.info(f"Inserted {len(SAMPLE_DATA['categories'])} categories")

    # Insert suppliers
    with connection.cursor() as cursor:
        for supplier in SAMPLE_DATA["suppliers"]:
            # Check if record already exists
            cursor.execute("SELECT count(*) FROM suppliers WHERE supplier_id = %s", 
                           (supplier["supplier_id"],))
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO suppliers (supplier_id, company_name, contact_name, contact_title, address, city, region, postal_code, country, phone) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (supplier["supplier_id"], supplier["company_name"], supplier["contact_name"], 
                     supplier["contact_title"], supplier["address"], supplier["city"], 
                     supplier["region"], supplier["postal_code"], supplier["country"], 
                     supplier["phone"])
                )
    connection.commit()
    logger.info(f"Inserted {len(SAMPLE_DATA['suppliers'])} suppliers")

    # Insert products
    with connection.cursor() as cursor:
        for product in SAMPLE_DATA["products"]:
            # Check if record already exists
            cursor.execute("SELECT count(*) FROM products WHERE product_id = %s", 
                           (product["product_id"],))
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """INSERT INTO products 
                       (product_id, product_name, supplier_id, category_id, quantity_per_unit, 
                        unit_price, units_in_stock, units_on_order, reorder_level, discontinued) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (product["product_id"], product["product_name"], product["supplier_id"], 
                     product["category_id"], product["quantity_per_unit"], product["unit_price"], 
                     product["units_in_stock"], product["units_on_order"], product["reorder_level"], 
                     product["discontinued"])
                )
    connection.commit()
    logger.info(f"Inserted {len(SAMPLE_DATA['products'])} products")

    # Insert customers
    with connection.cursor() as cursor:
        for customer in SAMPLE_DATA["customers"]:
            # Check if record already exists
            cursor.execute("SELECT count(*) FROM customers WHERE customer_id = %s", 
                           (customer["customer_id"],))
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """INSERT INTO customers 
                       (customer_id, company_name, contact_name, contact_title, address, 
                        city, region, postal_code, country, phone) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (customer["customer_id"], customer["company_name"], customer["contact_name"], 
                     customer["contact_title"], customer["address"], customer["city"], 
                     customer["region"], customer["postal_code"], customer["country"], 
                     customer["phone"])
                )
    connection.commit()
    logger.info(f"Inserted {len(SAMPLE_DATA['customers'])} customers")

    # Insert employees
    with connection.cursor() as cursor:
        for employee in SAMPLE_DATA["employees"]:
            # Check if record already exists
            cursor.execute("SELECT count(*) FROM employees WHERE employee_id = %s", 
                           (employee["employee_id"],))
            if cursor.fetchone()[0] == 0:
                birth_date = parse_date(employee["birth_date"])
                hire_date = parse_date(employee["hire_date"])
                
                cursor.execute(
                    """INSERT INTO employees 
                       (employee_id, last_name, first_name, title, title_of_courtesy, 
                        birth_date, hire_date, address, city, region, postal_code, 
                        country, home_phone, extension, notes, reports_to) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (employee["employee_id"], employee["last_name"], employee["first_name"], 
                     employee["title"], employee["title_of_courtesy"], birth_date, hire_date, 
                     employee["address"], employee["city"], employee["region"], 
                     employee["postal_code"], employee["country"], employee["home_phone"], 
                     employee["extension"], employee["notes"], employee["reports_to"])
                )
    connection.commit()
    logger.info(f"Inserted {len(SAMPLE_DATA['employees'])} employees")

    # Insert shippers
    with connection.cursor() as cursor:
        for shipper in SAMPLE_DATA["shippers"]:
            # Check if record already exists
            cursor.execute("SELECT count(*) FROM shippers WHERE shipper_id = %s", 
                           (shipper["shipper_id"],))
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO shippers (shipper_id, company_name, phone) VALUES (%s, %s, %s)",
                    (shipper["shipper_id"], shipper["company_name"], shipper["phone"])
                )
    connection.commit()
    logger.info(f"Inserted {len(SAMPLE_DATA['shippers'])} shippers")

    # Insert orders
    with connection.cursor() as cursor:
        for order in SAMPLE_DATA["orders"]:
            # Check if record already exists
            cursor.execute("SELECT count(*) FROM orders WHERE order_id = %s", 
                           (order["order_id"],))
            if cursor.fetchone()[0] == 0:
                order_date = parse_date(order["order_date"])
                required_date = parse_date(order["required_date"])
                shipped_date = parse_date(order["shipped_date"])
                
                cursor.execute(
                    """INSERT INTO orders 
                       (order_id, customer_id, employee_id, order_date, required_date, 
                        shipped_date, ship_via, freight, ship_name, ship_address, 
                        ship_city, ship_region, ship_postal_code, ship_country) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (order["order_id"], order["customer_id"], order["employee_id"], 
                     order_date, required_date, shipped_date, order["ship_via"], 
                     order["freight"], order["ship_name"], order["ship_address"], 
                     order["ship_city"], order["ship_region"], 
                     order["ship_postal_code"], order["ship_country"])
                )
    connection.commit()
    logger.info(f"Inserted {len(SAMPLE_DATA['orders'])} orders")

    # Insert order details
    with connection.cursor() as cursor:
        for detail in SAMPLE_DATA["order_details"]:
            # Check if record already exists
            cursor.execute("SELECT count(*) FROM order_details WHERE order_id = %s AND product_id = %s", 
                           (detail["order_id"], detail["product_id"]))
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """INSERT INTO order_details 
                       (order_id, product_id, unit_price, quantity, discount) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (detail["order_id"], detail["product_id"], detail["unit_price"], 
                     detail["quantity"], detail["discount"])
                )
    connection.commit()
    logger.info(f"Inserted {len(SAMPLE_DATA['order_details'])} order details")

def main():
    """Main function to set up the Northwind database"""
    logger.info("Setting up Northwind database...")
    
    try:
        with psycopg.connect(DB_URL) as connection:
            # Create tables
            create_tables(connection)
            
            # Insert sample data
            insert_sample_data(connection)
            
        logger.info("Northwind database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error setting up Northwind database: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main()