import ast
import operator
import os
import sqlite3

from flask import Flask, jsonify, request, abort

app = Flask(__name__)

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def safe_eval_arithmetic(expression):
    """Evaluate a simple numeric expression (+ - * /) without executing arbitrary code."""

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[type(node.op)](_eval(node.operand))
        raise ValueError("Expression non autorisee")

    parsed = ast.parse(expression, mode="eval")
    return _eval(parsed)

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
    cursor = db.execute(
        "SELECT id, title, done FROM tasks WHERE title LIKE ?",
        (f"%{title}%",),
    )
    rows = cursor.fetchall()
    return jsonify([{"id": r[0], "title": r[1], "done": bool(r[2])} for r in rows])


@app.route("/tasks/score", methods=["POST"])
def score_task():
    data = request.get_json(silent=True) or {}
    formula = data.get("formula", "0")
    try:
        score = safe_eval_arithmetic(formula)
    except (ValueError, SyntaxError, TypeError, ZeroDivisionError):
        abort(400, description="Formule invalide : seules les expressions arithmetiques (+ - * /) sont autorisees")
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
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)
