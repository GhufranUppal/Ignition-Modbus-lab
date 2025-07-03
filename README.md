# Ignition-Modbus-lab

An educational Python-based Modbus TCP simulator designed for hobbyists, automation enthusiasts, and SCADA learners aiming to explore Ignition's Modbus integration capabilities. This interactive project provides a hands-on environment to test and understand how Modbus registers map into Ignition SCADA systems.

The simulator, built using `PySimpleGUI` and `pymodbus`, includes dynamic data generation for motors and switchgear breakers, allowing learners to simulate realistic device behaviors, send commands, and visualize updates in real-time.

---

## Modbus Simulator

This Python-based Modbus TCP simulator is designed to emulate motor control and switchgear devices for testing SCADA systems like Ignition. It uses `pymodbus` and `PySimpleGUI` to provide a live, interactive interface where users can view and command Modbus data in real time.

### Features:
- Start a Modbus TCP server at any IP/port (default: `127.0.0.1:5020`)
- Command motors using `Cmd`, `Setpoint (Sp)`, and `HOA` inputs
- Toggle breaker status (On/Off)
- Live data updates for:
  - Motor status, trip, speed, load, temperature, amps, runtime
  - Breaker trip count, voltage, current

### How it works:
Once you start the simulator, the GUI allows you to:
1. Launch the Modbus server.
2. Send motor commands and observe changes in real-time data.
3. Set breaker states (1 or 0).
4. Monitor all values updated periodically in the interface.

### Screenshots

<p align="center">
  <img src="modbus-simulator/screenshots/Screenshot-Modbus-Simulator.png" width="300"/>
  <img src="modbus-simulator/screenshots/Screenshot-Modbus-Simulator-1.png" width="300"/>
  <img src="modbus-simulator/screenshots/Screenshot-Modbus-Simulator-2.png" width="300"/>
</p>

These screenshots demonstrate the simulator in action:

- The TCP Modbus server is successfully launched and listening on the specified IP and port.
- After issuing a motor **command** (Cmd = 1, HOA = 1 or 2), the motor transitions to **Running**.
- Live updates are visible for:
  - Motor parameters like speed setpoint (Sp), actual speed (ActSp), load, temperature, and runtime.
  - Breaker electrical readings like **Status**, **Trip Count**, **Voltage**, and **Current**.
- GUI refreshes at 1-second intervals, simulating realistic Modbus traffic.

🔗 [View Simulator Source Code](modbus-simulator/Modbus_simulator.py)

## 🔌 Ignition Integration

The Modbus Simulator is designed for seamless integration with the Ignition SCADA platform. Once the simulator is running, Ignition can connect using the Modbus TCP driver and map the motor and breaker registers to OPC tags.

### Live Integration Examples

<p align="center">
  <img src="Ignition-project/screenshots/Screenshot 2025-07-02 162417-Ignition-OPC-Breaker.png" width="300"/>
  <img src="Ignition-project/screenshots/Screenshot 2025-07-02 162417-Ignition-OPC-Breaker-1.png" width="300"/>
  <img src="Ignition-project/screenshots/Screenshot 2025-07-02 162417-Ignition-OPC-Motor.png" width="300"/>
  <img src="Ignition-project/screenshots/Screenshot 2025-07-02 162417-Ignition-OPC-Motor-1.png" width="300"/>
</p>

These screenshots show:
- How Ignition maps simulated Modbus registers from motors and breakers into OPC tags.
- Real-time tag values from Modbus devices.
- Integration through OPC Quick Client for rapid testing and validation.

You can import tag maps directly using the provided CSVs in the `modbus-maps` directory for motors and switchgear.

> 📂 [modbus-maps/Ignition-import-motors.csv](modbus-maps/Ignition-import-motors.csv)  
> 📂 [modbus-maps/Ignition_Import_Swichgear_Breaker.csv](modbus-maps/Ignition_Import_Swichgear_Breaker.csv)
