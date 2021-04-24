from flask import Flask, render_template, request, make_response, redirect
from validate_email import validate_email
import psycopg2, hashlib, os



app = Flask(__name__)

con = psycopg2.connect(database="kwitter", user="troyalfelt", password="Matlock",
host ="127.0.0.1", port="5432")

##CREATE TABLE users (
##	id bigserial,
##	user_name varchar(50),
##	password varchar(300),
##	email varchar(50),
##	salt varchar(300),
##	PRIMARY KEY (id)
##);
##	CREATE TABLE posts (
##	post_id bigserial,
##	id bigint,
##	user_name varchar(50),
##	post varchar(280),
##	PRIMARY KEY (post_id),
##	FOREIGN KEY(id) REFERENCES users(id)
##);
##CREATE TABLE comments (
##	comment_id bigserial,
##	id bigint,
##	post_id bigint,
##	user_name varchar(50),
##	comment varchar(280),
##	PRIMARY KEY (comment_id),
##	FOREIGN KEY(id) REFERENCES users(id),
##	FOREIGN KEY(post_id) REFERENCES posts(post_id)
##	);

pepper = r'e_XT<tUB%"Gg4F\or57i{^&MAcAaiH@-z|T&y3w8#HTcp~8GcS9K{Y&x?ZC_dxi}*m<T0sr{in\"SDf2\_\6$*{gqe>E2yDZ]}XJ'



@app.route('/')
def home():
    return render_template('/home.html')

@app.route('/create', methods = ['GET', 'POST'])
def register():
    usr = request.cookies.get('name')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        confirm = request.form['confirm']
        cur = con.cursor()
        cur.execute("""SELECT * FROM users WHERE user_name = %s""", (username,))
        account = cur.fetchone()
        cur.execute("""SELECT FROM users WHERE email = %s""", (email,))
        email_used = cur.fetchone()
        if account:
            print('Account already exists')
        elif not validate_email(email, check_mx=True):
            print('Invalid email address')
        elif email_used:
            print('Email address already in use')

        elif password == confirm:
            salt = os.urandom(32)   #Generate random salt
            s = ""
            for i in salt:
                s += str(i)
            salt = s

            password = hashlib.sha256((request.form['password'] + salt + pepper).encode('utf-8')).hexdigest()   #Retrieve password, and hash password and salt
            cur.execute("""INSERT INTO users(user_name, password, email, salt) VALUES (%s, %s, %s, %s)""", (username, password, email, salt))    #Store username, password, salt, and email
            con.commit()    #Commit changes to the database
            res = make_response(redirect('/home'))
            res.set_cookie('name', username, max_age = 60&60*1200)
            return res
        else:
            print("Password does not match confirmation, please try again.")


    return render_template('/create.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = con.cursor()
        cur.execute("""SELECT user_name, password, salt FROM users WHERE user_name = %s""", (username,))
        user_info = cur.fetchall()
        if user_info:
            user_name = user_info[0][0]
            password = user_info[0][1]
            salt = user_info[0][2]
        else:
            username = None
            password = None
            salt = None

        if password and password == hashlib.sha256((request.form['password'] + salt + pepper).encode('utf-8')).hexdigest():
            res = make_response(redirect('/cookie'))
            res.set_cookie('name', username, max_age = 60*60*2*600)
            return res
        else:
            print("Incorrect username/password")

    return render_template('/index.html')

@app.route('/cookie')
def set_id():
    username = request.cookies.get('name')
    res = make_response(redirect('/home'))
    cur = con.cursor()
    cur.execute("""SELECT id FROM users WHERE user_name = %s""", (username,))
    tupl = cur.fetchone()
    id = str(tupl[0])
    print("here it is")
    print(id)
    print(type(id))
    res.set_cookie('id', id, max_age = 1200000000)
    return res


@app.route('/logout')
def leave():
    res = make_response(redirect('/login'))
    res.set_cookie('name', '', expires=0)
    res.set_cookie('id', '', expires=0)
    return res

@app.route('/make_post', methods = ['POST'])
def pst():
    if request.method == "POST":
        if request.cookies.get('name') != None and request.cookies.get('id') != None:
            username = request.cookies.get('name')
            id = int(request.cookies.get('id'))
            print(id)
            post = request.form['post_space']
            cur = con.cursor()
            cur.execute("""INSERT INTO posts(id, user_name, post) VALUES(%s, %s, %s)""", (id, username, post))
            con.commit()
    return redirect('/home')

@app.route('/home')
def main():
    cur = con.cursor()
    cur.execute("""SELECT * FROM posts""")
    posts = cur.fetchall()
    cur.execute("""SELECT * FROM comments""")
    comments = cur.fetchall()
    return render_template('/home.html', posts = posts, comments = comments)

@app.route('/delete/<type>/<id_num>', methods = ['POST'])
def remove(type, id_num):
    if request.method == "POST":
        if type == "pst":
            cur = con.cursor()
            cur.execute("""DELETE FROM comments WHERE post_id = %s""", (id_num,))
            con.commit()
            cur.execute("""DELETE FROM posts WHERE post_id = %s""", (id_num,))
            con.commit()
            print("this deletes a post without comments")
            return redirect('/home')
        elif type == "comment":
            cur = con.cursor()
            cur.execute("""DELETE FROM comments WHERE comment_id = %s""", (id_num,))
            con.commit()
            print("this delets a comment")
            return redirect('/home')
    return redirect('/home')

@app.route('/comment/<post_id>', methods = ['POST'])
def comm(post_id):
    if request.method == "POST":
        id = int(request.cookies.get('id'))
        username = request.cookies.get('name')
        comment = request.form['comment']
        post = int(post_id)
        cur = con.cursor()
        cur.execute("""INSERT INTO comments(id, post_id, user_name, comment) VALUES(%s, %s, %s, %s)""", (id, post, username, comment))
        con.commit()
    return redirect('/home')

@app.route('/profile/<user>')
def render(user):
    cur = con.cursor()
    cur.execute("""SELECT * FROM posts WHERE user_name = %s""", (user,))
    all_posts = cur.fetchall()
    print(all_posts)
    return render_template('/profile.html', all_posts = all_posts, user = user)



if __name__ == '__main__':
    app.run(debug = True)
