import http.server as sv
import json
from player import Instance
from flask import Flask, request
from flask_cors import CORS
from ai import trainModel
import colorama
import threading

def init_app():
    global inst
    app = Flask(__name__)
    CORS(app)
    inst = Instance()
    ai_threads: list[threading.Thread] = []

    @app.get("/get/state")
    def get_gs():
        return inst.gameJson()

    @app.get("/get/ai_move")
    def get_ai_move():
        return inst.ai_nextMove()

    @app.get("/get/ai_acc")
    def get_ai_acc():
        return inst.ai_acc()
    
    # Check if all AI models have finished training. If finished, return true and clear the object.
    def checkTrainingDone():
        for t in ai_threads:
            if t.is_alive():
                return False
        ai_threads.clear()
        return True
    
    @app.get("/get/ai_training")
    def get_ai_training():
        if(checkTrainingDone()):
            return {"msg": "Ready"}
        else:
            return {"msg": "In Progress"}

    #Train model and add it to list of threads
    def launchTrainer(model: str, out: str):
        t = threading.Thread(target=trainModel, args=(model, out))
        ai_threads.append(t)
        t.start()

    @app.post("/act/train")
    def train():
        if checkTrainingDone():
            launchTrainer("cmd", "Cmd")
            launchTrainer("tt", "Card")
            launchTrainer("ft", "Card")
            launchTrainer("pt", "Card")
            launchTrainer("tc", "Card")
            return {"msg": "AI retraining started."}
        else:
            return {"error": "An AI is currently being trained, please wait before training a new one."}
        
    @app.post("/act/move")
    def move():
        if not request.is_json:
            return {"error": "The given data is not in JSON format."}
        return inst.turn(request.get_json())

    @app.post("/act/start")
    def start():
        restart = False
        if request.is_json and "close" in request.get_json() and request.get_json()["close"] == True:
            restart = True
        
        if inst.running and not restart:
            return {"error": "A game instance is already running."}
        elif inst.running:
            inst.close()
        inst.createNewInstance()
        
        return {"msg": "Successfully started a new game instance."}

    print(colorama.Fore.YELLOW + "Solitare server was started..." + colorama.Fore.RESET)
    return app