from flask import Flask, jsonify, render_template, request,Blueprint
from flask import session, g
from flask import current_app as app
import requests
import time
import sqlite3

from .config import CLIENT_ID, CLIENT_SECRET

bus_bp = Blueprint('bus', __name__)

# route
@bus_bp.route('/0south')
def zero_south():
    return render_template('0south.html')

@bus_bp.route('/18')
def one_eight():
    return render_template('18.html')

@bus_bp.route('/278')
def two_seven_eight():
    return render_template('278.html')

@bus_bp.route('/295')
def two_nine_five():
    return render_template('295.html')

@bus_bp.route('/949')
def nine_four_nine():
    return render_template('949.html')

@bus_bp.route('/heping')
def heping():
    return render_template('heping.html')

@bus_bp.route('/fuxing')
def fuxing():
    return render_template('fuxing.html')

@bus_bp.route('/235')
def two_three_five():
    return render_template('235.html')

@bus_bp.route('/237')
def two_three_seven():
    return render_template('237.html')

@bus_bp.route('/254')
def two_five_four():
    return render_template('254.html')

@bus_bp.route('/568')
def five_six_eight():
    return render_template('568.html')

@bus_bp.route('/663')
def six_six_three():
    return render_template('663.html')

@bus_bp.route('/672')
def six_seven_two():
    return render_template('672.html')

@bus_bp.route('/907')
def nine_zero_seven():
    return render_template('907.html')

# ====== 將 all_stop_names 提升為全域變數 ======
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
    "18": {
        "0": [ # To MRT Linguang Station (往捷運麟光站)
            "華江站", "人壽一村", "大理高中", "華江派出所", "龍山國小", "萬華分局", "桂林路", "昆明活動中心", "內江街", 
            "西門市場(漢中)", "寶慶路", "博愛路", "臺北郵局", "臺北車站(忠孝)", "臺大醫院", "捷運中正紀念堂站(中山)", 
            "捷運中正紀念堂站(勞保局)", "自來水西分處(寧波)", "聯合醫院婦幼院區一", "南昌家具街", "捷運古亭站(和平)", 
            "師大", "師大綜合大樓", "溫州街口", "大安森林公園", "龍門國中(和平)", "復興南路口", "國立臺北教育大學", 
            "臥龍街", "和平安和路口", "捷運六張犁站(和平)", "富陽街口", "黎忠市場", "捷運麟光站"
        ],
        "1": [ # To Wanhua (往萬華)
            "黎忠市場", "富陽街口", "捷運六張犁站(和平)", "和平安和路口", "臥龍街", "國立臺北教育大學", "復興南路口", 
            "國北教大實小", "龍門國中(和平)", "大安森林公園", "溫州街口", "師大綜合大樓", "師大", "捷運古亭站(和平)", 
            "羅斯福潮州街口", "捷運中正紀念堂站(羅斯福)", "一女中(公園)", "捷運台大醫院站", "博物館(館前)", 
            "臺北車站(開封)", "重慶南路一段", "二二八和平公園", "衡陽路", "西門市場(成都)", "西寧南路", "桂林昆明街口", 
            "桂林路", "萬華分局", "龍山國小", "華江派出所", "力霸社區", "華江站"
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
    },
    "和平幹線": {
        "0": [ # To Hengyang Rd (往衡陽路)
            "萬芳社區", "萬芳活動中心", "萬芳派出所", "公務人員訓練處", "萬美社區", "萬芳國宅", "萬寧街", "萬寧山莊", 
            "名門社區", "臥龍新村", "大我新舍", "麟光站", "黎忠市場", "富陽街口", "捷運六張犁站(和平)", "和平安和路口", 
            "臥龍街", "國立臺北教育大學", "復興南路口", "國北教大實小", "龍門國中(和平)", "大安森林公園", "溫州街口",
            "師大綜合大樓", "師大", "捷運古亭站(和平)", "羅斯福潮州街口", "捷運中正紀念堂站(羅斯福)", "捷運中正紀念堂站", 
            "景福門", "臺大醫院", "臺北車站(忠孝)", "重慶南路一段", "二二八和平公園"
        ],
        "1": [ # To Wanshang Community (往萬芳社區)
            "博愛路", "臺北郵局", "臺北車站(忠孝)", "捷運善導寺站", "開南中學", "仁愛林森路口", "捷運中正紀念堂站(羅斯福)", 
            "南昌家具街", "捷運古亭站(和平)", "師大", "師大綜合大樓", "溫州街口", "大安森林公園", "龍門國中(和平)", 
            "復興南路口", "國立臺北教育大學", "臥龍街", "和平安和路口", "捷運六張犁站(和平)", "富陽街口", "黎忠市場", "捷運麟光站",
            "麟光站", "大我新舍", "臥龍新村", "名門社區", "萬寧山莊", "萬寧街", "萬芳國宅", "萬美社區", "公務人員訓練處", 
            "萬芳派出所", "萬芳活動中心", "萬芳社區"
        ]
    },
    "復興幹線": {
        "0": [ # To Jingmei (往景美)
            "建北站", "臺北漁市", "第二果菜市場", "下埤里", "復興北村", "五常街口", "捷運中山國中站", "興安華城", 
            "捷運南京復興站", "芝麻大廈", "復興南路(埤頭里)", "捷運忠孝復興站", "懷生國中", "聯合醫院仁愛院區", 
            "東豐復興路口", "大安高工(捷運大安站)", "開平餐飲學校", "捷運科技大樓站", "復興南路口", "國北教大實小",
            "龍門國中(和平)", "大安森林公園", "溫州街口", "師大綜合大樓", "師大", "捷運古亭站(和平)", "羅斯福金門街口",
            "羅斯福浦城街口", "捷運台電大樓站", "台電大樓", "捷運公館站", "師大分部", "武功國小(興隆)", "景明街口",
            "憲光公寓", "景興國中", "景華公園"
        ],
        "1": [ # To Jianguo N. Rd (往建國北路)
            "景美國中", "財政園區", "萬隆", "捷運萬隆站", "武功國小(羅斯福)", "師大分部", "捷運公館站", "台電大樓", 
            "捷運台電大樓站", "師大路", "師大", "師大綜合大樓", "溫州街口", "大安森林公園", "龍門國中(和平)", 
            "復興南路口", "捷運科技大樓站", "開平餐飲學校", "大安高工(捷運大安站)", "捷運大安站(復興)","東豐復興路口", "聯合醫院仁愛院區", 
            "捷運忠孝復興站", "復興南路(中崙里)", "芝麻大廈", "捷運南京復興站", "興安華城", "民生東路口", "捷運中山國中站", 
            "民權龍江路口", "民權建國路口", "行天宮", "新生公園(林安泰)", "建北站"
        ]
    },
    "235": {
        "0": [ # To National Dr. Sun Yat-sen Memorial Hall (往國父紀念館)
            "西盛", "東方之星", "西盛館", "家麒新天地", "正豐", "大唐江山", "民安西路403巷口", "光華街口", "新寶社區",
            "光明里", "光華國小(民安西路)", "福祿新城一", "福祿新城二", "民安陸橋", "民安路", "後港社區", "建福路口",
            "宏泰社區", "三洋","營盤口", "捷運輔大站", "盲人重建院", "海山里", "新泰路口", "捷運新莊站(新莊郵局)",
            "新莊國小", "保元宮", "捷運頭前庄站", "頭前", "金陵女中", "中興街口", "捷運先嗇宮站", "五谷王廟", "重新大橋",
            "西門國小(臺大醫院北護分院)", "臺北護理健康大學", "內江街", "西門市場(漢中)", "臺北市憲兵隊", "東吳大學城中校區",
            "一女中(貴陽)", "一女中(公園)", "市立大學附小", "南門", "自來水西分處(寧波)", "聯合醫院婦幼院區一", "南昌家具街", 
            "捷運古亭站(和平)", "師大", "師大綜合大樓","溫州街口", "大安森林公園", "龍門國中(和平)", "復興南路口", 
            "國立臺北教育大學", "臥龍街", "全安里", "立人國際國中小學","文昌街口", "捷運信義安和站(安和)", "仁愛國中", 
            "敦化安和路口", "捷運忠孝敦化站", "阿波羅大廈", "交通部觀光署"
        ],
        "1": [ # To Xinzhuang (往新莊)
            "國父紀念館", "仁愛延吉街口", "仁愛國泰醫院", "仁愛安和路口", "仁愛安和路口", "仁愛國小", "捷運信義安和站(安和)",
            "文昌街口", "立人國際國中小學", "全安里", "安和路口", "臥龍街", "國立臺北教育大學", "復興南路口", "國北教大實小",
            "龍門國中(和平)", "大安森林公園", "溫州街口", "師大綜合大樓", "師大", "捷運古亭站(和平)", "南昌家具街",
            "聯合醫院婦幼院區一", "南昌路", "南門", "一女中(公園)", "一女中(貴陽)","衡陽路", "西門市場(成都)", "西門國小",
            "重新大橋", "五谷王廟", "捷運先嗇宮站", "中興街口", "金陵女中", "頭前", "捷運頭前庄站", "大眾廟","捷運新莊站(新莊郵局)",
            "新泰路口", "海山里", "盲人重建院", "捷運輔大站", "營盤口", "三洋(建福路)", "宏泰社區", "建福路口", "後港社區",
            "民安路", "民安陸橋", "福祿新城二", "福祿新城一", "光華國小(民安西路)", "光明里", "新寶社區",
            "光華街口", "民安西路403巷口", "大唐江山", "正豐", "西盛一", "家麒新天地", "西盛館", "東方之星", "西盛"
        ]
    },
    "237": {
        "0": [ # To MRT Dongmen Station (往捷運東門站)
            "富德", "象頭埔", "萬福橋", "捷運動物園站", "貓纜動物園站", "萬壽橋頭(新光)", "萬壽橋頭(秀明)", "萬興國小", 
            "政大一", "政大圖書館", "環山網球場", "六期運動場", "研創中心", "大草坪(自強宿舍)", "好漢坡", "大草坪(自強宿舍)", 
            "研創中心", "六期運動場", "環山網球場", "政大圖書館", "萬興圖書館", "大誠高中", "萬壽橋頭(秀明)", "萬壽橋頭(木柵)",
            "文山行政中心", "木柵市場", "景文中學(臺灣戲曲學院)", "司法新村", "忠順廟", "國泰新村(興隆)", "忠順街口", "木柵公園", 
            "馬明潭(再興中學)", "興隆山莊", "海巡署一", "海巡署", "文山運動中心(興隆)", "臺灣警察專科學校", "捷運萬芳醫院站",
            "中國科技大學(辛亥)", "興隆路口(辛亥)", "捷運辛亥站", "辛亥國小", "青峰活動中心", "自來水處(辛亥)",
            "大安運動中心", "大安健康服務中心", "復興南路口", "國北教大實小", "龍門國中(和平)", "大安森林公園",
            "溫州街口", "師大綜合大樓", "師大", "捷運古亭站(和平)", "捷運古亭站(杭州)", "潮州街口", "愛國東路口", "金甌女中",
            "捷運東門站(金山)"
        ],
        "1": [ # To Fude (往富德)
            "公企中心", "金山潮州街口", "師大", "師大綜合大樓", "溫州街口", "大安森林公園", "龍門國中(和平)", "復興南路口", 
            "國立臺北教育大學", "大安健康服務中心", "臺大國青大樓", "自來水處(辛亥)", "青峰活動中心", "臺北市懷愛館", 
            "辛亥國小", "捷運辛亥站", "捷運辛亥站一", "興隆路口(辛亥)", "捷運萬芳醫院站", "臺灣警察專科學校",
            "文山運動中心(興隆)", "海巡署", "海巡署一", "興隆山莊", "馬明潭(再興中學)", "木柵公園", "忠順街口", "國泰新村(興隆)",
            "忠順廟", "司法新村", "景文中學(臺灣戲曲學院)", "木柵市場", "文山行政中心", "萬壽橋頭(木柵)", "萬壽橋頭(秀明)",
            "萬興國小", "政大一", "萬興圖書館", "大誠高中", "萬壽橋頭(秀明)", "萬壽橋頭(新光)", "貓纜動物園站",
            "捷運動物園站", "萬福橋", "象頭埔", "富德"
        ]
    },
    "254": {
        "0": [ # To Minsheng Community (往民生社區)
            "中正環河路口", "捷運秀朗橋站", "尖山腳", "景平路景德街口", "捷運景平站", "東森廣場", "智光商職", "中興二村", 
            "中興新村", "得和路", "秀朗國小", "永元路", "福和橋(永元路)", "公館", "臺灣科技大學", "臺大癌醫(基隆路)", 
            "基隆長興街口", "和平高中", "捷運六張犁站(基隆路)", "喬治商職", "三興國小(臨江街觀光夜市)", "光復南路口",
            "三張犁", "市民住宅", "國父紀念館", "捷運國父紀念館站(光復)", "臺北市區監理所(光復)", "榮民服務處",
            "南京新村", "三軍總醫院松山分院", "長壽公園", "健康新城", "三民健康路口(西松高中)","三民路", "民生社區活動中心"
        ],
        "1": [ # To Da Peng New Village (往大鵬新村)
            "聯合二村", "介壽國中", "公教住宅", "富錦街口", "松山機場", "民生敦化路口", "長春敦化路口", "臺北小巨蛋", 
            "捷運南京復興站", "南京龍江路口", "南京建國路口", "捷運松江南京站", "長安松江路口", "光華商場", 
            "捷運忠孝新生站", "仁愛新生路口", "信義新生路口", "金華新生路口", "溫州街口", "師大綜合大樓", "師大",
            "捷運古亭站(和平)", "羅斯福金門街口", "羅斯福浦城街口", "捷運台電大樓站", "台電大樓",
            "捷運公館站", "福和橋(林森路)", "永元路", "秀朗國小", "得和路", "中興新村", "中興二村",
            "智光商職", "南勢角(景平路)", "捷運景平站", "景平路景德街口", "捷運秀朗橋站", "中正環河路口"
        ]
    },
    "568": {
        "0": [ # To MRT Linguang Station (往捷運麟光站)
            "華江站", "人壽一村", "大理高中", "華江派出所", "中國時報", "捷運龍山寺站", "昆明街口", "和平中華路口", 
            "植物園", "龍口市場", "泉州街", "和平西路一段", "南福板溪(南昌公園)", "捷運古亭站(和平)", "師大", "師大綜合大樓", 
            "溫州街口", "大安森林公園", "龍門國中(和平)", "復興南路口", "國立臺北教育大學", "臥龍街", "和平安和路口", 
            "捷運六張犁站(和平)", "富陽街口", "黎忠市場", "捷運麟光站"
        ],
        "1": [ # To Wanhua (往萬華)
            "捷運麟光站", "黎忠市場", "富陽街口", "捷運六張犁站(和平)", "和平安和路口", "臥龍街", "國立臺北教育大學", 
            "復興南路口", "國北教大實小", "龍門國中(和平)", "大安森林公園", "溫州街口", "師大綜合大樓", "師大", 
            "捷運古亭站(和平)", "南福板溪(南昌公園)", "和平西路一段", "泉州街", "龍口市場", "植物園", "和平中華路口",
            "昆明街口", "捷運龍山寺站", "中國時報", "華江派出所", "大理高中", "人壽一村", "華江站"
        ]
    },
    "663": {
        "0": [ # To National Dr. Sun Yat-sen Memorial Hall (往國父紀念館)
            "民安站", "民安國小", "福祿新城二", "福祿新城一", "光華國小(龍安路)", "龍安大第", "萬安公園", "裕民國小","丹鳳高中",
            "中正龍安路口", "丹鳳國小", "雙鳳富國路口", "捷運丹鳳站", "三洋", "營盤口", "捷運輔大站", "盲人重建院", "海山里",
            "新泰路口", "捷運新莊站(新莊郵局)", "新莊國小", "保元宮", "捷運頭前庄站", "頭前", "金陵女中", "中興街口",
            "捷運先嗇宮站", "五谷王廟", "重新大橋", "祖師廟(貴陽)", "貴陽街", "東吳大學城中校區", "一女中(貴陽)", "一女中(公園)",
            "市立大學附小", "南門", "自來水西分處(寧波)", "聯合醫院婦幼院區一", "南昌家具街", "捷運古亭站(和平)", "師大", "師大綜合大樓",
            "溫州街口", "大安森林公園", "龍門國中(和平)", "復興南路口", "國立臺北教育大學", "臥龍街", "全安里", "立人國際國中小學",
            "文昌街口", "捷運信義安和站(安和)", "仁愛國中", "敦化安和路口", "捷運忠孝敦化站", "阿波羅大廈", "交通部觀光署"
        ], 
        "1": [ # To Xinzhuang (往新莊)
            "國父紀念館", "仁愛延吉街口", "仁愛國泰醫院", "仁愛安和路口", "仁愛安和路口", "仁愛國小", "捷運信義安和站(安和)",
            "文昌街口", "立人國際國中小學", "全安里", "安和路口", "臥龍街", "國立臺北教育大學", "復興南路口", "國北教大實小",
            "龍門國中(和平)", "大安森林公園", "溫州街口", "師大綜合大樓", "師大", "捷運古亭站(和平)", "南昌家具街",
            "聯合醫院婦幼院區一", "南昌路", "南門", "一女中(公園)", "一女中(貴陽)","衡陽路", "西門市場(成都)", "西門國小",
            "重新大橋", "五谷王廟", "捷運先嗇宮站", "中興街口", "金陵女中", "頭前", "捷運頭前庄站", "大眾廟","捷運新莊站(新莊郵局)",
            "新泰路口", "海山里", "盲人重建院", "捷運輔大站", "營盤口", "三洋", "捷運丹鳳站", "雙鳳富國路口", "丹鳳國小",
            "中正龍安路口", "丹鳳高中", "裕民國小", "萬安公園", "龍安大第", "光華國小(龍安路)", "福祿新城一", "福祿新城二",
            "民安國小", "民安站"
        ]
    },
    "672": {
        "0": [ # To Minsheng Community (往民生社區)
            "中正環河路口", "捷運秀朗橋站", "尖山腳", "景平路景德街口", "捷運景平站", "東森廣場", "智光商職", "中興二村", 
            "中興新村", "得和路", "秀朗國小", "永元路", "福和橋(永元路)", "捷運公館站", "台電大樓", "捷運台電大樓站", 
            "羅斯福浦城街口", "羅斯福金門街口", "捷運古亭站(和平)", "師大", "師大綜合大樓", "溫州街口",
            "金華新生路口", "信義新生路口", "仁愛新生路口", "捷運忠孝新生站", "光華商場", "長安松江路口",
            "長安東路二段", "南京建國路口", "南京龍江路口", "捷運南京復興站", "南京敦化路口(小巨蛋)", "臺北小巨蛋", 
            "長庚醫院", "公教住宅", "介壽國中", "聯合二村", "民生社區活動中心"
        ],
        "1": [ # To Da Peng New Village (往大鵬新村)
            "三民路", "三民健康路口(西松高中)", "健康新城", "長壽公園", "三軍總醫院松山分院", "南京新村", "博仁醫院",
            "臺北市區監理所(光復)", "捷運國父紀念館站(光復)","國父紀念館","市民住宅", "三張犁", "光復南路口", "三興國小(臨江街觀光夜市)",
            "喬治商職", "捷運六張犁站(基隆路)", "和平高中", "基隆長興路口", "臺大癌醫(基隆路)", "臺灣科技大學",
            "公館", "福和橋(林森路)", "永元路", "秀朗國小", "得和路", "中興新村", "中興二村", "智光商職", "南勢角(景平路)",
            "捷運景平站", "景平路景德街口", "捷運秀朗橋站", "中正環河路口"
        ]
    },
    "907": {
        "0": [ #Trung Yi High School (往崇義高中)
            "華江站", "人壽一村", "大理高中", "華江派出所", "中國時報", "捷運龍山寺站", "昆明街口", "和平中華路口",
            "植物園", "龍口市場", "泉州街", "和平西路一段", "南福板溪(南昌公園)", "捷運古亭站(和平)", "師大", "師大綜合大樓",
            "溫州街口", "龍安國小(公務人力發展學院)", "臺大綜合體育館", "臺大", "捷運公館站", "公館", "臺灣科技大學", 
            "臺大癌醫(基隆路)", "基隆長興街口", "自來水處(辛亥)", "遠東世界中心", "東方科學園區", "連興街口", "汐止農會", 
            "汐止行政中心", "秀峰高中(忠孝東路)", "汐止後車站", "摩登家庭社區", "橋東", "崇義高中(忠孝東路)"
        ],
        "1": [ # To Wanhua (往萬華)
            "崇義高中(忠孝東路)", "橋東", "摩登家庭社區", "汐止後車站", "秀峰高中(忠孝東路)", "汐止行政中心", "汐止農會",
            "連興街口", "東方科學園區", "遠東世界中心", "自來水處(辛亥)", "基隆長興街口", "臺大癌醫(基隆路)",
            "臺灣科技大學", "公館", "捷運公館站", "臺大", "臺大綜合體育館", "溫州街口","師大", "師大綜合大樓", 
            "捷運古亭站(和平)", "南福板溪(南昌公園)", "和平西路一段", "泉州街", "龍口市場", "植物園", "和平中華路口",
            "昆明街口", "捷運龍山寺站", "中國時報", "華江派出所", "大理高中", "人壽一村", "華江站"
        ]
    }
}

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
@bus_bp.route('/api/eta')
def eta():
    route_name = request.args.get('route', '0南') 
    selected_direction = int(request.args.get('direction', '0')) # Default to direction 0
    access_token = get_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # API URLs - now dynamic based on route_name
    # Note: TDX API uses route name directly, direction is handled by filtering response
    N1 = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Taipei/{route_name}"
    A2 = f"https://tdx.transportdata.tw/api/basic/v2/Bus/RealTimeNearStop/City/Taipei/{route_name}?%24"

    # 這裡直接使用全域 all_stop_names
    route_stops_data = all_stop_names.get(route_name)
    if not route_stops_data:
        return jsonify({"error": "Route not found"}), 404
    
    stop_names = route_stops_data.get(str(selected_direction), [])
    if not stop_names:
        return jsonify({"error": f"Direction {selected_direction} not found for route {route_name}"}), 404

    # 查詢 ETA
    response_n1 = requests.get(N1, headers=headers)
    data_n1 = response_n1.json() if response_n1.status_code == 200 else []
    eta_dict = {}
    for item in data_n1:
        stop_name = item['StopName']['Zh_tw']
        api_direction = item.get('Direction') 
        if api_direction == selected_direction and stop_name in stop_names: 
            estimate = item.get('EstimateTime')
            if estimate is not None:
                eta_dict[stop_name] = {
                    "minutes": estimate // 60,
                    "seconds": estimate % 60
                }
            else:
                eta_dict[stop_name] = {"minutes": None, "seconds": None}

    # 查詢 PlateNumb 公車車牌
    response_a2 = requests.get(A2, headers=headers)
    data_a2 = response_a2.json() if response_a2.status_code == 200 else []
    plate_dict = {}
    for item in data_a2:
        stop_name = item['StopName']['Zh_tw']
        api_direction = item.get('Direction')
        if api_direction == selected_direction and stop_name in stop_names:
            plate = item.get('PlateNumb')
            if plate:
                if stop_name not in plate_dict:
                    plate_dict[stop_name] = []
                plate_dict[stop_name].append(plate)

    # 站牌狀態代碼字典
    status_dict = {}
    for item in data_n1:
        stop_name = item['StopName']['Zh_tw']
        api_direction = item.get('Direction') 
        if api_direction == selected_direction and stop_name in stop_names:
            status_dict[stop_name] = item.get('StopStatus')

    # 組合結果
    result = []
    for name in stop_names:
        eta_info = eta_dict.get(name, {"minutes": None, "seconds": None})
        plates = plate_dict.get(name, [])
        status_code = status_dict.get(name, 0)  # 預設為0(正常)
        
        # 狀態代碼對應的說明
        status_text = {
            0: '正常',
            1: '尚未發車',
            2: '交管不停靠',
            3: '末班車已過', 
            4: '今日未營運'
        }.get(status_code, '未知狀態')
        
        result.append({
            "stop_name": name,
            "minutes": eta_info["minutes"],
            "seconds": eta_info["seconds"],
            "plate_numbers": plates,
            "stop_status": status_code,
            "stop_status_text": status_text
        })

    return jsonify(result)

# favorites
_eta_cache = {}  # (route, direction): {'data': ..., 'ts': ...}

@bus_bp.route('/favorites')
def favorites():
    return render_template('favorites.html', all_stop_names=all_stop_names)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('user.db')
        db.row_factory = sqlite3.Row
    return db

@bus_bp.route('/favorites/add', methods=['POST'])
def add_favorite():
    data = request.get_json()
    user_id = session.get('user_id', 1)
    db = get_db()
    # 檢查是否已收藏過同一站牌
    cur = db.execute(
        'SELECT COUNT(*) FROM favorites WHERE user_id=? AND route=? AND direction=? AND stop_name=?',
        (user_id, data['route'], data['direction'], data['stop_name'])
    )
    exists = cur.fetchone()[0]
    if exists:
        return jsonify({'success': False, 'error': '此站牌已在收藏清單中'})
    # 檢查數量上限
    cur = db.execute('SELECT COUNT(*) FROM favorites WHERE user_id=?', (user_id,))
    count = cur.fetchone()[0]
    if count >= 5:
        return jsonify({'success': False, 'error': '最多只能收藏五個站牌'})
    db.execute('INSERT INTO favorites (user_id, route, direction, stop_name) VALUES (?, ?, ?, ?)',
               (user_id, data['route'], data['direction'], data['stop_name']))
    db.commit()
    return jsonify({'success': True})

@bus_bp.route('/favorites/list')
def list_favorites():
    user_id = session.get('user_id', 1)
    db = get_db()
    cur = db.execute('SELECT route, direction, stop_name FROM favorites WHERE user_id=?', (user_id,))
    favs = cur.fetchall()
    fav_list = [dict(route=f['route'], direction=f['direction'], stop_name=f['stop_name']) for f in favs]

    # 1. 找出所有 route/direction 組合
    route_dir_set = set((f['route'], f['direction']) for f in fav_list)
    eta_map = {}
    now = time.time()

    # 2. 批次查詢 ETA，30 秒內同組不重查
    for route, direction in route_dir_set:
        cache_key = (route, direction)
        cache = _eta_cache.get(cache_key)
        if cache and now - cache['ts'] < 30:
            eta_map[cache_key] = cache['data']
        else:
            try:
                r = requests.get(f"{request.url_root}bus/api/eta?route={route}&direction={direction}")
                if r.status_code == 200:
                    eta_map[cache_key] = r.json()
                    _eta_cache[cache_key] = {'data': eta_map[cache_key], 'ts': now}
                else:
                    eta_map[cache_key] = []
            except Exception:
                eta_map[cache_key] = []

    # 3. 填入每個收藏的 ETA
    result = []
    for fav in fav_list:
        eta_list = eta_map.get((fav['route'], fav['direction']), [])
        eta = None
        for s in eta_list:
            if s['stop_name'] == fav['stop_name']:
                eta = s['minutes']
                break
        result.append({
            'route': fav['route'],
            'direction': fav['direction'],
            'stop': fav['stop_name'],
            'eta': eta
        })
    return jsonify(result)

@bus_bp.route('/favorites/delete', methods=['POST'])
def delete_favorite():
    data = request.get_json()
    user_id = session.get('user_id', 1)
    db = get_db()
    db.execute(
        'DELETE FROM favorites WHERE user_id=? AND route=? AND direction=? AND stop_name=?',
        (user_id, data['route'], data['direction'], data['stop_name'])
    )
    db.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    bus_bp.run(debug=True)

