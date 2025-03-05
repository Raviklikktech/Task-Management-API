from flask import Flask, jsonify, request, Response
import datetime
import threading
import time
import queue
import json

app = Flask(__name__)

tasks = [
    {'id': 1, 'title': 'Grocery Shopping', 'completed': False, 'due_date': '2024-03-15'},
    {'id': 2, 'title': 'Pay Bills', 'completed': False, 'due_date': '2024-03-20'},
]
next_task_id = 3  # Global counter for task IDs
clients = []  # Stores active SSE connections


def send_notification(task_id):
    """Simulates sending a notification asynchronously."""
    time.sleep(2)  # Simulate delay
    print(f"Notification sent for task {task_id}")


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Retrieve all tasks."""
    return jsonify(tasks)


@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task."""
    global next_task_id
    data = request.get_json()

    new_task = {
        'id': next_task_id,
        'title': data['title'],
        'completed': False,
        'due_date': data.get('due_date') or datetime.date.today().strftime("%Y-%m-%d")
    }

    next_task_id += 1
    tasks.append(new_task)

    # Notify SSE clients
    notify_clients()

    return jsonify(new_task), 201


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task and send notifications asynchronously."""
    data = request.get_json()

    for task in tasks:
        if task['id'] == task_id:
            task.update(data)

            # Notify SSE clients
            notify_clients()

            # Send notification asynchronously
            notification_thread = threading.Thread(target=send_notification, args=(task_id,))
            notification_thread.start()

            return jsonify(task), 200

    return jsonify({'error': 'Task not found'}), 404


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    global tasks
    tasks = [task for task in tasks if task['id'] != task_id]

    # Notify SSE clients
    notify_clients()

    return jsonify({'message': 'Task deleted'}), 204


@app.route('/api/tasks/stream')
def task_stream():
    """Provides real-time updates using Server-Sent Events (SSE)."""
    def event_stream():
        """Generates events for SSE clients."""
        q = queue.Queue()
        clients.append(q)
        try:
            while True:
                event = q.get()
                yield f"data: {event}\n\n"
        except GeneratorExit:
            clients.remove(q)

    return Response(event_stream(), content_type="text/event-stream")


def notify_clients():
    """Send updates to all SSE clients."""
    update_event = json.dumps({"message": "Task list updated", "tasks": tasks})
    for client in clients:
        client.put(update_event)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
