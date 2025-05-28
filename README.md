# BeThermal

Temperature Presence Sensor with CircuitPython + TouchDesigner (Serial Communication)

This project uses a CircuitPython Feather board with an Adafruit MLX90640 thermal camera connected via STEMMA. It detects human presence based on temperature readings and sends data over **USB serial** to TouchDesigner for interactive control.

---

## Features

- Reads temperature data from the MLX90640 thermal camera via STEMMA/I2C
- Determines presence based on temperature threshold
- Sends serial messages with presence (0 or 1) and average temperature
- TouchDesigner project reads serial data, parses it, and uses it to control visuals or logic

---

## Hardware Requirements

- CircuitPython Feather board with USB serial support
- Adafruit MLX90640 thermal camera connected via STEMMA/I2C
- USB cable for serial communication with computer

---

## Software Components

### CircuitPython Code (`code.py`)

- Reads MLX90640 temperature data continuously
- Calculates average temperature
- Sends serial data in format:  
  `Sent → presence:<0 or 1>,temp:<temperature>`

### TouchDesigner Project (`presence_temp.toe`)

- Serial DAT to receive data from the USB serial port
- DAT Execute to parse presence and temperature values
- Separate DAT tables for `presence` and `temperature`
- DAT to CHOP conversion for use in networks
- Example temperature-driven LFO for dynamic modulation

---

## Setup Instructions

1. Connect the MLX90640 thermal camera to the Feather board via STEMMA/I2C.
2. Connect the Feather board to your computer via USB.
3. Upload and run `code.py` on the Feather board.
4. Open `presence_temp.toe` in TouchDesigner.
5. Configure the Serial DAT in TouchDesigner to read from the Feather’s serial port.
6. Observe presence and temperature data updating live.
7. Use the data channels to drive your visuals or logic.

---

## Notes

- Presence is detected by checking if the average temperature exceeds a set threshold.
- Adjust threshold in `code.py` to tune presence sensitivity.
- Ensure correct serial port is selected in TouchDesigner.
- This project assumes only the MLX90640 sensor; no additional PIR or other sensors used.

---

## License

MIT License — free to use and modify.

---

## Contact

For questions or contributions, open an issue or PR on GitHub.
