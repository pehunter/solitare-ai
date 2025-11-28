import http.server as sv
import json
from player import Instance
from flask import Flask, request

def init_app():
    global inst
    app = Flask(__name__)
    inst = Instance()

    @app.get("/get/state")
    def get_gs():
        return inst.gameJson()

    @app.get("/get/ai_move")
    def get_ai_move():
        return inst.ai_nextMove()

    @app.get("/get/ai_acc")
    def get_ai_acc():
        return inst.ai_acc()

    @app.post("/move")
    def move():
        if not request.is_json:
            return {"error": "The given data is not in JSON format."}
        return inst.turn(request.get_json())

    @app.post("/start")
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

    return app