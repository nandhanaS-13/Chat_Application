from flask import Flask,render_template,request,session,redirect,url_for
from flask_socketio import join_room,leave_room,send,SocketIO
import random
from string import ascii_uppercase

app=Flask(__name__)
app.config["SECRET_KEY"]="milanosuga"
socketio=SocketIO(app)

rooms={}

def generate_unique_code(length):
    while True:
        code=""
        for _ in range(length):
            code+= random.choice(ascii_uppercase)

        if code not in rooms:
            break
    return code    








@app.route("/",methods=["POST","GET"])
def home():
    session.clear()
    if request.method=="POST":
        name=request.form.get("name")
        code=request.form.get("code")
        join=request.form.get("join",False)
        create=request.form.get("create",False)

        if not name:
            return render_template("home.html",error="Please enter a name.",code=code,name=name)
        
        if join != False and not code:
            return render_template("home.html",error="Please enter a room code.",code=code,name=name)
        
        room =code
        if create !=False:
            room=generate_unique_code(4)
            rooms[room] = {"members":0,"messages": []}
        elif code not in rooms:
            return render_template("home.html",error="Room does not exist.",code=code,name=name)

        session["room"]=room
        session["name"]=name
        return redirect(url_for("room"))


    return render_template("home.html")

@app.route("/room")
def room():
   #guard clause so u cant go ito the room unless u made the registration. u should create or u should already have a room
   room=session.get("room")
   if room is None or session.get("name") is None or room not in rooms:
       return redirect(url_for("home"))
   return render_template("room.html",code=room,messages=rooms[room]["messages"])

#sending message to server ...server will send to all
@socketio.on("message")
def message(data):#we are going to handel the message and essentially retransmit it to everyone else
    room=session.get("room")
    if room not in rooms:
        return
#generating content to send 
    content={
        "name":session.get("name"),
        "message":data["data"]
    }
    send(content,to=room)
    rooms[room]["message"].append(content)
    print(f"{session.get('name')} said:{data['data']}")














# Flask - Socket connecting
@socketio.on("connect")#socketio is the name we downloaded the libraries
def connect(auth):
    room=session.get("room")
    name=session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
# if we get through this two statements we are going to join roomand pass the room code that the user should join
    join_room(room)
    send({"name":name,"message":"has entered the room"},to=room)#this is how u kind of emit a socket message to all the people  in a specific room........ sending a json message
    rooms[room]["members"]+=1
    print(f"{name} joined room {room}")


#flask- socket disconnect
@socketio.on("disconnect")
def disconnect():
    room=session.get("room")
    name=session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"]-=1
        if rooms[room]["members"]<=0:
            del rooms[room]


    send({"name":name,"message":"has left the room"},to=room)
    print(f"{name} left room {room}")






if __name__=="__main__":
    socketio.run(app,debug=True)