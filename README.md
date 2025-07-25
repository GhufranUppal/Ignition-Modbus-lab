# Ignition-Modbus-lab

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)

## Overview

This Python-based Modbus TCP simulator is designed for automation professionals, control engineers, and SCADA practitioners seeking to explore and validate Ignition’s Modbus integration. It provides a practical, hands-on environment to test how Modbus registers interface with Ignition SCADA systems.

Developed using `pymodbus` and `PySimpleGUI`, the simulator features dynamic data generation for motors and switchgear breakers—allowing users to emulate real-world device behavior, issue control commands, and visualize system responses in real time through an intuitive graphical interface.

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

### 🧪 Modbus Simulator Interface

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

This section showcases how the Modbus simulator integrates with Ignition using OPC UA.

### 🔧 Motor & Breaker Tags in Ignition

The simulator publishes motor and breaker data which is imported into Ignition using Modbus mapping. These tags are displayed in the OPC browser and update in real-time.

### 📸 Screenshots

<p align="center">
  <img src="Ignition-Project/screenshots/ignition-opc-motor-tags.png" width="300"/>
  <img src="Ignition-Project/screenshots/ignition-opc-motor-live-values.png" width="300"/>
  <img src="Ignition-Project/screenshots/ignition-opc-breaker-overview.png" width="300"/>
</p>

These screenshots show:

- OPC tag browser view with mapped Modbus addresses.
- Real-time values for motor commands, status, and process variables.
- Breaker electrical data including voltage, current, and trip count.

## 📂 Modbus Maps and Ignition Import

You can explore or download the Modbus register maps and corresponding Ignition import files directly from this repository:

- 🗂️ **Modbus Mapping CSVs** (used to configure the simulator):
  - [`Modbus_Motor_Map.csv`](modbus-maps/Modbus_Motor_Map.csv)
  - [`Modbus_Switchgear_Map.csv`](modbus-maps/Modbus_Switchgear_Map.csv)

- 📥 **Ignition Import-Ready CSVs**  
  (used to import tags through the **Ignition Gateway**):
  - [`Ignition-import-motors.csv`](modbus-maps/Ignition-import-motors.csv)
  - [`Ignition_Import_Switchgear_Breaker.csv`](modbus-maps/Ignition_Import_Switchgear_Breaker.csv)

> 📝 **Note:**  
> The Modbus map for the switchgear uses a **hexadecimal addressing scheme**, which is common in industrial PLC documentation.  
> However, **Ignition requires addresses in decimal format**, so make sure to convert all hexadecimal values to decimal before using them in Ignition.

## 🛠️ Ignition Designer Configuration

The Ignition Designer is used to visualize and configure the imported Modbus tags for both motors and switchgear devices.

These screenshots illustrate how the simulator data is brought to life within the Ignition Designer:

<p align="center">
  <img src="Ignition-Project/screenshots/Simulator_Designer.png" width="300"/>
  <img src="Ignition-Project/screenshots/Simulator_Designer_Switchgear.png" width="300"/>
  <img src="Ignition-Project/screenshots/UDT_Defination.png" width="300"/>
</p>

### Key Highlights:

- **Tag Hierarchy**: Motors and breakers are organized into folders for structured access.
- **Live Data Visualization**: Real-time values from the simulator are bound to components like labels and indicators.
- **UDT Implementation**: Motors and breakers are created as User Defined Types (UDTs) to standardize tag structures and simplify scaling.

These design elements help test Modbus tag behavior in a visual, scalable way inside Ignition.


## 🖥️ Motor Control UI with Ignition and Modbus TCP Simulator

This section shows how the Ignition Vision client is integrated with a custom Modbus TCP simulator to visualize and control motor status in real time.

### 🔴 Motor1 Stopped with Command Inputs

![Motor1 Stopped](./Ignition-Project/screenshots/Motors_Designer.png)

---

### 🔁 Mixed Motor States (Running, Stopped)

![Mixed Motor States](./Ignition-Project/screenshots/Motors_Designer_2.png)

---

### 🟢 All Motors Running

![All Motors Running](./Ignition-Project/screenshots/Motors_Designer_1.png)

---

### 🔧 Description

- Each motor component reflects live Modbus tag values: Amps, Status, Trip, Fault, HOA, and more.
- A custom Modbus TCP simulator written in Python is used to send commands and simulate states.
- Ignition Vision provides live feedback and dynamic color changes to show current motor conditions.
- This setup demonstrates full-loop control simulation using Ignition and Modbus TCP.

---
