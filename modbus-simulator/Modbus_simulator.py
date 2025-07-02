#!/usr/bin/env python3
import threading
import time
import random
import sys
import PySimpleGUI as sg
from pymodbus.datastore import ModbusSlaveContext, ModbusSequentialDataBlock, ModbusServerContext

# Try sync import first, else fallback
try:
    from pymodbus.server.sync import StartTcpServer
except ImportError:
    from pymodbus.server import StartTcpServer

# === Configuration ===
NUM_MOTORS      = 5
MOTOR_FIELDS    = ['Cmd','Status','Trip','Sp','ActSp','Load','Temp','Fault','RunTime','Reserved','HOA','Amps']
NUM_BREAKERS    = 5
BREAKER_FIELDS  = ['Status','TripCnt','Voltage','Current']
SW_UNIT         = 16      # slave ID (hex 0x10 = dec 16)
UPDATE_INTERVAL = 1.0       # seconds

# === Build Modbus context ===
slaves = {}
for mid in range(1, NUM_MOTORS+1):
    slaves[mid] = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, [0]*len(MOTOR_FIELDS))
    )
slaves[SW_UNIT] = ModbusSlaveContext(
    hr=ModbusSequentialDataBlock(0, [0]*(NUM_BREAKERS*len(BREAKER_FIELDS)))
)
ctx = ModbusServerContext(slaves=slaves, single=False)

# === Helpers ===
def safe_int(v, default=None):
    try:
        return int(v)
    except:
        return default

def human_motor(field, raw):
    if   field=='Status':  return 'Running' if raw else 'Stopped'
    if   field=='Trip':    return 'Tripped' if raw else 'OK'
    if   field=='Load':    return f'{raw}%'
    if   field=='Temp':    return f'{raw}°C'
    if   field=='Fault':   return f'Code {raw}' if raw else 'None'
    if   field=='RunTime': return f'{raw}s'
    if   field=='HOA':     return {0:'Off',1:'Hand',2:'Auto'}.get(raw,str(raw))
    if   field=='Amps':    return f'{raw}A'
    return str(raw)

def human_sg(field, raw):
    if   field=='Status':  return 'On' if raw else 'Off'
    if   field=='TripCnt': return str(raw)
    if   field=='Voltage': return f'{raw}V'
    if   field=='Current': return f'{raw}A'
    return str(raw)

# === Simulation threads ===
def update_motors():
    while True:
        for mid in range(1, NUM_MOTORS+1):
            slave = ctx[mid]
            cmd, sp, hoa = (
                slave.getValues(3, off, count=1)[0]
                for off in (0, 3, 10)
            )
            if hoa == 1:
                cmd = 1
            elif hoa == 2:
                cmd = random.choice([0,1])
            v      = mid
            status = 1 if cmd else 0
            trip   = (random.choices([0,1], weights=[90-v,10+v])[0] if status else 0)
            runtime_old = slave.getValues(3, 8, count=1)[0]
            vals = [
                cmd,
                status,
                trip,
                sp,
                sp if (status and not trip) else 0,
                (random.randint(30,90)+v) if status else 0,
                (random.randint(40,90)+v) if status else 25,
                (random.randint(1,10)*v) if trip else 0,
                runtime_old + (1 if (status and not trip) else 0),
                0,
                hoa,
                (random.randint(5,20)+v) if status else 0
            ]
            slave.setValues(3, 0, vals)
        time.sleep(UPDATE_INTERVAL)

def update_switchgear():
    while True:
        sg_slave = ctx[SW_UNIT]
        for b in range(NUM_BREAKERS):
            base = b * len(BREAKER_FIELDS)
            # keep manual status toggle
            status = sg_slave.getValues(3, base, count=1)[0]
            vals = [
                status,
                random.randint(0,5),
                random.randint(220,240),
                random.randint(0,100),
            ]
            sg_slave.setValues(3, base, vals)
        time.sleep(UPDATE_INTERVAL)

# === Server starter ===
def start_server(ip, port):
    try:
        StartTcpServer(ctx, address=(ip, int(port)))
    except Exception as e:
        sg.popup_error(f"Server error: {e}")

# === GUI ===
def gui():
    sg.theme('DarkBlue3')

    # Build live-data rows once
    data_rows = []
    for m in range(1, NUM_MOTORS+1):
        for i, fld in enumerate(MOTOR_FIELDS):
            data_rows.append([
                sg.Text(f"Motor {m} {fld}", size=(18,1)),
                sg.Text("", key=f"-MRAW{m}{i}-", size=(8,1)),
                sg.Text("", key=f"-MHUM{m}{i}-", size=(12,1)),
            ])
    for b in range(1, NUM_BREAKERS+1):
        for i, fld in enumerate(BREAKER_FIELDS):
            data_rows.append([
                sg.Text(f"Breaker {b} {fld}", size=(18,1)),
                sg.Text("", key=f"-SRAW{b}{i}-", size=(8,1)),
                sg.Text("", key=f"-SHUM{b}{i}-", size=(12,1)),
            ])

    layout = [
        [sg.Text("Modbus TCP Simulator", font=('Helvetica',14,'bold'))],
        [sg.Text("IP:"), sg.InputText("127.0.0.1", key="-IP-", size=(14,1)),
         sg.Text("Port:"), sg.InputText("5020", key="-PORT-", size=(6,1)),
         sg.Button("Start Server")],
        [sg.HorizontalSeparator()],
        [sg.Text("Motor Commands", font=('Helvetica',12,'bold'))],
        [sg.Text("ID (1-5):"), sg.InputText("1", key="-MID-", size=(4,1)),
         sg.Text("Cmd:"), sg.InputText("", key="-MCMD-", size=(4,1)),
         sg.Text("Sp:"),  sg.InputText("", key="-MSP-",  size=(4,1)),
         sg.Text("HOA:"), sg.InputText("", key="-MHOA-", size=(4,1)),
         sg.Button("Send Motor Cmd")],
        [sg.HorizontalSeparator()],
        [sg.Text("Breaker Commands", font=('Helvetica',12,'bold'))],
        [sg.Text("ID (1-5):"), sg.InputText("1", key="-BID-", size=(4,1)),
         sg.Text("Status (0/1):"), sg.InputText("", key="-BSTAT-", size=(4,1)),
         sg.Button("Set Breaker")],
        [sg.HorizontalSeparator()],
        [sg.Text("Live Data", font=('Helvetica',12,'bold'))],
        [sg.Column(data_rows, scrollable=True, size=(700,400))]
    ]

    window = sg.Window("Modbus Simulator", layout, finalize=True)

    while True:
        evt, vals = window.read(timeout=int(UPDATE_INTERVAL*1000))
        if evt == sg.WIN_CLOSED:
            break

        if evt == "Start Server":
            threading.Thread(target=start_server,
                             args=(vals["-IP-"], vals["-PORT-"]),
                             daemon=True).start()
            sg.popup(f"Server started at {vals['-IP-']}:{vals['-PORT-']}")

        elif evt == "Send Motor Cmd":
            uid = safe_int(vals["-MID-"])
            if not uid or uid < 1 or uid > NUM_MOTORS:
                sg.popup_error(f"Motor ID must be 1–{NUM_MOTORS}")
            else:
                slave = ctx[uid]
                for field_key, offset in (("-MCMD-",0), ("-MSP-",3), ("-MHOA-",10)):
                    v = safe_int(vals[field_key])
                    if v is not None:
                        slave.setValues(3, offset, [v])

        elif evt == "Set Breaker":
            bid = safe_int(vals["-BID-"])
            st  = safe_int(vals["-BSTAT-"])
            if not bid or bid < 1 or bid > NUM_BREAKERS or st not in (0,1):
                sg.popup_error(f"Breaker ID must be 1–{NUM_BREAKERS}, status 0 or 1")
            else:
                base = (bid-1)*len(BREAKER_FIELDS)
                ctx[SW_UNIT].setValues(3, base, [st])

        # Refresh live data
        for m in range(1, NUM_MOTORS+1):
            for i, fld in enumerate(MOTOR_FIELDS):
                raw = ctx[m].getValues(3, i, count=1)[0]
                window[f"-MRAW{m}{i}-"].update(raw)
                window[f"-MHUM{m}{i}-"].update(human_motor(fld, raw))
        for b in range(1, NUM_BREAKERS+1):
            for i, fld in enumerate(BREAKER_FIELDS):
                addr = (b-1)*len(BREAKER_FIELDS) + i
                raw = ctx[SW_UNIT].getValues(3, addr, count=1)[0]
                window[f"-SRAW{b}{i}-"].update(raw)
                window[f"-SHUM{b}{i}-"].update(human_sg(fld, raw))

    window.close()

if __name__ == "__main__":
    # start sim threads
    threading.Thread(target=update_motors,    daemon=True).start()
    threading.Thread(target=update_switchgear, daemon=True).start()
    # auto-start server on default
    threading.Thread(target=start_server, args=("0.0.0.0","5020"), daemon=True).start()
    gui()
