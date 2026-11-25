from dataclasses import dataclass

@dataclass
class AllSensorsData:
    time_stamp:int
    ctd_temperature:float
    ctd_pressure:float
    ctd_oxygen:float
    ecov2_chl:int

    def to_json():
        #ask claude to figure out how to output in json
        print('json here')



AllSensorsData.ctd_oxygen = 5.5
AllSensorsData.ecov2_chl = 1

print(AllSensorsData.ecov2_chl)