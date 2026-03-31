import requests
import time

URL = "http://127.0.0.1:8000/query/ask"

queries = [

    
    # HARD (RETRY TRIGGERS)
    "Find top customers using wrong column mapping",
    "Show total sales using incorrect relationships",
    "Get customer revenue using mismatched keys",
    "Calculate average revenue but confuse orders and payments",
    "Join customers and payments using wrong column name",
    "Find total sales using non direct join between tables",
    "Show customer data with incorrect aggregation logic",
    "Compute revenue but mix order_id and customer_id",
    "Find top cities by revenue using wrong schema assumption",
    "Give total revenue but incorrectly join customers and payments",

    

]


for i, query in enumerate(queries, start=1):
    try:
        response = requests.post(
            URL,
            json={
                "prompt": query,
                "schema_name": "sales_db"
            },
            timeout=30
        )

        print(f"\n--- Query {i} ---")
        print("Prompt:", query)
        print("Response:", response.json())

        time.sleep(2)

    except requests.exceptions.Timeout:
        print(f"⏳ Timeout for query {i}: {query}")
        continue

    except Exception as e:
        print(f"Error for query {i}: {e}")