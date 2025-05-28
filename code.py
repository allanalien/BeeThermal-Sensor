import time
import board
import busio
import adafruit_mlx90640
import wifi
import socketpool

# WiFi credentials
SSID = "Topogigios"
PASSWORD = "damian666"

# TouchDesigner IP and UDP port
TD_IP = "192.168.50.224"
TD_PORT = 8000

# Temperature threshold for presence detection
PRESENCE_THRESHOLD = 28.0  # adjust based on environment

print("Connecting to WiFi...")
wifi.radio.connect(SSID, PASSWORD)
print("Connected to", SSID)

# Setup UDP
pool = socketpool.SocketPool(wifi.radio)
udp = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)

# Setup thermal sensor
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

# Main loop
while True:
    frame = [0] * 768
    try:
        mlx.getFrame(frame)

        max_temp = max(frame)
        avg_temp = sum(frame) / len(frame)

        presence = 1 if max_temp > PRESENCE_THRESHOLD else 0

        message = f"presence:{presence},temp:{max_temp:.2f}"
        udp.sendto(message.encode(), (TD_IP, TD_PORT))

        print(f"Sent → {message}")

    except Exception as e:
        print("Sensor error:", e)

    time.sleep(1)
