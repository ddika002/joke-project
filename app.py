from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)

# Connect to SQLite database
DATABASE = 'jokes.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# GET /jokes/random
@app.route('/jokes/random', methods=['GET'])
def get_random_joke():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT j.*, c.name AS category_name FROM jokes j JOIN categories c ON j.category_id = c.id ORDER BY RANDOM() LIMIT 1")
    joke = cursor.fetchone()
    cursor.close()
    if joke:
        return jsonify({'id': joke[0], 'joke_text': joke[1], 'category_id': joke[2], 'likes': joke[3], 'dislikes': joke[4]})
    else:
        return jsonify({'error': 'No jokes available'}), 404
    
# GET /jokes/random/:category
@app.route('/jokes/random/<string:category>', methods=['GET'])
def get_random_joke_by_category(category):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT j.*, c.name AS category_name FROM jokes j JOIN categories c ON j.category_id = c.id WHERE c.name = ? ORDER BY RANDOM() LIMIT 1", [category])
    joke = cursor.fetchone()
    cursor.close()
    if joke:
        return jsonify({'id': joke[0], 'joke_text': joke[1], 'category_id': joke[2], 'likes': joke[3], 'dislikes': joke[4]})
    else:
        return jsonify({'error': f'No jokes available in the category: {category}'}), 404


# POST /categories
@app.route('/categories', methods=['POST'])
def add_category():
    name = request.json.get('name')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO categories (name) VALUES (?)", [name])
    db.commit()
    category_id = cursor.lastrowid
    cursor.close()
    return jsonify({'message': 'Category added successfully', 'id': category_id}), 201

# POST /jokes/:category
@app.route('/jokes/<string:category>', methods=['POST'])
def add_joke(category):
    joke_text = request.json.get('joke_text')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM categories WHERE name = ?", [category])
    category_id = cursor.fetchone()
    if not category_id:
        cursor.close()
        return jsonify({'error': 'Category not found'}), 404
    else:
        category_id = category_id[0]
        cursor.execute("INSERT INTO jokes (joke_text, category_id) VALUES (?, ?)", [joke_text, category_id])
        db.commit()
        joke_id = cursor.lastrowid
        cursor.close()
        return jsonify({'message': 'Joke added successfully', 'id': joke_id}), 201
    
# Function to get list of categories
def get_categories():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()
    cursor.close()
    return [{'id': category[0], 'name': category[1]} for category in categories]

# GET /categories
@app.route('/categories', methods=['GET'])
def list_categories():
    categories = get_categories()
    return jsonify(categories)
    
# Function to get all jokes for a category
def get_jokes_by_category(category):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, joke_text, category_id, likes, dislikes FROM jokes WHERE category_id = ?", [category])
    jokes = cursor.fetchall()
    cursor.close()
    return [{'id': joke[0], 'joke_text': joke[1], 'category_id': joke[2], 'likes': joke[3], 'dislikes': joke[4]} for joke in jokes]

# GET /jokes/:category
@app.route('/jokes/<string:category>', methods=['GET'])
def list_jokes_by_category(category):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM categories WHERE name = ?", [category])
    category_id = cursor.fetchone()
    cursor.close()

    if not category_id:
        return jsonify({'error': 'Category not found'}), 404

    jokes = get_jokes_by_category(category_id[0])
    return jsonify(jokes)

# Function to get a joke by ID
def get_joke_by_id(joke_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, joke_text, category_id, likes, dislikes FROM jokes WHERE id = ?", [joke_id])
    joke = cursor.fetchone()
    cursor.close()
    if joke:
        return {'id': joke[0], 'joke_text': joke[1], 'category_id': joke[2], 'likes': joke[3], 'dislikes': joke[4]}
    else:
        return None

# GET /jokes/:id
@app.route('/jokes/<int:joke_id>', methods=['GET'])
def get_joke(joke_id):
    joke = get_joke_by_id(joke_id)
    if joke:
        return jsonify(joke)
    else:
        return jsonify({'error': 'Joke not found'}), 404
# POST /jokes/:id/category/:category
@app.route('/joke/<int:joke_id>/category/<string:category>', methods=['POST'])
def copy_joke_to_category(joke_id, category):
    db = get_db()
    cursor = db.cursor()

    # First, check if the joke exists
    cursor.execute("SELECT * FROM jokes WHERE id = ?", [joke_id])
    joke_row = cursor.fetchone()
    if not joke_row:
        cursor.close()
        return jsonify({'error': 'Joke not found'}), 404

    # Next, check if the category exists
    cursor.execute("SELECT id FROM categories WHERE name = ?", [category])
    category_row = cursor.fetchone()
    if not category_row:
        cursor.close()
        return jsonify({'error': 'Category not found'}), 404

    # Extract category id
    category_id = category_row[0]

    # Finally, insert a new entry for the joke in the new category
    cursor.execute("INSERT INTO jokes (joke_text, category_id) VALUES (?, ?)", [joke_row[1], category_id])
    db.commit()
    new_joke_id = cursor.lastrowid

    cursor.close()
    return jsonify({'message': 'Joke copied to new category successfully', 'id': new_joke_id}), 201


# POST /joke/:id/:type
@app.route('/joke/<int:joke_id>/<string:type>', methods=['POST'])
def vote_joke(joke_id, type):
    if type != 'like' and type != 'dislike':
        return jsonify({'error': 'Invalid vote type'}), 400
    else:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(f"UPDATE jokes SET {type}s = {type}s + 1 WHERE id = ?", [joke_id])
        if cursor.rowcount == 0:
            cursor.close()
            return jsonify({'error': 'Joke not found'}), 404
        else:
            db.commit()
            cursor.close()
            return jsonify({'message': f'Vote recorded successfully for {type}'}), 200

if __name__ == '__main__':
    app.run(debug=True)
