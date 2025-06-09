# 坐坐巴 SitsitBus

## 專案簡介
坐坐巴是一個以 Flask 為後端框架、結合多種前端技術的公車到站時間預測平台。平台整合即時公車動態、公車到站時刻模型、使用者個人化收藏等功能，協助民眾在通勤時更精準掌握公車動態，減少等待誤差，提升搭乘效率。

## 特色功能
- **TDX 公車即時動態**：整合台北市公車即時動態資料，提供即時到站預測。
- **即時公車到站預測模型**：結合尖峰/離峰、天氣等多重因素，提供更貼近實際的預估到站時間。
- **多路線查詢**：支援多條台北市公車路線，動態顯示路線圖與站牌資訊。
- **個人化收藏**：可收藏常用路線與站牌，快速查詢預估到站時間。
- **獨家公車造型**：提供可愛的公車造型，增添使用樂趣。
- **會員登入/註冊**：提供帳號註冊與登入。

## 技術架構
- **後端**：Python 3, Flask, Blueprint 模組化
- **前端**：HTML5, CSS3, JavaScript
- **資料來源**：TDX 平台即時公車資料
- **模板引擎**：Jinja2
- **使用者認證**：Flask session/cookie
- **靜態資源**：自訂 CSS、圖片、字型等

## 專案結構
```
web/
├── blueprints/         # Flask blueprint 模組（bus, login, model, skin）
│   └── config.py       # 公車以及天氣 API 金鑰設定（需自行建立與填入個人資料）
├── data/               # 資料相關程式碼
├── models_code/        # 機器學習模型程式碼
├── models/             # 機器學習模型檔案（.pkl）
├── static/             # 靜態資源（js, css, 圖片等）
│   └── skins/          # 公車造型相關資源
├── templates/          # 前端 HTML 頁面（Jinja2 模板與所有平台內用到的 HTML）
├── main.py             # Flask 主程式
├── user.db             # 使用者資料庫
├── README.md           # 說明文件
```

## 快速開始
1. **建立 API 金鑰設定檔**
    - 請在 `web/blueprints/` 目錄下找到 `config.py`，並填入你的 TDX `CLIENT_ID`、`CLIENT_SECRET` 及氣象資料開放平台的 `WEATHER_API_KEY`，格式如下：
      ```python
      CLIENT_ID = '你的TDX_CLIENT_ID'
      CLIENT_SECRET = '你的TDX_CLIENT_SECRET'
      WEATHER_API_KEY = '你的氣象資料API_KEY'
      ```
    - TDX 交通資料平台申請網址：[https://tdx.transportdata.tw/](https://tdx.transportdata.tw/)
    - 中央氣象局氣象資料開放平台申請網址：[https://opendata.cwa.gov.tw/](https://opendata.cwa.gov.tw/)
2. **安裝相依套件**
    ```bash
    pip install flask requests bcrypt
    ```
3. **啟動伺服器**
    ```bash
    flask --app main run --reload
    ```

## 主要路由
- `/`：首頁（含歡迎導引）
- `/about`：關於我們
- `/bus/<route>`：公車路線查詢
- `/login/`：登入/註冊
- `/favorites`：收藏站牌

## 團隊與致謝
- 本專案為工業技術研究院所開設「AI與大數據實戰養成班（第六梯次）」小組專題成果。
- 本專案由團隊組員協作完成，感謝課程老師與助教指導。
- 感謝 TDX 平台與大臺北公車 eBus 提供資料與介面設計參考。
- 感謝 中央氣象局氣象資料開放平台 提供天氣資料。

## 聯絡方式
如有建議或合作意願，歡迎來信：sitsitbus@gmail.com

---

> 本專案僅供學術與教學用途，請勿用於商業行為。