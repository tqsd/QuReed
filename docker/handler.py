from flask import Flask, request, redirect, url_for, make_response, Response
import docker
import uuid
import requests
import logging

app = Flask(__name__)
client = docker.from_env()

# Set up logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Dictionary to store session-container mappings
session_containers = {}

# Create or get a Docker network for internal communication
network_name = "session_network"
try:
    network = client.networks.get(network_name)
except docker.errors.NotFound:
    network = client.networks.create(network_name, driver="bridge")

@app.route('/', defaults={'path': ''})
@app.route('/path:path', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_request(path):
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        response = make_response(redirect(url_for('handle_request', path=path)))
        response.set_cookie('session_id', session_id)
        return response

    if session_id not in session_containers:
        # Start a new container within the Docker network
        app.logger.info(f"Creating new container")
        container = client.containers.run(
            "my-flet-app",
            detach=True,
            network=network_name
        )
        container.reload()  # Reload to update attributes
        ip_address = container.attrs['NetworkSettings']['Networks'][network_name]['IPAddress']
        session_containers[session_id] = ip_address
    else:
        ip_address = session_containers[session_id]

    # Formulate the destination URL
    dest_url = f'http://{ip_address}:8080/{path}'

    # Forward the request to the destination URL
    method = request.method
    if method == 'GET':
        resp = requests.get(dest_url, params=request.args, stream=True)
    elif method == 'POST':
        resp = requests.post(dest_url, json=request.json, data=request.form, files=request.files, stream=True)
    elif method == 'PUT':
        resp = requests.put(dest_url, json=request.json, data=request.form, stream=True)
    elif method == 'DELETE':
        resp = requests.delete(dest_url, stream=True)
    else:
        return "Unsupported HTTP method", 405

    # Stream the response back to the client
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, headers)
    return response

@app.route('/cleanup')
def cleanup():
    # Stop and remove containers
    for session_id, ip_address in list(session_containers.items()):
        container = client.containers.list(filters={"network": network_name, "ancestor": "my-flet-app"})
        for cont in container:
            if cont.attrs['NetworkSettings']['Networks'][network_name]['IPAddress'] == ip_address:
                cont.stop()
                cont.remove()
        del session_containers[session_id]
    return 'Cleanup successful'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
