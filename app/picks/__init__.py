from flask import Blueprint

bp = Blueprint('picks', __name__)

from app.picks import routes
