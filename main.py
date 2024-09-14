import os
from io import StringIO
from flask import request, render_template, redirect, url_for, session
import flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from blogTrans import strTToHtml
from validate_image import validate_image

#app定义
app = flask.Flask(__name__)
app.secret_key = 'xxxxxxx'

#导通mysql并建立映射
host = "localhost",
port = 3306,
user = "root",
password = "123456",
database = "blog",
charset = "utf8"
# 配置app参数
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/blog?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True  # True跟踪数据库的修改，及时发送信号
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 10
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
db = SQLAlchemy(app)


class Blog(db.Model):
    __tablename__ = "Blog"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    time = db.Column(db.String(63), nullable=False)
    content =db.Column(db.Text, nullable=False)

class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(63), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    signature = db.Column(db.String(255), nullable=False)
    color_sign = db.Column(db.String(15), nullable=False)
    back_class = db.Column(db.String(15), nullable=False)
    back_photo = db.Column(db.String(255), nullable=False)

with app.app_context():
    db.create_all()

administrators = [1,2]  # 管理员列表

# home
@app.route('/')
def html_home():
    #查询登录状态
    user_id = session.get('user_id')
    if user_id:
        change_str = "<a href=\"/add\">此时此刻，写下你自己的博客 </a><a href=\"/space/"
        change_str += str(user_id)
        change_str += "\">个人中心 </a><a href=\"/logout\">登出</a>"
        if user_id in administrators:
            change_str += "<a href=\"/user_change\"> 管理用户</a>"
    else:
        change_str = "<a href=\"/login\">登录 </a><a href=\"/register\">注册</a>"

    #查询全部并格式化成html语句
    blog_list = Blog.query.all()
    html_str=""
    for blog in reversed(blog_list):
        html_str += "<li class=\"title\"><a href=\"/post/"
        html_str += str(blog.id)
        html_str += "\" class=\"blog\">"
        html_str += blog.title
        html_str += "</a><br><p>"
        html_str += blog.time

        user = User.query.filter_by(id=blog.author).first()
        if user:
            html_str += "<a href=\"/space/"
            html_str += str(user.id)
            html_str += "\">"
            html_str += user.username
            html_str += "</a></p></li>"
        else:
            html_str += "</p></li>"

    if html_str == "":
        html_str ="<li class=\"title\">程序员已删库跑路</li>"

    fin = open('templates/html_home.html', encoding='utf-8',mode= 'r')
    whole_str=""
    for line in fin:
        if line.strip() == '<ul id="list">':
            whole_str += line.strip() + html_str
        elif line.strip() =="<span id=\"date\"></span>":
            whole_str += line.strip() + change_str
        else:
            whole_str += line.strip()
    fin.close()

    return whole_str

# using post
@app.route("/post/<post_id>")
def post_detail(post_id):
    #根据post_id查找post
    blog=Blog.query.get(post_id)
    if blog:
        owner = User.query.filter_by(id=blog.author).first()
        fin = open('templates/post_detail.html', encoding='utf-8', mode='r')
        whole_str = ""
        text_str=""

        content_io=StringIO(blog.content)
        for line in content_io:
            text_str+=strTToHtml(line.strip())

        for line in fin:
            if line.strip() == "<title id=\"replace_title1\">" or line.strip() == "<h1 id=\"replace_title2\">":
                whole_str += line.strip() + '\n'
                whole_str += blog.title + '\n'
            elif line.strip() == "<p id=\"replace_time\">":
                whole_str += line.strip() + '\n'
                user = User.query.filter_by(id=blog.author).first()
                whole_str += "发表时间： " + blog.time + "<a href=\"/space/" + str(user.id) + "\"> " + user.username + "</a>" +'\n'
            elif line.strip() == "<div class=\"white\" id=\"replace_content\">":
                whole_str += line.strip() + '\n'
                whole_str += text_str + '\n'
            elif line.strip() == "background-image: url('/static/home/blue.png');":
                whole_str += "background-image: url('" + owner.back_photo + "');"
            else:
                whole_str += line.strip() + '\n'
        fin.close()

        return whole_str
    else:
        return render_template("html_error.html")

# add
@app.route('/add')
def html_add():
    user_id = session.get('user_id')
    user = User.query.filter_by(id=user_id).first()
    if user_id:
        return render_template('html_add.html', user=user)
    else:
        return render_template('html_error.html')

# add_preview
@app.route('/add_preview', methods=['POST'])
def html_add_preview():
    content = request.form['content']
    html_str=""
    whole_str=""

    content_io = StringIO(content)
    for line in content_io:
        html_str += strTToHtml(line.strip())

    fin = open('templates/post_preview.html', encoding='utf-8', mode='r')

    for line in fin:
        if line.strip() == "<div class=\"white\" id=\"replace_preview\">":
            whole_str += line.strip() + html_str
        else:
            whole_str += line.strip()
    fin.close()

    return whole_str

# add_post
@app.route('/add_post', methods=['POST'])
def add_post():
    user_id = session.get('user_id')
    if not user_id:
        return render_template('html_error.html')

    form=request.form
    title = form['title']
    content = form['content']
    time = form['time']
    # 1.创建ORM对象
    blog = Blog(author=user_id, title=title, time=time, content=content)
    # 2.将ORM对象添加到db.session中
    db.session.add(blog)
    # 3.将db.session中的改变同步到数据库中
    db.session.commit()
    return redirect(url_for("post_detail",post_id=blog.id),  code=302)

# login
@app.route('/login', methods=['GET', 'POST'])
def html_login():
    error = ""
    username = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if not user:
            error = '用户不存在'
        elif not check_password_hash(user.password, password):
            error = '密码不正确.'
        else:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('html_home'))
    return render_template('html_login.html', error=error, username=username)

# register
@app.route('/register', methods=['GET', 'POST'])
def html_register():
    error = ""
    username = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        _password = request.form['_password']

        user = User.query.filter_by(username=username).first()

        if user:
            error = '用户名已存在'
        elif not (password == _password):
            error = '两次密码不一致.'
        else:
            # 1.创建ORM对象
            user = User(username=username, password=generate_password_hash(password), signature="这个人什么也没有留下", color_sign="black", back_class="white", back_photo="/static/home/blue.png")
            # 2.将ORM对象添加到db.session中
            db.session.add(user)
            # 3.将db.session中的改变同步到数据库中
            db.session.commit()

            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('html_home'))
    return render_template('html_register.html', error = error, username = username)

# logout
@app.route('/logout')
def html_logout():
    user_id = session.get('user_id')
    if user_id:
        session.clear()
    return redirect(url_for('html_home'))

# space
@app.route('/space/<owner_id>')
def html_space(owner_id):
    #查询登录状态
    user_id = session.get('user_id')
    user=User.query.filter_by(id=user_id).first()
    owner=User.query.filter_by(id=owner_id).first()
    if not owner:
        return render_template('html_error.html')
    if user and (user.id == owner.id):
        change_str = "<a href=\"/add\">此时此刻，写下你自己的博客</a><a href=\"/space_change\"> 修改个人主页</a><a href=\"/\"> 回到主页</a><a href=\"/password_change\"> 修改密码</a><a href=\"/logout\"> 登出</a>"
    else:
        change_str = "<a href=\"/\"> 回到主页</a>"

    #查询全部并格式化成html语句
    blog_list = Blog.query.filter_by(author=owner_id).all()
    html_str=""
    for blog in reversed(blog_list):
        html_str += "<li class=\"title\"><a href=\"/post/"
        html_str += str(blog.id)
        html_str += "\" class=\"blog\">"
        html_str += blog.title
        html_str += "</a><br><p>"
        html_str += blog.time
        if user and (user.id == owner.id):
            html_str += "<a href=\"/post_change/"
            html_str += str(blog.id)
            html_str += "\"> 修改</a><a href=\"/post_delete/"
            html_str += str(blog.id)
            html_str += "\"> 删除</a></p></li>"
        elif user and user.id in administrators and (owner.id not in administrators):
            html_str += "<a href=\"/post_delete/"
            html_str += str(blog.id)
            html_str += "\"> 删除</a></p></li>"
        else:
            html_str += "</p></li>"

    if html_str == "":
        html_str ="<li class=\"title\">这个人什么也没有留下</li>"

    fin = open('templates/html_space.html', encoding='utf-8',mode= 'r')
    whole_str=""
    for line in fin:
        if line.strip() == '<ul id="list">':
            whole_str += line.strip() + html_str
        elif line.strip() == "<title>":
            whole_str += line.strip() + owner.username + "的个人空间"
        elif line.strip() == "background-image: url('/static/home/blue.png');":
            whole_str += "background-image: url('" + owner.back_photo + "');"
        elif line.strip() == "<div class=\"deep_white\" style=\"position: fixed;top: 0;right: 0;width: 100%;\">":
            whole_str += "<div class=\"deep_" + owner.back_class + "\" style=\"position: fixed;top: 0;right: 0;width: 100%;\">"
        elif line.strip() == "<h2 style=\"color: pink\">":
            whole_str += "<h2 style=\"color:" + owner.color_sign + "\">" + owner.signature
        elif line.strip() == "<span id=\"date\"></span>":
            whole_str += line.strip() + change_str
        elif line.strip() == "<h1 id=\"name_blog\">":
            whole_str += line.strip() + owner.username + "的个人博客"
        elif line.strip() == "<div class=\"white\">":
            whole_str += "<div class=\"" + owner.back_class + "\">"
        else:
            whole_str += line.strip()
    fin.close()

    return whole_str

# space_change
@app.route('/space_change', methods=['GET', 'POST'])
def html_space_change():
    # 查询登录状态
    user_id = session.get('user_id')
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return render_template('html_error.html')

    if request.method == 'POST':
        user.signature = request.form["signature"]
        user.color_sign = request.form["color_sign"]
        if request.form["back_class"]:
            user.back_class=request.form["back_class"]

        #检查文件上传
        uploaded_file = request.files['image']
        filename = uploaded_file.filename
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext in app.config['UPLOAD_EXTENSIONS'] and file_ext == validate_image(uploaded_file.stream):
                uploaded_file.save(os.path.join('static/user', str(user.id) + file_ext))
                user.back_photo="/static/user/" + str(user.id) + file_ext

        db.session.commit()

        return redirect(url_for("html_space", owner_id=user_id))
    else:
        change_str = "<a href=\"/\"> 回到主页</a>"
        # 查询全部并格式化成html语句
        fin = open('templates/html_space_change.html', encoding='utf-8', mode='r')
        whole_str = ""
        for line in fin:
            if line.strip() == "<title>":
                whole_str += line.strip() + "修改" + user.username + "的空间样式"
            elif line.strip() == "background-image: url('/static/home/blue.png');":
                whole_str += "background-image: url('" + user.back_photo + "');"
            elif line.strip() == "<div class=\"deep_white\" style=\"position: fixed;top: 0;right: 0;width: 100%;\" id=\"div_deep\">":
                whole_str += "<div class=\"deep_" + user.back_class + "\" style=\"position: fixed;top: 0;right: 0;width: 100%;\" id=\"div_deep\">"
            elif line.strip() == "<input class=\"title\" id=\"signature\" name=\"signature\" value=\"签名\" style=\"color:black\">":
                whole_str += "<input class=\"title\" id=\"signature\" name=\"signature\" value=\"" + user.signature + "\" style=\"color:" + user.color_sign + "\">"
            elif line.strip() == "<span id=\"date\"></span>":
                whole_str += line.strip() + change_str
            elif line.strip() == "<h1 id=\"name_blog\">":
                whole_str += line.strip() + user.username + "的个人博客"
            elif line.strip() == "<div class=\"white\" id=\"div_light\">":
                whole_str += "<div class=\"" + user.back_class + "\" id=\"div_light\">"
            elif line.strip() == "<input type=\"color\" name=\"color_sign\" id=\"color_sign\" value=\"black\" oninput=\"color_sign_change();\">":
                whole_str += "<input type=\"color\" name=\"color_sign\" id=\"color_sign\" value=\"" + user.color_sign + "\" oninput=\"color_sign_change();\">"
            else:
                whole_str += line.strip()
        fin.close()
        return whole_str

# password_change
@app.route('/password_change', methods=['GET', 'POST'])
def html_password_change():
    # 查询登录状态
    user_id = session.get('user_id')
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return render_template('html_error.html')

    error = ""
    username = ""
    if request.method == 'POST':
        password = request.form['password']
        change_password1 = request.form['change_password1']
        change_password2 = request.form['change_password2']

        if not check_password_hash(user.password, password):
            error = '密码不正确.'
        elif not change_password1 == change_password2:
            error = '两次新密码不一致.'
        else:
            user.password=generate_password_hash(change_password1)
            db.session.commit()
            session.clear()
            return redirect(url_for('html_login'))
    return render_template('html_password_change.html', error=error)

# post_change
@app.route('/post_change/<post_id>', methods=['GET', 'POST'])
def post_change(post_id):
    user_id = session.get('user_id')
    if not user_id:
        return render_template('html_error.html')

    blog = Blog.query.filter_by(id=post_id).first()
    if not blog:
        return render_template('html_error.html')

    owner = User.query.filter_by(id=blog.author).first()
    user = User.query.filter_by(id=user_id).first()
    if not owner:
        return render_template('html_error.html')

    if not (owner.id==user.id):
        return render_template('html_error.html')

    if request.method == 'POST':
        blog.title = request.form['title']
        blog.content = request.form['content']

        db.session.commit()
        return redirect(url_for("post_detail", post_id=blog.id), code=302)

    html = "/post_change/" + str(post_id)
    return render_template('post_change.html',blog=blog,html=html, user=user)

# post_delete
@app.route('/post_delete/<post_id>')
def post_delete(post_id):
    user_id = session.get('user_id')
    if not user_id:
        return render_template('html_error.html')

    blog = Blog.query.filter_by(id=post_id).first()
    if not blog:
        return render_template('html_error.html')

    owner = User.query.filter_by(id=blog.author).first()
    user = User.query.filter_by(id=user_id).first()
    if not owner:
        return render_template('html_error.html')

    if not (owner.id==user.id or (user.id in administrators and (owner.id not in administrators))):
        return render_template('html_error.html')

    db.session.delete(blog)
    db.session.commit()
    return redirect(url_for("html_space", owner_id=owner.id), code=302)

# user_delete
@app.route('/user_delete/<owner_id>')
def user_delete(owner_id):
    user_id = session.get('user_id')
    if not user_id:
        return render_template('html_error.html')

    if not (user_id in administrators):
        return render_template('html_error.html')

    owner = User.query.filter_by(id=owner_id).first()
    if (not owner) or owner.id in administrators:
        return render_template('html_error.html')

    # 先删除帖子
    blog_list = Blog.query.filter_by(author=owner_id).all()
    for blog in blog_list:
        db.session.delete(blog)

    db.session.delete(owner)
    db.session.commit()
    return redirect(url_for("user_change"), code=302)

# user_change
@app.route('/user_change')
def user_change():
    #查询登录状态
    user_id = session.get('user_id')
    if not user_id:
        return render_template('html_error.html')
    if not (user_id in administrators):
        return render_template('html_error.html')

    #查询全部并格式化成html语句
    user_list = User.query.all()
    html_str=""
    for owner in user_list:
        html_str += "<li class=\"title\"><a href=\"/space/"
        html_str += str(owner.id)
        html_str += "\" class=\"user\">"
        html_str += "用户id:" + str(owner.id)
        html_str += "</a><br><p>"
        html_str += owner.username

        if not(owner.id in administrators):
            html_str += "<a href=\"/user_delete/"
            html_str += str(owner.id)
            html_str += "\">"
            html_str += "删除该用户"
            html_str += "</a></p></li>"
        else:
            html_str += "<span> 该用户是管理员"
            html_str += "</span></p></li>"

    if html_str == "":
        html_str ="<li class=\"title\">程序员已删库跑路</li>"

    fin = open('templates/user_change.html', encoding='utf-8',mode= 'r')
    whole_str=""
    for line in fin:
        if line.strip() == '<ul id="list">':
            whole_str += line.strip() + html_str
        else:
            whole_str += line.strip()
    fin.close()

    return whole_str


if __name__=="__main__":
    app.run(port=2020,host="127.0.0.1",debug=True)   #调用run方法，设定端口号，启动服务
    #app.run(port=5000, host="100.81.181.213", debug=True)  # 调用run方法，设定端口号，启动服务
