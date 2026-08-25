import argparse
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

def load_csv_files(data_dir, location, config):

  files = list(data_dir.glob(f"{location}_*.csv"))

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

# # 月ごとの平均気温を全取得
# def month_avg(df):
#   df["月"] = df["年月日"].dt.month

#   return (
#     df.groupby(["月"])[
#       ["平均気温(℃)", "最高気温(℃)", "最低気温(℃)"]
#     ].mean()
#   )

# # 月・日ごとの平均気温を全取得
# def daily_avg(df):
#   df["月"] = df["年月日"].dt.month
#   df["日"] = df["年月日"].dt.day

#   return (
#     df.groupby(["月", "日"])[
#       ["平均気温(℃)", "最高気温(℃)", "最低気温(℃)"]
#     ].mean()
#   )

# # 全期間の平均気温を取得
# def all_avg(df):
#   return df[
#     ["平均気温(℃)", "最高気温(℃)", "最低気温(℃)"]
#   ].mean()

# make_statsからの取得
def get_stats(input_file, config):

  try:
    stats = pd.read_csv(
      input_file,
      encoding=config["DEFAULT"]["output_encoding"]
    )

  except FileNotFoundError as e:
    logging.error(str(e))
    print(f"エラー: {e}")
    sys.exit(1)

  logging.info(f"Statsファイル読み込み完了: {input_file}")

  return stats

# 指定日の実測値を取得
def get_target_temp(df, target_date):
  return df[
    df["年月日"] == target_date
  ]

# --------------------
# 指定日付の差分分析
# --------------------

# 指定日と月の比較
def month_diff(input_file, location, target_temp, config):
  # StatsのCSVファイルを取得
  df = get_stats(input_file, config)

  # 指定日の月を取得
  target_month = target_temp["年月日"].iloc[0].month

  # カラム設定
  avg_tmp = config["DEFAULT"]["avg_tmp"]
  max_tmp = config["DEFAULT"]["max_tmp"]
  min_tmp = config["DEFAULT"]["min_tmp"]

  # 指定日の月に対応する平均値を取得
  df = df[
    df["月"] == target_month
  ]

  # 全地点の指定日の月に対する平均値を取得
  all_avg = df.groupby(["location", "月"])[
    [avg_tmp, max_tmp, min_tmp]
  ].mean()
  all_avg = all_avg.mean().to_frame().T
  # print(all_avg)

  # ターゲット地点の指定日の月に対する平均値を取得
  target_avg = df[
    df["location"] == location
  ]
  # print(target_avg)

  # target_tempを比較用に加工
  actual = target_temp[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  # 全地点の指定日の月に対する平均値を比較用に加工
  base_all = all_avg[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  # ターゲット地点の指定日の月に対する平均値を比較ように加工
  base_target = target_avg[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  return pd.DataFrame({
    "実測値": actual,
    "地点基準値": base_target,
    "差(地点)": actual - base_target,
    "全体基準値": base_all,
    "差(全体)": actual - base_all
  }).round(1)

# 指定日と月・日の比較
def daily_diff(input_file, location, target_temp, config):
  # StatsのCSVファイルを取得
  df = get_stats(input_file, config)

  # 指定日の月・日を取得
  target_month = target_temp["年月日"].iloc[0].month
  target_day = target_temp["年月日"].iloc[0].day

  # カラム設定
  avg_tmp = config["DEFAULT"]["avg_tmp"]
  max_tmp = config["DEFAULT"]["max_tmp"]
  min_tmp = config["DEFAULT"]["min_tmp"]

  # 指定日の月・日に対する平均値を取得
  df = df[
    (df["月"] == target_month) &
    (df["日"] == target_day)
  ]

  # 全地点の指定日の月・日に対する平均値を取得
  all_avg = df.groupby(["location", "月", "日"])[
    [avg_tmp, max_tmp, min_tmp]
  ].mean()
  all_avg = all_avg.mean().to_frame().T
  # print(all_avg)

  # ターゲット地点の指定日の月・日に対する平均値を取得
  target_avg = df[
    df["location"] == location
  ]
  # print(target_avg)

  # target_tempを比較用に加工
  actual = target_temp[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  # 全地点の指定日の月・日に対する平均値を比較用に加工
  base_all = all_avg[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  # ターゲット地点の指定日の月・日に対する平均値を比較ように加工
  base_target = target_avg[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  return pd.DataFrame({
    "実測値": actual,
    "地点基準値": base_target,
    "差(地点)": actual - base_target,
    "全体基準値": base_all,
    "差(全体)": actual - base_all
  }).round(1)

# 指定日と全期間の比較
def all_diff(input_file, location, target_temp, config):
  # StatsのCSVファイルを取得
  df = get_stats(input_file, config)
  # print(df)

  # カラム設定
  avg_tmp = config["DEFAULT"]["avg_tmp"]
  max_tmp = config["DEFAULT"]["max_tmp"]
  min_tmp = config["DEFAULT"]["min_tmp"]

  # 全地点の平均値を取得
  all_avg = df.mean(numeric_only=True).to_frame().T
  # print(all_avg)

  # ターゲット地点の平均値を取得
  target_avg = df[
    df["location"] == location
  ]
  # print(target_avg)

  # target_tempを比較用に加工
  actual = target_temp[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  # 全地点の平均値を比較用に加工
  base_all = all_avg[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  # ターゲット地点の平均値を比較用に加工
  base_target = target_avg[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  return pd.DataFrame({
    "実測値": actual,
    "地点基準値": base_target,
    "差(地点)": actual - base_target,
    "全体基準値": base_all,
    "差(全体)": actual - base_all
  }).round(1)
  

# --------------------
# CSV出力
# --------------------

# CSV出力前にフォーマットを整える
def make_csv_result(result, comparison, location, config):
  # 地点マスタを取得
  location_dir = Path(config["DEFAULT"]["location_input_dir"])
  location_file = (location_dir / "locations.csv")
  try:
    df = pd.read_csv(location_file, encoding=config["DEFAULT"]["output_encoding"])

  except FileNotFoundError as e:
    logging.error(str(e))
    print(f"エラー: {e}")
    sys.exit(1)

  location_name = df.loc[
    df["location"] == location,
    "location_name"
  ].iloc[0]
  # print(location_name)
  result = result.copy()
  result.insert(0, "比較対象", comparison)
  result.insert(1, "地点", location_name)
  result = result.reset_index()
  result = result.rename(columns={"index": "項目"})

  return result

# 整えたフォーマットをCSVで出力
def save_csv(df, output_file, config):
  output_file.parent.mkdir(exist_ok=True)

  df.to_csv(
    output_file,
    index=False,
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

  input_dir = Path(
    config["DEFAULT"]["input_dir"]
  )

  stats_dir = Path(
    config["DEFAULT"]["stats_input_dir"]
  )

  month_stats_file = (stats_dir / "month_stats.csv")
  daily_stats_file = (stats_dir / "daily_stats.csv")
  all_stats_file = (stats_dir / "overall_stats.csv")

  output_dir = Path(
    config["DEFAULT"]["output_dir"]
  )

  # --------------------
  # CLI
  # --------------------

  parser = argparse.ArgumentParser(
    description="気温分析ツール"
  )

  parser.add_argument(
    "--location",
    required=True,
    help="分析対象場所を英数字で指定"
  )

  parser.add_argument(
    "--date",
    required=True,
    help="分析対象日をyyyymmddで指定"
  )

  args = parser.parse_args()

  logging.info("date=%s", args.date)

  # --------------------
  # CSV読み込み
  # --------------------

  try:
    df = load_csv_files(input_dir, args.location, config)

  except FileNotFoundError as e:
    logging.error(str(e))
    print(f"エラー: {e}")
    sys.exit(1)

  logging.info("CSV読み込み完了")

  # --------------------
  # 分析
  # --------------------

  # 年月日をdatetimeに変換
  trans_date(df)

  # 対象日を取得
  target_date = pd.Timestamp(args.date)

  # 対象日の実測値を取得
  target_temp = get_target_temp(df, target_date)
  # print(target_temp)

  # 月ごと、日ごと、全期間の平均値比較結果を取得
  result_m = month_diff(month_stats_file, args.location, target_temp, config)
  # print(result_m)

  result_d = daily_diff(daily_stats_file, args.location, target_temp, config)
  # print(result_d)

  result_a = all_diff(all_stats_file, args.location, target_temp, config)
  # print(result_a)

  # --------------------
  # 出力
  # --------------------

  # 「比較対象」カラムの値設定
  comparison_m = str(target_date.month) + "月平均"  # 月
  comparison_d = str(target_date.month) + "月" + str(target_date.day) + "日平均"  # 日
  comparison_a = "全期間平均" # 全期間

  # CSV出力用にフォーマット整形
  month_result = make_csv_result(result_m, comparison_m, args.location, config)
  daily_result = make_csv_result(result_d, comparison_d, args.location, config)
  all_result = make_csv_result(result_a, comparison_a, args.location, config)

  result = pd.concat([
    month_result,
    daily_result,
    all_result
  ], ignore_index=True)
  # print(result)

  filename = args.location + "_" + args.date + ".csv"
  output_file = (output_dir / filename)
  save_csv(result, output_file, config)
  print(f"\n出力先: {output_file}")
  logging.info("出力完了: %s", output_file)
  logging.info("==========  END  ==========")


if __name__ == "__main__":
  main()