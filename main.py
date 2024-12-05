from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure random string

# MySQL Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',  # Change this to your MySQL username
    'password': 'cmd82.207',  # Change this to your MySQL password
    'database': 'billing_app'
}

# Database connection
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Home Page - Billing
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    conn.close()
    return render_template('index.html', items=items)

# Generate Bill
@app.route('/bill', methods=['POST'])
def generate_bill():
    customer_name = request.form['customer_name']
    items = request.form.getlist('item')
    quantities = request.form.getlist('quantity')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    total_price = 0
    bill_items = []
    for item, quantity in zip(items, quantities):
        quantity = int(quantity)
        if quantity > 0:
            cursor.execute("SELECT name, price FROM items WHERE name = %s", (item,))
            item_data = cursor.fetchone()
            price = item_data['price']
            item_total = price * quantity
            total_price += item_total
            bill_items.append({
                'name': item,
                'quantity': quantity,
                'price': price,
                'total': item_total
            })
            cursor.execute(
                "INSERT INTO sales (customer_name, item, quantity, total_price) VALUES (%s, %s, %s, %s)",
                (customer_name, item, quantity, item_total)
            )

    conn.commit()
    conn.close()
    return render_template('bill.html', customer_name=customer_name, bill_items=bill_items, total_price=total_price)

# Manage Items
@app.route('/items', methods=['GET', 'POST'])
def manage_items():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        try:
            cursor.execute("INSERT INTO items (name, price) VALUES (%s, %s)", (name, price))
            conn.commit()
            flash('Item added successfully!', 'success')
        except mysql.connector.errors.IntegrityError:
            flash('Item already exists! Please add a unique item.', 'error')

    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    conn.close()
    return render_template('items.html', items=items)

# Edit Item
@app.route('/edit_item/<int:item_id>', methods=['POST'])
def edit_item(item_id):
    name = request.form['name']
    price = request.form['price']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET name = %s, price = %s WHERE id = %s", (name, price, item_id))
    conn.commit()
    conn.close()
    flash('Item updated successfully!', 'success')
    return redirect(url_for('manage_items'))

# Delete Item
@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
    conn.commit()
    conn.close()
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('manage_items'))

# Monthly Report
@app.route('/report')
def report():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT customer_name, item, quantity, total_price, date FROM sales WHERE MONTH(date) = MONTH(CURRENT_DATE()) ORDER BY date DESC")
    sales = cursor.fetchall()
    conn.close()
    return render_template('report.html', sales=sales)

if __name__ == '__main__':
    app.run(debug=True)

