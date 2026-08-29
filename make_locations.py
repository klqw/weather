import configparser
import csv
import logging
import sys
from pathlib import Path
import pandas as pd

def load_config():
  config = configparser.ConfigParser()
  config.read(
    "config.ini",
    encoding="utf-8"
  )

  return config

# 地点マスタ作成
def build_location_master(data_dir, config):
  files = list(data_dir.glob("*.csv"))

  if not files:
    raise FileNotFoundError("CSVファイルがありません")

  locations = []
  registered_locations = set()

  for file in files:
    loc = {}
    with open(file, encoding=config["DEFAULT"]["input_encoding"]) as f:
      reader = csv.reader(f)

      # 0~1行目をスキップして、地点名の行を取得
      next(reader)
      next(reader)
      row = next(reader)

      location = file.name.split("_")[0]
      location_name = next(value for value in row if value)

    if location not in registered_locations:
      loc = {
        "location": location,
        "location_name": location_name
      }
      registered_locations.add(location)
      locations.append(loc)

  return locations

# 地点マスタCSV出力
def save_csv(locations, output_file, config):
  output_file.parent.mkdir(
    parents=True,
    exist_ok=True
  )
  df = pd.DataFrame(locations)

  df.to_csv(
    output_file,
    index=False,
    encoding=config["DEFAULT"]["output_encoding"]
  )


# --------------------
# main関数
# --------------------
def main():
  config = load_config()

  logging.basicConfig(
    filename=config["DEFAULT"]["log_file"],
    level=logging.INFO,
    encoding=config["DEFAULT"]["log_encoding"],
    format="%(asctime)s %(levelname)s [%(filename)s] %(message)s"
  )

  logging.info("========== START ==========")

  input_dir = Path(config["DEFAULT"]["input_dir"])
  output_dir = Path(config["DEFAULT"]["output_dir"])
  output_file = (output_dir / config["DEFAULT"]["location_dir"] / "locations.csv")

  # CSV読み込み
  try:
    locations = build_location_master(input_dir, config)

  except FileNotFoundError as e:
    logging.error(str(e))
    print(f"エラー: {e}")
    sys.exit(1)

  logging.info("CSV読み込み完了")

  # 地点マスタ出力
  save_csv(locations, output_file, config)
  print(f"\n出力先: {output_file}")
  logging.info("出力完了: %s", output_file)
  logging.info("==========  END  ==========")


if __name__ == "__main__":
  main()