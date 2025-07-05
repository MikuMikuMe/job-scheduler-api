Creating a job-scheduler API involves using various libraries and tools in Python. A good choice for this project is Flask for the API and Celery for job scheduling and priority management. Redis can be used as a message broker to handle requests and responses between Flask and Celery.

Below is a full implementation of a basic job-scheduler API using Flask, Celery, and Redis. This program covers managing and scheduling background jobs with priorities and retry logic. You will need to have Python installed, along with the necessary packages: `flask`, `celery`, and `redis`.

### Setup Instructions
1. Ensure you have Redis installed and running.
2. Install necessary Python packages using pip:
   ```bash
   pip install flask celery redis
   ```
3. Save the following script as `app.py`.

```python
from flask import Flask, request, jsonify
from celery import Celery
from celery.exceptions import MaxRetriesExceededError
from celery.schedules import crontab
import time

# Initialize Flask app
app = Flask(__name__)

# Configure Redis as the broker for Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Celery Task Definition
@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_job(self, data, priority):
    """Background task that simulates processing a job."""
    try:
        # Simulate job processing time
        time.sleep(5)
        result = {
            'status': 'success',
            'data': data,
            'priority': priority
        }
        return result
    except Exception as e:
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            return {'status': 'failure', 'error': str(e)}

@app.route('/schedule-job', methods=['POST'])
def schedule_job():
    """Endpoint to schedule a new job."""
    data = request.json
    job_data = data.get('data', {})
    priority = data.get('priority', 'normal')  # Normal is default if no priority provided

    # Validate priority input
    if priority not in ['low', 'normal', 'high']:
        return jsonify({'error': 'Invalid priority level. Choose from low, normal, high.'}), 400

    # Adding to Celery with priority routing
    try:
        result = process_job.apply_async((job_data, priority), priority=priority_map(priority))
        return jsonify({'status': 'Job scheduled', 'task_id': result.id}), 202
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-status/<task_id>', methods=['GET'])
def get_status(task_id):
    """Endpoint to get the status of a specific task."""
    task = process_job.AsyncResult(task_id)
    if task.state == 'PENDING':
        return jsonify({'status': 'Pending...'})
    elif task.state != 'FAILURE':
        response = {
            'status': task.state,
            'result': task.result
        }
        return jsonify(response)
    else:
        # Something went wrong in the background job
        return jsonify({'status': 'Failure', 'error': str(task.result)}), 400

def priority_map(priority):
    """Maps priority to Celery's priority levels."""
    mapping = {
        'low': 0,
        'normal': 5,
        'high': 9
    }
    return mapping.get(priority, 5)

# Flask application entry point
if __name__ == '__main__':
    app.run(debug=True)
```

### Workflow
1. **Flask API**: Handles incoming HTTP requests, specifically to schedule jobs and check their status.
2. **Celery**: Manages the queuing and execution of jobs based on the defined tasks.
3. **Redis**: Acts as a message broker for Celery to communicate with and store job states.

### Execution
- Start the Redis server.
- Start the Celery worker in a separate terminal:
  ```bash
  celery -A app.celery worker --loglevel=info
  ```
- Start the Flask server by running the `app.py` file:
  ```bash
  python app.py
  ```
- Use any HTTP client (like Postman) to send a POST request to `http://localhost:5000/schedule-job` with JSON payload specifying the job data and priority (options: low, normal, high).
- Check the job status by sending a GET request to `http://localhost:5000/get-status/<task_id>` with the `task_id` obtained from scheduling.

This implementation includes error handling such as invalid priority levels, potential processing errors, and job retries (3 retries in case of failures) using Celery's built-in mechanisms. Adjust configurations as needed to fit your specific use case or deployment environment.