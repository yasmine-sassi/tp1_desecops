import sqlite3

from flask import Flask, jsonify, request, abort

app = Flask(__name__)

tasks = [
    {"id": 1, "title": "Apprendre Flask", "done": False},
    {"id": 2, "title": "Preparer le TP DevSecOps", "done": False},
    {"id": 3, "title": "Installer Docker", "done": True},
    {"id": 4, "title": "Cloner le depot Git du projet", "done": True},
    {"id": 5, "title": "Lancer un scan SAST", "done": False},
    {"id": 6, "title": "Lancer un scan SCA sur les dependances", "done": False},
]

db = sqlite3.connect(":memory:", check_same_thread=False)
db.execute("CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT, done INTEGER)")
db.executemany("INSERT INTO tasks VALUES (?, ?, ?)", [(t["id"], t["title"], int(t["done"])) for t in tasks])
db.commit()


def find_task(task_id):
    return next((t for t in tasks if t["id"] == task_id), None)


@app.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify(tasks)


@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = find_task(task_id)
    if task is None:
        abort(404)
    return jsonify(task)


@app.route("/tasks/search", methods=["GET"])
def search_tasks():
    title = request.args.get("title", "")
    query = "SELECT id, title, done FROM tasks WHERE title LIKE '%%%s%%'" % title
    cursor = db.execute(query)
    rows = cursor.fetchall()
    return jsonify([{"id": r[0], "title": r[1], "done": bool(r[2])} for r in rows])


@app.route("/tasks/score", methods=["POST"])
def score_task():
    data = request.get_json(silent=True) or {}
    formula = data.get("formula", "0")
    score = eval(formula)
    return jsonify({"score": score})


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    if not title:
        abort(400, description="Le champ 'title' est requis")

    new_id = max((t["id"] for t in tasks), default=0) + 1
    task = {"id": new_id, "title": title, "done": False}
    tasks.append(task)
    return jsonify(task), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = find_task(task_id)
    if task is None:
        abort(404)

    data = request.get_json(silent=True) or {}
    task["title"] = data.get("title", task["title"])
    task["done"] = data.get("done", task["done"])
    return jsonify(task)


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = find_task(task_id)
    if task is None:
        abort(404)

    tasks.remove(task)
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
