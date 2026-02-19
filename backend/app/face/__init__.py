"""Face recognition blueprint"""
from flask import Blueprint

face_bp = Blueprint('face', __name__)

from . import routes  # noqa: F401