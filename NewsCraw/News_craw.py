import requests
from bs4 import BeautifulSoup
import pandas as pd
import tkinter as tk
import time
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import logging

import re
# Chrome 로그를 출력하기 위한 설정
logging.basicConfig(level=logging.INFO)

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
chrome_options.add_argument("--headless")  # 브라우저 창 숨기기

service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def crawl_news():
    keyword = keyword_entry.get()
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()
    page_count = int(page_entry.get())
    portal = portal_combobox.get()

    # 시작 날짜와 종료 날짜의 월과 일 추출
    start_month = start_date[4:6]
    start_day = start_date[6:8]
    end_month = end_date[4:6]
    end_day = end_date[6:8]

    filtered_list = []

    if not keyword or not start_date or not end_date or not page_count or not portal:
        messagebox.showwarning("경고", "모든 필드를 입력해주세요.")
        return

    try:
        # 결과를 담을 데이터프레임 생성
        data = []

        # 페이지별 크롤링 수행
        for page in range(1, page_count + 1):
            # 뉴스 검색 URL 생성
            if portal == 'naver':
                url = f"https://search.naver.com/search.naver?where=news&query={keyword}&sm=tab_opt&sort=0&photo=0&field=0&reporter_article=&pd=3&ds={start_date}&de={end_date}&docid=&nso=so:r,p:from{start_date.replace('.', '')}to{end_date.replace('.', '')},a:all&mynews=0&cluster_rank=37&start={(page - 1) * 10 + 1}&refresh_start=0"
            elif portal == 'daum':
                # daum 사이트 설정
                driver.get("https://finance.daum.net/news#economy")
                selkeyword = driver.find_element(By.NAME, "keyword")
                selkeyword.click()
                selkeyword.send_keys(keyword)

                # keyword 검색
                searchBtn = driver.find_element(By.CSS_SELECTOR,"#boxRightSidebar > div:nth-child(1) > div.searchB > form > a")
                searchBtn.click()
                # 페이지 로딩 대기 (적절한 대기 시간을 설정해야 합니다.)
                time.sleep(5)


            # 페이지 HTML 가져오기
            html = driver.page_source
            # HTTP GET 요청
            if portal == 'naver':
                response = requests.get(url)
                response.raise_for_status()  # 요청이 실패한 경우 예외 발생

            # HTML 파싱
            if portal == 'naver':
                soup = BeautifulSoup(response.text, 'html.parser')
            elif portal == 'daum':
                soup = BeautifulSoup(html, 'html.parser')

            # 뉴스 목록 추출
            if portal == 'naver':
                news_list = soup.select('.list_news > li')
                print(f"naver_news_list={news_list}")
            elif portal == 'daum':
                news_list = soup.select('#boxSearchs > div.box_contents > div > ul > li')

                for news in news_list :
                    date_str = news.select_one('.date').text
                    print(date_str)
                    # 뉴스 날짜에서 월과 일 추출
                    news_month, news_day = re.findall(r"\d+", date_str)

                    # 월과 일을 정수로 변환하여 비교
                    if int(start_month) <= int(news_month) <= int(end_month) and int(start_day) <= int(news_day) <= int(
                            end_day):
                        filtered_list.append(news)
                news_list = filtered_list

                print(f"다음news_list={news_list}")
            # 페이지별 결과 저장
            for news in news_list:
                if portal == 'naver':
                    title = news.select_one('.news_tit').text
                    link = news.select_one('.news_tit')['href']
                    date_elements = news.select('.info_group > span.info')
                    date_str = ''
                    for element in date_elements:
                        if not element.select_one('i.spnew.ico_paper'):
                            date_str = element.text
                            break
                elif portal == 'daum':
                    title = news.select_one('.tit').text
                    link = news.select_one('.tit')['href']
                    date_str = news.select_one('.date').text

                # 시간 전 표기 변환
                if portal == 'naver':
                    if '시간 전' in date_str:
                        hours_ago = int(re.search(r'\d+', date_str).group())
                        date = (datetime.now() - timedelta(hours=hours_ago)).strftime('%Y-%m-%d')
                    elif '일 전' in date_str:
                        days_ago = int(re.search(r'\d+', date_str).group())
                        date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                    elif '분 전' in date_str:
                        minutes_ago = int(re.search(r'\d+', date_str).group())
                        date = (datetime.now() - timedelta(minutes=minutes_ago)).strftime('%Y-%m-%d')
                    elif '초 전' in date_str:
                        seconds_ago = int(re.search(r'\d+', date_str).group())
                        date = (datetime.now() - timedelta(seconds=seconds_ago)).strftime('%Y-%m-%d')
                    else:
                        date = date_str

                elif portal == 'daum':
                        date = date_str

                data.append([title, link, date])

        # 데이터프레임 생성
        df = pd.DataFrame(data, columns=['제목', '링크', '날짜'])

        # 파일 다이얼로그로 저장 경로 선택
        save_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=(("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")))

        if save_path:
            # 엑셀 파일로 저장
            df.to_excel(save_path, index=False)
            messagebox.showinfo("알림", f"{save_path} 파일로 저장되었습니다.")

    except Exception as e:
        messagebox.showerror("오류", str(e))


# GUI 창 생성
window = tk.Tk()
window.title("뉴스 웹 크롤링")
window.geometry("400x350")

# 키워드 입력 레이블 및 엔트리
keyword_label = tk.Label(window, text="뉴스 키워드:")
keyword_label.pack()
keyword_entry = tk.Entry(window)
keyword_entry.pack()

# 시작일 입력 레이블 및 엔트리
start_date_label = tk.Label(window, text="시작일 (YYYY.MM.DD):")
start_date_label.pack()
start_date_entry = tk.Entry(window)
start_date_entry.pack()

# 종료일 입력 레이블 및 엔트리
end_date_label = tk.Label(window, text="종료일 (YYYY.MM.DD):")
end_date_label.pack()
end_date_entry = tk.Entry(window)
end_date_entry.pack()

# 페이지 수 입력 레이블 및 엔트리
page_label = tk.Label(window, text="페이지 수:")
page_label.pack()
page_entry = tk.Entry(window)
page_entry.pack()

# 포털 선택 콤보박스 레이블
portal_label = tk.Label(window, text="뉴스 포털:")
portal_label.pack()

# 포털 선택 콤보박스
portal_combobox = ttk.Combobox(window, values=['naver', 'daum'])
portal_combobox.pack()
portal_combobox.set('naver')  # 초기 선택값

# 수행 버튼
crawl_button = tk.Button(window, text="크롤링 시작", command=crawl_news)
crawl_button.pack()

# GUI 실행
window.mainloop()