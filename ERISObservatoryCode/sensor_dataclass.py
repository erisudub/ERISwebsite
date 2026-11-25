import csv
import json
import os
from dataclasses import dataclass, asdict, fields
from datetime import datetime
from typing import Optional


@dataclass
class CTDData:
    """One reading from the SeaCAT CTD."""
    temperature: Optional[float] = None
    conductivity: Optional[float] = None
    pressure: Optional[float] = None
    pressure_temperature_raw: Optional[float] = None
    oxygen_phase: Optional[float] = None
    oxygen_temperature: Optional[float] = None


@dataclass
class EcoV2Data:
    """One reading from the ECO V2."""
    sn: Optional[str] = None
    chl_hgo: Optional[int] = None
    chl_fv: Optional[int] = None
    bb_hgo: Optional[int] = None
    bb_fv: Optional[int] = None
    fdom_hgo: Optional[int] = None
    fdom_fv: Optional[int] = None
    input_voltage: Optional[float] = None


@dataclass
class MooringSample:
    """One sample from the mooring. Instruments not sampled are left as None."""
    timestamp: Optional[float] = None
    ctd: Optional[CTDData] = None
    ecov2: Optional[EcoV2Data] = None
    # TODO: add the third instrument here, e.g. `other: Optional[OtherData] = None`,
    # and add it to INSTRUMENTS below.

    # Instrument field name -> its dataclass. Used to build fixed CSV columns,
    # so every daily file has the same header no matter which instruments sampled.
    INSTRUMENTS = {
        "ctd": CTDData,
        "ecov2": EcoV2Data,
    }

    def to_json(self, indent: int = 4) -> str:
        """Return the sample as pretty-printed, nested JSON."""
        return json.dumps(asdict(self), indent=indent)

    @classmethod
    def csv_columns(cls) -> list:
        """Flat column names: timestamp, then <instrument>_<field> for each instrument."""
        columns = ["timestamp"]
        for prefix, instrument_cls in cls.INSTRUMENTS.items():
            columns += [f"{prefix}_{f.name}" for f in fields(instrument_cls)]
        return columns

    def to_csv_row(self) -> dict:
        """Flatten into one row. An absent instrument gives blank cells."""
        row = {"timestamp": self.timestamp}
        for prefix in self.INSTRUMENTS:
            data = getattr(self, prefix)
            if data is not None:
                for name, value in asdict(data).items():
                    row[f"{prefix}_{name}"] = value
        return row

    def write_to_file(self, directory: str = ".") -> str:
        """Append this sample as one CSV row to that day's output file.

        Each day gets its own file, e.g. sensor_output_2026-11-23.txt, dated
        from the sample's timestamp (or the current time if it has none).
        The first row of every new file is the CSV header (column names),
        so the whole file can be pasted straight into a spreadsheet.
        Missing (None) values and absent instruments are written as empty cells.
        Returns the path of the file written to.
        """
        when = datetime.fromtimestamp(self.timestamp) if self.timestamp is not None else datetime.now()
        os.makedirs(directory, exist_ok=True)
        file_pathway = os.path.join(directory, f"sensor_output_{when:%Y-%m-%d}.txt")

        write_header = not os.path.exists(file_pathway) or os.path.getsize(file_pathway) == 0
        with open(file_pathway, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_columns())
            if write_header:
                writer.writeheader()
            writer.writerow(self.to_csv_row())
        return file_pathway


if __name__ == '__main__':
    # Example: CTD sampled, ECO V2 not sampled this time.
    sample = MooringSample(
        timestamp=1700000000.0,
        ctd=CTDData(temperature=524288, conductivity=6050.123),
        ecov2=EcoV2Data(chl_hgo=1000, bb_hgo=2000, fdom_hgo=1000),
    )
    print(sample.to_json())
    print("Wrote to", sample.write_to_file())
