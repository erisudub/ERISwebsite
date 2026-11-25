import logging
import random
import serial
from sensor_dataclass import CTDData

log = logging.getLogger("seacat")


class FakeSBE16:
    """Pretends to be an SBE 16plus on a serial port, for testing without hardware.

    Has the same write() / read_until() methods as serial.Serial, so the
    driver below works with either one.
    """

    def __init__(self):
        self.reply = b""

    def write(self, data):
        cmd = data.decode().strip().lower()
        if cmd == "ts":
            # Fake raw sample: temperature (A/D counts), conductivity (Hz), pressure (A/D counts),
            # pressure temperature (counts), SBE63 oxygen phase (us), SBE63 temperature (V)
            text = (f"{random.randint(500000, 550000)}, {6000 + random.random() * 100:.3f}, "
                    f"{random.randint(600000, 610000)}, {random.randint(2400, 2600)}, "
                    f"{30 + random.random():.3f}, {0.8 + random.random() / 10:.6f}")
        elif cmd == "ds":
            text = "SBE 16plus V 2.5.2  SERIAL NO. 01607777\r\nstatus = not logging"
        elif cmd == "stopprofile":
            text = "<Executed/>"
        else:
            text = "?CMD"
        # Real instrument echoes the command, sends its reply, then the S> prompt.
        self.reply = f"{cmd}\r\n{text}\r\nS>".encode()

    def read_until(self, expected=b"S>"):
        reply, self.reply = self.reply, b""
        return reply


class SeaCATDriver:
    def __init__(self, port=None, emulate=False):
        if emulate:
            log.info("Using emulated SBE 16plus")
            self.serial_handle = FakeSBE16()
        else:
            # TODO (eris_team): check baud rate and timeout against the instrument's setup.
            log.info("Opening serial port %s", port)
            self.serial_handle = serial.Serial(port, baudrate=9600, timeout=60)

    def send_command(self, cmd):
        """Send a command and return the reply text, up to the S> prompt."""
        # TODO (eris_team): the real instrument may need a wake-up first and may
        # time out. Handle a reply that doesn't end in "S>".
        log.info("Sending: %s", cmd)
        self.serial_handle.write(f"{cmd}\r\n".encode())
        reply = self.serial_handle.read_until(b"S>").decode()
        log.debug("Reply: %r", reply)
        return reply

    def stop_profiling_wake_instrument(self):
        return self.send_command("stopprofile")

    def get_ds(self):
        return self.send_command("ds")  # TODO (eris_team): parse this later if needed

    def take_sample(self):
        reply = self.send_command("ts")
        return self.parse_reply(reply)

    def parse_reply(self, reply):
        """Turn a TS reply into CTDData.

        Raw values only; conversion to engineering units happens on the server.
        Assumes raw decimal output with an SBE 63 oxygen sensor, columns:
        temperature, conductivity, pressure, pressure temperature, oxygen phase, oxygen temperature.
        TODO (eris_team): set the instrument's output format to raw decimal and
        confirm the column order on the real instrument.
        """
        data_line = reply.splitlines()[1]  # line 0 is the echoed command
        temp, cond, pres, pres_temp, oxy_phase, oxy_temp = [float(x) for x in data_line.split(",")]
        log.info("Sample (raw): T=%s, C=%s, P=%s, Ptemp=%s, O2 phase=%s, O2 temp=%s",
                 temp, cond, pres, pres_temp, oxy_phase, oxy_temp)
        return CTDData(temperature=temp, conductivity=cond, pressure=pres,
                       pressure_temperature_raw=pres_temp, oxygen_phase=oxy_phase,
                       oxygen_temperature=oxy_temp)


if __name__ == "__main__":
    # Change INFO to DEBUG to also see the full raw replies from the instrument.
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ctd = SeaCATDriver(emulate=True)  # set emulate=False and pass port="/dev/tty..." for the real one
    ctd.stop_profiling_wake_instrument()
    ctd.get_ds()
    ctd.take_sample()
