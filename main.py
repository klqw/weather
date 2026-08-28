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
  
# 指定日の最大値取得
def daily_max(input_file, location, target_temp, config):
  # StatsのCSVファイルを取得
  df = get_stats(input_file, config)

  # 指定日の月・日を取得
  target_month = target_temp["年月日"].iloc[0].month
  target_day = target_temp["年月日"].iloc[0].day

  # カラム設定
  avg_tmp = config["DEFAULT"]["avg_tmp"]
  max_tmp = config["DEFAULT"]["max_tmp"]
  min_tmp = config["DEFAULT"]["min_tmp"]

  # 指定日の月・日に対する最高値を取得
  df = df[
    (df["月"] == target_month) &
    (df["日"] == target_day)
  ]

  # ターゲット地点の指定日の月・日に対する最高値を取得
  target_max = df[
    df["location"] == location
  ]

  return target_max

# 指定日の最小値取得
def daily_min(input_file, location, target_temp, config):
  # StatsのCSVファイルを取得
  df = get_stats(input_file, config)

  # 指定日の月・日を取得
  target_month = target_temp["年月日"].iloc[0].month
  target_day = target_temp["年月日"].iloc[0].day

  # カラム設定
  avg_tmp = config["DEFAULT"]["avg_tmp"]
  max_tmp = config["DEFAULT"]["max_tmp"]
  min_tmp = config["DEFAULT"]["min_tmp"]

  # 指定日の月・日に対する最高値を取得
  df = df[
    (df["月"] == target_month) &
    (df["日"] == target_day)
  ]

  # ターゲット地点の指定日の月・日に対する最高値を取得
  target_min = df[
    df["location"] == location
  ]
  
  return target_min

# 指定日の最大値と最小値からスコアを計算
def calc_score(max_input_file, min_input_file, location, target_temp, config):
  # Statsの最大値CSVファイルを取得
  max_df = get_stats(max_input_file, config)

  # Statsの最小値CSVファイルを取得
  min_df = get_stats(min_input_file, config)

  # 指定日の月・日を取得
  target_month = target_temp["年月日"].iloc[0].month
  target_day = target_temp["年月日"].iloc[0].day

  # カラム設定
  avg_tmp = config["DEFAULT"]["avg_tmp"]
  max_tmp = config["DEFAULT"]["max_tmp"]
  min_tmp = config["DEFAULT"]["min_tmp"]

  # 指定地点 & 指定日の最大値を取得
  max_location_daily_df = max_df[
    (max_df["location"] == location) &
    (max_df["月"] == target_month) &
    (max_df["日"] == target_day)
  ]
  # スコア計算用に加工
  max_loc_day = max_location_daily_df[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  # 指定地点 & 指定月の最大値を取得
  max_location_month_df = max_df[
    (max_df["location"] == location) &
    (max_df["月"] == target_month)
  ]
  # スコア計算用に加工
  max_loc_mon = max_location_month_df[
    [avg_tmp, max_tmp, min_tmp]
  ].max()

  # 指定地点 & 全期間の最大値を取得
  max_location_all_df = max_df[
    (max_df["location"] == location)
  ]
  # スコア計算用に加工
  max_loc_all = max_location_all_df[
    [avg_tmp, max_tmp, min_tmp]
  ].max()

  # 全地点 指定日の最大値を取得
  max_daily_df = max_df[
    (max_df["月"] == target_month) &
    (max_df["日"] == target_day)
  ]
  # スコア計算用に加工
  max_day = max_daily_df[
    [avg_tmp, max_tmp, min_tmp]
  ].max()

  # 全地点 & 指定月の最大値を取得
  max_month_df = max_df[
    (max_df["月"] == target_month)
  ]
  # スコア計算用に加工
  max_mon = max_month_df[
    [avg_tmp, max_tmp, min_tmp]
  ].max()

  # 全地点 & 全期間の最大値を取得、加工
  max_all = max_df[
    [avg_tmp, max_tmp, min_tmp]
  ].max()

  # 指定地点 & 指定日の最小値を取得
  min_location_daily_df = min_df[
    (min_df["location"] == location) &
    (min_df["月"] == target_month) &
    (min_df["日"] == target_day)
  ]
  # スコア計算用に加工
  min_loc_day = min_location_daily_df[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  # 指定地点 & 指定月の最小値を取得
  min_location_month_df = min_df[
    (min_df["location"] == location) &
    (min_df["月"] == target_month)
  ]
  # スコア計算用に加工
  min_loc_mon = min_location_month_df[
    [avg_tmp, max_tmp, min_tmp]
  ].min()

  # 指定地点 & 全期間の最小値を取得
  min_location_all_df = min_df[
    (min_df["location"] == location)
  ]
  # スコア計算用に加工
  min_loc_all = min_location_all_df[
    [avg_tmp, max_tmp, min_tmp]
  ].min()

  # 全地点 指定日の最小値を取得
  min_daily_df = min_df[
    (min_df["月"] == target_month) &
    (min_df["日"] == target_day)
  ]
  # スコア計算用に加工
  min_day = min_daily_df[
    [avg_tmp, max_tmp, min_tmp]
  ].min()

  # 全地点 & 指定月の最小値を取得
  min_month_df = min_df[
    (min_df["月"] == target_month)
  ]
  # スコア計算用に加工
  min_mon = min_month_df[
    [avg_tmp, max_tmp, min_tmp]
  ].min()

  # 全地点 & 全期間の最小値を取得、加工
  min_all = min_df[
    [avg_tmp, max_tmp, min_tmp]
  ].min()

  """
  print("指定地点・指定日")
  print(max_loc_day)
  print(min_loc_day)
  print("指定地点・指定月")
  print(max_loc_mon)
  print(min_loc_mon)
  print("指定地点・全期間")
  print(max_loc_all)
  print(min_loc_all)
  print("全地点・指定日")
  print(max_day)
  print(min_day)
  print("全地点・指定月")
  print(max_mon)
  print(min_mon)
  print("全地点・全期間")
  print(max_all)
  print(min_all)
  """

  # 最大値を取得
  max_df = daily_max(max_input_file, location, target_temp, config)

  # 最小値を取得
  min_df = daily_min(min_input_file, location, target_temp, config)

  # 基準値の整形
  base = target_temp[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  # 最大値の整形
  max = max_df[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  # 最小値の整形
  min = min_df[
    [avg_tmp, max_tmp, min_tmp]
  ].iloc[0]

  # スコアのラベル(カラム名)を設定
  ld = config["DEFAULT"]["ld_score"]
  lm = config["DEFAULT"]["lm_score"]
  la = config["DEFAULT"]["la_score"]
  ad = config["DEFAULT"]["ad_score"]
  am = config["DEFAULT"]["am_score"]
  aa = config["DEFAULT"]["aa_score"]

  result = pd.DataFrame({
    ld: (base - min_loc_day) / (max_loc_day - min_loc_day) * 99 + 1,
    lm: (base - min_loc_mon) / (max_loc_mon - min_loc_mon) * 99 + 1,
    la: (base - min_loc_all) / (max_loc_all - min_loc_all) * 99 + 1,
    ad: (base - min_day) / (max_day - min_day) * 99 + 1,
    am: (base - min_mon) / (max_mon - min_mon) * 99 + 1,
    aa: (base - min_all) / (max_all - min_all) * 99 + 1
  }).round().astype(int)

  return result

# --------------------
# CSV出力
# --------------------

# CSV出力前にフォーマットを整える
def make_csv_result(result, comparison, location, score, config):
  # 地点マスタを取得
  location_dir = Path(config["DEFAULT"]["location_input_dir"])
  location_file = (location_dir / "locations.csv")
  try:
    df = pd.read_csv(location_file, encoding=config["DEFAULT"]["output_encoding"])

  except FileNotFoundError as e:
    logging.error(str(e))
    print(f"エラー: {e}")
    sys.exit(1)

  # 地点名取得
  location_name = df.loc[
    df["location"] == location,
    "location_name"
  ].iloc[0]
  # print(location_name)

  # 出力用DataFrameに 比較対象, 地点, スコアを追加
  result = result.copy()
  result.insert(0, "比較対象", comparison)
  result.insert(1, "地点", location_name)
  result = result.reset_index()
  result = result.rename(columns={"index": "項目"})
  result = result.join(
    score,
    on="項目"
  )
  # print(result)

  return result

# 整えたフォーマットをCSVで出力
def save_csv(df, output_file, config):
  output_file.parent.mkdir(
    parents=True,
    exist_ok=True
  )

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

  # Avg Stats
  month_stats_file = (stats_dir / "month_stats.csv")
  daily_stats_file = (stats_dir / "daily_stats.csv")
  all_stats_file = (stats_dir / "overall_stats.csv")

  # Max, Min Stats
  max_stats_file = (stats_dir / "max_stats.csv")
  min_stats_file = (stats_dir / "min_stats.csv")

  output_dir = Path(
    config["DEFAULT"]["result_dir"]
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

  # 日ごとの平均値比較結果を取得
  result_d = daily_diff(daily_stats_file, args.location, target_temp, config)
  # print(result_d)

  # 月ごとの平均値比較結果を取得
  result_m = month_diff(month_stats_file, args.location, target_temp, config)
  # print(result_m)

  # 全期間の平均値比較結果を取得
  result_a = all_diff(all_stats_file, args.location, target_temp, config)
  # print(result_a)

  # 指定地点 & 指定日 からスコアを算出
  score = calc_score(max_stats_file, min_stats_file, args.location, target_temp, config)
  # print(score)

  # スコアのラベル(カラム名)を設定
  ld = config["DEFAULT"]["ld_score"]
  lm = config["DEFAULT"]["lm_score"]
  la = config["DEFAULT"]["la_score"]
  ad = config["DEFAULT"]["ad_score"]
  am = config["DEFAULT"]["am_score"]
  aa = config["DEFAULT"]["aa_score"]

  # 日ごとのスコアをそれぞれ格納
  score_d = score[[ld, ad]]
  score_d.columns = ["地点スコア", "全体スコア"]
  # print(score_d)

  # 月ごとのスコアをそれぞれ格納
  score_m = score[[lm, am]]
  score_m.columns = ["地点スコア", "全体スコア"]
  # print(score_m)

  # 全期間のスコアをそれぞれ格納
  score_a = score[[la, aa]]
  score_a.columns = ["地点スコア", "全体スコア"]
  # print(score_a)

  # --------------------
  # 出力
  # --------------------

  # 「比較対象」カラムの値設定
  comparison_m = str(target_date.month) + "月平均"  # 月
  comparison_d = str(target_date.month) + "月" + str(target_date.day) + "日平均"  # 日
  comparison_a = "全期間平均" # 全期間

  # CSV出力用にフォーマット整形
  daily_result = make_csv_result(result_d, comparison_d, args.location, score_d, config)
  month_result = make_csv_result(result_m, comparison_m, args.location, score_m, config)
  all_result = make_csv_result(result_a, comparison_a, args.location, score_a, config)

  result = pd.concat([
    daily_result,
    month_result,
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