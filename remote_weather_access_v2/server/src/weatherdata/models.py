from ..extensions import db


class BaseStationData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timepoint = db.Column(db.DateTime, unique=True, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)

    def __init__(self, temperature, humidity, timepoint=None):
        self.timepoint = timepoint
        self.temperature = temperature
        self.humidity = humidity


class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timepoint = db.Column(db.DateTime, unique=True, nullable=False)
    pressure = db.Column(db.Float, nullable=False)
    uv = db.Column(db.Float, nullable=False)

    def __init__(self, pressure, uv, timepoint=None):
        self.timepoint = timepoint
        self.pressure = pressure
        self.uv = uv


class RainSensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    begin_time = db.Column(db.DateTime, unique=True, nullable=False)
    end_time = db.Column(db.DateTime, unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)

    def __init__(self, begin_time, end_time, amount):
        self.begin_time = begin_time
        self.end_time = end_time
        self.amount = amount


class WindSensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timepoint = db.Column(db.DateTime, unique=True, nullable=False)
    direction = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    gusts = db.Column(db.Float, nullable=False)

    def __init__(self, direction, speed, temperature, gusts, timepoint=None):
        self.timepoint = timepoint
        self.direction = direction
        self.speed = speed
        self.temperature = temperature
        self.gusts = gusts


class WeatherStation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    rain_calib_factor = db.Column(db.Float, nullable=False)

    def __init__(self, device, location, latitude, longitude, height, rain_calib_factor):
        self.device = device
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.height = height
        self.rain_calib_factor = rain_calib_factor


class CombiSensor(db.Model):
    sensor_id = db.Column(db.String, primary_key=True)
    description = db.Column(db.String, nullable=False)

    def __init__(self, sensor_id, description):
        self.sensor_id = sensor_id
        self.description = description


class RainDataMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rain_counter = db.Column(db.Float, nullable=False)

    def __init__(self, rain_counter):
        self.rain_counter = rain_counter
