from flask import Flask, flash, render_template, request, redirect, url_for, g, session
import sqlite3
from datetime import datetime, timedelta, timezone
import smtplib
app = Flask(__name__)

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("money.db")
        db.row_factory = sqlite3.Row
    return db

@app.route('/' , methods = ["GET", "POST"])
def initialize():
    session.clear()
    return redirect(url_for('home'))

@app.route('/home', methods = ["GET", "POST"])
def home():
    return render_template("home.html")

@app.route('/info', methods = ["GET", "POST"])
def info():
    if session.get('username') == None:
        flash("請先登入","error")
        return redirect(url_for('login'))
    
    db_1 = get_db()
    cursor = db_1.cursor()
    person = session.get('username')
    email = cursor.execute('select email from users where username = "%s";'% (person, )).fetchone()[0]
    historys = []
    tmp = cursor.execute('select * from history where person1 = "%s" or person2 = "%s" order by date desc;'% (person, person, )).fetchall()
    for i in tmp:
        if(i[2] == 1):
            historys.append([str(i[0]) + " 欠 " + str(i[1]) + " " + str(i[3]) + " 元", str(i[4])])
        elif(i[2] == 2):
            historys.append([str(i[0]) + " 還 " + str(i[1]) + " " + str(i[3]) + " 元", str(i[4])])
            
    querys1 = []
    querys2 = []
    tmp = cursor.execute('select * from records where person1 = "%s";'% (person, )).fetchall()
    for i in tmp:
        querys1.append("你欠 " + str(i[1]) + " " + str(i[2]) + " 元")
        
    tmp = cursor.execute('select * from records where person2 = "%s";'% (person, )).fetchall()
    for i in tmp:
        querys2.append([str(i[0]) + " 欠你 " + str(i[2]) + " 元", str(i[0]), i[2]])
    
    return render_template("info.html", email = email, historys = historys, querys1 = querys1, querys2 = querys2)

@app.route('/owemoney', methods = ["GET", "POST"])
def owemoney():
    if session.get('username') == None:
        flash("請先登入","error")
        return redirect(url_for('login'))
    
    db_1 = get_db()
    cursor = db_1.cursor()
    tmp = cursor.execute('select username from users').fetchall()
    person = []
    for i in tmp:
        person.append(i[0])
    
    return render_template("owemoney.html", persons = person)

@app.route('/returnmoney', methods = ["GET", "POST"])
def returnmoney():
    if session.get('username') == None:
        flash("請先登入","error")
        return redirect(url_for('login'))
    
    db_1 = get_db()
    cursor = db_1.cursor()
    tmp = cursor.execute('select username from users').fetchall()
    person = []
    for i in tmp:
        person.append(i[0])
    
    return render_template("returnmoney.html", persons = person)
'''
@app.route('/cart',methods=['GET','POST'])
def cart():
    if session.get('username') == None:
        flash("請先登入","error")
        return redirect(url_for('login'))
    
    username = str(session.get('username'))
    db_1 = get_db()
    cursor = db_1.cursor()
    tmp = cursor.execute("SELECT item1, item2, item3, item4, item5 FROM Carts WHERE username=?", (username,)).fetchone()
    
    return render_template("cart.html")
'''
@app.route('/owe_submit',methods=['GET','POST'])
def owe_submit():    
    db_1 = get_db()
    cursor = db_1.cursor()
    person1 = str(request.form["person1"])
    person2 = str(request.form["person2"])
    amount = int(request.form["amount"])
    note = str(request.form["note"])
    
    if(session.get('username') != person1 and session.get('username') != person2):
        flash("其中一個人必須是自己", 'error')
        return redirect(url_for('owemoney'))
    elif(person1 == person2):
        flash("不能都選擇同一人", 'error')
        return redirect(url_for('owemoney'))
    
    cnt = cursor.execute('select count( * ) as cnt from history;').fetchone()[0]
    cursor.execute('insert into history values("%s", "%s", %s, %s, "%s", %s);'% (person1, person2, 1, amount, note, cnt + 1, ))
    tmp = cursor.execute('select * from records where (person1 = "%s" and person2 = "%s") or (person2 = "%s" and person1 = "%s");'% (person1, person2, person1, person2, )).fetchone()
    if(tmp == None):
        cursor.execute('insert into records values("%s", "%s", %s);'% (person1, person2, amount, ))
        db_1.commit()
    else:
        if(tmp[0] == person1):
            amount += tmp[2]
            cursor.execute('UPDATE records SET amount=%s WHERE person1="%s" and person2="%s";'% (amount, person1, person2))
            db_1.commit()
        else:
            amount = tmp[2] - amount
            if(amount < 0):
                cursor.execute('UPDATE records SET person1="%s", person2="%s", amount=%s WHERE person1="%s" and person2="%s";'% (person1, person2, amount * -1, person2, person1))
                db_1.commit()
            elif(amount == 0):
                cursor.execute('delete from records where person1 = "%s" and person2 = "%s";'% (person2, person1, ))
                db_1.commit()
            else:
                cursor.execute('UPDATE records SET amount=%s WHERE person1="%s" and person2="%s";'% (amount, person2, person1))
                db_1.commit()

    flash("更新成功", 'success')
    return redirect(url_for('owemoney'))

@app.route('/return_submit',methods=['GET','POST'])
def return_submit():    
    db_1 = get_db()
    cursor = db_1.cursor()
    person1 = str(request.form["person1"])
    person2 = str(request.form["person2"])
    amount = int(request.form["amount"])
    
    if(session.get('username') != person1 and session.get('username') != person2):
        flash("其中一個人必須是自己", 'error')
        return redirect(url_for('returnmoney'))
    elif(person1 == person2):
        flash("不能都選擇同一人", 'error')
        return redirect(url_for('returnmoney'))
    
    cnt = cursor.execute('select count( * ) as cnt from history;').fetchone()[0]
    cursor.execute('insert into history values("%s", "%s", %s, %s, "(無)",%s);'% (person1, person2, 2, amount, cnt + 1, ))
    tmp = cursor.execute('select * from records where (person1 = "%s" and person2 = "%s") or (person2 = "%s" and person1 = "%s");'% (person1, person2, person1, person2, )).fetchone()
    if(tmp == None):
        cursor.execute('insert into records values("%s", "%s", %s);'% (person2, person1, amount, ))
        db_1.commit()
    else:
        if(tmp[0] == person2):
            amount += tmp[2]
            cursor.execute('UPDATE records SET amount=%s WHERE person1="%s" and person2="%s";'% (amount, person2, person1))
            db_1.commit()
        else:
            amount = tmp[2] - amount
            if(amount < 0):
                cursor.execute('UPDATE records SET person1="%s", person2="%s", amount=%s WHERE person1="%s" and person2="%s";'% (person2, person1, amount * -1, person1, person2))
                db_1.commit()
            elif(amount == 0):
                cursor.execute('delete from records where person1 = "%s" and person2 = "%s";'% (person1, person2, ))
                db_1.commit()
            else:
                cursor.execute('UPDATE records SET amount=%s WHERE person1="%s" and person2="%s";'% (amount, person1, person2))
                db_1.commit()

    flash("更新成功", 'success')
    return redirect(url_for('returnmoney'))

@app.route('/sendmail/<person>-<amount>',methods=['GET','POST'])
def sendmail(person, amount):    
    db_1 = get_db()
    cursor = db_1.cursor()
    nowperson = session.get('username')
    smtp=smtplib.SMTP('smtp.gmail.com', 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.login('bendtail@g.ncu.edu.tw','xqoe wayf lqnl lesy')
    from_addr='bendtail@g.ncu.edu.tw'
    
    to_addr = str(cursor.execute('select email from users where username = "%s";'% (person, )).fetchone()[0])
    
    msg="Subject:該還錢了\n你欠了 " + nowperson + " " + str(amount) + " 元，現在是時候還錢了!"
    status=smtp.sendmail(from_addr, to_addr, msg.encode())
    if status=={}:
        flash("信件已寄出", 'success')
    else:
        flash("信件傳送失敗", 'error')
    smtp.quit()
    
    return redirect(url_for('info'))

@app.route('/register',methods=['GET','POST'])
def register():
    return render_template("register.html")

@app.route('/login',methods=['GET','POST'])
def login():
    return render_template("login.html")

@app.route('/logout',methods=['GET','POST'])
def logout(): 
    session.clear()
    flash("已登出","success")
    return redirect(url_for('home'))

@app.route("/login_submit", methods=["GET", "POST"])
def login_submit():
    if request.method == "POST":
        name = str(request.form["username"])
        password = str(request.form["password"])
        db_1 = get_db()
        cursor = db_1.cursor()
        user = cursor.execute('SELECT * FROM Users WHERE username="%s" AND password="%s";'% (name, password, )).fetchone()
        if user:
            session["username"] = name
            db_1.commit()           
            flash("登入成功", 'success')
            return redirect(url_for('home'))
        else:
            if cursor.execute('SELECT * FROM Users WHERE username="%s";'% (name,)).fetchone():
                flash("密碼錯誤", 'error')
                return redirect(url_for('login'))
            else:
                flash("使用者不存在 請註冊", 'error')
                return redirect(url_for('login'))
    
    return redirect(url_for('login'))

@app.route("/register_submit", methods=["GET", "POST"])
def register_submit():
    if request.method=="POST":
        name = str(request.form["username"])
        password = str(request.form["password"])
        email = str(request.form["email"])
        db_1=get_db()
        cursor=db_1.cursor()
        user=cursor.execute('select * from users where username = "%s";'% (name,)).fetchone()

        if user!=None:
            flash("此名稱已被使用", 'error')
            return redirect(url_for('register'))
        else:
            cursor.execute('INSERT INTO Users VALUES ("%s", "%s", "%s");'% (name, password, email, ))
            db_1.commit()
            flash("註冊成功", 'success')
            return redirect(url_for('login'))
    return redirect(url_for('register'))


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.secret_key = 'password'
    app.run(debug=True)
