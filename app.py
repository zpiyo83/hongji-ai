# app.py
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'MC-B0CEAEBD20E540ABA2F0ED0F5134C908'  # 设置一个密钥用于会话管理
CORS(app)  # 允许所有来源的请求

# 配置
BASE_URL = 'https://api.mindcraft.com.cn/v1/'
API_KEY = 'MC-B0CEAEBD20E540ABA2F0ED0F5134C908'
client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# 简单的用户存储
users = {}

@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        if username in users:
            return render_template('index.html', user_points=users[username]['points'])
        else:
            session.pop('username', None)  # 清除无效的会话
            return redirect(url_for('login'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return '用户名或密码错误'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return '用户名已存在'
        users[username] = {
            'password': generate_password_hash(password),
            'points': 10000
        }
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/api/send-message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({"error": "未登录"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "无效的请求数据"}), 400
            
        message = data.get('message')
        if not message:
            return jsonify({"error": "消息不能为空"}), 400

        # 检查用户积分
        username = session['username']
        user = users.get(username)
        if not user:
            return jsonify({"error": "用户不存在"}), 404

        params = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是智酱，是由智匠MindCraft开发的智能机器人，你是人类的好朋友，帮助他们解决各种问题。"},
                {"role": "user", "content": message}
            ],
            "temperature": 0.2,
            "max_tokens": 4000,
            "stream": False
        }

        try:
            response = client.chat.completions.create(**params)
            
            # 直接获取响应文本
            ai_response = response.choices[0].message.content
            
            return jsonify({"response": ai_response})

        except Exception as e:
            print(f"OpenAI API 错误: {str(e)}")  # 添加日志
            return jsonify({"error": "AI服务暂时不可用"}), 503

    except Exception as e:
        print(f"处理请求错误: {str(e)}")  # 添加日志
        return jsonify({"error": "服务器内部错误"}), 500

if __name__ == '__main__':
    app.run(debug=True)