import mysql.connector

def connect_db():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="assistant_ia"
    )


def register_user(nom,email,password):

    db = connect_db()
    cursor = db.cursor()

    query = "INSERT INTO users (nom,email,password) VALUES (%s,%s,%s)"

    cursor.execute(query,(nom,email,password))

    db.commit()

    cursor.close()
    db.close()


def login_user(email,password):

    db = connect_db()
    cursor = db.cursor(dictionary=True)

    query = "SELECT * FROM users WHERE email=%s AND password=%s"

    cursor.execute(query,(email,password))

    user = cursor.fetchone()

    cursor.close()
    db.close()

    return user


def save_search(user_id,question,reponse):

    db = connect_db()
    cursor = db.cursor()

    query = """
    INSERT INTO recherches (user_id,question,reponse)
    VALUES (%s,%s,%s)
    """

    cursor.execute(query,(user_id,question,reponse))

    db.commit()

    cursor.close()
    db.close()


def save_chat(user_id,role,message):

    db = connect_db()
    cursor = db.cursor()

    query = """
    INSERT INTO chat_history (user_id,role,message)
    VALUES (%s,%s,%s)
    """

    cursor.execute(query,(user_id,role,message))

    db.commit()

    cursor.close()
    db.close()
