
from flask import Flask
from .controllers import bp

app = Flask(__name__)
app.config["SECRET_KEY"] = "ipc2_proyecto2_201503980"
app.register_blueprint(bp)
