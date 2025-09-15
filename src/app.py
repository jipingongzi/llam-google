from flask import Flask, render_template, request, Response, jsonify
import threading
import time
from main import start as main_start
from rag.model_vector import query as rag_query
from llama_index.core.query_engine import BaseQueryEngine

app = Flask(__name__)

# 全局变量存储查询引擎和初始化状态
query_engine = None
initialized = False
initialization_error = None


def initialize():
    """在后台线程中初始化查询引擎"""
    global query_engine, initialized, initialization_error
    try:
        # 调用main.py中的start方法
        query_engine = main_start()
        initialized = True
    except Exception as e:
        initialization_error = str(e)
        initialized = True  # 即使出错也标记为已初始化（只是初始化失败）
        print(f"初始化失败: {e}")


# 启动时在后台线程初始化
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
        return Response(
            'event: error\ndata: {"message": "系统尚未初始化完成，请稍后再试"}\n\n',
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
    question = data.get('question', '')

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
                # 先处理引号转义
                escaped_token = token.replace('"', '\\"')
                # 再使用处理后的字符串
                yield f'data: {{"token": "{escaped_token}"}}\n\n'
                # 短暂延迟，避免响应太快
                time.sleep(0.01)
            # 发送完成事件
            yield 'event: complete\ndata: {}\n\n'
        except Exception as e:
            yield f'event: error\ndata: {{"message": "处理查询时出错: {str(e)}"}}\n\n'

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
