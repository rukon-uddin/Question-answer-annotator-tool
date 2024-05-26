from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import json
import os
from flask_session import Session
import redis

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY', default='BAD_SECRET_KEY')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.from_url('redis://127.0.0.1:6379')
server_session = Session(app)


questions_answers = {}
alreadyLoaded = 0
dfIndexCounter = {}
alldfData = {}
qa_pairs = {}

# data = pd.read_csv("allDf/chunk_1.csv")

@app.route('/', methods=['GET', 'POST'])
def index():
    global alreadyLoaded
    dfFiles = os.listdir("allDf")
    if alreadyLoaded == 0:
        for i in dfFiles:
            dfIndexCounter[i] = 0
            session[i] = 0
            questions_answers[i] = {}
            alldfData[i] = pd.read_csv(f"allDf/{i}")

        for i in os.listdir("savedData"):
            with open(f'savedData/{i}', 'r', encoding='utf-8') as file:
                data = json.load(file)
            questions_answers[i.split(".json")[0]+".csv"] = data
        
    else:
        for i in dfFiles:
            session[i] = 0
            
            # dfIndexCounter[i.split(".json")[0]+".csv"] = len(data)

    alreadyLoaded = 1
    return render_template('index.html', df=dfFiles)


@app.route('/<string:fileName>', methods=['GET', 'POST'])
def chunks(fileName):
    if fileName == "favicon.ico":
        # Return an appropriate response or handle it differently
        return ""
    
    sIndex = session[fileName]
    text = alldfData[fileName]['text'].iloc[sIndex]

    
    if request.method == 'POST':
        
        if text not in questions_answers[fileName]:
            questions_answers[fileName][text] = {}
        for key, values in request.form.lists():
            questions_answers[fileName][text][key] = values

    
    if text not in questions_answers[fileName]:
        return render_template('chunkss.html', name = fileName, text=text, questions_answers=questions_answers[fileName].get(sIndex, {}), currentIdx = sIndex, endIdx = len(alldfData[fileName]))
    else:
        return render_template('chunkss.html', name = fileName, text=text, questions_answers=questions_answers[fileName][text], currentIdx = sIndex, endIdx = len(alldfData[fileName]))


@app.route('/next/<string:fileName>', methods=['POST'])
def next_text(fileName):
    if session[fileName] < len(alldfData[fileName]) - 1:
        session[fileName] += 1
    else:
        session[fileName] = 0


    with open(f'savedData/{fileName.split(".csv")[0]}.json', 'w', encoding='utf-8') as f:
        json.dump(questions_answers[fileName], f, ensure_ascii=False)
    
    
    return jsonify({"success": True})


@app.route('/prev/<string:fileName>', methods=['POST'])
def prev_text(fileName):
    if session[fileName] > 0:
        session[fileName] -= 1
    else:
         session[fileName] = 0

    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, host="192.168.10.92", port=5035)