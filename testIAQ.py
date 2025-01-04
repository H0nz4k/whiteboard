import bme680
import time

# Inicializace senzoru
sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)

# Nastavení oversamplingu
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

# Nastavení heater profilu
sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

# Funkce pro výpočet IAQ
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

print('Sledování IAQ...')
while True:
    if sensor.get_sensor_data():
        temperature = sensor.data.temperature
        pressure = sensor.data.pressure
        humidity = sensor.data.humidity
        gas_resistance = sensor.data.gas_resistance

        iaq = calculate_iaq(gas_resistance, humidity)

        print(f"Temperature: {temperature:.2f} °C")
        print(f"Pressure: {pressure:.2f} hPa")
        print(f"Humidity: {humidity:.2f} %")
        print(f"Gas resistance: {gas_resistance} ohms")
        print(f"IAQ (estimated): {iaq:.2f}")
        
        time.sleep(1)

