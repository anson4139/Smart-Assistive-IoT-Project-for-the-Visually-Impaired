# GitHub 設定與連線教學 (雙模式版)

本文件提供兩種方式將專案上傳到 GitHub：**文字指令 (CLI)** 與 **圖形介面 (VS Code GUI)**。
**注意：無論用哪種方式，都必須先完成「第一步：安裝 Git」。**

## 第一步：下載與安裝 Git (必做)

因為你的電腦目前沒有 Git，我們需要先安裝。

1.  **下載**：
    *   前往官網：[https://git-scm.com/download/win](https://git-scm.com/download/win)
    *   點選 **"Click here to download"** (通常會自動下載 64-bit setup)。

2.  **安裝**：
    *   執行下載的 `.exe` 檔案。
    *   安裝過程中會有很多選項，**全部按 "Next" (下一步) 到底**，使用預設值即可。
    *   等待安裝完成。

3.  **驗證**：
    *   安裝好後，請 **完全關閉** 目前的 VS Code，然後重新打開。

---

## 方式一：使用 VS Code 圖形介面 (推薦，最簡單)

你不需要打任何指令，直接用 VS Code 的按鈕操作。

### 1. 初始化專案
1.  點選 VS Code 左側的 **「原始碼控制」 (Source Control)** 圖示 (長得像分岔的樹枝，通常是第三個)。
2.  你會看到一個藍色按鈕 **「Initialize Repository」 (初始化存放庫)**，給它點下去。
    *(如果沒看到，請確認你有先關閉再開啟 VS Code，讓它抓到剛裝好的 Git)*

### 2. 提交檔案 (Commit)
1.  初始化後，你會看到左側列出所有檔案 (標示 U，代表 Untracked)。
2.  在上方輸入框 ("Message") 寫下：`Initial commit`。
3.  按下上方的 **「Commit」 (提交)** 按鈕 (或是打勾圖示)。
    *   *若跳出視窗問你要不要把所有變更加入，選 **Yes**。*
    *   *若跳出視窗說不知道你是誰，請看下方「補充：設定身份」。*

### 3. 發佈到 GitHub
1.  提交完後，按鈕會變成 **「Publish Branch」 (發佈分支)**。
2.  點下去，VS Code 會跳出選單問你要發佈到哪。
3.  選擇 **「Publish to GitHub private repository」** (私人) 或 **「public」** (公開)。
4.  接著會跳出瀏覽器視窗要求你登入 GitHub 並授權 VS Code，請按 **Authorize**。
5.  完成！右下角會跳出 "Successfully published..." 通知。

---

## 方式二：使用終端機指令 (進階)

如果你喜歡打字，或圖形介面卡住，可以用這個方式。

### 1. 設定你的身份 (只需做一次)
```powershell
git config --global user.name "你的英文名字"
git config --global user.email "你的Email"
```

### 2. 初始化與提交
```powershell
git init
git add .
git commit -m "Initial commit"
```

### 3. 連線 GitHub
先去 GitHub 網站手動建立一個新的 Repository (不要勾選 Add README)，然後複製網址。
```powershell
git remote add origin https://github.com/anson4139/Smart-Assistive-IoT-Project-for-the-Visually-Impaired.git
git push -u origin main
```

---

## 補充：設定身份 (圖形介面若報錯)

如果你在「方式一」按 Commit 時跳出錯誤說 * "Please tell me who you are" *，請打開終端機 (Ctrl+`) 輸入：
```powershell
git config --global user.name "你的名字"
git config --global user.email "你的信箱"
```
輸入完後再回去按 Commit 就會成功了！
