"""
FastAPI Backend for Inventory Management System
Full CRUD operations for all entities
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import sqlite3
from datetime import datetime, date

app = FastAPI(
    title="Inventory Management System API",
    description="REST API with full CRUD operations",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

# ==================== MODELS ====================

class UserRegister(BaseModel):
    username: str
    password: str
    email: EmailStr
    role: str = "Manager"

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class LocationCreate(BaseModel):
    name: str
    address: str

class LocationResponse(BaseModel):
    id: int
    name: str
    address: str
    items: int = 0
    printers: int = 0

class InventoryItemCreate(BaseModel):
    name: str
    sku: str
    category_id: int
    quantity: int
    min_stock: int
    price: float
    location_id: int

class InventoryItemResponse(BaseModel):
    id: int
    name: str
    sku: str
    category_id: int
    category_name: str
    quantity: int
    min_stock: int
    price: float
    total_price: float
    location_id: int
    location_name: str
    status: str

class PrinterCreate(BaseModel):
    model: str
    serial_number: str
    location_id: int
    status: str = "Active"
    supplies: Optional[str] = None

class PrinterResponse(BaseModel):
    id: int
    model: str
    serial_number: str
    location_id: int
    location_name: str
    status: str
    supplies: Optional[str]

class TransactionCreate(BaseModel):
    item_id: int
    location_id: int
    transaction_type: str
    quantity: int
    price_per_unit: float
    payment_status: str = "Pending"
    payment_date: Optional[str] = None
    notes: Optional[str] = None

class FinancialSummary(BaseModel):
    total_spent: float
    total_pending: float
    total_paid: float
    transactions_by_location: List[dict]

# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/register", response_model=UserResponse)
def register(user: UserRegister):
    """Register new user"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
            (user.username, user.password, user.email, user.role)
        )
        db.commit()
        user_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        new_user = cursor.fetchone()
        db.close()
        
        return {
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "role": new_user["role"]
        }
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(status_code=400, detail="Username or email already exists")

@app.post("/api/auth/login")
def login(credentials: UserLogin):
    """Login user"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                   (credentials.username, credentials.password))
    user = cursor.fetchone()
    db.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }

# ==================== DASHBOARD ====================

@app.get("/api/dashboard/metrics")
def get_dashboard_metrics():
    """Get dashboard metrics with financial data"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM inventory_items")
    total_items = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM inventory_items WHERE quantity < min_stock")
    low_stock = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM locations")
    total_locations = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM printers")
    total_printers = cursor.fetchone()["count"]
    
    cursor.execute("SELECT SUM(total_amount) as total FROM transactions")
    result = cursor.fetchone()
    total_spent = result["total"] if result["total"] else 0
    
    cursor.execute("SELECT SUM(total_amount) as total FROM transactions WHERE payment_status = 'Pending'")
    result = cursor.fetchone()
    pending_payments = result["total"] if result["total"] else 0
    
    db.close()
    
    return {
        "total_items": total_items,
        "low_stock_count": low_stock,
        "total_locations": total_locations,
        "total_printers": total_printers,
        "total_spent": round(total_spent, 2),
        "pending_payments": round(pending_payments, 2),
        "paid_amount": round(total_spent - pending_payments, 2)
    }

@app.get("/api/dashboard/charts")
def get_dashboard_charts():
    """Get chart data for dashboard"""
    db = get_db()
    cursor = db.cursor()
    
    # Monthly inventory trend
    cursor.execute("""
        SELECT strftime('%Y-%m', created_at) as month, 
               SUM(quantity) as inventory,
               COUNT(*) as items
        FROM inventory_items
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY month DESC
        LIMIT 6
    """)
    inventory_trend = [dict(row) for row in cursor.fetchall()]
    
    # Category distribution
    cursor.execute("""
        SELECT c.name, COUNT(ii.id) as count
        FROM categories c
        LEFT JOIN inventory_items ii ON c.id = ii.category_id
        GROUP BY c.name
    """)
    category_dist = [dict(row) for row in cursor.fetchall()]
    
    db.close()
    
    return {
        "inventory_trend": inventory_trend,
        "category_distribution": category_dist
    }

# ==================== CATEGORIES ====================

@app.get("/api/categories")
def get_categories():
    """Get all categories"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY name")
    categories = cursor.fetchall()
    db.close()
    return [dict(cat) for cat in categories]

@app.post("/api/categories")
def create_category(category: CategoryCreate):
    """Create new category"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("INSERT INTO categories (name, description) VALUES (?, ?)",
                      (category.name, category.description))
        db.commit()
        cat_id = cursor.lastrowid
        cursor.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
        new_cat = cursor.fetchone()
        db.close()
        return dict(new_cat)
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(status_code=400, detail="Category already exists")

# ==================== INVENTORY CRUD ====================

@app.get("/api/inventory", response_model=List[InventoryItemResponse])
def get_inventory():
    """Get all inventory items"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
    SELECT ii.*, c.name AS category_name, l.name AS location_name,
           p.model AS printer_name,
           (ii.quantity * ii.price) AS total_price
    FROM inventory_items ii
    LEFT JOIN categories c ON ii.category_id = c.id
    LEFT JOIN locations l ON ii.location_id = l.id
    LEFT JOIN printers p ON ii.printer_id = p.id
    ORDER BY ii.created_at DESC
    """)
    items = cursor.fetchall()
    db.close()
    
    return [dict(item) for item in items]

@app.post("/api/inventory", response_model=InventoryItemResponse)
def create_inventory_item(item: InventoryItemCreate):
    """Create new inventory item"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        status = "Low Stock" if item.quantity < item.min_stock else "In Stock"
        cursor.execute(
            "INSERT INTO inventory_items (name, sku, category_id, quantity, min_stock, price, location_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (item.name, item.sku, item.category_id, item.quantity, item.min_stock, item.price, item.location_id, status)
        )
        db.commit()
        item_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT ii.*, c.name as category_name, l.name as location_name,
                   (ii.quantity * ii.price) as total_price
            FROM inventory_items ii
            LEFT JOIN categories c ON ii.category_id = c.id
            LEFT JOIN locations l ON ii.location_id = l.id
            WHERE ii.id = ?
        """, (item_id,))
        new_item = cursor.fetchone()
        db.close()
        
        return dict(new_item)
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(status_code=400, detail="SKU already exists")

@app.put("/api/inventory/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item(item_id: int, item: InventoryItemCreate):
    """Update inventory item"""
    db = get_db()
    cursor = db.cursor()
    
    status = "Low Stock" if item.quantity < item.min_stock else "In Stock"
    cursor.execute(
        "UPDATE inventory_items SET name = ?, sku = ?, category_id = ?, quantity = ?, min_stock = ?, price = ?, location_id = ?, status = ? WHERE id = ?",
        (item.name, item.sku, item.category_id, item.quantity, item.min_stock, item.price, item.location_id, status, item_id)
    )
    db.commit()
    
    cursor.execute("""
        SELECT ii.*, c.name as category_name, l.name as location_name,
               (ii.quantity * ii.price) as total_price
        FROM inventory_items ii
        LEFT JOIN categories c ON ii.category_id = c.id
        LEFT JOIN locations l ON ii.location_id = l.id
        WHERE ii.id = ?
    """, (item_id,))
    updated_item = cursor.fetchone()
    db.close()
    
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return dict(updated_item)

@app.delete("/api/inventory/{item_id}")
def delete_inventory_item(item_id: int):
    """Delete inventory item"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM inventory_items WHERE id = ?", (item_id,))
    db.commit()
    db.close()
    return {"message": "Item deleted successfully"}

# ==================== LOCATIONS CRUD ====================

@app.get("/api/locations", response_model=List[LocationResponse])
def get_locations():
    """Get all locations"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM locations ORDER BY name")
    locations = cursor.fetchall()
    
    result = []
    for loc in locations:
        cursor.execute("SELECT COUNT(*) as count FROM inventory_items WHERE location_id = ?", (loc["id"],))
        items_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM printers WHERE location_id = ?", (loc["id"],))
        printers_count = cursor.fetchone()["count"]
        
        result.append({
            "id": loc["id"],
            "name": loc["name"],
            "address": loc["address"],
            "items": items_count,
            "printers": printers_count
        })
    
    db.close()
    return result

@app.post("/api/locations", response_model=LocationResponse)
def create_location(location: LocationCreate):
    """Create new location"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("INSERT INTO locations (name, address) VALUES (?, ?)", 
                      (location.name, location.address))
        db.commit()
        location_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM locations WHERE id = ?", (location_id,))
        new_location = cursor.fetchone()
        db.close()
        
        return {
            "id": new_location["id"],
            "name": new_location["name"],
            "address": new_location["address"],
            "items": 0,
            "printers": 0
        }
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(status_code=400, detail="Location already exists")

@app.put("/api/locations/{location_id}", response_model=LocationResponse)
def update_location(location_id: int, location: LocationCreate):
    """Update location"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("UPDATE locations SET name = ?, address = ? WHERE id = ?",
                  (location.name, location.address, location_id))
    db.commit()
    
    cursor.execute("SELECT * FROM locations WHERE id = ?", (location_id,))
    updated_loc = cursor.fetchone()
    
    if not updated_loc:
        db.close()
        raise HTTPException(status_code=404, detail="Location not found")
    
    cursor.execute("SELECT COUNT(*) as count FROM inventory_items WHERE location_id = ?", (location_id,))
    items_count = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM printers WHERE location_id = ?", (location_id,))
    printers_count = cursor.fetchone()["count"]
    
    db.close()
    
    return {
        "id": updated_loc["id"],
        "name": updated_loc["name"],
        "address": updated_loc["address"],
        "items": items_count,
        "printers": printers_count
    }

@app.delete("/api/locations/{location_id}")
def delete_location(location_id: int):
    """Delete location"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM locations WHERE id = ?", (location_id,))
    db.commit()
    db.close()
    return {"message": "Location deleted successfully"}

# ==================== PRINTERS CRUD ====================

@app.get("/api/printers", response_model=List[PrinterResponse])
def get_printers():
    """Get all printers"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, l.name as location_name
        FROM printers p
        LEFT JOIN locations l ON p.location_id = l.id
        ORDER BY p.created_at DESC
    """)
    printers = cursor.fetchall()
    db.close()
    return [dict(printer) for printer in printers]

@app.post("/api/printers", response_model=PrinterResponse)
def create_printer(printer: PrinterCreate):
    """Create new printer"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO printers (model, serial_number, location_id, status, supplies) VALUES (?, ?, ?, ?, ?)",
            (printer.model, printer.serial_number, printer.location_id, printer.status, printer.supplies)
        )
        db.commit()
        printer_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT p.*, l.name as location_name
            FROM printers p
            LEFT JOIN locations l ON p.location_id = l.id
            WHERE p.id = ?
        """, (printer_id,))
        new_printer = cursor.fetchone()
        db.close()
        
        return dict(new_printer)
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(status_code=400, detail="Serial number already exists")

@app.put("/api/printers/{printer_id}", response_model=PrinterResponse)
def update_printer(printer_id: int, printer: PrinterCreate):
    """Update printer"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        "UPDATE printers SET model = ?, serial_number = ?, location_id = ?, status = ?, supplies = ? WHERE id = ?",
        (printer.model, printer.serial_number, printer.location_id, printer.status, printer.supplies, printer_id)
    )
    db.commit()
    
    cursor.execute("""
        SELECT p.*, l.name as location_name
        FROM printers p
        LEFT JOIN locations l ON p.location_id = l.id
        WHERE p.id = ?
    """, (printer_id,))
    updated_printer = cursor.fetchone()
    db.close()
    
    if not updated_printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    return dict(updated_printer)

@app.delete("/api/printers/{printer_id}")
def delete_printer(printer_id: int):
    """Delete printer"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM printers WHERE id = ?", (printer_id,))
    db.commit()
    db.close()
    return {"message": "Printer deleted successfully"}

# ==================== TRANSACTIONS & FINANCIAL ====================

@app.get("/api/transactions")
def get_transactions():
    """Get all transactions"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT t.*, ii.name as item_name, l.name as location_name
        FROM transactions t
        LEFT JOIN inventory_items ii ON t.item_id = ii.id
        LEFT JOIN locations l ON t.location_id = l.id
        ORDER BY t.created_at DESC
    """)
    transactions = cursor.fetchall()
    db.close()
    return [dict(t) for t in transactions]

@app.post("/api/transactions")
def create_transaction(transaction: TransactionCreate):
    """Create new transaction"""
    db = get_db()
    cursor = db.cursor()
    
    total_amount = transaction.quantity * transaction.price_per_unit
    
    cursor.execute(
        "INSERT INTO transactions (item_id, location_id, transaction_type, quantity, price_per_unit, total_amount, payment_status, payment_date, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (transaction.item_id, transaction.location_id, transaction.transaction_type, transaction.quantity, 
         transaction.price_per_unit, total_amount, transaction.payment_status, transaction.payment_date, transaction.notes)
    )
    db.commit()
    trans_id = cursor.lastrowid
    
    # Update inventory if it's a sale
    if transaction.transaction_type == 'sale':
        cursor.execute("UPDATE inventory_items SET quantity = quantity - ? WHERE id = ?",
                      (transaction.quantity, transaction.item_id))
        db.commit()
    
    cursor.execute("""
        SELECT t.*, ii.name as item_name, l.name as location_name
        FROM transactions t
        LEFT JOIN inventory_items ii ON t.item_id = ii.id
        LEFT JOIN locations l ON t.location_id = l.id
        WHERE t.id = ?
    """, (trans_id,))
    new_trans = cursor.fetchone()
    db.close()
    
    return dict(new_trans)

@app.get("/api/financial/summary")
def get_financial_summary():
    """Get financial summary"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT SUM(total_amount) as total FROM transactions")
    result = cursor.fetchone()
    total_spent = result["total"] if result["total"] else 0
    
    cursor.execute("SELECT SUM(total_amount) as total FROM transactions WHERE payment_status = 'Pending'")
    result = cursor.fetchone()
    pending = result["total"] if result["total"] else 0
    
    cursor.execute("SELECT SUM(total_amount) as total FROM transactions WHERE payment_status = 'Paid'")
    result = cursor.fetchone()
    paid = result["total"] if result["total"] else 0
    
    cursor.execute("""
        SELECT l.name as location, 
               SUM(CASE WHEN t.payment_status = 'Pending' THEN t.total_amount ELSE 0 END) as pending,
               SUM(CASE WHEN t.payment_status = 'Paid' THEN t.total_amount ELSE 0 END) as paid,
               SUM(t.total_amount) as total
        FROM transactions t
        LEFT JOIN locations l ON t.location_id = l.id
        GROUP BY l.name
    """)
    by_location = [dict(row) for row in cursor.fetchall()]
    
    db.close()
    
    return {
        "total_spent": round(total_spent, 2),
        "total_pending": round(pending, 2),
        "total_paid": round(paid, 2),
        "transactions_by_location": by_location
    }

# ==================== REPORTS ====================

@app.get("/api/reports/low-stock")
def get_low_stock_report():
    """Get low stock items"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT ii.*, c.name as category_name, l.name as location_name,
               (ii.quantity * ii.price) as total_value
        FROM inventory_items ii
        LEFT JOIN categories c ON ii.category_id = c.id
        LEFT JOIN locations l ON ii.location_id = l.id
        WHERE ii.quantity < ii.min_stock
        ORDER BY ii.quantity ASC
    """)
    
    items = cursor.fetchall()
    db.close()
    
    return [dict(item) for item in items]

@app.get("/api/reports/inventory-value")
def get_inventory_value_report():
    """Get total inventory value by category and location"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT c.name as category,
               SUM(ii.quantity * ii.price) as total_value,
               SUM(ii.quantity) as total_quantity
        FROM inventory_items ii
        LEFT JOIN categories c ON ii.category_id = c.id
        GROUP BY c.name
    """)
    by_category = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT l.name as location,
               SUM(ii.quantity * ii.price) as total_value,
               COUNT(ii.id) as item_count
        FROM inventory_items ii
        LEFT JOIN locations l ON ii.location_id = l.id
        GROUP BY l.name
    """)
    by_location = [dict(row) for row in cursor.fetchall()]
    
    db.close()
    
    return {
        "by_category": by_category,
        "by_location": by_location
    }

@app.get("/api/health")
def health_check():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)