import requests
from bs4 import BeautifulSoup
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from datetime import datetime, timedelta
import re

def crawl_news():
    keyword = keyword_entry.get()
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()
    page_count = int(page_entry.get())

    if not keyword or not start_date or not end_date or not page_count:
        messagebox.showwarning("경고", "모든 필드를 입력해주세요.")
        return

    try:
        # 결과를 담을 데이터프레임 생성
        data = []

        # 페이지별 크롤링 수행
        for page in range(1, page_count + 1):
            # 뉴스 검색 URL 생성
            url = f"https://search.naver.com/search.naver?where=news&query={keyword}&sm=tab_opt&sort=0&photo=0&field=0&reporter_article=&pd=3&ds={start_date}&de={end_date}&docid=&nso=so:r,p:from{start_date.replace('.', '')}to{end_date.replace('.', '')},a:all&mynews=0&cluster_rank=37&start={(page - 1) * 10 + 1}&refresh_start=0"

            # HTTP GET 요청
            response = requests.get(url)
            response.raise_for_status()  # 요청이 실패한 경우 예외 발생

            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')

            # 뉴스 목록 추출
            news_list = soup.select('.list_news > li')

            # 페이지별 결과 저장
            for news in news_list:
                title = news.select_one('.news_tit').text
                link = news.select_one('.news_tit')['href']
                content = news.select_one('.news_dsc').text
                # 날짜 추출
                # date_element = news.select_one('.info_group > span.info:not(.info > i.spnew.ico_paper)')
                # date_str = date_element.text if date_element else ''
                date_elements = news.select('.info_group > span.info')
                date_str = ''
                for element in date_elements:
                    if not element.select_one('i.spnew.ico_paper'):
                        date_str = element.text
                        break


                # 시간 전 표기 변환
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
                keyword_count = content.count(keyword)

                data.append([title, link, date, keyword_count])

        # 데이터프레임 생성
        df = pd.DataFrame(data, columns=['제목', '링크', '날짜', f"키워드 '{keyword}' 출현 횟수"])

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
window.geometry("400x250")

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

# 수행 버튼
crawl_button = tk.Button(window, text="크롤링 시작", command=crawl_news)
crawl_button.pack()

# GUI 실행
window.mainloop()