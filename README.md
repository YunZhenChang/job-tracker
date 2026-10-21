# 求職進度追蹤器

用 Python 與 Streamlit 製作的小型網頁工具，用來記錄每一筆求職投遞的狀態與面試日期。

<!-- 截圖：用「載入範例資料」的畫面截一張，存成 docs/screenshot.png，再把下面這行的註解拿掉
![畫面截圖](docs/screenshot.png)
-->

## 功能

- 新增、編輯、刪除投遞紀錄（公司、職稱、狀態、投遞日期、面試日期、連結、備註）
- 在列表上直接切換狀態（已投遞、面試中、已獲 Offer、未錄取、已撤回）
- 各狀態數量統計與長條圖
- 搜尋公司或職稱、依狀態篩選、依日期或公司名稱排序
- 7 天內有面試時顯示提醒
- 輸入驗證（必填欄位、連結格式）與刪除前二次確認
- 「載入範例資料」按鈕，第一次打開就能看到效果

## 使用技術

Python 3.11、Streamlit、pandas、Altair。資料以 JSON 檔存在本機，沒有資料庫與後端服務。

## 執行方式

```bash
python -m venv .venv
.venv\Scripts\activate           # macOS / Linux：source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

瀏覽器會開啟 `http://localhost:8501`。

## 資料儲存與隱私

- 預設為**展示模式**（`app.py` 中 `PERSIST = False`）：資料只保留在目前這次瀏覽，重新整理後清空，每位訪客的資料互不相通。適合部署成公開連結。
- 若要在自己的電腦長期使用，把 `PERSIST` 改成 `True`，紀錄會存在 `app.py` 旁邊的 `jobs.json`。`jobs.json` 已列入 `.gitignore`，不會被上傳。
- 公開展示頁請只用範例資料，不要輸入真實的投遞紀錄。

## 設計筆記

- Streamlit 每次互動都會從頭重跑整支程式，所以狀態（紀錄清單、正在編輯的項目）放在 `st.session_state`。
- 使用者輸入的文字在顯示前會跳脫 Markdown 符號，避免被當成格式指令。
- 讀寫 `jobs.json` 時處理了檔案不存在、內容損毀與寫入失敗的情況。

## 已知限制

- 資料只存在單一裝置，沒有多人或跨裝置同步。
- 目前沒有匯出功能，也沒有自動化測試。
