from flask import Flask, render_template, request, Response, jsonify, send_from_directory
import threading
import time
import os
import json
from main import start as main_start
from rag.model_vector import query as rag_query
from llama_index.core.query_engine import BaseQueryEngine

app = Flask(__name__)

# 全局变量存储查询引擎和初始化状态
query_engine = None
initialized = False
initialization_error = None
initialization_lock = threading.Lock()  # 初始化锁，防止并发初始化
initialization_complete = threading.Event()  # 初始化完成事件


def initialize():
    """在后台线程中初始化查询引擎"""
    global query_engine, initialized, initialization_error

    # 确保初始化只执行一次
    with initialization_lock:
        if initialized:
            return

        try:
            # 调用main.py中的start方法
            query_engine = main_start()
            initialization_error = None
        except Exception as e:
            initialization_error = str(e)
            print(f"初始化失败: {e}")
        finally:
            initialized = True
            initialization_complete.set()  # 标记初始化完成


# 启动时在后台线程初始化
# 添加判断，仅在主进程中执行初始化
if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
    threading.Thread(target=initialize, daemon=True).start()


@app.route('/')
def index():
    """渲染聊天界面"""
    return render_template('index.html')


@app.route('/status')
def status():
    """返回系统初始化状态"""
    return jsonify({
        'initialized': initialized,
        'error': initialization_error
    })


@app.route('/query', methods=['POST'])
def query():
    """处理用户查询并返回流式响应"""
    if not initialized:
        # 等待初始化完成（最多等待30秒）
        if not initialization_complete.wait(30):
            return Response(
                'event: error\ndata: {"message": "系统初始化超时，请刷新页面重试"}\n\n',
                mimetype='text/event-stream'
            )

    if initialization_error:
        return Response(
            f'event: error\ndata: {{"message": "系统初始化失败: {initialization_error}"}}\n\n',
            mimetype='text/event-stream'
        )

    if not query_engine or not isinstance(query_engine, BaseQueryEngine):
        return Response(
            'event: error\ndata: {"message": "查询引擎未正确初始化"}\n\n',
            mimetype='text/event-stream'
        )

    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return Response(
            'event: error\ndata: {"message": "请输入问题"}\n\n',
            mimetype='text/event-stream'
        )

    def generate():
        """生成流式响应"""
        try:
            # 调用rag的query方法获取生成器
            for token in rag_query(question, query_engine):
                json_data = json.dumps({"token": token})
                yield f'data: {json_data}\n\n'
                time.sleep(0.01)  # 控制流输出速度
            yield 'event: complete\ndata: {}\n\n'
        except Exception as e:
            error_msg = f'处理查询时出错: {str(e)}'
            yield f'event: error\ndata: {{"message": "{error_msg}"}}\n\n'

    return Response(generate(), mimetype='text/event-stream')


# 配置图片文件夹路径
project_root = os.path.dirname(app.root_path)
app.config['PIC_FOLDER'] = os.path.join(project_root, 'doc', 'pic')


@app.route('/pic/<filename>')
def get_pic(filename):
    """获取图片"""
    return send_from_directory(app.config['PIC_FOLDER'], filename)


if __name__ == '__main__':
    # 生产环境建议关闭debug模式，并使用专业WSGI服务器
    app.run(debug=True, threaded=True, use_reloader=False)  # 可选：关闭自动重载
