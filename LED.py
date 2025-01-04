from gpiozero import LED
from time import sleep

led1 = LED(18)

for _ in range(2):  # Cyklus se opakuje 10x
    led1.on()
    sleep(0.8)
    led1.off()
    sleep(0.8)
    led1.on()
    sleep(0.8)
    led1.off()
    sleep(0.8)
exit(0)

