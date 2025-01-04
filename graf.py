import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress

# Generování ukázkových dat pro demonstraci
np.random.seed(0)
time_index = pd.date_range(start="2024-10-01", periods=100, freq="H")
iaq_values = 20 + np.random.normal(0, 1, size=len(time_index))  # IAQ kolem 20
temp_values = 22 + np.random.normal(0, 0.5, size=len(time_index))  # Teplota kolem 22°C
humidity_values = 40 + np.random.normal(0, 2, size=len(time_index))  # Vlhkost kolem 40%

# Vytvoření DataFrame
data = pd.DataFrame({
    "Timestamp": time_index, 
    "IAQ": iaq_values, 
    "Temperature": temp_values, 
    "Humidity": humidity_values
})
data.set_index("Timestamp", inplace=True)

# Funkce pro přidání trendové čáry
def add_trend_line(ax, x, y, color):
    slope, intercept, _, _, _ = linregress(range(len(y)), y)
    trend_line = intercept + slope * np.arange(len(y))
    ax.plot(x, trend_line, color=color, linestyle="--", label="Trend Line")

# Vykreslení všech tří grafů s trendovými čarami
fig, axs = plt.subplots(3, 1, figsize=(10, 15), sharex=True)

# Graf IAQ s trendovou čárou
axs[0].plot(data.index, data["IAQ"], label="IAQ", color="green")
add_trend_line(axs[0], data.index, data["IAQ"], "darkgreen")
axs[0].set_ylim(18, 22)
axs[0].set_title("IAQ (Indoor Air Quality) Over Time")
axs[0].set_ylabel("IAQ Value")
axs[0].legend()
axs[0].grid(True)

# Graf teploty s trendovou čárou
axs[1].plot(data.index, data["Temperature"], label="Temperature", color="orange")
add_trend_line(axs[1], data.index, data["Temperature"], "darkorange")
axs[1].set_ylim(21, 23)
axs[1].set_title("Temperature Over Time")
axs[1].set_ylabel("Temperature (°C)")
axs[1].legend()
axs[1].grid(True)

# Graf vlhkosti s trendovou čárou
axs[2].plot(data.index, data["Humidity"], label="Humidity", color="blue")
add_trend_line(axs[2], data.index, data["Humidity"], "darkblue")
axs[2].set_ylim(35, 45)
axs[2].set_title("Humidity Over Time")
axs[2].set_xlabel("Timestamp")
axs[2].set_ylabel("Humidity (%)")
axs[2].legend()
axs[2].grid(True)

# Uložení grafu jako obrázek pro použití na webové stránce
plt.tight_layout()
plt.savefig('/opt/camera_stream/templates/static/iaq_temperature_humidity_graphs.png')
plt.close()  # Zavře graf, aby se uvolnila paměť

