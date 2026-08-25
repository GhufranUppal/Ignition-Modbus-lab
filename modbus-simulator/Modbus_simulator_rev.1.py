#!/usr/bin/env python3
import threading
import time
import random
import tkinter as tk
from tkinter import ttk, messagebox

from pymodbus.datastore import ModbusSequentialDataBlock

# Device context class (pymodbus 2.x vs 3.x+)
try:
    from pymodbus.datastore import ModbusSlaveContext as DeviceContext
except Exception:
    from pymodbus.datastore.context import ModbusDeviceContext as DeviceContext

# Server context class (pymodbus 2.x vs 3.x+)
try:
    from pymodbus.datastore import ModbusServerContext
except Exception:
    from pymodbus.datastore.context import ModbusServerContext

# Server starter (pymodbus 2.x vs 3.x+)
try:
    from pymodbus.server.sync import StartTcpServer
except Exception:
    from pymodbus.server import StartTcpServer


# pymodbus device contexts internally offset every request by +1, which shifts
# the register map by one relative to our 0-based data blocks (and makes a block
# of exactly N registers reject a read of N values). This subclass removes that
# offset so Modbus addresses map directly onto the block indices we read/write.
class ZeroBasedDeviceContext(DeviceContext):
    def getValues(self, func_code, address, count=1):
        return self.store[self.decode(func_code)].getValues(address, count)

    def setValues(self, func_code, address, values):
        return self.store[self.decode(func_code)].setValues(address, values)


# =====================
# === Configuration ===
# =====================
NUM_MOTORS      = 5
MOTOR_FIELDS    = ['Cmd','Status','Trip','Sp','ActSp','Load','Temp','Fault','RunTime','Reserved','HOA','Amps']

NUM_BREAKERS    = 5
BREAKER_FIELDS  = ['Status','TripCnt','Voltage','Current']

SW_UNIT         = 16
UPDATE_INTERVAL = 1.0  # seconds


# ==========================================================
# === Build datablocks FIRST (we will read/write these only)
# ==========================================================
motor_hr_blocks = {}
for mid in range(1, NUM_MOTORS + 1):
    motor_hr_blocks[mid] = ModbusSequentialDataBlock(0, [0] * len(MOTOR_FIELDS))

sw_hr_block = ModbusSequentialDataBlock(0, [0] * (NUM_BREAKERS * len(BREAKER_FIELDS)))


# ==========================================
# === Build Modbus server context from blocks
# ==========================================
devices = {}
for mid in range(1, NUM_MOTORS + 1):
    devices[mid] = ZeroBasedDeviceContext(hr=motor_hr_blocks[mid])

devices[SW_UNIT] = ZeroBasedDeviceContext(hr=sw_hr_block)

# pymodbus 2.x vs 3.x ctor differences
try:
    ctx = ModbusServerContext(slaves=devices, single=False)   # 2.x
except TypeError:
    ctx = ModbusServerContext(devices=devices, single=False)  # 3.x+


# =================
# === Helpers ===
# =================
def safe_int(v, default=None):
    try:
        v = str(v).strip()
        if v == "":
            return default
        return int(v)
    except Exception:
        return default

def human_motor(field, raw):
    if field == 'Status':  return 'Running' if raw else 'Stopped'
    if field == 'Trip':    return 'Tripped' if raw else 'OK'
    if field == 'Load':    return f'{raw}%'
    if field == 'Temp':    return f'{raw}°C'
    if field == 'Fault':   return f'Code {raw}' if raw else 'None'
    if field == 'RunTime': return f'{raw}s'
    if field == 'HOA':     return {0:'Off',1:'Hand',2:'Auto'}.get(raw, str(raw))
    if field == 'Amps':    return f'{raw}A'
    return str(raw)

def human_sg(field, raw):
    if field == 'Status':  return 'On' if raw else 'Off'
    if field == 'TripCnt': return str(raw)
    if field == 'Voltage': return f'{raw}V'
    if field == 'Current': return f'{raw}A'
    return str(raw)


# ==================================
# === Simulation threads (BLOCKS) ===
# ==================================
def update_motors():
    while True:
        for mid in range(1, NUM_MOTORS + 1):
            blk = motor_hr_blocks[mid]

            cmd = blk.getValues(0, 1)[0]   # Cmd
            sp  = blk.getValues(3, 1)[0]   # Sp
            hoa = blk.getValues(10, 1)[0]  # HOA

            # HOA behavior
            if hoa == 1:        # Hand forces ON
                cmd = 1
            elif hoa == 2:      # Auto randomly toggles
                cmd = random.choice([0, 1])

            v = mid
            status = 1 if cmd else 0
            trip   = (random.choices([0, 1], weights=[90 - v, 10 + v])[0] if status else 0)

            runtime_old = blk.getValues(8, 1)[0]

            vals = [
                cmd,
                status,
                trip,
                sp,
                sp if (status and not trip) else 0,
                (random.randint(30, 90) + v) if status else 0,
                (random.randint(40, 90) + v) if status else 25,
                (random.randint(1, 10) * v) if trip else 0,
                runtime_old + (1 if (status and not trip) else 0),
                0,
                hoa,
                (random.randint(5, 20) + v) if status else 0
            ]

            blk.setValues(0, vals)

        time.sleep(UPDATE_INTERVAL)

def update_switchgear():
    while True:
        blk = sw_hr_block
        for b in range(NUM_BREAKERS):
            base = b * len(BREAKER_FIELDS)

            # keep manual status toggle
            status = blk.getValues(base, 1)[0]

            vals = [
                status,
                random.randint(0, 5),
                random.randint(220, 240),
                random.randint(0, 100)
            ]
            blk.setValues(base, vals)

        time.sleep(UPDATE_INTERVAL)


# ====================
# === Modbus server ===
# ====================
_server_started = False
_server_lock = threading.Lock()

def start_server(ip, port, on_error=None):
    try:
        print(f"Starting Modbus server at {ip}:{int(port)}")
        try:
            StartTcpServer(context=ctx, address=(ip, int(port)))  # 3.x+
        except TypeError:
            StartTcpServer(ctx, address=(ip, int(port)))          # 2.x
    except Exception as e:
        if on_error:
            on_error(e)


# =================
# === Tkinter UI ===
# =================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Modbus Simulator (Tkinter)")
        self.geometry("980x760")
        self.minsize(920, 680)

        ttk.Label(self, text="Modbus TCP Simulator", font=("Helvetica", 18, "bold")).pack(pady=(12, 10))

        self._build_server_frame()
        self._build_motor_cmd_frame()
        self._build_breaker_cmd_frame()
        self._build_live_data()

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w").pack(fill="x", side="bottom")

        # refresh loop
        self.after(200, self.refresh_live_data)

    def _build_server_frame(self):
        frm = ttk.LabelFrame(self, text="Server")
        frm.pack(fill="x", padx=12, pady=(0, 10))

        ttk.Label(frm, text="IP:").grid(row=0, column=0, padx=(10, 4), pady=10, sticky="w")
        self.ip_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(frm, textvariable=self.ip_var, width=18).grid(row=0, column=1, padx=4, pady=10, sticky="w")

        ttk.Label(frm, text="Port:").grid(row=0, column=2, padx=(18, 4), pady=10, sticky="w")
        self.port_var = tk.StringVar(value="5020")
        ttk.Entry(frm, textvariable=self.port_var, width=8).grid(row=0, column=3, padx=4, pady=10, sticky="w")

        ttk.Button(frm, text="Start Server", command=self.on_start_server).grid(
            row=0, column=4, padx=(18, 10), pady=10, sticky="w"
        )
        frm.columnconfigure(5, weight=1)

    def _build_motor_cmd_frame(self):
        frm = ttk.LabelFrame(self, text="Motor Commands")
        frm.pack(fill="x", padx=12, pady=(0, 10))

        ttk.Label(frm, text=f"ID (1-{NUM_MOTORS}):").grid(row=0, column=0, padx=(10, 4), pady=10, sticky="w")
        self.mid_var = tk.StringVar(value="1")
        ttk.Entry(frm, textvariable=self.mid_var, width=6).grid(row=0, column=1, padx=4, pady=10, sticky="w")

        ttk.Label(frm, text="Cmd:").grid(row=0, column=2, padx=(14, 4), pady=10, sticky="w")
        self.mcmd_var = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.mcmd_var, width=6).grid(row=0, column=3, padx=4, pady=10, sticky="w")

        ttk.Label(frm, text="Sp:").grid(row=0, column=4, padx=(14, 4), pady=10, sticky="w")
        self.msp_var = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.msp_var, width=6).grid(row=0, column=5, padx=4, pady=10, sticky="w")

        ttk.Label(frm, text="HOA:").grid(row=0, column=6, padx=(14, 4), pady=10, sticky="w")
        self.mhoa_var = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.mhoa_var, width=6).grid(row=0, column=7, padx=4, pady=10, sticky="w")

        ttk.Button(frm, text="Send Motor Cmd", command=self.on_send_motor_cmd).grid(
            row=0, column=8, padx=(18, 10), pady=10, sticky="w"
        )
        frm.columnconfigure(9, weight=1)

    def _build_breaker_cmd_frame(self):
        frm = ttk.LabelFrame(self, text="Breaker Commands")
        frm.pack(fill="x", padx=12, pady=(0, 10))

        ttk.Label(frm, text=f"ID (1-{NUM_BREAKERS}):").grid(row=0, column=0, padx=(10, 4), pady=10, sticky="w")
        self.bid_var = tk.StringVar(value="1")
        ttk.Entry(frm, textvariable=self.bid_var, width=6).grid(row=0, column=1, padx=4, pady=10, sticky="w")

        ttk.Label(frm, text="Status (0/1):").grid(row=0, column=2, padx=(14, 4), pady=10, sticky="w")
        self.bstat_var = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.bstat_var, width=6).grid(row=0, column=3, padx=4, pady=10, sticky="w")

        ttk.Button(frm, text="Set Breaker", command=self.on_set_breaker).grid(
            row=0, column=4, padx=(18, 10), pady=10, sticky="w"
        )
        frm.columnconfigure(5, weight=1)

    def _build_live_data(self):
        frm = ttk.LabelFrame(self, text="Live Data")
        frm.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.canvas = tk.Canvas(frm, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(frm, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = ttk.Frame(self.canvas)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.inner_id, width=e.width))
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        header = ttk.Frame(self.inner)
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        ttk.Label(header, text="Point", width=28, font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Raw",   width=10, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Human", width=18, font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky="w")

        self.live_labels = {}
        r = 1

        for m in range(1, NUM_MOTORS + 1):
            for i, fld in enumerate(MOTOR_FIELDS):
                row = ttk.Frame(self.inner)
                row.grid(row=r, column=0, sticky="ew", padx=8, pady=1)

                ttk.Label(row, text=f"Motor {m} {fld}", width=28).grid(row=0, column=0, sticky="w")
                raw_lbl = ttk.Label(row, text="", width=10)
                raw_lbl.grid(row=0, column=1, sticky="w")
                hum_lbl = ttk.Label(row, text="", width=18)
                hum_lbl.grid(row=0, column=2, sticky="w")

                self.live_labels[("M", m, i)] = (raw_lbl, hum_lbl)
                r += 1

        for b in range(1, NUM_BREAKERS + 1):
            for i, fld in enumerate(BREAKER_FIELDS):
                row = ttk.Frame(self.inner)
                row.grid(row=r, column=0, sticky="ew", padx=8, pady=1)

                ttk.Label(row, text=f"Breaker {b} {fld}", width=28).grid(row=0, column=0, sticky="w")
                raw_lbl = ttk.Label(row, text="", width=10)
                raw_lbl.grid(row=0, column=1, sticky="w")
                hum_lbl = ttk.Label(row, text="", width=18)
                hum_lbl.grid(row=0, column=2, sticky="w")

                self.live_labels[("S", b, i)] = (raw_lbl, hum_lbl)
                r += 1

    def _on_mousewheel(self, event):
        delta = int(-1 * (event.delta / 120))
        self.canvas.yview_scroll(delta, "units")

    # -------- Actions --------
    def on_start_server(self):
        global _server_started
        ip = self.ip_var.get().strip()
        port = safe_int(self.port_var.get(), default=None)

        if not ip:
            messagebox.showerror("Error", "IP cannot be empty.")
            return
        if port is None or port <= 0 or port > 65535:
            messagebox.showerror("Error", "Port must be 1–65535.")
            return

        with _server_lock:
            if _server_started:
                messagebox.showinfo("Info", "Server already started.")
                return
            _server_started = True

        def on_err(e):
            self.after(0, lambda: messagebox.showerror("Server error", str(e)))

        threading.Thread(target=start_server, args=(ip, port, on_err), daemon=True).start()
        self.status_var.set(f"Server started at {ip}:{port}")
        messagebox.showinfo("Server", f"Server started at {ip}:{port}")

    def on_send_motor_cmd(self):
        uid = safe_int(self.mid_var.get(), default=None)
        if uid is None or uid < 1 or uid > NUM_MOTORS:
            messagebox.showerror("Error", f"Motor ID must be 1–{NUM_MOTORS}.")
            return

        blk = motor_hr_blocks[uid]
        cmd = safe_int(self.mcmd_var.get(), default=None)
        sp  = safe_int(self.msp_var.get(), default=None)
        hoa = safe_int(self.mhoa_var.get(), default=None)

        if cmd is not None:
            blk.setValues(0, [cmd])
        if sp is not None:
            blk.setValues(3, [sp])
        if hoa is not None:
            blk.setValues(10, [hoa])

        self.status_var.set(f"Motor {uid}: wrote Cmd/Sp/HOA (blank ignored).")

    def on_set_breaker(self):
        bid = safe_int(self.bid_var.get(), default=None)
        st  = safe_int(self.bstat_var.get(), default=None)

        if bid is None or bid < 1 or bid > NUM_BREAKERS:
            messagebox.showerror("Error", f"Breaker ID must be 1–{NUM_BREAKERS}.")
            return
        if st not in (0, 1):
            messagebox.showerror("Error", "Breaker status must be 0 or 1.")
            return

        base = (bid - 1) * len(BREAKER_FIELDS)
        sw_hr_block.setValues(base, [st])
        self.status_var.set(f"Breaker {bid}: status set to {st}.")

    # -------- Refresh loop --------
    def refresh_live_data(self):
        # Update WITHOUT dying if one point fails
        try:
            for m in range(1, NUM_MOTORS + 1):
                blk = motor_hr_blocks[m]
                for i, fld in enumerate(MOTOR_FIELDS):
                    raw = blk.getValues(i, 1)[0]
                    raw_lbl, hum_lbl = self.live_labels[("M", m, i)]
                    raw_lbl.config(text=str(raw))
                    hum_lbl.config(text=human_motor(fld, raw))

            blk = sw_hr_block
            for b in range(1, NUM_BREAKERS + 1):
                for i, fld in enumerate(BREAKER_FIELDS):
                    addr = (b - 1) * len(BREAKER_FIELDS) + i
                    raw = blk.getValues(addr, 1)[0]
                    raw_lbl, hum_lbl = self.live_labels[("S", b, i)]
                    raw_lbl.config(text=str(raw))
                    hum_lbl.config(text=human_sg(fld, raw))

            self.status_var.set("Refreshing...")

        except Exception as e:
            # show the error but keep refreshing next cycle
            self.status_var.set(f"Refresh error: {e}")

        self.after(int(UPDATE_INTERVAL * 1000), self.refresh_live_data)


def main():
    threading.Thread(target=update_motors, daemon=True).start()
    threading.Thread(target=update_switchgear, daemon=True).start()
    App().mainloop()


if __name__ == "__main__":
    main()
