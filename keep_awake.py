import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# 自動で起こしたい対象のStreamlitアプリのURLリスト
URLS = [
    "https://japan-pharma-19.streamlit.app/",
    "https://jpe2018-kaisei.streamlit.app/"
]

def wake_up_app(driver, url):
    try:
        print(f"--- 巡回中: {url} ---")
        driver.get(url)
        time.sleep(5)
        
        buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Yes, get this app back up!')]")
        if buttons:
            buttons[0].click()
            print(f"👉 スリープ状態を検知しました。起こすためのボタンをクリックしました！")
            time.sleep(10)
        else:
            print(f"✅ アプリは既に起動しています（スリープしていません）。")
            
    except Exception as e:
        print(f"❌ エラーが発生しました ({url}): {e}")

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    for url in URLS:
        wake_up_app(driver, url)
        time.sleep(3)
        
    driver.quit()

if __name__ == "__main__":
    main()
