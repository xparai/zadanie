from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect

import MySQLdb   
import time
import random
import math
import serial
import configparser as ConfigParser

ser=serial.Serial("/dev/ttyACM0",9600)
ser.baudrate=9600

async_mode = None

app = Flask(__name__)

config = ConfigParser.ConfigParser()
config.read('config.cfg')
myhost = config.get('mysqlDB', 'host')
myuser = config.get('mysqlDB', 'user')
mypasswd = config.get('mysqlDB', 'passwd')
mydb = config.get('mysqlDB', 'db')
print (myhost)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 


def background_thread(args):
    count = 0
    dataCounter = 0 
    dataList = []
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)     
    while True:
        if args:
          A = dict(args).get('A')
          btnV = dict(args).get('btn_value')
          sliderV = dict(args).get('slider_value')
          dbV = dict(args).get('db_value')
          
        else:
          A = 1
          dbV = 'nieco'
          btnV = 'null'
          sliderV = 0
          
          
        
        #print A
        read_ser=ser.readline()
        read_ser=str(read_ser)
        hodnoty=read_ser.split(',')
        teplota=hodnoty[0]
        osvetlenie=hodnoty[1]
        teplota=teplota[2:]
        osvetlenie=osvetlenie[:3]
        
        print(float(osvetlenie))
        print(args)
        socketio.sleep(1)
        count += 1
        dataCounter +=1
        prem = random.random()
        
        if dbV == 'start':
          dataDict = {
            "t": time.time(),
            "x": dataCounter,
            "y": osvetlenie,
            "y2": teplota}
          dataList.append(dataDict)
        else:
          if len(dataList)>0:
            print (str(dataList))
            fuj = str(dataList).replace("'", "\"")
            print (fuj)
            cursor = db.cursor()
            cursor.execute("SELECT MAX(id) FROM zaverecne")
            maxid = cursor.fetchone()
            cursor.execute("INSERT INTO zaverecne (id, hodnoty) VALUES (%s, %s)", (maxid[0] + 1, fuj))
            db.commit()
          dataList = []
          dataCounter = 0
        
        #if len(dataList)>0:
        #  print str(dataList)
        #  print str(dataList).replace("'", "\"")
        
        socketio.emit('my_response',
                      {'data': float(teplota),'osvetlenie': float(osvetlenie) ,'count': count},
                      namespace='/test')
    db.close()

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)
       
@app.route('/graphlive', methods=['GET', 'POST'])
def graphlive():
    return render_template('graphlive.html', async_mode=socketio.async_mode)
      
@socketio.on('my_event', namespace='/test')
def test_message(message):   
#    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['A'] = message['value']
    
    session['db_value']='nieco1'
    session['display']='nieco1'
    
    
    
    print("connected")
    
#    emit('my_response',
#         {'data': message['value'], 'count': session['receive_count']})
 
@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
#    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('display', namespace='/test')
def db_message3(message):   
#    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['display'] = message['value']
    print(session['display'])

    
    
#Zobrazenie
@socketio.on('db_event', namespace='/test')
def db_message2(message):   
#    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['db_value'] = message['value']
    print(session['db_value'])


@socketio.on('click_event', namespace='/test')
def db_message(message):
    session['A'] = message['value']
    num = str(message['value'])
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
    cursor = db.cursor()
    print (num)
    cursor.execute("SELECT hodnoty FROM zaverecne WHERE id=%s", [num])
    rv = cursor.fetchone()
    
    

    fo = open("static/files/test.txt","a+")    
    val = str(rv[0])
    fo.write("%s\r\n" %val)
    db.close()
    print("done")
    
    

@socketio.on('slider_event', namespace='/test')
def slider_message(message):  
    #print message['value']   
    session['slider_value'] = message['value']  

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)