from weathernetwork.common.combisensordataset import CombiSensorDataset

class CombiSensorArray(object):
    """description of class"""
    
    # definition of the database sensor IDs
    ID_IN = "IN"
    ID_OUT_1 = "OUT1"
    ID_OUT_2 = "OUT2"
    ID_OUT_3 = "OUT3"
    ID_OUT_4 = "OUT4"
    ID_OUT_5 = "OUT5"

    DESCRIPTION_IN = "Indoor sensor"
    DESCRIPTION_OUT_1 = "Outdoor sensor 1"
    DESCRIPTION_OUT_2 = "Outdoor sensor 2"
    DESCRIPTION_OUT_3 = "Outdoor sensor 3"
    DESCRIPTION_OUT_4 = "Outdoor sensor 4"
    DESCRIPTION_OUT_5 = "Outdoor sensor 5"


    def __init__(self, sensor_in, sensor_out_1, sensor_out_2, sensor_out_3, sensor_out_4, sensor_out_5):
        self._in = sensor_in
        self._out1 = sensor_out_1
        self._out2 = sensor_out_2
        self._out3 = sensor_out_3
        self._out4 = sensor_out_4
        self._out5 = sensor_out_5


    @staticmethod
    def get_sensors():
        return { CombiSensorArray.ID_IN : CombiSensorArray.DESCRIPTION_IN, \
                 CombiSensorArray.ID_OUT_1 : CombiSensorArray.DESCRIPTION_OUT_1, \
                 CombiSensorArray.ID_OUT_2 : CombiSensorArray.DESCRIPTION_OUT_2, \
                 CombiSensorArray.ID_OUT_3 : CombiSensorArray.DESCRIPTION_OUT_3, \
                 CombiSensorArray.ID_OUT_4 : CombiSensorArray.DESCRIPTION_OUT_4, \
                 CombiSensorArray.ID_OUT_5 : CombiSensorArray.DESCRIPTION_OUT_5,}


    def get_vals(self):
        return [ 
            CombiSensorDataset( CombiSensorArray.ID_IN, self._in.get_temperature(), self._in.get_humidity() ),
            CombiSensorDataset( CombiSensorArray.ID_OUT_1, self._out1.get_temperature(), self._out1.get_humidity() ),
            CombiSensorDataset( CombiSensorArray.ID_OUT_2, self._out2.get_temperature(), self._out2.get_humidity() ),
            CombiSensorDataset( CombiSensorArray.ID_OUT_3, self._out3.get_temperature(), self._out3.get_humidity() ),
            CombiSensorDataset( CombiSensorArray.ID_OUT_4, self._out4.get_temperature(), self._out4.get_humidity() ),
            CombiSensorDataset( CombiSensorArray.ID_OUT_5, self._out5.get_temperature(), self._out5.get_humidity() ),
            ]
