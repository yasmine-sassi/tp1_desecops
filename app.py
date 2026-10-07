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
