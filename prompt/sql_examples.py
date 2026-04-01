SQL_EXAMPLES = [

{
"question": "Show all customers",
"sql": """
SELECT id, name, city
FROM customers;
"""
},

{
"question": "Show all orders with customer names",
"sql": """
SELECT c.name, o.id, o.amount, o.order_date
FROM customers c
JOIN orders o
ON c.id = o.customer_id;
"""
},

{
"question": "Show each customer's orders and payment method",
"sql": """
SELECT c.name, o.id, o.order_date, p.payment_method
FROM customers c
JOIN orders o
ON c.id = o.customer_id
JOIN payments p
ON o.id = p.order_id;
"""
},

{
"question": "Show all orders with payment details",
"sql": """
SELECT o.id, o.amount, o.order_date, p.payment_method, p.amount
FROM orders o
JOIN payments p
ON o.id = p.order_id;
"""
},

{
"question": "Show all customers and their total order amount",
"sql": """
SELECT c.name, SUM(o.amount) AS total_orders
FROM customers c
JOIN orders o
ON c.id = o.customer_id
GROUP BY c.name;
"""
},

{
"question": "Find the customer who placed the most orders",
"sql": """
SELECT c.name, COUNT(o.id) AS total_orders
FROM customers c
JOIN orders o
ON c.id = o.customer_id
GROUP BY c.name
ORDER BY total_orders DESC
LIMIT 1; 
"""
},

{
"question": "List orders that do not have a payment",
"sql": """
SELECT o.id, o.amount, o.order_date
FROM orders o
LEFT JOIN payments p
ON o.id = p.order_id
WHERE p.id IS NULL;
"""
},

{
"question": "Show payment details with customer names",
"sql": """
SELECT c.name, p.payment_method, p.amount, p.payment_date
FROM customers c
JOIN orders o
ON c.id = o.customer_id
JOIN payments p
ON o.id = p.order_id;
"""
},

{
"question": "Show total payment amount for each customer",
"sql": """
SELECT c.name, SUM(p.amount) AS total_paid
FROM customers c
JOIN orders o
ON c.id = o.customer_id
JOIN payments p
ON o.id = p.order_id
GROUP BY c.name;
"""
},

{
"question": "Show customers who have not placed any orders",
"sql": """
SELECT c.id, c.name
FROM customers c
LEFT JOIN orders o
ON c.id = o.customer_id
WHERE o.id IS NULL;
"""
},
{
"question": "Find customers who made multiple payments",
"sql": """
SELECT c.name, COUNT(p.id) AS payment_count
FROM customers c
JOIN orders o ON c.id = o.customer_id
JOIN payments p ON o.id = p.order_id
GROUP BY c.name
HAVING COUNT(p.id) > 1;

"""
},

{
"question": "Rank customers based on total spending",
"sql": """
SELECT c.name,
       SUM(o.amount) AS total_spent,
       RANK() OVER (ORDER BY SUM(o.amount) DESC) AS rank_position
FROM customers c
JOIN orders o ON c.id = o.customer_id
GROUP BY c.name;
"""
}

]
