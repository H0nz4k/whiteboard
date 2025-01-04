import csv
import time
import bme680

sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)

sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

def log_data_to_csv():
    with open('/opt/camera_stream/bme680_data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        # Check if file is empty before writing header
        if file.tell() == 0:
            writer.writerow(['Time', 'Temperature', 'Pressure', 'Humidity', 'IAQ'])
        while True:
            if sensor.get_sensor_data():
                temperature = sensor.data.temperature
                pressure = sensor.data.pressure
                humidity = sensor.data.humidity
                gas_resistance = sensor.data.gas_resistance
                iaq = calculate_iaq(gas_resistance, humidity)

                current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([current_time, temperature, pressure, humidity, iaq])
                file.flush()
                print(f"Logged at {current_time}")
                time.sleep(1800)


def calculate_iaq(gas_resistance, humidity):
    humidity_baseline = 40.0
    humidity_weighting = 0.25
    gas_offset = gas_resistance - 10000
    humidity_offset = humidity - humidity_baseline

    if humidity_offset > 0:
        humidity_score = (100 - humidity_baseline - humidity_offset) / (100 - humidity_baseline) * (humidity_weighting * 100)
    else:
        humidity_score = (humidity_baseline + humidity_offset) / humidity_baseline * (humidity_weighting * 100)

    if gas_offset > 0:
        gas_score = (gas_resistance / 1000) * (100 - (humidity_weighting * 100))
    else:
        gas_score = 0

    iaq = humidity_score + gas_score
    return iaq

log_data_to_csv()

