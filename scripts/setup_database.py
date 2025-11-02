"""
Database setup script for Inventory Management System
Creates all necessary tables and seeds initial data
Run this script first: python setup_database.py
"""

import sqlite3
import os
from datetime import datetime

def setup_database():
    """Create database tables and seed initial data"""
    
    # Create database in the current directory (backend folder)
    db_path = 'inventory.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Creating database tables...")
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create locations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            address TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create inventory_items table with pricing
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            category_id INTEGER,
            quantity INTEGER NOT NULL,
            min_stock INTEGER NOT NULL,
            price REAL NOT NULL,
            location_id INTEGER NOT NULL,
            printer_id INTEGER,
            status TEXT DEFAULT 'In Stock',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations(id),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (printer_id) REFERENCES printers(id)
        )
    ''')
    
    # Create printers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS printers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            serial_number TEXT UNIQUE,
            location_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Active',
            supplies TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations(id)
        )
    ''')
    
    # Create transactions table for financial tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            location_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price_per_unit REAL NOT NULL,
            total_amount REAL NOT NULL,
            payment_status TEXT DEFAULT 'Pending',
            payment_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES inventory_items(id),
            FOREIGN KEY (location_id) REFERENCES locations(id)
        )
    ''')
    
    # Create stock_movements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            from_location_id INTEGER,
            to_location_id INTEGER,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES inventory_items(id),
            FOREIGN KEY (from_location_id) REFERENCES locations(id),
            FOREIGN KEY (to_location_id) REFERENCES locations(id)
        )
    ''')
    
    print("✅ Database tables created successfully!")
    
    # Seed initial data
    try:
        print("🌱 Seeding initial data...")
        
        # Add demo users
        cursor.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)", 
                      ('admin', 'admin123', 'admin@ims.com', 'Admin'))
        cursor.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)", 
                      ('manager', 'manager123', 'manager@ims.com', 'Manager'))
        print("  ✓ Added demo users")
        
        # Add categories
        categories = [
            ('Toner', 'Toner cartridges for printers'),
            ('Paper', 'Printing paper and materials'),
            ('Ink', 'Ink cartridges'),
            ('Supplies', 'General office supplies'),
        ]
        for name, desc in categories:
            cursor.execute("INSERT INTO categories (name, description) VALUES (?, ?)", (name, desc))
        print("  ✓ Added categories")
        
        # Add locations
        locations = [
            ('Main School', '123 Education Street, District A'),
            ('Branch School A', '456 Learning Avenue, District B'),
            ('Branch School B', '789 Knowledge Boulevard, District C'),
            ('Central Office', '321 Administration Lane, Downtown'),
        ]
        for name, address in locations:
            cursor.execute("INSERT INTO locations (name, address) VALUES (?, ?)", (name, address))
        print("  ✓ Added locations")
        
        # Add printers first (before inventory items reference them)
        printers = [
            ('HP LaserJet Pro MFP M428fdw', 'SN-HP-001', 1, 'Active', 'Toner, Paper'),
            ('Canon imagePRESS C165', 'SN-CN-001', 2, 'Active', 'Toner, Ink'),
            ('Xerox VersaLink C405', 'SN-XR-001', 3, 'Maintenance', 'Toner'),
            ('Ricoh MP C3004ex', 'SN-RC-001', 1, 'Active', 'Toner, Paper, Ink'),
            ('Brother MFC-L8900CDW', 'SN-BR-001', 4, 'Active', 'Toner, Paper'),
            ('Epson WorkForce Pro WF-C5790', 'SN-EP-001', 2, 'Active', 'Ink, Paper'),
        ]
        for model, serial, loc_id, status, supplies in printers:
            cursor.execute(
                "INSERT INTO printers (model, serial_number, location_id, status, supplies) VALUES (?, ?, ?, ?, ?)",
                (model, serial, loc_id, status, supplies)
            )
        print("  ✓ Added printers")
        
        # Add inventory items with pricing and printer_id
        items = [
            ('Toner Cartridge Black HP 305A', 'TCB-001', 1, 150, 50, 45.99, 1, 1, 'In Stock'),
            ('Toner Cartridge Color Canon 046', 'TCC-001', 1, 45, 50, 55.99, 2, 2, 'Low Stock'),
            ('Paper A4 500 sheets Premium', 'PA4-500', 2, 500, 200, 5.99, 1, 1, 'In Stock'),
            ('Ink Cartridge Epson 603XL', 'IC-001', 3, 20, 30, 25.50, 3, 3, 'Low Stock'),
            ('Toner Cartridge Brother TN-2420', 'TCB-002', 1, 80, 40, 42.99, 4, 5, 'In Stock'),
            ('Paper A4 80gsm 2500 sheets', 'PA4-2500', 2, 300, 150, 22.99, 1, 4, 'In Stock'),
            ('Ink Cartridge HP 302XL Black', 'IC-002', 3, 35, 25, 29.99, 2, 6, 'In Stock'),
            ('Toner Cartridge Xerox 106R03623', 'TCX-001', 1, 15, 30, 68.99, 3, 3, 'Low Stock'),
        ]
        for name, sku, cat_id, qty, min_stock, price, loc_id, printer_id, status in items:
            cursor.execute(
                "INSERT INTO inventory_items (name, sku, category_id, quantity, min_stock, price, location_id, printer_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, sku, cat_id, qty, min_stock, price, loc_id, printer_id, status)
            )
        print("  ✓ Added inventory items")
        
        # Add sample transactions
        transactions = [
            (1, 1, 'sale', 50, 45.99, 2299.50, 'Pending', None, 'Delivered to Main School'),
            (2, 2, 'sale', 30, 55.99, 1679.70, 'Pending', None, 'Delivered to Branch A'),
            (3, 1, 'sale', 100, 5.99, 599.00, 'Paid', '2024-01-15', 'Bulk order for Main School'),
            (4, 3, 'sale', 15, 25.50, 382.50, 'Pending', None, 'Emergency order'),
            (5, 4, 'sale', 40, 42.99, 1719.60, 'Pending', None, 'Monthly supplies'),
        ]
        for item_id, loc_id, trans_type, qty, price, total, status, pay_date, notes in transactions:
            cursor.execute(
                "INSERT INTO transactions (item_id, location_id, transaction_type, quantity, price_per_unit, total_amount, payment_status, payment_date, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (item_id, loc_id, trans_type, qty, price, total, status, pay_date, notes)
            )
        print("  ✓ Added sample transactions")
        
        conn.commit()
        print("\n✅ Database setup completed successfully!")
        print("\n📋 Demo Credentials:")
        print("   Admin: admin / admin123")
        print("   Manager: manager / manager123")
        print("\n🚀 You can now run the backend: uvicorn main:app --reload")
        
    except sqlite3.IntegrityError as e:
        print(f"⚠️  Database already contains data: {e}")
        print("   Skipping initial data insertion")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()