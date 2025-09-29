# -*- coding: utf-8 -*-
"""
네이버 블로그 공감 자동화 프로그램
Version: 1.0.9
Last Updated: 2024-09-28

=== 버전 히스토리 ===
v1.0.9 (2024-09-28)
- 네이버 블로그 페이지네이션 구조에 맞게 완전 수정
- aria-label 기반 페이지 번호 인식 (예: "8페이지", "현재7페이지")
- "다음" 버튼(.button_next) 클릭으로 그룹 이동 지원
- URL 변경 확인으로 실제 페이지 이동 검증
- AngularJS 컨트롤러에서 현재 페이지 번호 추출 지원

v1.0.6 (2024-09-28)
- 공감 상태 확인 로직 수정 (__reaction__zeroface 클래스 기반)
- 공감 전: __reaction__zeroface 클래스 있음, 공감 후: 클래스 없음
- 페이지네이션 검색 방법 추가 (6가지 방법으로 확장)
- 전체 링크 검색 기능 추가로 더 확실한 페이지 이동

v1.0.5 (2024-09-28)
- 페이지네이션 기능 대폭 개선
- 5가지 방법으로 다음 페이지 링크 검색 (텍스트, CSS, href, JavaScript, 페이지네이션 영역)
- 더 안정적이고 확실한 페이지 이동 로직 구현

v1.0.4 (2024-09-28)
- 초본 코드 기반으로 공감 기능 수정
- 초본에서 잘 작동하던 CSS 셀렉터와 클릭 방식 적용
- 복잡한 클릭 방법들을 제거하고 단순한 button.click() 사용
- 공감 타입 선택 기능 유지

v1.0.3 (2024-09-28)
- onclick="return false;" 문제 해결
- onclick 속성 제거 후 클릭하는 로직 추가
- 부모 요소의 onclick 실행 후 버튼 클릭하는 방법 추가
- 네이버 블로그 API 직접 호출 방법 추가

v1.0.2 (2024-09-28)
- StaleElementReferenceException 오류 해결
- 요소 무효화 시 자동으로 요소를 다시 찾는 로직 추가
- 공감 기능이 정상 작동함을 확인 (37개 공감 성공)

v1.0.1 (2024-09-28)
- 공감 진행 문제 디버깅을 위한 상세 로그 추가
- 찾은 버튼들의 클래스, aria-pressed, 표시 상태 정보 출력
- 각 게시글 처리 과정 상세 로깅

v1.0.0 (2024-09-28)
- 초기 버전 생성
- 네이버 로그인 기능
- 블로그 공감 자동화 기능
- 페이지네이션 처리
- 시작 페이지 설정 기능
- 공감 상태 확인 및 건너뛰기 기능
- 다양한 클릭 방법 시도 (JavaScript 이벤트, ActionChains 등)
- CSS 셀렉터 최적화 (a.u_likeit_button._face 타겟팅)
- 클래스명 정확한 파싱 (split() 사용)
"""

import sys
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

# Windows 콘솔 한글 인코딩 설정
if sys.platform.startswith('win'):
    import codecs
    import locale
    
    try:
        os.system('chcp 65001 > nul')
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
        locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
    except:
        pass

class BlogLikeAutomationGUI:
    def __init__(self):
        """GUI 초기화"""
        self.root = tk.Tk()
        self.root.title("네이버 블로그 공감 자동화 프로그램")
        self.root.geometry("800x700")
        self.root.configure(bg='#f0f0f0')
        
        # 변수 초기화
        self.driver = None
        self.wait = None
        self.is_running = False
        self.stop_requested = False
        self.automation_thread = None
        
        # 통계 변수
        self.like_count = 0
        self.total_posts = 0
        self.current_page = 1
        self.skipped_count = 0
        self.start_page = 1
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="네이버 블로그 공감 자동화 프로그램", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 로그인 정보 프레임
        login_frame = ttk.LabelFrame(main_frame, text="로그인 정보", padding="10")
        login_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(login_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.id_var = tk.StringVar(value="cms045757")
        id_entry = ttk.Entry(login_frame, textvariable=self.id_var, width=20)
        id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(login_frame, text="비밀번호:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.pw_var = tk.StringVar(value="!7476458aA")
        pw_entry = ttk.Entry(login_frame, textvariable=self.pw_var, show="*", width=20)
        pw_entry.grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        # 블로그 URL 입력 프레임
        url_frame = ttk.LabelFrame(main_frame, text="블로그 URL", padding="10")
        url_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(url_frame, text="블로그 URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.url_var = tk.StringVar(value="https://blog.naver.com/")
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 설정 프레임
        settings_frame = ttk.LabelFrame(main_frame, text="설정", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 스크롤 딜레이 설정
        ttk.Label(settings_frame, text="스크롤 딜레이(초):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.scroll_delay_var = tk.StringVar(value="2")
        scroll_delay_entry = ttk.Entry(settings_frame, textvariable=self.scroll_delay_var, width=10)
        scroll_delay_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # 클릭 딜레이 설정
        ttk.Label(settings_frame, text="클릭 딜레이(초):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.click_delay_var = tk.StringVar(value="1")
        click_delay_entry = ttk.Entry(settings_frame, textvariable=self.click_delay_var, width=10)
        click_delay_entry.grid(row=0, column=3, sticky=tk.W)
        
        # 시작 페이지 설정
        ttk.Label(settings_frame, text="시작 페이지:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.start_page_var = tk.StringVar(value="1")
        start_page_entry = ttk.Entry(settings_frame, textvariable=self.start_page_var, width=10)
        start_page_entry.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        
        # 제어 버튼 프레임
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        # 시작 버튼
        self.start_button = ttk.Button(control_frame, text="시작", command=self.start_automation,
                                      style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # 중지 버튼
        self.stop_button = ttk.Button(control_frame, text="중지", command=self.stop_automation,
                                     state='disabled')
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        # 브라우저 열기 버튼
        ttk.Button(control_frame, text="브라우저 열기", command=self.open_browser).grid(row=0, column=2)
        
        # 진행 상황 프레임
        progress_frame = ttk.LabelFrame(main_frame, text="진행 상황", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 상태 라벨
        self.status_var = tk.StringVar(value="대기 중...")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, sticky=tk.W)
        
        # 통계 라벨
        self.stats_var = tk.StringVar(value="공감: 0개, 건너뜀: 0개, 페이지: 1")
        stats_label = ttk.Label(progress_frame, textvariable=self.stats_var)
        stats_label.grid(row=1, column=1, sticky=tk.E)
        
        # 로그 프레임
        log_frame = ttk.LabelFrame(main_frame, text="실행 로그", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 로그 텍스트 영역
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        login_frame.columnconfigure(1, weight=1)
        login_frame.columnconfigure(3, weight=1)
        url_frame.columnconfigure(1, weight=1)
        progress_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def log_message(self, message):
        """로그 메시지 추가"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def setup_driver(self):
        """Chrome WebDriver 설정"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 10)
            
            self.log_message("Chrome WebDriver 설정 완료")
            return True
            
        except Exception as e:
            self.log_message(f"WebDriver 설정 오류: {e}")
            return False
            
    def login_to_naver(self):
        """네이버 로그인"""
        try:
            self.log_message("네이버 로그인 시작...")
            
            self.driver.get("https://nid.naver.com/nidlogin.login")
            self.wait.until(EC.presence_of_element_located((By.ID, "id")))
            
            user_id = self.id_var.get()
            password = self.pw_var.get()
            
            # ID 입력
            pyperclip.copy(user_id)
            id_field = self.wait.until(EC.element_to_be_clickable((By.ID, "id")))
            id_field.click()
            time.sleep(0.5)
            id_field.send_keys(Keys.CONTROL + "v")
            time.sleep(1)
            
            # 비밀번호 입력
            pyperclip.copy(password)
            pw_field = self.driver.find_element(By.ID, "pw")
            pw_field.click()
            time.sleep(0.5)
            pw_field.send_keys(Keys.CONTROL + "v")
            time.sleep(1)
            
            # 로그인 버튼 클릭
            login_button = self.wait.until(EC.element_to_be_clickable((By.ID, "log.login")))
            login_button.click()
            time.sleep(3)
            
            # 로그인 성공 확인
            current_url = self.driver.current_url
            if "nid.naver.com" not in current_url:
                self.log_message("네이버 로그인 성공!")
                return True
            else:
                self.log_message("로그인 실패")
                return False
                
        except Exception as e:
            self.log_message(f"로그인 오류: {e}")
            return False
    
    def scroll_to_bottom(self):
        """페이지 하단까지 스크롤"""
        try:
            # 현재 스크롤 위치 저장
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # 페이지 하단으로 스크롤
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 새 콘텐츠 로딩 대기
                time.sleep(float(self.scroll_delay_var.get()))
                
                # 새로운 스크롤 높이 계산
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # 더 이상 로드할 콘텐츠가 없으면 중단
                if new_height == last_height:
                    break
                    
                last_height = new_height
                
        except Exception as e:
            self.log_message(f"스크롤 중 오류: {e}")
    
    def is_already_liked(self, like_button):
        """이미 공감을 눌렀는지 확인 (__reaction__zeroface 클래스 기반)"""
        try:
            # __reaction__zeroface 클래스가 있으면 공감 안 함, 없으면 공감 함
            zeroface_icon = like_button.find_element(By.CSS_SELECTOR, ".u_likeit_icon.__reaction__zeroface")
            if zeroface_icon:
                self.log_message(f"디버그: __reaction__zeroface 클래스 발견 -> 아직 공감 안 함")
                return False
            else:
                self.log_message(f"디버그: __reaction__zeroface 클래스 없음 -> 이미 공감함")
                return True
                
        except NoSuchElementException:
            # __reaction__zeroface 클래스가 없으면 이미 공감한 상태
            self.log_message(f"디버그: __reaction__zeroface 클래스 없음 -> 이미 공감함")
            return True
        except Exception as e:
            self.log_message(f"공감 상태 확인 중 오류: {e}")
            return False
    
    def go_to_start_page(self, start_page_num):
        """지정된 시작 페이지로 이동"""
        try:
            self.log_message(f"시작 페이지 {start_page_num}로 이동합니다...")
            
            # 시작 페이지 버튼 찾기
            start_page_button = None
            
            # 방법 1: 페이지 번호 링크로 직접 이동
            try:
                start_page_button = self.driver.find_element(By.LINK_TEXT, str(start_page_num))
                self.log_message(f"시작 페이지 {start_page_num} 링크를 찾았습니다.")
            except NoSuchElementException:
                # 방법 2: CSS 셀렉터로 페이지 번호 찾기
                try:
                    start_page_button = self.driver.find_element(By.CSS_SELECTOR, f"a[href*='page={start_page_num}']")
                    self.log_message(f"시작 페이지 {start_page_num} 링크를 CSS로 찾았습니다.")
                except NoSuchElementException:
                    # 방법 3: JavaScript로 페이지 번호 링크 찾기
                    start_page_button = self.driver.execute_script(f"""
                        var links = document.querySelectorAll('a');
                        for (var i = 0; i < links.length; i++) {{
                            if (links[i].textContent.trim() === '{start_page_num}') {{
                                return links[i];
                            }}
                        }}
                        return null;
                    """)
                    if start_page_button:
                        self.log_message(f"JavaScript로 시작 페이지 {start_page_num} 링크를 찾았습니다.")
            
            if start_page_button:
                # 시작 페이지로 스크롤
                self.driver.execute_script("arguments[0].scrollIntoView(true);", start_page_button)
                time.sleep(1)
                
                # JavaScript로 클릭 (더 안정적)
                try:
                    self.driver.execute_script("arguments[0].click();", start_page_button)
                    time.sleep(3)
                    self.log_message(f"시작 페이지 {start_page_num}로 이동했습니다.")
                except Exception as js_click_e:
                    # 일반 클릭 시도
                    try:
                        start_page_button.click()
                        time.sleep(3)
                        self.log_message(f"시작 페이지 {start_page_num}로 이동했습니다. (일반 클릭)")
                    except Exception as normal_click_e:
                        self.log_message(f"시작 페이지 이동 실패: {normal_click_e}")
                        return False
                
                # 페이지 이동 후 현재 페이지 번호 확인
                time.sleep(2)
                actual_page = self.get_current_page_number()
                self.current_page = actual_page
                self.log_message(f"실제 이동된 시작 페이지: {actual_page}")
                
                return True
            else:
                self.log_message(f"시작 페이지 {start_page_num}로 이동할 수 없습니다.")
                return False
                
        except Exception as e:
            self.log_message(f"시작 페이지 이동 중 오류: {e}")
            return False
    
    def find_and_click_like_buttons(self):
        """공감 버튼 찾기 및 클릭 (초본 코드 기반)"""
        try:
            # 초본 코드와 동일한 셀렉터 사용
            like_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                ".u_likeit_list_module._reactionModule._reactionModule_BLOG")
            
            self.log_message(f"페이지에서 {len(like_buttons)}개의 공감 버튼을 발견했습니다.")
            
            clicked_count = 0
            skipped_count = 0
            
            for i, button in enumerate(like_buttons):
                if self.stop_requested:
                    break
                    
                try:
                    # 버튼이 화면에 보이는지 확인
                    if not button.is_displayed():
                        continue
                    
                    # 이미 공감했는지 확인
                    is_liked = self.is_already_liked(button)
                    if is_liked:
                        skipped_count += 1
                        self.skipped_count += 1
                        self.log_message(f"게시글 {i+1}: 이미 공감한 게시글입니다. 건너뜁니다.")
                        continue
                    else:
                        self.log_message(f"게시글 {i+1}: 공감하지 않은 게시글입니다. 공감을 진행합니다.")
                    
                    # 버튼으로 스크롤
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(0.5)
                    
                    # 초본 코드와 동일한 방식으로 공감 버튼 클릭
                    button.click()
                    time.sleep(float(self.click_delay_var.get()))
                    
                    # 기본 공감 클릭 (공감 타입 선택 제거)
                    self.log_message(f"게시글 {i+1}: 기본 공감 클릭 완료")
                    
                    clicked_count += 1
                    self.like_count += 1
                    
                    # 통계 업데이트
                    self.stats_var.set(f"공감: {self.like_count}개, 건너뜀: {self.skipped_count}개, 페이지: {self.current_page}")
                    
                except Exception as e:
                    self.log_message(f"게시글 {i+1} 공감 버튼 클릭 중 오류: {e}")
                    continue
            
            self.log_message(f"이번 페이지에서 {clicked_count}개의 공감을 클릭하고, {skipped_count}개를 건너뛰었습니다.")
            return clicked_count
            
        except Exception as e:
            self.log_message(f"공감 버튼 찾기 중 오류: {e}")
            return 0
    
    def go_to_next_page(self):
        """다음 페이지로 이동 (네이버 블로그 페이지네이션 구조 기반)"""
        try:
            # 현재 페이지 번호 확인
            current_page_num = self.get_current_page_number()
            next_page_num = current_page_num + 1
            
            self.log_message(f"현재 페이지: {current_page_num}, 다음 페이지: {next_page_num}")
            
            # 현재 URL 저장 (페이지 이동 확인용)
            current_url = self.driver.current_url
            self.log_message(f"현재 URL: {current_url}")
            
            next_page_button = None
            
            # 방법 1: 다음 페이지 번호 직접 클릭 (같은 그룹 내에서)
            try:
                # aria-label로 다음 페이지 찾기 (예: "8페이지")
                next_page_button = self.driver.find_element(By.CSS_SELECTOR, f"a[aria-label='{next_page_num}페이지']")
                self.log_message(f"다음 페이지 {next_page_num} 링크를 aria-label로 찾았습니다.")
            except NoSuchElementException:
                # 방법 2: 텍스트로 다음 페이지 번호 찾기
                try:
                    next_page_button = self.driver.find_element(By.LINK_TEXT, str(next_page_num))
                    self.log_message(f"다음 페이지 {next_page_num} 링크를 텍스트로 찾았습니다.")
                except NoSuchElementException:
                    # 방법 3: "다음" 버튼 클릭 (다음 그룹으로 이동)
                    try:
                        next_page_button = self.driver.find_element(By.CSS_SELECTOR, ".button_next")
                        self.log_message("다음 그룹으로 이동하는 '다음' 버튼을 찾았습니다.")
                    except NoSuchElementException:
                        # 방법 4: JavaScript로 다음 페이지 찾기
                        try:
                            next_page_button = self.driver.execute_script(f"""
                                // 1. 다음 페이지 번호 직접 찾기
                                var nextPageLink = document.querySelector('a[aria-label="{next_page_num}페이지"]');
                                if (nextPageLink) return nextPageLink;
                                
                                // 2. 텍스트로 다음 페이지 찾기
                                var links = document.querySelectorAll('a.item');
                                for (var i = 0; i < links.length; i++) {{
                                    if (links[i].textContent.trim() === '{next_page_num}') {{
                                        return links[i];
                                    }}
                                }}
                                
                                // 3. "다음" 버튼 찾기
                                var nextButton = document.querySelector('.button_next');
                                if (nextButton) return nextButton;
                                
                                return null;
                            """)
                            if next_page_button:
                                self.log_message("JavaScript로 다음 페이지 버튼을 찾았습니다.")
                        except Exception as e:
                            self.log_message(f"JavaScript 검색 중 오류: {e}")
            
            if next_page_button:
                # 다음 페이지로 스크롤
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_page_button)
                time.sleep(1)
                
                # JavaScript로 클릭 (더 안정적)
                try:
                    self.driver.execute_script("arguments[0].click();", next_page_button)
                    time.sleep(3)
                    self.log_message(f"페이지 이동 버튼을 클릭했습니다.")
                except Exception as js_click_e:
                    # 일반 클릭 시도
                    try:
                        next_page_button.click()
                        time.sleep(3)
                        self.log_message(f"페이지 이동 버튼을 클릭했습니다. (일반 클릭)")
                    except Exception as normal_click_e:
                        self.log_message(f"페이지 이동 실패: {normal_click_e}")
                        return False
                
                # 페이지 이동 후 URL 변경 확인
                time.sleep(2)
                new_url = self.driver.current_url
                self.log_message(f"새 URL: {new_url}")
                
                # URL이 변경되었는지 확인
                if new_url != current_url:
                    self.log_message("URL이 변경되었습니다. 페이지 이동 성공!")
                    # 현재 페이지 번호 재확인
                    actual_page = self.get_current_page_number()
                    self.current_page = actual_page
                    self.log_message(f"실제 이동된 페이지: {actual_page}")
                    return True
                else:
                    self.log_message("URL이 변경되지 않았습니다. 페이지 이동 실패!")
                    return False
                
            else:
                self.log_message(f"다음 페이지로 이동할 수 없습니다. 마지막 페이지일 수 있습니다.")
                return False
                
        except Exception as e:
            self.log_message(f"다음 페이지 이동 중 오류: {e}")
            return False
    
    def get_current_page_number(self):
        """현재 페이지 번호 가져오기 (네이버 블로그 구조 기반)"""
        try:
            # 방법 1: 네이버 블로그 페이지네이션에서 현재 페이지 찾기
            # aria-current="page"를 가진 요소 찾기
            try:
                current_page_element = self.driver.find_element(By.CSS_SELECTOR, "a[aria-current='page'] strong")
                page_num = int(current_page_element.text.strip())
                if page_num > 0:
                    return page_num
            except (NoSuchElementException, ValueError):
                pass
            
            # 방법 2: aria-label="현재X페이지" 찾기
            try:
                current_page_element = self.driver.find_element(By.CSS_SELECTOR, "a[aria-label*='현재'][aria-label*='페이지']")
                aria_label = current_page_element.get_attribute("aria-label")
                # "현재7페이지"에서 숫자 추출
                import re
                match = re.search(r'현재(\d+)페이지', aria_label)
                if match:
                    return int(match.group(1))
            except (NoSuchElementException, ValueError):
                pass
            
            # 방법 3: JavaScript로 현재 페이지 찾기
            current_page = self.driver.execute_script("""
                // 1. aria-current="page"를 가진 요소 찾기
                var currentElement = document.querySelector('a[aria-current="page"] strong');
                if (currentElement) {
                    var num = parseInt(currentElement.textContent.trim());
                    if (num > 0) return num;
                }
                
                // 2. aria-label에서 현재 페이지 찾기
                var currentLink = document.querySelector('a[aria-label*="현재"][aria-label*="페이지"]');
                if (currentLink) {
                    var label = currentLink.getAttribute('aria-label');
                    var match = label.match(/현재(\\d+)페이지/);
                    if (match) {
                        return parseInt(match[1]);
                    }
                }
                
                // 3. pagination 컨트롤러에서 현재 페이지 가져오기
                if (window.angular && window.angular.element) {
                    var element = angular.element(document.querySelector('[ng-controller]'));
                    if (element && element.scope()) {
                        var scope = element.scope();
                        if (scope.blogHomeCtrl && scope.blogHomeCtrl.currentPage) {
                            return scope.blogHomeCtrl.currentPage;
                        }
                    }
                }
                
                // 4. URL에서 페이지 번호 추출
                var url = window.location.href;
                var pageMatch = url.match(/[?&]page=(\\d+)/);
                if (pageMatch) {
                    return parseInt(pageMatch[1]);
                }
                
                return 1;
            """)
            
            return current_page if current_page and current_page > 0 else 1
            
        except Exception as e:
            self.log_message(f"현재 페이지 번호 확인 중 오류: {e}")
            return self.current_page
    
    def automation_worker(self):
        """자동화 작업 스레드"""
        try:
            self.is_running = True
            self.stop_requested = False
            self.like_count = 0
            self.total_posts = 0
            self.current_page = 1
            self.skipped_count = 0
            
            # 시작 페이지 설정
            try:
                self.start_page = int(self.start_page_var.get())
                if self.start_page < 1:
                    self.start_page = 1
            except ValueError:
                self.start_page = 1
                self.log_message("시작 페이지가 올바르지 않아 기본값 1로 설정합니다.")
            
            # WebDriver 설정
            if not self.setup_driver():
                return
            
            # 로그인
            if not self.login_to_naver():
                return
            
            # 블로그 URL 접속
            blog_url = self.url_var.get()
            if not blog_url:
                self.log_message("블로그 URL을 입력해주세요.")
                return
            
            self.log_message(f"블로그 접속: {blog_url}")
            self.driver.get(blog_url)
            time.sleep(3)
            
            # 시작 페이지로 이동 (1페이지가 아닌 경우)
            if self.start_page > 1:
                if not self.go_to_start_page(self.start_page):
                    self.log_message(f"시작 페이지 {self.start_page}로 이동에 실패했습니다. 1페이지부터 시작합니다.")
                    self.start_page = 1
                    self.current_page = 1
                else:
                    self.log_message(f"시작 페이지 {self.start_page}로 이동 완료!")
            else:
                self.log_message("1페이지부터 시작합니다.")
            
            # 페이지별 처리
            while not self.stop_requested:
                self.log_message(f"페이지 {self.current_page} 처리 시작...")
                
                # 페이지 하단까지 스크롤
                self.scroll_to_bottom()
                
                # 공감 버튼 클릭
                clicked_likes = self.find_and_click_like_buttons()
                
                # 다음 페이지로 이동 (공감 개수와 관계없이)
                if not self.go_to_next_page():
                    self.log_message("더 이상 페이지가 없습니다.")
                    break
                
                # 공감할 게시글이 없고 페이지도 없으면 종료
                if clicked_likes == 0:
                    self.log_message("이번 페이지에서 공감할 게시글이 없었습니다.")
                
                # 페이지 간 대기
                time.sleep(2)
            
            # 완료
            self.status_var.set("완료")
            self.stats_var.set(f"공감: {self.like_count}개, 건너뜀: {self.skipped_count}개, 페이지: {self.current_page}")
            self.log_message(f"자동화 완료! 총 {self.like_count}개의 공감을 클릭하고, {self.skipped_count}개를 건너뛰었습니다.")
            
        except Exception as e:
            self.log_message(f"자동화 작업 오류: {e}")
        finally:
            self.is_running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
    
    def start_automation(self):
        """자동화 시작"""
        if self.is_running:
            return
        
        # 유효성 검사
        if not self.url_var.get():
            messagebox.showerror("오류", "블로그 URL을 입력해주세요.")
            return
        
        if not self.id_var.get() or not self.pw_var.get():
            messagebox.showerror("오류", "로그인 정보를 입력해주세요.")
            return
        
        # 시작 페이지 유효성 검사
        try:
            start_page = int(self.start_page_var.get())
            if start_page < 1:
                messagebox.showerror("오류", "시작 페이지는 1 이상의 숫자로 입력해주세요.")
                return
        except ValueError:
            messagebox.showerror("오류", "시작 페이지는 숫자로만 입력해주세요.")
            return
        
        # UI 상태 변경
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # 로그 초기화
        self.log_text.delete('1.0', tk.END)
        self.progress_var.set(0)
        self.status_var.set("시작 중...")
        
        # 자동화 스레드 시작
        self.automation_thread = threading.Thread(target=self.automation_worker, daemon=True)
        self.automation_thread.start()
    
    def stop_automation(self):
        """자동화 중지"""
        self.stop_requested = True
        self.log_message("중지 요청됨...")
    
    def open_browser(self):
        """브라우저 열기"""
        try:
            if not self.driver:
                if not self.setup_driver():
                    return
            
            self.driver.get("https://www.naver.com")
            self.log_message("브라우저가 열렸습니다.")
        except Exception as e:
            self.log_message(f"브라우저 열기 오류: {e}")
            
    def run(self):
        """GUI 실행"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """프로그램 종료 시 처리"""
        if self.is_running:
            if messagebox.askokcancel("종료", "자동화가 실행 중입니다. 정말 종료하시겠습니까?"):
                self.stop_requested = True
                if self.driver:
                    self.driver.quit()
                self.root.destroy()
        else:
            if self.driver:
                self.driver.quit()
            self.root.destroy()

if __name__ == "__main__":
    app = BlogLikeAutomationGUI()
    app.run()
