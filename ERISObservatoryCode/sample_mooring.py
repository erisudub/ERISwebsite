import logging
import time

from ecov2 import EcoV2Driver
from seacat import SeaCATDriver
from sensor_dataclass import MooringSample


def sample_mooring(ctd_port=None, eco_port=None, emulate=False):
    """Take one sample from each instrument and return it as a JSON string."""
    sample = MooringSample(timestamp=time.time())

    # SeaCAT first: it pumps for ~40 s, and take_sample() waits until it's done.
    ctd = SeaCATDriver(port=ctd_port, emulate=emulate)
    ctd.stop_profiling_wake_instrument()
    sample.ctd = ctd.take_sample()

    # Then the ECO V2.
    eco = EcoV2Driver(port=eco_port, emulate=emulate)
    eco.stop_sampling_wake_instrument()
    sample.ecov2 = eco.take_sample()

    return sample.to_json()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # For the real instruments: sample_mooring(ctd_port="/dev/tty...", eco_port="/dev/tty...")
    json_string = sample_mooring(emulate=True)
    print(json_string)  # TODO: send json_string to the database
