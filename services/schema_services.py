from sqlalchemy import text
from fastapi import HTTPException

# SCHEMA CACHE
SCHEMA_CACHE = {}

# ALLOWED DATABASES
ALLOWED_SCHEMAS = {
    "askdb",
    "sales_db",
    "ecommerce_db",
    "employee_db",
    "banking_db",
    "hospital_db"
}

# SCHEMA DESCRIPTION 
def get_schema_description(db, database_name: str):

    # CACHE HIT
    if database_name in SCHEMA_CACHE:
        print(f"[CACHE HIT] Schema: {database_name}")
        return SCHEMA_CACHE[database_name]

    print(f"[CACHE MISS] Fetching schema: {database_name}")

    # VALIDATION
    if database_name not in ALLOWED_SCHEMAS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid schema '{database_name}'"
        )

    try:
        # FETCH SCHEMA (WITH DATA TYPES)
        query = text("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = :db
            ORDER BY table_name
        """)

        rows = db.execute(query, {"db": database_name}).fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No tables found in '{database_name}'"
            )

        # GROUP TABLES
        tables = {}

        for table, column, dtype in rows:
            tables.setdefault(table, []).append((column, dtype))

        # BUILD SMART SCHEMA TEXT
        schema_parts = []

        for table, cols in tables.items():

            table_desc = f"Stores information about {table.replace('_', ' ')}"

            column_lines = []

            for col, dtype in cols:
                col_lower = col.lower()

                # SMART COLUMN DESCRIPTION
                if col_lower == "id":
                    desc = "primary key"
                elif col_lower.endswith("_id"):
                    desc = "foreign key reference"
                elif "date" in col_lower:
                    desc = "date field"
                elif "amount" in col_lower or "price" in col_lower:
                    desc = "numeric value"
                else:
                    desc = "data field"

                column_lines.append(f"- {col} ({dtype}): {desc}")

            table_block = (
                f"Table: {table}\n"
                f"Description: {table_desc}\n"
                f"Columns:\n"
                f"{chr(10).join(column_lines)}"
            )

            schema_parts.append(table_block)

        schema_text = "\n\n".join(schema_parts)

        # STORE CACHE
        SCHEMA_CACHE[database_name] = schema_text

        return schema_text

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )