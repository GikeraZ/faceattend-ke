"""Attendance blueprint"""
from flask import Blueprint

attendance_bp = Blueprint('attendance', __name__)

from . import routes  # noqa: F401