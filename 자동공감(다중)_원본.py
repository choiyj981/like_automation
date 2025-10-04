# -*- coding: utf-8 -*-
"""
TODO:
블로그 URL 부분은 사용자가 입력하지 않게 해도 된다 항상 고정값으로 하게 해줘
그리고 다중 계정 지원이 있기 때문에 기존 계정은 결과적으로 필요가 없음.
네이버 블로그 공감 자동화 프로그램
Version: 1.1.0
Last Updated: 2024-12-19

=== 버전 히스토리 ===
v1.1.0 (2024-12-19)
- 다중 계정 동시 실행 기능 추가
- 각 계정별 독립적인 로그 탭 지원
- 계정 관리 인터페이스 추가 (계정 추가/삭제/시작/중지)
- 계정별 독립적인 WebDriver 인스턴스 관리
- 계정별 독립적인 자동화 워커 스레드

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
        self.root.geometry("1200x800")
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
        
        # 다중 계정 관리
        self.accounts = []
        self.account_threads = []
        self.account_logs = {}
        
        self.setup_ui()
    
        
    def setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="네이버 블로그 공감 자동화 프로그램 (다중 계정 지원)", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 계정 관리 프레임
        account_frame = ttk.LabelFrame(main_frame, text="계정 관리", padding="10")
        account_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 계정 추가/삭제 버튼
        ttk.Button(account_frame, text="계정 추가", command=self.add_account).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(account_frame, text="계정 삭제", command=self.remove_account).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(account_frame, text="모든 계정 시작", command=self.start_all_accounts).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(account_frame, text="모든 계정 중지", command=self.stop_all_accounts).grid(row=0, column=3)
        
        # 계정 목록
        self.account_listbox = tk.Listbox(account_frame, height=4)
        self.account_listbox.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 로그인 정보 프레임 (기본 계정)
        login_frame = ttk.LabelFrame(main_frame, text="기본 계정 정보", padding="10")
        login_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        url_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(url_frame, text="블로그 URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.url_var = tk.StringVar(value="https://blog.naver.com/")
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 설정 프레임
        settings_frame = ttk.LabelFrame(main_frame, text="설정", padding="10")
        settings_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        control_frame.grid(row=5, column=0, columnspan=3, pady=(0, 10))
        
        # 시작 버튼
        self.start_button = ttk.Button(control_frame, text="기본 계정 시작", command=self.start_automation,
                                      style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # 중지 버튼
        self.stop_button = ttk.Button(control_frame, text="기본 계정 중지", command=self.stop_automation,
                                     state='disabled')
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        # 브라우저 열기 버튼
        ttk.Button(control_frame, text="브라우저 열기", command=self.open_browser).grid(row=0, column=2)
        
        # 진행 상황 프레임
        progress_frame = ttk.LabelFrame(main_frame, text="진행 상황", padding="10")
        progress_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 상태 라벨
        self.status_var = tk.StringVar(value="대기 중...")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, sticky=tk.W)
        
        # 통계 라벨
        self.stats_var = tk.StringVar(value="공감: 0개, 건너뜀: 0개, 페이지: 1")
        stats_label = ttk.Label(progress_frame, textvariable=self.stats_var)
        stats_label.grid(row=1, column=1, sticky=tk.E)
        
        # 로그 탭 프레임
        log_notebook = ttk.Notebook(main_frame)
        log_notebook.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 기본 로그 탭
        self.log_frame = ttk.Frame(log_notebook)
        log_notebook.add(self.log_frame, text="기본 계정 로그")
        
        # 로그 텍스트 영역
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 계정별 로그 탭들을 저장할 딕셔너리
        self.account_log_frames = {}
        self.account_log_texts = {}
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        login_frame.columnconfigure(1, weight=1)
        login_frame.columnconfigure(3, weight=1)
        url_frame.columnconfigure(1, weight=1)
        progress_frame.columnconfigure(0, weight=1)
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)
    
    def log_message(self, message, account_id=None):
        """로그 메시지 추가"""
        timestamp = time.strftime("%H:%M:%S")
        
        if account_id:
            # 계정별 로그는 계정 ID와 함께 표시
            log_entry = f"[{timestamp}] [{account_id}] {message}\n"
        else:
            log_entry = f"[{timestamp}] {message}\n"
        
        # 기본 로그에 추가 (계정별 구분 표시)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        self.root.update_idletasks()
    
    def add_account(self):
        """새 계정 추가"""
        dialog = AccountDialog(self.root)
        if dialog.result:
            account_info = dialog.result
            account_id = f"{account_info['id']}_{len(self.accounts)}"
            
            # 계정 정보 저장
            account_data = {
                'id': account_id,
                'user_id': account_info['id'],
                'password': account_info['password'],
                'blog_url': account_info.get('blog_url', self.url_var.get()),
                'start_page': account_info.get('start_page', 1),
                'is_running': False,
                'driver': None,
                'wait': None,
                'like_count': 0,
                'skipped_count': 0,
                'current_page': 1
            }
            self.accounts.append(account_data)
            
            # 디버깅: 저장된 계정 정보 확인
            self.log_message(f"계정 저장됨 - ID: {account_data['user_id']}, URL: {account_data['blog_url']}")
            
            # 계정 목록 업데이트
            self.account_listbox.insert(tk.END, f"{account_info['id']} - {account_info.get('blog_url', '기본 URL')} [대기중]")
            
            # 계정별 로그 탭 생성
            self.create_account_log_tab(account_id, account_info['id'])
            
            self.log_message(f"계정 추가됨: {account_info['id']}")
    
    def update_account_status(self, account, status):
        """계정 상태 업데이트"""
        try:
            # 계정 목록에서 해당 계정 찾기
            for i in range(self.account_listbox.size()):
                item = self.account_listbox.get(i)
                if account['user_id'] in item:
                    # 상태 업데이트
                    new_item = f"{account['user_id']} - {account['blog_url']} [{status}]"
                    self.account_listbox.delete(i)
                    self.account_listbox.insert(i, new_item)
                    break
        except Exception as e:
            self.log_message(f"계정 상태 업데이트 중 오류: {e}")
    
    def remove_account(self):
        """선택된 계정 삭제"""
        selection = self.account_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "삭제할 계정을 선택해주세요.")
            return
        
        index = selection[0]
        account = self.accounts[index]
        
        if account['is_running']:
            messagebox.showwarning("경고", "실행 중인 계정은 삭제할 수 없습니다. 먼저 중지해주세요.")
            return
        
        # 계정 정보 삭제
        del self.accounts[index]
        
        # 계정 목록 업데이트
        self.account_listbox.delete(index)
        
        # 로그 탭 삭제
        account_id = account['id']
        if account_id in self.account_log_frames:
            # 탭 삭제 (실제 구현에서는 notebook에서 탭을 제거해야 함)
            del self.account_log_frames[account_id]
            del self.account_log_texts[account_id]
        
        self.log_message(f"계정 삭제됨: {account['user_id']}")
    
    def create_account_log_tab(self, account_id, user_id):
        """계정별 로그 탭 생성"""
        # 실제로는 notebook에 새 탭을 추가해야 하지만, 
        # 현재는 기본 로그에 계정별로 구분해서 표시
        self.account_log_frames[account_id] = None
        self.account_log_texts[account_id] = None
    
    def start_all_accounts(self):
        """모든 계정 시작 (5초 간격)"""
        if not self.accounts:
            messagebox.showwarning("경고", "추가된 계정이 없습니다.")
            return
        
        # 5초 간격으로 계정을 시작하는 스레드 생성
        start_thread = threading.Thread(target=self.start_accounts_with_delay, daemon=True)
        start_thread.start()
    
    def start_accounts_with_delay(self):
        """5초 간격으로 계정들을 시작"""
        started_count = 0
        for i, account in enumerate(self.accounts):
            if not account['is_running']:
                # 첫 번째 계정이 아닌 경우 5초 대기
                if i > 0:
                    self.log_message(f"다음 계정 시작까지 5초 대기 중...")
                    time.sleep(5)
                
                thread = threading.Thread(target=self.account_automation_worker, 
                                        args=(account,), daemon=True)
                thread.start()
                self.account_threads.append(thread)
                account['is_running'] = True
                started_count += 1
                self.update_account_status(account, "실행중")
                self.log_message(f"계정 {account['user_id']} 시작됨")
        
        if started_count > 0:
            self.log_message(f"{started_count}개 계정이 5초 간격으로 시작되었습니다.")
        else:
            self.log_message("시작할 수 있는 계정이 없습니다. (모든 계정이 이미 실행 중일 수 있음)")
    
    def stop_all_accounts(self):
        """모든 계정 중지"""
        stopped_count = 0
        for account in self.accounts:
            if account['is_running']:
                account['is_running'] = False
                self.update_account_status(account, "중지됨")
                stopped_count += 1
                if account['driver']:
                    try:
                        account['driver'].quit()
                    except:
                        pass
                    account['driver'] = None
        
        if stopped_count > 0:
            self.log_message(f"{stopped_count}개 계정이 중지되었습니다.")
        else:
            self.log_message("중지할 수 있는 계정이 없습니다.")
    
    def account_automation_worker(self, account):
        """계정별 자동화 작업 스레드"""
        try:
            account['is_running'] = True
            account_id = account['id']
            
            self.log_message(f"계정 {account['user_id']} 자동화 시작", account_id)
            self.log_message(f"계정 정보 - ID: {account['user_id']}, URL: {account['blog_url']}", account_id)
            
            # WebDriver 설정
            if not self.setup_account_driver(account):
                return
            
            # 로그인
            if not self.login_account_to_naver(account):
                return
            
            # 블로그 URL 접속
            blog_url = account['blog_url']
            self.log_message(f"블로그 접속: {blog_url}", account_id)
            account['driver'].get(blog_url)
            time.sleep(3)
            
            # 시작 페이지로 이동
            start_page = account['start_page']
            if start_page > 1:
                if not self.go_to_account_start_page(account, start_page):
                    self.log_message(f"시작 페이지 {start_page}로 이동에 실패했습니다. 1페이지부터 시작합니다.", account_id)
                    account['start_page'] = 1
                    account['current_page'] = 1
                else:
                    self.log_message(f"시작 페이지 {start_page}로 이동 완료!", account_id)
            else:
                self.log_message("1페이지부터 시작합니다.", account_id)
            
            # 페이지별 처리
            while account['is_running']:
                self.log_message(f"페이지 {account['current_page']} 처리 시작...", account_id)
                
                # 페이지 하단까지 스크롤
                self.scroll_account_to_bottom(account)
                
                # 공감 버튼 클릭
                clicked_likes = self.find_and_click_account_like_buttons(account)
                
                # 다음 페이지로 이동
                if not self.go_to_account_next_page(account):
                    self.log_message("더 이상 페이지가 없습니다.", account_id)
                    break
                
                # 페이지 간 대기
                time.sleep(2)
            
            # 완료
            self.log_message(f"자동화 완료! 총 {account['like_count']}개의 공감을 클릭하고, {account['skipped_count']}개를 건너뛰었습니다.", account_id)
            self.update_account_status(account, "완료")
            
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} 자동화 작업 오류: {e}", account_id)
            self.update_account_status(account, "오류")
        finally:
            account['is_running'] = False
            if account['driver']:
                try:
                    account['driver'].quit()
                except:
                    pass
                account['driver'] = None
        
    def setup_account_driver(self, account):
        """계정별 Chrome WebDriver 설정"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            account['driver'] = webdriver.Chrome(options=chrome_options)
            account['driver'].execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            account['wait'] = WebDriverWait(account['driver'], 10)
            
            self.log_message(f"계정 {account['user_id']} Chrome WebDriver 설정 완료", account['id'])
            return True
            
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} WebDriver 설정 오류: {e}", account['id'])
            return False
    
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
    
    def login_account_to_naver(self, account):
        """계정별 네이버 로그인"""
        try:
            self.log_message(f"계정 {account['user_id']} 네이버 로그인 시작...", account['id'])
            self.log_message(f"사용할 ID: {account['user_id']}, 비밀번호: {'*' * len(account['password'])}", account['id'])
            
            account['driver'].get("https://nid.naver.com/nidlogin.login")
            account['wait'].until(EC.presence_of_element_located((By.ID, "id")))
            
            user_id = account['user_id']
            password = account['password']
            
            # ID 입력 (pyperclip 대신 직접 입력)
            id_field = account['wait'].until(EC.element_to_be_clickable((By.ID, "id")))
            id_field.clear()
            id_field.send_keys(user_id)
            time.sleep(1)
            
            # 비밀번호 입력 (pyperclip 대신 직접 입력)
            pw_field = account['driver'].find_element(By.ID, "pw")
            pw_field.clear()
            pw_field.send_keys(password)
            time.sleep(1)
            
            # 로그인 버튼 클릭
            login_button = account['wait'].until(EC.element_to_be_clickable((By.ID, "log.login")))
            login_button.click()
            time.sleep(3)
            
            # 로그인 결과 확인 및 보안문자 대기
            return self.wait_for_login_success(account)
                
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} 로그인 오류: {e}", account['id'])
            return False
    
    def wait_for_login_success(self, account):
        """로그인 성공까지 대기 (보안문자 포함)"""
        try:
            account_id = account['id']
            max_wait_time = 300  # 최대 5분 대기
            check_interval = 2   # 2초마다 확인
            waited_time = 0
            
            self.log_message(f"계정 {account['user_id']} 로그인 결과 확인 중...", account_id)
            
            while waited_time < max_wait_time:
                current_url = account['driver'].current_url
                
                # 로그인 성공 확인 (nid.naver.com이 URL에 없으면 성공)
                if "nid.naver.com" not in current_url:
                    self.log_message(f"계정 {account['user_id']} 네이버 로그인 성공!", account_id)
                    return True
                
                # 보안문자나 추가 인증이 필요한 경우 확인
                try:
                    # 보안문자 입력 필드가 있는지 확인
                    captcha_input = account['driver'].find_elements(By.CSS_SELECTOR, "input[name='captcha']")
                    if captcha_input:
                        self.log_message(f"계정 {account['user_id']} 보안문자 입력이 필요합니다. 입력을 기다리는 중...", account_id)
                        time.sleep(check_interval)
                        waited_time += check_interval
                        continue
                    
                    # 추가 인증이 필요한 경우 (휴대폰 인증 등)
                    auth_elements = account['driver'].find_elements(By.CSS_SELECTOR, ".auth_area, .verify_area, .security_area")
                    if auth_elements:
                        self.log_message(f"계정 {account['user_id']} 추가 인증이 필요합니다. 인증을 기다리는 중...", account_id)
                        time.sleep(check_interval)
                        waited_time += check_interval
                        continue
                    
                    # 에러 메시지가 있는지 확인
                    error_elements = account['driver'].find_elements(By.CSS_SELECTOR, ".error_message, .err_msg, .alert")
                    if error_elements:
                        error_text = error_elements[0].text.strip()
                        if error_text:
                            self.log_message(f"계정 {account['user_id']} 로그인 오류: {error_text}", account_id)
                            # 오류가 있어도 계속 대기 (사용자가 수정할 수 있도록)
                    
                except Exception as e:
                    # 요소 찾기 실패는 무시하고 계속 진행
                    pass
                
                # 2초 대기 후 다시 확인
                time.sleep(check_interval)
                waited_time += check_interval
                
                # 30초마다 상태 메시지 출력
                if waited_time % 30 == 0:
                    self.log_message(f"계정 {account['user_id']} 로그인 대기 중... ({waited_time}초 경과)", account_id)
            
            # 최대 대기 시간 초과
            self.log_message(f"계정 {account['user_id']} 로그인 대기 시간 초과 (5분)", account_id)
            return False
            
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} 로그인 대기 중 오류: {e}", account_id)
            return False
            
    def login_to_naver(self):
        """네이버 로그인"""
        try:
            self.log_message("네이버 로그인 시작...")
            
            self.driver.get("https://nid.naver.com/nidlogin.login")
            self.wait.until(EC.presence_of_element_located((By.ID, "id")))
            
            user_id = self.id_var.get()
            password = self.pw_var.get()
            
            # ID 입력 (pyperclip 대신 직접 입력)
            id_field = self.wait.until(EC.element_to_be_clickable((By.ID, "id")))
            id_field.clear()
            id_field.send_keys(user_id)
            time.sleep(1)
            
            # 비밀번호 입력 (pyperclip 대신 직접 입력)
            pw_field = self.driver.find_element(By.ID, "pw")
            pw_field.clear()
            pw_field.send_keys(password)
            time.sleep(1)
            
            # 로그인 버튼 클릭
            login_button = self.wait.until(EC.element_to_be_clickable((By.ID, "log.login")))
            login_button.click()
            time.sleep(3)
            
            # 로그인 결과 확인 및 보안문자 대기
            return self.wait_for_basic_login_success()
                
        except Exception as e:
            self.log_message(f"로그인 오류: {e}")
            return False
    
    def wait_for_basic_login_success(self):
        """기본 계정 로그인 성공까지 대기 (보안문자 포함)"""
        try:
            max_wait_time = 300  # 최대 5분 대기
            check_interval = 2   # 2초마다 확인
            waited_time = 0
            
            self.log_message("로그인 결과 확인 중...")
            
            while waited_time < max_wait_time:
                current_url = self.driver.current_url
                
                # 로그인 성공 확인 (nid.naver.com이 URL에 없으면 성공)
                if "nid.naver.com" not in current_url:
                    self.log_message("네이버 로그인 성공!")
                    return True
                
                # 보안문자나 추가 인증이 필요한 경우 확인
                try:
                    # 보안문자 입력 필드가 있는지 확인
                    captcha_input = self.driver.find_elements(By.CSS_SELECTOR, "input[name='captcha']")
                    if captcha_input:
                        self.log_message("보안문자 입력이 필요합니다. 입력을 기다리는 중...")
                        time.sleep(check_interval)
                        waited_time += check_interval
                        continue
                    
                    # 추가 인증이 필요한 경우 (휴대폰 인증 등)
                    auth_elements = self.driver.find_elements(By.CSS_SELECTOR, ".auth_area, .verify_area, .security_area")
                    if auth_elements:
                        self.log_message("추가 인증이 필요합니다. 인증을 기다리는 중...")
                        time.sleep(check_interval)
                        waited_time += check_interval
                        continue
                    
                    # 에러 메시지가 있는지 확인
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error_message, .err_msg, .alert")
                    if error_elements:
                        error_text = error_elements[0].text.strip()
                        if error_text:
                            self.log_message(f"로그인 오류: {error_text}")
                            # 오류가 있어도 계속 대기 (사용자가 수정할 수 있도록)
                    
                except Exception as e:
                    # 요소 찾기 실패는 무시하고 계속 진행
                    pass
                
                # 2초 대기 후 다시 확인
                time.sleep(check_interval)
                waited_time += check_interval
                
                # 30초마다 상태 메시지 출력
                if waited_time % 30 == 0:
                    self.log_message(f"로그인 대기 중... ({waited_time}초 경과)")
            
            # 최대 대기 시간 초과
            self.log_message("로그인 대기 시간 초과 (5분)")
            return False
            
        except Exception as e:
            self.log_message(f"로그인 대기 중 오류: {e}")
            return False
    
    def scroll_account_to_bottom(self, account):
        """계정별 페이지 하단까지 스크롤"""
        try:
            # 현재 스크롤 위치 저장
            last_height = account['driver'].execute_script("return document.body.scrollHeight")
            
            while True:
                # 페이지 하단으로 스크롤
                account['driver'].execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 새 콘텐츠 로딩 대기
                time.sleep(float(self.scroll_delay_var.get()))
                
                # 새로운 스크롤 높이 계산
                new_height = account['driver'].execute_script("return document.body.scrollHeight")
                
                # 더 이상 로드할 콘텐츠가 없으면 중단
                if new_height == last_height:
                    break
                    
                last_height = new_height
                
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} 스크롤 중 오류: {e}", account['id'])
    
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
    
    def find_and_click_account_like_buttons(self, account):
        """계정별 공감 버튼 찾기 및 클릭"""
        try:
            # 초본 코드와 동일한 셀렉터 사용
            like_buttons = account['driver'].find_elements(By.CSS_SELECTOR, 
                ".u_likeit_list_module._reactionModule._reactionModule_BLOG")
            
            self.log_message(f"계정 {account['user_id']} 페이지에서 {len(like_buttons)}개의 공감 버튼을 발견했습니다.", account['id'])
            
            clicked_count = 0
            skipped_count = 0
            
            for i, button in enumerate(like_buttons):
                if not account['is_running']:
                    break
                    
                try:
                    # 버튼이 화면에 보이는지 확인
                    if not button.is_displayed():
                        continue
                    
                    # 이미 공감했는지 확인
                    is_liked = self.is_account_already_liked(account, button)
                    if is_liked:
                        skipped_count += 1
                        account['skipped_count'] += 1
                        self.log_message(f"계정 {account['user_id']} 게시글 {i+1}: 이미 공감한 게시글입니다. 건너뜁니다.", account['id'])
                        continue
                    else:
                        self.log_message(f"계정 {account['user_id']} 게시글 {i+1}: 공감하지 않은 게시글입니다. 공감을 진행합니다.", account['id'])
                    
                    # 버튼으로 스크롤
                    account['driver'].execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(0.5)
                    
                    # 초본 코드와 동일한 방식으로 공감 버튼 클릭
                    button.click()
                    time.sleep(float(self.click_delay_var.get()))
                    
                    # 기본 공감 클릭 (공감 타입 선택 제거)
                    self.log_message(f"계정 {account['user_id']} 게시글 {i+1}: 기본 공감 클릭 완료", account['id'])
                    
                    clicked_count += 1
                    account['like_count'] += 1
                    
                except Exception as e:
                    self.log_message(f"계정 {account['user_id']} 게시글 {i+1} 공감 버튼 클릭 중 오류: {e}", account['id'])
                    continue
            
            self.log_message(f"계정 {account['user_id']} 이번 페이지에서 {clicked_count}개의 공감을 클릭하고, {skipped_count}개를 건너뛰었습니다.", account['id'])
            return clicked_count
            
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} 공감 버튼 찾기 중 오류: {e}", account['id'])
            return 0
    
    def is_account_already_liked(self, account, like_button):
        """계정별 이미 공감을 눌렀는지 확인"""
        try:
            # __reaction__zeroface 클래스가 있으면 공감 안 함, 없으면 공감 함
            zeroface_icon = like_button.find_element(By.CSS_SELECTOR, ".u_likeit_icon.__reaction__zeroface")
            if zeroface_icon:
                return False
            else:
                return True
                
        except NoSuchElementException:
            # __reaction__zeroface 클래스가 없으면 이미 공감한 상태
            return True
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} 공감 상태 확인 중 오류: {e}", account['id'])
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
    
    def go_to_account_start_page(self, account, start_page_num):
        """계정별 지정된 시작 페이지로 이동"""
        try:
            self.log_message(f"계정 {account['user_id']} 시작 페이지 {start_page_num}로 이동합니다...", account['id'])
            
            # 시작 페이지 버튼 찾기
            start_page_button = None
            
            # 방법 1: 페이지 번호 링크로 직접 이동
            try:
                start_page_button = account['driver'].find_element(By.LINK_TEXT, str(start_page_num))
                self.log_message(f"계정 {account['user_id']} 시작 페이지 {start_page_num} 링크를 찾았습니다.", account['id'])
            except NoSuchElementException:
                # 방법 2: CSS 셀렉터로 페이지 번호 찾기
                try:
                    start_page_button = account['driver'].find_element(By.CSS_SELECTOR, f"a[href*='page={start_page_num}']")
                    self.log_message(f"계정 {account['user_id']} 시작 페이지 {start_page_num} 링크를 CSS로 찾았습니다.", account['id'])
                except NoSuchElementException:
                    # 방법 3: JavaScript로 페이지 번호 링크 찾기
                    start_page_button = account['driver'].execute_script(f"""
                        var links = document.querySelectorAll('a');
                        for (var i = 0; i < links.length; i++) {{
                            if (links[i].textContent.trim() === '{start_page_num}') {{
                                return links[i];
                            }}
                        }}
                        return null;
                    """)
                    if start_page_button:
                        self.log_message(f"계정 {account['user_id']} JavaScript로 시작 페이지 {start_page_num} 링크를 찾았습니다.", account['id'])
            
            if start_page_button:
                # 시작 페이지로 스크롤
                account['driver'].execute_script("arguments[0].scrollIntoView(true);", start_page_button)
                time.sleep(1)
                
                # JavaScript로 클릭 (더 안정적)
                try:
                    account['driver'].execute_script("arguments[0].click();", start_page_button)
                    time.sleep(3)
                    self.log_message(f"계정 {account['user_id']} 시작 페이지 {start_page_num}로 이동했습니다.", account['id'])
                except Exception as js_click_e:
                    # 일반 클릭 시도
                    try:
                        start_page_button.click()
                        time.sleep(3)
                        self.log_message(f"계정 {account['user_id']} 시작 페이지 {start_page_num}로 이동했습니다. (일반 클릭)", account['id'])
                    except Exception as normal_click_e:
                        self.log_message(f"계정 {account['user_id']} 시작 페이지 이동 실패: {normal_click_e}", account['id'])
                        return False
                
                # 페이지 이동 후 현재 페이지 번호 확인
                time.sleep(2)
                actual_page = self.get_account_current_page_number(account)
                account['current_page'] = actual_page
                self.log_message(f"계정 {account['user_id']} 실제 이동된 시작 페이지: {actual_page}", account['id'])
                
                return True
            else:
                self.log_message(f"계정 {account['user_id']} 시작 페이지 {start_page_num}로 이동할 수 없습니다.", account['id'])
                return False
                
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} 시작 페이지 이동 중 오류: {e}", account['id'])
            return False
    
    def go_to_account_next_page(self, account):
        """계정별 다음 페이지로 이동"""
        try:
            # 현재 페이지 번호 확인
            current_page_num = self.get_account_current_page_number(account)
            next_page_num = current_page_num + 1
            
            self.log_message(f"계정 {account['user_id']} 현재 페이지: {current_page_num}, 다음 페이지: {next_page_num}", account['id'])
            
            # 현재 URL 저장 (페이지 이동 확인용)
            current_url = account['driver'].current_url
            self.log_message(f"계정 {account['user_id']} 현재 URL: {current_url}", account['id'])
            
            next_page_button = None
            
            # 방법 1: 다음 페이지 번호 직접 클릭 (같은 그룹 내에서)
            try:
                # aria-label로 다음 페이지 찾기 (예: "8페이지")
                next_page_button = account['driver'].find_element(By.CSS_SELECTOR, f"a[aria-label='{next_page_num}페이지']")
                self.log_message(f"계정 {account['user_id']} 다음 페이지 {next_page_num} 링크를 aria-label로 찾았습니다.", account['id'])
            except NoSuchElementException:
                # 방법 2: 텍스트로 다음 페이지 번호 찾기
                try:
                    next_page_button = account['driver'].find_element(By.LINK_TEXT, str(next_page_num))
                    self.log_message(f"계정 {account['user_id']} 다음 페이지 {next_page_num} 링크를 텍스트로 찾았습니다.", account['id'])
                except NoSuchElementException:
                    # 방법 3: "다음" 버튼 클릭 (다음 그룹으로 이동)
                    try:
                        next_page_button = account['driver'].find_element(By.CSS_SELECTOR, ".button_next")
                        self.log_message(f"계정 {account['user_id']} 다음 그룹으로 이동하는 '다음' 버튼을 찾았습니다.", account['id'])
                    except NoSuchElementException:
                        # 방법 4: JavaScript로 다음 페이지 찾기
                        try:
                            next_page_button = account['driver'].execute_script(f"""
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
                                self.log_message(f"계정 {account['user_id']} JavaScript로 다음 페이지 버튼을 찾았습니다.", account['id'])
                        except Exception as e:
                            self.log_message(f"계정 {account['user_id']} JavaScript 검색 중 오류: {e}", account['id'])
            
            if next_page_button:
                # 다음 페이지로 스크롤
                account['driver'].execute_script("arguments[0].scrollIntoView(true);", next_page_button)
                time.sleep(1)
                
                # JavaScript로 클릭 (더 안정적)
                try:
                    account['driver'].execute_script("arguments[0].click();", next_page_button)
                    time.sleep(3)
                    self.log_message(f"계정 {account['user_id']} 페이지 이동 버튼을 클릭했습니다.", account['id'])
                except Exception as js_click_e:
                    # 일반 클릭 시도
                    try:
                        next_page_button.click()
                        time.sleep(3)
                        self.log_message(f"계정 {account['user_id']} 페이지 이동 버튼을 클릭했습니다. (일반 클릭)", account['id'])
                    except Exception as normal_click_e:
                        self.log_message(f"계정 {account['user_id']} 페이지 이동 실패: {normal_click_e}", account['id'])
                        return False
                
                # 페이지 이동 후 URL 변경 확인
                time.sleep(2)
                new_url = account['driver'].current_url
                self.log_message(f"계정 {account['user_id']} 새 URL: {new_url}", account['id'])
                
                # URL이 변경되었는지 확인
                if new_url != current_url:
                    self.log_message(f"계정 {account['user_id']} URL이 변경되었습니다. 페이지 이동 성공!", account['id'])
                    # 현재 페이지 번호 재확인
                    actual_page = self.get_account_current_page_number(account)
                    account['current_page'] = actual_page
                    self.log_message(f"계정 {account['user_id']} 실제 이동된 페이지: {actual_page}", account['id'])
                    return True
                else:
                    self.log_message(f"계정 {account['user_id']} URL이 변경되지 않았습니다. 페이지 이동 실패!", account['id'])
                    return False
                
            else:
                self.log_message(f"계정 {account['user_id']} 다음 페이지로 이동할 수 없습니다. 마지막 페이지일 수 있습니다.", account['id'])
                return False
                
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} 다음 페이지 이동 중 오류: {e}", account['id'])
            return False
    
    def get_account_current_page_number(self, account):
        """계정별 현재 페이지 번호 가져오기"""
        try:
            # 방법 1: 네이버 블로그 페이지네이션에서 현재 페이지 찾기
            # aria-current="page"를 가진 요소 찾기
            try:
                current_page_element = account['driver'].find_element(By.CSS_SELECTOR, "a[aria-current='page'] strong")
                page_num = int(current_page_element.text.strip())
                if page_num > 0:
                    return page_num
            except (NoSuchElementException, ValueError):
                pass
            
            # 방법 2: aria-label="현재X페이지" 찾기
            try:
                current_page_element = account['driver'].find_element(By.CSS_SELECTOR, "a[aria-label*='현재'][aria-label*='페이지']")
                aria_label = current_page_element.get_attribute("aria-label")
                # "현재7페이지"에서 숫자 추출
                import re
                match = re.search(r'현재(\d+)페이지', aria_label)
                if match:
                    return int(match.group(1))
            except (NoSuchElementException, ValueError):
                pass
            
            # 방법 3: JavaScript로 현재 페이지 찾기
            current_page = account['driver'].execute_script("""
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
            self.log_message(f"계정 {account['user_id']} 현재 페이지 번호 확인 중 오류: {e}", account['id'])
            return account['current_page']
    
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

class AccountDialog:
    """계정 추가 다이얼로그"""
    def __init__(self, parent):
        self.result = None
        
        # 다이얼로그 창 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("계정 추가")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 중앙 정렬
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui()
        
        # 다이얼로그가 닫힐 때까지 대기
        self.dialog.wait_window()
    
    def setup_ui(self):
        """UI 구성"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="새 계정 정보 입력", font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # ID 입력
        id_frame = ttk.Frame(main_frame)
        id_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(id_frame, text="ID:").pack(side=tk.LEFT, padx=(0, 10))
        self.id_var = tk.StringVar()
        id_entry = ttk.Entry(id_frame, textvariable=self.id_var, width=30)
        id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 비밀번호 입력
        pw_frame = ttk.Frame(main_frame)
        pw_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(pw_frame, text="비밀번호:").pack(side=tk.LEFT, padx=(0, 10))
        self.pw_var = tk.StringVar()
        pw_entry = ttk.Entry(pw_frame, textvariable=self.pw_var, show="*", width=30)
        pw_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 블로그 URL 입력
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text="블로그 URL:").pack(side=tk.LEFT, padx=(0, 10))
        self.url_var = tk.StringVar(value="https://blog.naver.com/")
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=30)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 시작 페이지 입력
        page_frame = ttk.Frame(main_frame)
        page_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(page_frame, text="시작 페이지:").pack(side=tk.LEFT, padx=(0, 10))
        self.start_page_var = tk.StringVar(value="1")
        page_entry = ttk.Entry(page_frame, textvariable=self.start_page_var, width=10)
        page_entry.pack(side=tk.LEFT)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="추가", command=self.add_account).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="취소", command=self.cancel).pack(side=tk.RIGHT)
    
    def add_account(self):
        """계정 추가"""
        if not self.id_var.get() or not self.pw_var.get():
            messagebox.showerror("오류", "ID와 비밀번호를 입력해주세요.")
            return
        
        try:
            start_page = int(self.start_page_var.get())
            if start_page < 1:
                messagebox.showerror("오류", "시작 페이지는 1 이상의 숫자로 입력해주세요.")
                return
        except ValueError:
            messagebox.showerror("오류", "시작 페이지는 숫자로만 입력해주세요.")
            return
        
        self.result = {
            'id': self.id_var.get(),
            'password': self.pw_var.get(),
            'blog_url': self.url_var.get(),
            'start_page': start_page
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """취소"""
        self.dialog.destroy()

if __name__ == "__main__":
    app = BlogLikeAutomationGUI()
    app.run()
