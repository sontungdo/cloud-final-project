from flask import Flask, render_template, redirect, g, request, url_for, jsonify, Response
import mysql.connector
import urllib
import json

DATABASE = 'todolist'

app = Flask(__name__)
app.config.from_object(__name__)

@app.route("/api/items")
def get_items():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, what_to_do, due_date, status FROM entries')
    entries = cur.fetchall()
    cur.close()
    tdlist = [dict(id=row[0], what_to_do=row[1], due_date=row[2], status=row[3])
              for row in entries]
    response = Response(json.dumps(tdlist), mimetype='application/json')
    return response

@app.route("/api/items", methods=['POST'])
def add_item():
    db = get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO entries (what_to_do, due_date) VALUES (%s, %s)',
                (request.json['what_to_do'], request.json['due_date']))
    new_id = cur.lastrowid
    db.commit()
    cur.close()
    return jsonify({"id": new_id})

@app.route("/api/items/<int:item_id>", methods=['DELETE'])
def delete_item(item_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM entries WHERE id=%s", (item_id,))
    db.commit()
    cur.close()
    return jsonify({"result": True})

@app.route("/api/items/<int:item_id>", methods=['PUT'])
def update_item(item_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE entries SET status='done' WHERE id=%s", (item_id,))
    db.commit()
    cur.close()
    return jsonify({"result": True})

def get_db():
    if not hasattr(g, 'mysql_db'):
        g.mysql_db = mysql.connector.connect(
            host="localhost",
            database=DATABASE,
            user="todo_app",
            password="todo_password"
        )
    return g.mysql_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'mysql_db'):
        g.mysql_db.close()

if __name__ == "__main__":
    app.run("0.0.0.0", port=5001)
