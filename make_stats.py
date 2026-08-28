import configparser
import logging
import sys
from pathlib import Path
import pandas as pd

# --------------------
# 設定ファイル
# --------------------
def load_config():
  config = configparser.ConfigParser()

  config.read(
    "config.ini",
    encoding="utf-8"
  )

  return config

def load_csv_files(data_dir, config):

  files = list(data_dir.glob("*.csv"))

  if not files:
    raise FileNotFoundError("CSVファイルがありません")

  dfs = []

  for file in files:
    logging.info("読み込み: %s", file)
    df = pd.read_csv(
      file,
      encoding=config["DEFAULT"]["input_encoding"],
      skiprows=[0, 1, 2, 4, 5],
      usecols=[0, 1, 4, 7]
    )

    # ファイル名からlocationを取得
    location = file.name.split("_")[0]
    # locationカラムを追加
    df["location"] = location

    dfs.append(df)

  return pd.concat(dfs, ignore_index=True)


# --------------------
# データいじり
# --------------------

# 年月日をdatetimeに変換
def trans_date(df):
  df["年月日"] = pd.to_datetime(
    df["年月日"],
    format="%Y/%m/%d"
  )

# locationごと & 月ごとの平均気温を全取得
def month_location_avg(df, config):
  df["月"] = df["年月日"].dt.month

  return (
    df.groupby(["location", "月"])[
      [
        config["DEFAULT"]["avg_tmp"],
        config["DEFAULT"]["max_tmp"],
        config["DEFAULT"]["min_tmp"]
      ]
    ].mean()
  )

# locationごと & 月・日ごとの平均気温を全取得
def daily_location_avg(df, config):
  df["月"] = df["年月日"].dt.month
  df["日"] = df["年月日"].dt.day

  return (
    df.groupby(["location", "月", "日"])[
      [
        config["DEFAULT"]["avg_tmp"],
        config["DEFAULT"]["max_tmp"],
        config["DEFAULT"]["min_tmp"]
      ]
    ].mean()
  )

# locationごと & 全期間の平均気温を取得
def all_location_avg(df, config):
  return (
    df.groupby("location")[
      [
        config["DEFAULT"]["avg_tmp"],
        config["DEFAULT"]["max_tmp"],
        config["DEFAULT"]["min_tmp"]
      ]
    ].mean()
  )

# locationごと & 月・日ごとの各気温の最高値を全取得
def daily_location_max(df, config):
  df["月"] = df["年月日"].dt.month
  df["日"] = df["年月日"].dt.day

  return (
    df.groupby(["location", "月", "日"])[
      [
        config["DEFAULT"]["avg_tmp"],
        config["DEFAULT"]["max_tmp"],
        config["DEFAULT"]["min_tmp"]
      ]
    ].max()
  )

# locationごと & 月・日ごとの各気温の最低値を全取得
def daily_location_min(df, config):
  df["月"] = df["年月日"].dt.month
  df["日"] = df["年月日"].dt.day

  return (
    df.groupby(["location", "月", "日"])[
      [
        config["DEFAULT"]["avg_tmp"],
        config["DEFAULT"]["max_tmp"],
        config["DEFAULT"]["min_tmp"]
      ]
    ].min()
  )

# --------------------
# CSV出力
# --------------------

# 整えたフォーマットをCSVで出力
def save_csv(df, output_file, config):
  output_file.parent.mkdir(
    parents=True,
    exist_ok=True
  )

  df.to_csv(
    output_file,
    encoding=config["DEFAULT"]["output_encoding"]
  )


# --------------------
# main処理
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

  # --------------------
  # CSV読み込み
  # --------------------
  try:
    df = load_csv_files(input_dir, config)

  except FileNotFoundError as e:
    logging.error(str(e))
    print(f"エラー: {e}")
    sys.exit(1)

  logging.info("CSV読み込み完了")

  # --------------------
  # データ加工
  # --------------------

  # 年月日をdatetimeに変換
  trans_date(df)

  # 月ごと、日ごと、全期間の平均値比較結果を取得
  result_m = month_location_avg(df, config)
  # print(result_m)

  result_d = daily_location_avg(df, config)
  # print(result_d)

  result_a = all_location_avg(df, config)
  # print(result_a)

  # locationごと & 月・日ごとの各気温の最高値を全取得
  result_max = daily_location_max(df, config)

  # locationごと & 月・日ごとの各気温の最低値を全取得
  result_min = daily_location_min(df, config)

  # --------------------
  # 出力
  # --------------------

  # 出力ファイル名指定
  month_filename = "month_stats.csv"
  daily_filename = "daily_stats.csv"
  all_filename = "overall_stats.csv"
  max_filename = "max_stats.csv"
  min_filename = "min_stats.csv"

  # 出力ファイルパス指定
  month_output_file = (output_dir / config["DEFAULT"]["stats_dir"] / month_filename)
  daily_output_file = (output_dir / config["DEFAULT"]["stats_dir"] / daily_filename)
  all_output_file = (output_dir / config["DEFAULT"]["stats_dir"] / all_filename)
  max_output_file = (output_dir / config["DEFAULT"]["stats_dir"] / max_filename)
  min_output_file = (output_dir / config["DEFAULT"]["stats_dir"] / min_filename)

  # 月、月・日、全期間のCSV出力
  save_csv(result_m, month_output_file, config)
  save_csv(result_d, daily_output_file, config)
  save_csv(result_a, all_output_file, config)
  save_csv(result_max, max_output_file, config)
  save_csv(result_min, min_output_file, config)
  print(f"\n月ごとのCSV出力先: {month_output_file}")
  print(f"月・日ごとのCSV出力先: {daily_output_file}")
  print(f"全期間のCSV出力先: {all_output_file}")
  print(f"最高値のCSV出力先: {max_output_file}")
  print(f"最低値のCSV出力先: {min_output_file}")
  logging.info("出力完了(month): %s", month_output_file)
  logging.info("出力完了(daily): %s", daily_output_file)
  logging.info("出力完了(overall): %s", all_output_file)
  logging.info("出力完了(max): %s", max_output_file)
  logging.info("出力完了(min): %s", min_output_file)
  logging.info("==========  END  ==========")

if __name__ == "__main__":
  main()