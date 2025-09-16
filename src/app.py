from flask import Flask, render_template, request, Response, jsonify, send_from_directory
import threading
import time
import os
import json
from main import start as main_start
from rag.model_vector import query as rag_query
from llama_index.core.query_engine import BaseQueryEngine

app = Flask(__name__)

query_engine = None
initialized = False
initialization_error = None
initialization_lock = threading.Lock()
initialization_complete = threading.Event()


def initialize():
    global query_engine, initialized, initialization_error
    with initialization_lock:
        if initialized:
            return
        try:
            query_engine = main_start()
            initialization_error = None
        except Exception as e:
            initialization_error = str(e)
            print(f"error: {e}")
        finally:
            initialized = True
            initialization_complete.set()


if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
    threading.Thread(target=initialize, daemon=True).start()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/status')
def status():
    return jsonify({
        'initialized': initialized,
        'error': initialization_error
    })


@app.route('/query', methods=['POST'])
def query():
    if not initialized:
        if not initialization_complete.wait(30):
            return Response(
                'event: error\ndata: {"message": "init timeout"}\n\n',
                mimetype='text/event-stream'
            )

    if initialization_error:
        return Response(
            f'event: error\ndata: {{"message": "error: {initialization_error}"}}\n\n',
            mimetype='text/event-stream'
        )

    if not query_engine or not isinstance(query_engine, BaseQueryEngine):
        return Response(
            'event: error\ndata: {"message": "query engine error"}\n\n',
            mimetype='text/event-stream'
        )

    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return Response(
            'event: error\ndata: {"message": "input question"}\n\n',
            mimetype='text/event-stream'
        )

    def generate():
        try:
            for token in rag_query(question, query_engine):
                json_data = json.dumps({"token": token})
                yield f'data: {json_data}\n\n'
                time.sleep(0.01)
            yield 'event: complete\ndata: {}\n\n'
        except Exception as e:
            error_msg = f'error: {str(e)}'
            yield f'event: error\ndata: {{"message": "{error_msg}"}}\n\n'

    return Response(generate(), mimetype='text/event-stream')


project_root = os.path.dirname(app.root_path)
app.config['PIC_FOLDER'] = os.path.join(project_root, 'doc', 'pic')


@app.route('/pic/<filename>')
def get_pic(filename):
    return send_from_directory(app.config['PIC_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True, threaded=True, use_reloader=False)
