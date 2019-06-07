from ..extensions import db


class BaseStationData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timepoint = db.Column(db.DateTime, unique=True, nullable=False)
    temp = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)

    def __init__(self, timepoint, temp, humidity):
        self.timepoint = timepoint
        self.temp = temp
        self.humidity = humidity
