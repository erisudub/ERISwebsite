import logging
import random
import serial
from sensor_dataclass import EcoV2Data

log = logging.getLogger("ecov2")


class FakeEcoV2:
    """Pretends to be an ECO V2 on a serial port, for testing without hardware.

    Has the same write() / read_until() methods as serial.Serial, so the
    driver below works with either one.
    """

    def __init__(self):
        self.reply = b""

    def write(self, data):
        cmd = data.decode().strip().lower()
        if cmd == "ts":
            # Fake sample: serial number, chl (hgo, fv), bb (hgo, fv), fdom (hgo, fv), input voltage
            values = ["BBFL2W-1234",
                      random.randint(50, 4000), random.randint(0, 1),
                      random.randint(50, 4000), random.randint(0, 1),
                      random.randint(50, 4000), random.randint(0, 1),
                      f"{12 + random.random():.2f}"]
            text = "\t".join(str(v) for v in values)  # ECO V2 separates values with tabs
        elif cmd == "!!!!!":
            text = "stopped"
        else:
            text = "?CMD"
        # Reply, then <Executed/> to mark the end.
        self.reply = f"{text}\r\n<Executed/>\r\n".encode()

    def read_until(self, expected=b"<Executed/>\r\n"):
        reply, self.reply = self.reply, b""
        return reply


class EcoV2Driver:
    def __init__(self, port=None, emulate=False):
        if emulate:
            log.info("Using emulated ECO V2")
            self.serial_handle = FakeEcoV2()
        else:
            log.info("Opening serial port %s", port)
            self.serial_handle = serial.Serial(port, baudrate=19200, timeout=10)

    def send_command(self, cmd):
        """Send a command and return the reply text, up to <Executed/>."""
        # TODO (eris_team): make sure this works, or should we look for \r\n
        log.info("Sending: %s", cmd)
        self.serial_handle.write(f"{cmd}\r\n".encode())
        reply = self.serial_handle.read_until(b"<Executed/>\r\n").decode()
        log.debug("Reply: %r", reply)
        return reply

    def stop_sampling_wake_instrument(self):
        """'!!!!!' stops the ECO V2 if it is sampling and wakes it up."""
        return self.send_command("!!!!!")

    def take_sample(self):
        reply = self.send_command("ts")
        return self.parse_reply(reply)

    def parse_reply(self, reply):
        """Turn a TS reply into EcoV2Data.

        Values are tab-separated. Assumes columns: serial number, chl hgo, chl fv, bb hgo, bb fv,
        fdom hgo, fdom fv, input voltage.
        TODO (eris_team): run GetOutStr on the real ECO V2 and confirm this order,
        and check whether the instrument echoes the command (data would then be line 1).
        """
        print(f'ECOV2 reply to parse: {reply}')
        data_line = reply.splitlines()[0]
        sn, chl_hgo, chl_fv, bb_hgo, bb_fv, fdom_hgo, fdom_fv, volts = [x.strip() for x in data_line.split("\t")]
        log.info("Sample: sn=%s, chl=%s, bb=%s, fdom=%s, V=%s", sn, chl_hgo, bb_hgo, fdom_hgo, volts)
        return EcoV2Data(sn=sn, chl_hgo=int(chl_hgo), chl_fv=int(chl_fv),
                         bb_hgo=int(bb_hgo), bb_fv=int(bb_fv),
                         fdom_hgo=int(fdom_hgo), fdom_fv=int(fdom_fv),
                         input_voltage=float(volts))


if __name__ == "__main__":
    # Change INFO to DEBUG to also see the full raw replies from the instrument.
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    eco = EcoV2Driver(emulate=True)  # set emulate=False and pass port="/dev/tty..." for the real one
    eco.stop_sampling_wake_instrument()
    eco.take_sample()
