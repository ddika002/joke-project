import sqlite3


create_jokes_table_query = """
CREATE TABLE jokes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    joke_text TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    likes INTEGER DEFAULT 0,
    dislikes INTEGER DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
"""

create_categories_table_query = """
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
"""

def create_tables():
    try:
        conn = sqlite3.connect('jokes.db')
        cursor = conn.cursor()

        
        cursor.execute(create_categories_table_query)
        cursor.execute(create_jokes_table_query)

        conn.commit()
        print("Tables created successfully.")
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
    finally:
        if conn:
            conn.close()

# Execute the function to create tables
create_tables()
