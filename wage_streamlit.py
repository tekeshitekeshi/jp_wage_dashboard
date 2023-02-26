import numpy as np
import pandas as pd
import streamlit as st
import pydeck as pdk
import plotly.express as px


st.title("日本の賃金データダッシュボード")

df_jp_ind = pd.read_csv("./csv_data/雇用_医療福祉_一人当たり賃金_全国_全産業.csv",encoding="shift_jis")
df_jp_category = pd.read_csv("./csv_data/雇用_医療福祉_一人当たり賃金_全国_大分類.csv",encoding="shift_jis")
df_pref_ind = pd.read_csv("./csv_data/雇用_医療福祉_一人当たり賃金_都道府県_全産業.csv",encoding="shift_jis")

st.header("■2019年：一人当たり平均賃金のヒートマップ")

jp_lat_lon = pd.read_csv("./pref_lat_lon.csv")
jp_lat_lon = jp_lat_lon.rename(columns={"pref_name":"都道府県名"})
jp_lat_lon

df_pref_map = df_pref_ind[(df_pref_ind["年齢"] == "年齢計")&(df_pref_ind["集計年"]==2019)]
df_pref_map = pd.merge(df_pref_map,jp_lat_lon,on="都道府県名")
#明示的に見せるために引数としてonを使う

#地図上に可視化していくが、賃金データをそのままでもいいが正規化処理を行う。
#正規化は最小値０、最大値１とする。
df_pref_map["一人当たり賃金（相対値）"]=((df_pref_map["一人当たり賃金（万円）"]-df_pref_map["一人当たり賃金（万円）"].min())/(df_pref_map["一人当たり賃金（万円）"].max()-df_pref_map["一人当たり賃金（万円）"].min()))

#pydeckを使うときは４つ設定が必要。下はview。中心地は東京の緯度経度
view = pdk.ViewState(
    longitude=139.691648,
    latitude=35.689185,
    zoom=4,
    pitch=40.5,
)
#2つ目はlayer
layer = pdk.Layer(
    "HeatmapLayer",
    data=df_pref_map,
    opacity=0.4, #ヒートマップにするときの不透明度
    get_position=["lon","lat"],#緯度経度
    threshold=0.3,#どこの値を閾値とするか
    get_weight = "一人当たり賃金（相対値）"#複数の列があった場合にどの列をヒートマップとして可視化するかを指定するための引数
)

layer_map = pdk.Deck(
    layers=layer,
    initial_view_state=view,
)

st.pydeck_chart(layer_map)

show_df = st.checkbox("Show DataFrame")
if show_df == True:
    st.write(df_pref_map) #チェックボックスがTrueになったらデータフレームを表示する処理

#集計年別の一人当たり賃金の推移をグラフ化、ダッシュボードに表示。
#１つ目は全国の平均賃金の推移。２つ目は都道府県ごとの平均賃金の推移
#２つ目の都道府県別はセレクトボックスでどの都道府県をグラフ化させるか選択できるようにする
st.header("■集計年別の一人当たり賃金（万円）の推移")
df_ts_mean = df_jp_ind[(df_jp_ind["年齢"]=="年齢計")]

#グラフ化したときに全国のデータか都道府県のデータかわかりやすくするために列が一人当たり賃金になっているところの列名を変える
df_ts_mean = df_ts_mean.rename(columns={"一人当たり賃金（万円）":"全国_一人当たり賃金（万円）"})

#都道府県ごとのデータを準備。df_pref_indのデータフレームから全国と同じように年齢列が年齢計になっている列を抽出する
df_pref_mean = df_pref_ind[(df_pref_ind["年齢"] == "年齢計")]

pref_list = df_pref_mean["都道府県名"].unique()
option_pref = st.selectbox(
    "都道府県",
    (pref_list))
df_pref_mean = df_pref_mean[df_pref_mean["都道府県名"] == option_pref]


#df_ts_meanとdf_pref_meanを結合して必要な列に絞ってグラフを変える
df_mean_line = pd.merge(df_ts_mean,df_pref_mean,on="集計年")
df_mean_line = df_mean_line[["集計年","全国_一人当たり賃金（万円）","一人当たり賃金（万円）"]]
df_mean_line = df_mean_line.set_index("集計年")
st.line_chart(df_mean_line)

#バブルチャート
st.header("■年齢別の全国一人当たり平均賃金（万円）")
df_mean_bubble = df_jp_ind[df_jp_ind["年齢"] !="年齢計"]

#ｘ軸に一人当たり賃金、ｙ軸は年間賞与、バブルサイズは所定内給与額にする
fig = px.scatter(df_mean_bubble, #plotlyexpressで散布図はバブルチャートを描くためにはscatterメソッドを使う
                x="一人当たり賃金（万円）",
                y="年間賞与その他特別給与額（万円）",
                range_x = [150,700],
                range_y = [0,150],
                size="所定内給与額（万円）",
                size_max=38,#バブルの大きさの最大値
                color="年齢",#プロットするどのグループに値して色分けするかを決める引数としてカラーで指定
                animation_frame="集計年",#アニメーションを決める引数。集計年ごとを見たい
                animation_group="年齢")#streamlitからplotlyを呼び出して使うことができる
st.plotly_chart(fig)



#産業別のアニメ―－しょんをつくる.年齢情報も追加する
#セレクトボックスも追加させて横棒グラフも変化させる
st.header("■産業別の賃金推移")
year_list = df_jp_category["集計年"].unique()
option_year = st.selectbox(
    "集計年",
    (year_list))
wage_list = ["一人当たり賃金（万円）","所定内給与額（万円）","年間賞与その他特別給与額（万円）"]
option_wage = st.selectbox(
    "賃金の種類",
    (wage_list))

#セレクトボックスで選択された集計値＝optionyearを集計年で条件抽出する
df_mean_categ = df_jp_category[(df_jp_category["集計年"] == option_year)]

 #一人当たり賃金は４００万円とかだけど所定内給与は３０万円とかなので自動的に変更させる
 
 #選択された賃金の種類によって最大値を取得する行動を変える↓
#選択された賃金の種類が列名として入って、その列の中の最大値を取得してmax_xという変数に格納される。賃金の種類に応じて変動する
max_x = df_mean_categ[option_wage].max() + 50

fig = px.bar(df_mean_categ, 
            x=option_wage,
            y="産業大分類名",
            color="産業大分類名",
            animation_frame="年齢",
            range_x = [0,max_x],
            orientation="h", #横棒グラフに設定するもの
            width=800, #横サイズ
            height=500)#たてサイズ
st.plotly_chart(fig)

st.text("出典：RESAS（地域経済分析システム）")
st.text("本結果はRESAS（地域経済分析システム）を加工して作成")