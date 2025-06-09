from flask import Flask, jsonify, render_template, request,Blueprint
import requests
import time
import os
import pickle
import numpy as np
from geopy.distance import geodesic  # 新增導入geodesic函數

from .config import CLIENT_ID, CLIENT_SECRET, WEATHER_API_KEY

model_bp = Blueprint('model', __name__)

# API 路由
@model_bp.route('/predict', methods=['POST'])
def predict():
    try:
        input_data = request.get_json()
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400

        prediction = predict_wait_time(input_data)
        return jsonify({
            "prediction": prediction,
            "unit": "seconds"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#####
# 快取 token 與過期時間
_token_cache = {
    "access_token": None,
    "expires_at": 0
}

def get_token():
    now = time.time()
    # 若 token 未過期則直接回傳
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    url = 'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token'
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    res = requests.post(url, headers=headers, data=data)
    if res.status_code == 200:
        token_json = res.json()
        access_token = token_json['access_token']
        expires_in = token_json.get('expires_in', 1800)  # 預設 1800 秒
        _token_cache["access_token"] = access_token
        _token_cache["expires_at"] = now + expires_in - 60  # 提前 60 秒刷新
        return access_token
    else:
        return None

# TDX API 取得即時到站資訊
@model_bp.route('/api/model_eta')
def model_eta():
    route_name = request.args.get('route', '295')
    selected_direction = int(request.args.get('direction', '0'))
    access_token = get_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    # 取得站名清單
    all_stop_names = {
        "0南": {
            "0": [ # To MRT Dongmen Station (往捷運東門站)
                "萬芳社區", "萬芳活動中心", "萬芳國小", "萬芳6號公園", "萬利街口", "棕櫚泉社區", "文山運動中心(萬芳)", 
                "臺灣警察專科學校", "捷運萬芳醫院站", "中國科技大學(興隆)", "興隆國小", "興德國小", "興隆市場", "靜心高中", 
                "憲光公寓", "景明街口", "武功國小(興隆)", "師大分部", "捷運公館站", "臺大", "臺大綜合體育館", "溫州街口", 
                "師大綜合大樓", "師大", "金山潮州街口", "公企中心", "捷運東門站(金山)"
            ],
            "1": [ # To Wanshang Community (往萬芳社區)
                "信義永康街口(捷運東門站)", "金華新生路口", "和平新生路口", "龍安國小(公務人力發展學院)", "臺大綜合體育館", 
                "臺大", "捷運公館站", "師大分部", "武功國小(興隆)", "景明街口", "憲光公寓", "靜心高中", "興隆市場", 
                "興德國小", "興隆國小", "捷運萬芳醫院站", "臺灣警察專科學校", "文山運動中心(萬芳)", "棕櫚泉社區", 
                "萬利街口", "捷運萬芳社區站", "萬芳6號公園", "萬芳國小", "萬芳活動中心", "萬芳社區"
            ]
        },
        "278": {
            "0": [ # To MRT Neihu Station (往捷運內湖站)
                "景福街", "溪口國小", "捷運景美站", "財政園區", "萬隆", "捷運萬隆站", "武功國小(羅斯福)", "師大分部", "捷運公館站", 
                "台電大樓", "捷運台電大樓站", "羅斯福浦城街口", "羅斯福金門街口", "捷運古亭站(和平)", "師大", "師大綜合大樓", 
                "溫州街口", "大安森林公園", "龍門國中(和平)", "復興南路口", "國立臺北教育大學", "臥龍街", "成功國宅", "大安國中", 
                "信義敦化路口", "仁愛國中", "安和敦化路口", "捷運忠孝敦化站", "市民大道口", "臺視", "美仁里", "榮民服務處", 
                "南京新村", "三軍總醫院松山分院", "長壽公園", "健康新城", "三民健康路口(西松高中)", "三民路", "新東街口", 
                "民生國中", "新益里", "民權大橋", "時報廣場", "三民國中", "內湖行政大樓", "國防醫學中心", "三總內湖站", 
                "將軍嶺", "方濟中學", "成功路三段", "湖光市場", "捷運內湖站"
            ],
            "1": [ # To MRT Jingmei Station (往捷運景美站)
                "金龍路口", "碧湖國小", "內湖派出所", "達人高中(臺灣戲曲學院)", "內湖國小", "西湖圖書館(湖光教會)", "西湖圖書館(湖光教會)","湖光國宅", 
                "捷運文德站(碧湖公園)", "內湖高中", "方濟中學", "將軍嶺", "三總內湖站", "國防醫學中心", "內湖行政大樓", 
                "三民國中", "時報廣場", "民權大橋", "新益里", "民生國中", "新東街口", "三民路", "三民健康路口(西松高中)", 
                "健康新城", "長壽公園", "三軍總醫院松山分院", "南京新村", "博仁醫院", "臺北市區監理所(光復)", 
                "捷運國父紀念館站(光復)", "交通部觀光署", "阿波羅大廈", "捷運忠孝敦化站", "頂好市場", "懷生國中", 
                "聯合醫院仁愛院區", "東豐復興路口", "大安高工(捷運大安站)", "開平餐飲學校", "捷運科技大樓站", "復興南路口", 
                "國北教大實小", "龍門國中(和平)", "大安森林公園", "溫州街口", "師大綜合大樓", "師大", "捷運古亭站(和平)", 
                "羅斯福金門街口", "羅斯福浦城街口", "捷運台電大樓站", "台電大樓", "捷運公館站", "師大分部", 
                "武功國小(羅斯福)", "捷運萬隆站", "萬隆", "財政園區", "捷運景美站", "溪口國小", "景福街"
            ]
        },
        "295": {
            "0": [ # To Taipei Main Station (往臺北車站)
                "富德", "象頭埔", "萬福橋", "捷運動物園站", "貓纜動物園站", "萬壽橋頭(新光)", "萬壽橋頭(秀明)", "萬興國小", 
                "新光路口", "指南路口", "木南公園", "景文中學", "司法新村", "忠順廟", "國泰新村(木新)", "力行國小", 
                "木新市場", "景美女中", "木新路口", "實踐國中", "中港抽水站", "溝子口(幸福華興)", "辛亥路6段21巷口", 
                "懷恩隧道", "中國科技大學(辛亥)", "興隆路口(辛亥)", "捷運辛亥站", "辛亥國小", "青峰活動中心", 
                "自來水處(辛亥)", "大安運動中心", "大安健康服務中心", "復興南路口", "國北教大實小", "龍門國中(和平)", 
                "大安森林公園", "溫州街口", "師大綜合大樓", "師大", "捷運古亭站(和平)", "南昌家具街", "聯合醫院婦幼院區一", 
                "南昌路", "南門", "一女中(公園)", "捷運台大醫院站", "臺北車站(青島)"
            ],
            "1": [ # To Fude (往富德)
                "青島林森路口", "成功中學(林森)", "開南中學", "仁愛林森路口", "捷運中正紀念堂站(羅斯福)", "南昌家具街", 
                "捷運古亭站(和平)", "師大", "師大綜合大樓", "溫州街口", "大安森林公園", "龍門國中(和平)", "復興南路口", 
                "國立臺北教育大學", "大安健康服務中心", "臺大國青大樓", "自來水處(辛亥)", "青峰活動中心", "辛亥國小", 
                "捷運辛亥站", "捷運辛亥站一", "興隆路口(辛亥)", "中國科技大學(辛亥)", "懷恩隧道", "溝子口(幸福華興)", 
                "中港抽水站", "實踐國中", "木新區民活動中心", "木新市場", "力行國小", "國泰新村(木新)", "忠順廟", 
                "司法新村", "景文中學", "木南公園", "指南路口", "政大", "萬興圖書館", "大誠高中", "萬壽橋頭(秀明)", 
                "萬壽橋頭(新光)", "貓纜動物園站", "捷運動物園站", "萬福橋", "象頭埔", "富德"
            ]
        },
        "949": {
            "0": [ # To MRT Guting Station (往捷運古亭站)
                "石碇高中", "八分寮", "北深松柏街口", "僑新新村", "土庫", "賴仲坑", "翠谷山莊", "深美橋", "草地頭", 
                "變電所", "深坑國小", "深坑區公所", "深坑", "深坑郵局", "台新工廠", "東南科技大學", "萬順寮", "草地尾", 
                "富德里", "文和橋", "富德", "象頭埔", "萬福橋", "石壁坑", "風動石", "自來水處(辛亥)", "大安運動中心", 
                "臺大計資中心", "新民國小", "捷運台電大樓站", "羅斯福浦城街口", "羅斯福金門街口", "捷運古亭站(和平)", 
                "師大", "師大綜合大樓", "溫州街口", "大安森林公園", "龍門國中(辛亥路口)"
            ],
            "1": [ # To Shenkeng (往深坑)
                "臺大計資中心", "臺大國青大樓", "自來水處(辛亥)", "風動石", "石壁坑", "萬福橋", "象頭埔", "富德", "文和橋", 
                "富德里", "草地尾", "萬順寮", "東南科技大學", "台新工廠", "深坑郵局", "深坑", "深坑區公所", "深坑國小", 
                "變電所", "草地頭", "深美橋", "翠谷山莊", "賴仲坑", "土庫", "僑新新村", "北深松柏街口", "八分寮", "石碇高中"
            ]
        }
    }
    stop_names = all_stop_names.get(route_name, {}).get(str(selected_direction), [])

    # 取得 A2 取得 plate, routeuid, direction, stop_seq, BusPosition
    A2_url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/RealTimeNearStop/City/Taipei/{route_name}?%24"
    A2_resp = requests.get(A2_url, headers=headers)
    a2_data = A2_resp.json() if A2_resp.status_code == 200 else []

    # 從 A2 中提取每個站點的車牌號
    plate_dict = {}
    for item in a2_data:
        stop_name = item.get("StopName", {}).get("Zh_tw")
        api_direction = item.get("Direction")
        if stop_name and api_direction == selected_direction:
            plate = item.get("PlateNumb")
            if plate:
                if stop_name not in plate_dict:
                    plate_dict[stop_name] = []
                plate_dict[stop_name].append(plate)

    # 取得 A1 取得 speed
    A1_url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/RealTimeByFrequency/City/Taipei/{route_name}%24"
    A1_resp = requests.get(A1_url, headers=headers)
    a1_data = A1_resp.json() if A1_resp.status_code == 200 else []

    # 取得 N1 取得 EstimateTime
    N1_url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Taipei/{route_name}"
    N1_resp = requests.get(N1_url, headers=headers)
    n1_data = N1_resp.json() if N1_resp.status_code == 200 else []

    # 只抓一次天氣資料
    temp, wind, rain = get_weather_data(print_debug=True)

    # N1: stop_name, EstimateTime, N1_time
    n1_dict = {}
    for item in n1_data:
        stop_name = item.get("StopName", {}).get("Zh_tw")
        if stop_name:
            n1_dict[stop_name] = {
                "EstimateTime": item.get("EstimateTime"),
                "N1_time": item.get("UpdateTime", None)
            }

    # 組合回傳格式
    result = []
    now = time.localtime()
    hour = now.tm_hour
    minute = now.tm_min
    weekday = now.tm_wday  # 0=Monday
    peak = 1 if (7 <= hour < 9) or (17 <= hour < 19) else 0
    daytype = 0 if weekday in (5, 6) else 1

    for name in stop_names:
        minutes = None
        seconds = None
        wait = None
        
        # 使用預設特徵值
        plate_encoded = 0  # 默認值
        speed = 15.0  # 平均速度值
        distance = 0.0  # 默認距離
        rt_delay_sec = 0  # 默認延遲值
        
        # 取得官方預計時間
        estimate_time = n1_dict.get(name, {}).get("EstimateTime")
        
        # 準備特徵
        features = {
            "PlateNumb_encoded": plate_encoded,
            "Speed": speed,
            "Distance": distance,
            "rt_delay_sec": rt_delay_sec,
            "Hour": hour,
            "Minute": minute,
            "Weekday": weekday,
            "peak": peak,
            "daytype": daytype,
            "rain": rain,
            "temp": temp,
            "wind": wind
        }
        
        # 若 EstimateTime 有值，加入 features，否則不用
        use_modelA = estimate_time is not None
        if use_modelA:
            features["EstimateTime"] = estimate_time
            
        # 載入模型預測
        try:
            if use_modelA:
                model = load_model(route_name, "modelA")
                feature_order = ["PlateNumb_encoded", "Speed", "Distance", "rt_delay_sec", "Hour", "Minute", "Weekday", "peak", "daytype", "rain", "temp", "wind", "EstimateTime"]
            else:
                model = load_model(route_name, "modelB")
                feature_order = ["PlateNumb_encoded", "Speed", "Distance", "rt_delay_sec", "Hour", "Minute", "Weekday", "peak", "daytype", "rain", "temp", "wind"]
            X = np.array([[features[k] for k in feature_order]])
            wait = float(model.predict(X)[0])
            
            # 若模型預測成功，則計算分鐘和秒，否則維持 None
            if wait is not None:
                minutes = int(wait // 60)
                seconds = int(wait % 60)
        except Exception as e:
            print(f"[Model Predict Error] stop={name}, error={e}")
        
        # 獲取該站點的車牌（如果有）
        plates = plate_dict.get(name, [])
        
        # 與 bus.py 保持一致的回傳格式，但只包含模型預測結果
        result.append({
            "stop_name": name,
            "minutes": minutes,
            "seconds": seconds,
            "plate_numbers": plates,
            "wait": wait
        })

    return jsonify(result)

# 模型的預測邏輯
def get_weather_data(print_debug=True):
    # 氣象觀測 API
    weather_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001"
    rain_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001"
    params = {
        "Authorization": WEATHER_API_KEY,
        "format": "JSON"
    }
    # 取得氣象觀測資料
    try:
        weather_resp = requests.get(weather_url, params=params, timeout=3)
        weather_data = weather_resp.json()
        stations = weather_data["records"]["Station"]
        taipei_station = next((s for s in stations if "臺北" in s["StationName"]), None)
        temp = float(taipei_station["WeatherElement"]["AirTemperature"]) if taipei_station else 25.0
        wind = float(taipei_station["WeatherElement"]["WindSpeed"]) if taipei_station else 2.0
    except Exception:
        temp = 25.0
        wind = 2.0

    # 取得雨量資料
    try:
        rain_resp = requests.get(rain_url, params=params, timeout=3)
        rain_data = rain_resp.json()
        stations = rain_data["records"]["Station"]
        taipei_station = next((s for s in stations if "臺北" in s["StationName"]), None)
        rain = float(taipei_station["RainfallElement"]["Past10Min"]["Precipitation"]) if taipei_station else 0.0
    except Exception:
        rain = 0.0
    if print_debug:
        print(f"[Weather Debug] temp={temp}, wind={wind}, rain={rain}")  
    return temp, wind, rain

def predict_wait_time(data, weather=None):
    # 取得即時資料
    route_name = data.get("RouteName", "")
    stop_name = data.get("StopName", "")
    selected_direction = data.get("Direction", 0)
    city = "Taipei"  # 可根據實際需求調整
    access_token = get_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    # 從 A2 取得所有公車位置資料
    A2_url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/RealTimeNearStop/City/{city}/{route_name}?%24"
    try:
        A2_resp = requests.get(A2_url, headers=headers, timeout=5)
        a2_data = A2_resp.json() if A2_resp.status_code == 200 else []
    except Exception as e:
        print(f"[A2 API Error] {e}")
        a2_data = []

    # 獲取站牌座標
    stops_url = f"https://tdx.transportdata.tw/api/basic/V3/Map/Bus/Network/StopOfRoute/City/Taipei/RouteName/{route_name}"
    try:
        stops_resp = requests.get(stops_url, headers=headers, timeout=5)
        stops_data = stops_resp.json() if stops_resp.status_code == 200 else []
    except Exception as e:
        print(f"[Stops API Error] {e}")
        stops_data = []

    # 找到目標站牌的座標
    target_lat = None
    target_lon = None
    if stops_data:
        for stop_route in stops_data.get("StopOfRoutes", []):
            for stop in stop_route.get("Stops", []):
                if stop.get("StopName", {}).get("Zh_tw") == stop_name and stop_route.get("Direction") == selected_direction:
                    target_lat = stop.get("StopPosition", {}).get("PositionLat")
                    target_lon = stop.get("StopPosition", {}).get("PositionLon")
                    break
    
    # 取得指定站牌的相關公車
    station_buses = []
    for item in a2_data:
        if (item.get("Direction") == selected_direction and 
            item.get("StopName", {}).get("Zh_tw") == stop_name):
            station_buses.append(item)

    # 從 A1 取得所有公車速度資料
    A1_url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/RealTimeByFrequency/City/{city}/{route_name}%24"
    try:
        A1_resp = requests.get(A1_url, headers=headers, timeout=5)
        a1_data = A1_resp.json() if A1_resp.status_code == 200 else []
    except Exception as e:
        print(f"[A1 API Error] {e}")
        a1_data = []

    # 從 N1 取得估計到站時間
    N1_url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/{city}/{route_name}"
    try:
        N1_resp = requests.get(N1_url, headers=headers, timeout=5)
        n1_data = N1_resp.json() if N1_resp.status_code == 200 else []
    except Exception as e:
        print(f"[N1 API Error] {e}")
        n1_data = []
    
    # 找到目標站牌的估計時間
    estimate_time = None
    n1_time = None
    for item in n1_data:
        if (item.get("Direction") == selected_direction and 
            item.get("StopName", {}).get("Zh_tw") == stop_name):
            estimate_time = item.get("EstimateTime")
            n1_time = item.get("UpdateTime", None)
            break

    # 若沒有站牌資料或沒有公車接近此站
    if not station_buses:
        # 建立速度字典
        speed_dict = {}
        for item in a1_data:
            plate = item.get("PlateNumb")
            if plate:
                speed_dict[plate] = item.get("Speed", 0)
        
        # 找到最接近該站的車輛
        closest_bus = None
        min_distance = float('inf')
        for item in a2_data:
            if item.get("Direction") == selected_direction:
                # 取得車輛順序與站牌順序，計算距離
                bus_seq = item.get("StopSequence", 0)
                
                # 從 N1 找到目標站牌的順序
                target_seq = 0
                for n1_item in n1_data:
                    if (n1_item.get("Direction") == selected_direction and 
                        n1_item.get("StopName", {}).get("Zh_tw") == stop_name):
                        target_seq = n1_item.get("StopSequence", 0)
                        break
                
                if bus_seq and target_seq:
                    seq_distance = target_seq - bus_seq
                    if seq_distance > 0 and seq_distance < min_distance:
                        min_distance = seq_distance
                        closest_bus = item
        
        if closest_bus:
            plate = closest_bus.get("PlateNumb", "")
            speed = speed_dict.get(plate, 15.0)
            
            # 使用geodesic計算實際距離
            bus_pos = closest_bus.get("BusPosition", {})
            bus_lat = bus_pos.get("PositionLat")
            bus_lon = bus_pos.get("PositionLon")
            if target_lat is not None and target_lon is not None and bus_lat is not None and bus_lon is not None:
                distance = geodesic((bus_lat, bus_lon), (target_lat, target_lon)).kilometers
            else:
                # 使用站牌間平均距離*站點數估算實際距離 (km)
                distance = min_distance * 0.5
            a2_time = closest_bus.get("UpdateTime", None)
        else:
            plate = ""
            speed = 15.0
            distance = 0.0
            a2_time = None
    else:
        # 有車輛接近此站，使用最近車輛資料
        closest_bus = station_buses[0]
        plate = closest_bus.get("PlateNumb", "")
        
        # 從 A1 獲取該車輛速度
        speed = 0
        for item in a1_data:
            if item.get("PlateNumb") == plate:
                speed = item.get("Speed", 0)
                break
                
        bus_pos = closest_bus.get("BusPosition", {})
        bus_lat = bus_pos.get("PositionLat")
        bus_lon = bus_pos.get("PositionLon")
        distance = 0.1  # 預設100公尺
        if target_lat is not None and target_lon is not None and bus_lat is not None and bus_lon is not None:
            distance = geodesic((bus_lat, bus_lon), (target_lat, target_lon)).kilometers
        a2_time = closest_bus.get("UpdateTime", None)

    # PlateNumb_encoded
    plate_encoded = encode_plate(plate)
    
    # rt_delay_sec
    rt_delay_sec = 0
    try:
        if a2_time and n1_time:
            t1 = time.mktime(time.strptime(a2_time, "%Y-%m-%dT%H:%M:%S+08:00"))
            t2 = time.mktime(time.strptime(n1_time, "%Y-%m-%dT%H:%M:%S+08:00"))
            rt_delay_sec = abs(int(t1 - t2))
    except Exception:
        rt_delay_sec = 0

    now = time.localtime()
    hour = now.tm_hour
    minute = now.tm_min
    weekday = now.tm_wday
    peak = 1 if (7 <= hour < 9) or (17 <= hour < 19) else 0
    daytype = 0 if weekday in (5, 6) else 1

    # 天氣
    if weather:
        temp, wind, rain = weather
    else:
        temp, wind, rain = get_weather_data(print_debug=False)

    # 使用實際特徵值建立預測特徵
    features = {
        "PlateNumb_encoded": plate_encoded, # 車牌
        "Speed": speed if speed > 0 else 15.0, # 速度（若為 0 則使用預設值）
        "Distance": distance, # 與站點距離
        "rt_delay_sec": rt_delay_sec, # API 延遲時間
        "Hour": hour, # 當前小時
        "Minute": minute, # 當前分鐘
        "Weekday": weekday, # 當前星期
        "peak": peak, # 是否尖峰時段
        "daytype": daytype, # 當前日期類型
        "rain": rain, # 當前降雨量
        "temp": temp, # 當前溫度
        "wind": wind # 當前風速
    }
    use_modelA = estimate_time is not None
    if use_modelA:
        features["EstimateTime"] = estimate_time

    try:
        if use_modelA:
            model = load_model(route_name, "modelA")
            feature_order = ["PlateNumb_encoded", "Speed", "Distance", "rt_delay_sec", "Hour", "Minute", "Weekday", "peak", "daytype", "rain", "temp", "wind", "EstimateTime"]
        else:
            model = load_model(route_name, "modelB")
            feature_order = ["PlateNumb_encoded", "Speed", "Distance", "rt_delay_sec", "Hour", "Minute", "Weekday", "peak", "daytype", "rain", "temp", "wind"]
        X = np.array([[features[k] for k in feature_order]]) # 根據特徵順序建立輸入矩陣
        wait = float(model.predict(X)[0])
    except Exception as e:
        wait = None

    return round(wait, 3) if wait is not None else None


# 模型快取，避免重複載入
_model_cache = {}

# 路線名稱對應模型檔案名稱
ROUTE_MODEL_MAP = {
    "0南": "r0south",
    "278": "r278",
    "295": "r295",
    "949": "r949"
}

def load_model(route_name, model_type):
    # 將 route_name 轉換為模型檔案名稱
    model_route = ROUTE_MODEL_MAP.get(route_name) # 使用 ROUTE_MODEL_MAP 字典將使用者可讀的路線名稱轉換為標準化的模型檔案前綴
    if not model_route:
        raise FileNotFoundError(f"Unsupported route_name: {route_name}")
    key = f"{model_route}_{model_type}" # 生成唯一的快取鍵
    if key in _model_cache: # 檢查模型是否已在記憶體快取中
        return _model_cache[key]
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', f"{model_route}_xgb_{model_type}.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, "rb") as f: # 模型載入與序列化處理
        model = pickle.load(f)
    _model_cache[key] = model # 快取更新與返回
    return model

def encode_plate(plate):
    # 建立一個簡單的編碼器，機器學習模型無法直接處理文字資料
    # 保留車牌的唯一性，同時讓模型能處理該特徵
    # 這裡直接用 hash 取絕對值再模 10000
    return abs(hash(plate)) % 10000 if plate else 0

# 啟動伺服器
if __name__ == '__main__':
    model_bp.run(debug=True)