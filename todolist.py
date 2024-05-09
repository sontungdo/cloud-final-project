from flask import Flask, render_template, redirect, g, request, url_for, jsonify, json
import urllib
import requests

app = Flask(__name__)
# TODO_API_URL = "http://"+os.environ['TODO_API_IP']+":5001"
TODO_API_URL = "http://localhost:5001"

@app.route("/")
def show_list():
    resp = requests.get(TODO_API_URL + "/api/items")
    resp = resp.json()
    return render_template('index.html', todolist=resp)

@app.route("/add", methods=['POST'])
def add_entry():
    requests.post(TODO_API_URL + "/api/items", json={
        "what_to_do": request.form['what_to_do'],
        "due_date": request.form['due_date']
    })
    return redirect(url_for('show_list'))

@app.route("/delete/<int:item_id>")
def delete_entry(item_id):
    requests.delete(TODO_API_URL + "/api/items/" + str(item_id))
    return redirect(url_for('show_list'))

@app.route("/mark/<int:item_id>")
def mark_as_done(item_id):
    requests.put(TODO_API_URL + "/api/items/" + str(item_id))
    return redirect(url_for('show_list'))

if __name__ == "__main__":
    app.run("0.0.0.0", port=5002)
