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
import json
import re
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

# 현대적 Apple 스타일 색상
class Colors:
    # 라이트 모드 (iOS 17+ 스타일)
    BACKGROUND = "#F2F2F7"
    CARD = "#FFFFFF"
    PRIMARY_TEXT = "#000000"
    SECONDARY_TEXT = "#8E8E93"
    DIVIDER = "#C6C6C8"
    ACTION_BLUE = "#007AFF"
    ACTION_BLUE_HOVER = "#0051D5"
    ACTION_BLUE_DISABLED = "#AEAEB2"
    SUCCESS = "#30D158"
    WARNING = "#FF9F0A"
    ERROR = "#FF453A"

# 현대적 Apple 스타일 폰트
class Fonts:
    # Windows 현대적 폰트 (Inter, Pretendard 스타일)
    LARGE_TITLE_WIN = ("Inter", 32, "bold")
    TITLE_WIN = ("Inter", 24, "bold")
    HEADLINE_WIN = ("Inter", 20, "bold")
    BODY_WIN = ("Inter", 16, "normal")
    CALL_OUT_WIN = ("Inter", 15, "normal")
    SUBHEAD_WIN = ("Inter", 14, "normal")
    FOOTNOTE_WIN = ("Inter", 12, "normal")
    CAPTION_WIN = ("Inter", 11, "normal")
    
    # 폰트 폴백 시스템
    @staticmethod
    def get_font(font_type):
        try:
            return getattr(Fonts, font_type)
        except AttributeError:
            return ("Segoe UI", 14, "normal")

class AppleStyle:
    @staticmethod
    def configure_styles():
        """현대적 Apple 스타일 설정"""
        style = ttk.Style()
        
        # 기본 테마 설정
        style.theme_use('clam')
        
        # 프레임 스타일
        style.configure('Card.TFrame', 
                       background=Colors.CARD,
                       relief='flat',
                       borderwidth=0)
        
        # 라벨 스타일
        style.configure('Title.TLabel',
                       background=Colors.CARD,
                       foreground=Colors.PRIMARY_TEXT,
                       font=Fonts.get_font('TITLE_WIN'))
        
        style.configure('Headline.TLabel',
                       background=Colors.CARD,
                       foreground=Colors.PRIMARY_TEXT,
                       font=Fonts.get_font('HEADLINE_WIN'))
        
        style.configure('Body.TLabel',
                       background=Colors.CARD,
                       foreground=Colors.PRIMARY_TEXT,
                       font=Fonts.get_font('BODY_WIN'))
        
        style.configure('Secondary.TLabel',
                       background=Colors.CARD,
                       foreground=Colors.SECONDARY_TEXT,
                       font=Fonts.get_font('SUBHEAD_WIN'))
        
        # 버튼 스타일
        style.configure('Primary.TButton',
                       background=Colors.ACTION_BLUE,
                       foreground='white',
                       font=Fonts.get_font('BODY_WIN'),
                       relief='flat',
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Primary.TButton',
                 background=[('active', Colors.ACTION_BLUE_HOVER),
                           ('disabled', Colors.ACTION_BLUE_DISABLED)])
        
        style.configure('Secondary.TButton',
                       background=Colors.CARD,
                       foreground=Colors.ACTION_BLUE,
                       font=Fonts.get_font('BODY_WIN'),
                       relief='flat',
                       borderwidth=1,
                       focuscolor='none')
        
        style.map('Secondary.TButton',
                 background=[('active', Colors.BACKGROUND)])
        
        # 엔트리 스타일
        style.configure('Modern.TEntry',
                       fieldbackground=Colors.CARD,
                       foreground=Colors.PRIMARY_TEXT,
                       font=Fonts.get_font('BODY_WIN'),
                       relief='flat',
                       borderwidth=1,
                       focuscolor=Colors.ACTION_BLUE)
        
        # 체크박스 스타일
        style.configure('Modern.TCheckbutton',
                       background=Colors.CARD,
                       foreground=Colors.PRIMARY_TEXT,
                       font=Fonts.get_font('BODY_WIN'),
                       focuscolor='none')
        
        # 프로그레스바 스타일
        style.configure('Modern.Horizontal.TProgressbar',
                       background=Colors.ACTION_BLUE,
                       troughcolor=Colors.DIVIDER,
                       borderwidth=0,
                       lightcolor=Colors.ACTION_BLUE,
                       darkcolor=Colors.ACTION_BLUE)
        
        # 노트북 스타일
        style.configure('Modern.TNotebook',
                       background=Colors.CARD,
                       borderwidth=0)
        
        style.configure('Modern.TNotebook.Tab',
                       background=Colors.BACKGROUND,
                       foreground=Colors.SECONDARY_TEXT,
                       font=Fonts.get_font('SUBHEAD_WIN'),
                       padding=[20, 10],
                       borderwidth=0)
        
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', Colors.CARD),
                           ('active', Colors.BACKGROUND)],
                 foreground=[('selected', Colors.PRIMARY_TEXT),
                           ('active', Colors.ACTION_BLUE)])
    
    @staticmethod
    def create_modern_checkbox(parent, text, variable, **kwargs):
        """현대적인 체크박스 생성"""
        frame = tk.Frame(parent, bg=Colors.CARD)
        
        # 체크박스
        checkbox = ttk.Checkbutton(frame, 
                                 text=text, 
                                 variable=variable,
                                 style='Modern.TCheckbutton',
                                 **kwargs)
        checkbox.pack(side=tk.LEFT, padx=(0, 10))
        
        return frame, checkbox

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
        self.root.geometry("1400x900")
        self.root.configure(bg=Colors.BACKGROUND)
        
        # Apple 스타일 적용
        AppleStyle.configure_styles()
        
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
        self.end_page = None  # None이면 끝까지
        
        # 다중 계정 관리
        self.accounts = []
        self.account_threads = []
        self.account_logs = {}
        
        # 설정 파일 경로
        self.config_file = 'config.json'
        
        # config 초기화
        self.config = {}
        
        # 스케줄링 관련 변수 초기화
        self.scheduler_running = False
        self.scheduler = None
        
        # 실행 중인 계정 추적
        self.running_accounts = set()  # 실행 중인 계정 ID들을 저장
        
        self.setup_ui()
        
        # 설정 파일에서 계정 정보 로드
        self.load_config()
    
    
        
    def setup_ui(self):
        """현대적 Apple 스타일 UI 구성"""
        # 메인 컨테이너 (스크롤 가능)
        self.create_scrollable_container()
        
        # 헤더 섹션
        self.create_header()
        
        # 계정 관리 섹션
        self.create_account_section()
        
        # 설정 섹션
        self.create_settings_section()
        
        # 제어 섹션
        self.create_control_section()
        
        # 스케줄링 섹션
        self.create_schedule_section()
        
        # 진행 상황 섹션
        self.create_progress_section()
        
        # 로그 섹션
        self.create_log_section()
    
    def create_scrollable_container(self):
        """스크롤 가능한 메인 컨테이너 생성"""
        # 메인 캔버스
        self.main_canvas = tk.Canvas(self.root, bg=Colors.BACKGROUND, highlightthickness=0)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 스크롤 가능한 프레임
        self.scrollable_frame = ttk.Frame(self.main_canvas, style='Card.TFrame')
        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # 마우스 휠 이벤트 바인딩
        def _on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            self.main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.main_canvas.unbind_all("<MouseWheel>")
        
        self.main_canvas.bind('<Enter>', _bind_to_mousewheel)
        self.main_canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # 프레임 크기 업데이트
        def _on_frame_configure(event):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        
        self.scrollable_frame.bind('<Configure>', _on_frame_configure)
    
    def create_header(self):
        """헤더 섹션 생성"""
        header_frame = ttk.Frame(self.scrollable_frame, style='Card.TFrame', padding="20")
        header_frame.pack(fill=tk.X, padx=15, pady=(10, 0))
        
        # 제목
        title_label = ttk.Label(header_frame, 
                               text="네이버 블로그 공감 자동화", 
                               style='Title.TLabel')
        title_label.pack(anchor=tk.W)
        
        # 부제목
        subtitle_label = ttk.Label(header_frame, 
                                  text="다중 계정 지원 • 현대적 UI", 
                                  style='Secondary.TLabel')
        subtitle_label.pack(anchor=tk.W, pady=(2, 0))
        
    def create_account_section(self):
        """계정 관리 섹션 생성 (서로이웃_사전필터링.py 스타일)"""
        # 계정 관리 카드
        account_card = ttk.Frame(self.scrollable_frame, style='Card.TFrame', padding="15")
        account_card.pack(fill=tk.X, padx=15, pady=10)
        
        # 섹션 제목
        section_title = ttk.Label(account_card, text="계정 설정 (config.json 기반)", style='Headline.TLabel')
        section_title.pack(anchor=tk.W, pady=(0, 15))
        
        # 툴바 프레임
        toolbar_frame = ttk.Frame(account_card, style='Card.TFrame')
        toolbar_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 설정 저장/불러오기 버튼
        ttk.Button(toolbar_frame, text="💾 설정 저장", command=self.save_config_manual, 
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar_frame, text="📁 설정 불러오기", command=self.load_config, 
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar_frame, text="🔄 설정 초기화", command=self.reset_config, 
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 8))
        
        # 계정 그리드 생성
        self.create_account_grid(account_card)
        
        # 계정 관련 변수 초기화
        self.accounts_data = []
        self.selected_accounts = []
        self.account_checkboxes = {}
        self.account_checkbox_vars = {}
    
    def create_account_grid(self, parent):
        """계정 설정 그리드 생성 (서로이웃_사전필터링.py와 동일한 구조)"""
        # 그리드 컨테이너
        grid_frame = ttk.Frame(parent, style='Card.TFrame')
        grid_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 헤더 행
        headers = ["실행", "계정", "아이디", "비밀번호", "블로그 URL", "시작 페이지", "끝 페이지"]
        for i, header in enumerate(headers):
            header_label = ttk.Label(grid_frame, text=header, style='Secondary.TLabel')
            header_label.grid(row=0, column=i, padx=8, pady=(0, 8), sticky=tk.W)
        
        # 계정 1
        self.create_account_row(grid_frame, 1, "계정 1")
        
        # 계정 2
        self.create_account_row(grid_frame, 2, "계정 2")
        
        # 계정 3
        self.create_account_row(grid_frame, 3, "계정 3")
        
        # 그리드 컬럼 가중치 설정
        for i in range(7):
            grid_frame.columnconfigure(i, weight=1)
    
    def create_account_row(self, parent, row, account_name):
        """개별 계정 행 생성"""
        # 계정 데이터 로드
        account_data = self.config['accounts'][row-1] if self.config and len(self.config['accounts']) > row-1 else {}
        
        # 현대적 체크박스
        check_var = tk.BooleanVar(value=account_data.get('enabled', row == 1))
        setattr(self, f'account{row}_check', check_var)
        
        # 체크박스 프레임
        checkbox_frame = tk.Frame(parent, bg=Colors.CARD)
        checkbox_frame.grid(row=row, column=0, padx=8, pady=8, sticky=tk.W)
        
        checkbox = tk.Checkbutton(checkbox_frame, variable=check_var,
                                 bg=Colors.CARD, fg=Colors.ACTION_BLUE,
                                 activebackground=Colors.CARD,
                                 activeforeground=Colors.ACTION_BLUE,
                                 selectcolor=Colors.CARD,
                                 relief='flat', bd=0)
        checkbox.pack()
        
        # 계정 라벨
        account_label = ttk.Label(parent, text=account_name, style='Body.TLabel')
        account_label.grid(row=row, column=1, padx=8, pady=8, sticky=tk.W)
        
        # 아이디 입력
        id_entry = ttk.Entry(parent, style='Modern.TEntry', width=15)
        id_entry.grid(row=row, column=2, padx=8, pady=8, sticky=(tk.W, tk.E))
        id_entry.insert(0, account_data.get('id', f'아이디{row}'))
        setattr(self, f'account{row}_id', id_entry)
        
        # 비밀번호 입력
        pw_entry = ttk.Entry(parent, style='Modern.TEntry', width=15, show="*")
        pw_entry.grid(row=row, column=3, padx=8, pady=8, sticky=(tk.W, tk.E))
        pw_entry.insert(0, account_data.get('password', f'비밀번호{row}'))
        setattr(self, f'account{row}_pw', pw_entry)
        
        # 블로그 URL 입력
        url_entry = ttk.Entry(parent, style='Modern.TEntry', width=20)
        url_entry.grid(row=row, column=4, padx=8, pady=8, sticky=(tk.W, tk.E))
        url_entry.insert(0, account_data.get('blog_url', 'https://blog.naver.com/'))
        setattr(self, f'account{row}_url', url_entry)
        
        # 시작 페이지 입력
        start_page_entry = ttk.Entry(parent, style='Modern.TEntry', width=8)
        start_page_entry.grid(row=row, column=5, padx=8, pady=8, sticky=(tk.W, tk.E))
        start_page_entry.insert(0, str(account_data.get('start_page', 1)))
        setattr(self, f'account{row}_start_page', start_page_entry)
        
        # 끝 페이지 입력
        end_page_entry = ttk.Entry(parent, style='Modern.TEntry', width=8)
        end_page_entry.grid(row=row, column=6, padx=8, pady=8, sticky=(tk.W, tk.E))
        end_page_entry.insert(0, str(account_data.get('end_page', '')))
        setattr(self, f'account{row}_end_page', end_page_entry)
    
    def create_settings_section(self):
        """설정 섹션 생성"""
        # 설정 카드
        settings_card = ttk.Frame(self.scrollable_frame, style='Card.TFrame', padding="15")
        settings_card.pack(fill=tk.X, padx=15, pady=10)
        
        # 섹션 제목
        section_title = ttk.Label(settings_card, text="자동화 설정", style='Headline.TLabel')
        section_title.pack(anchor=tk.W, pady=(0, 10))
        
        # 설정 그리드
        settings_grid = ttk.Frame(settings_card, style='Card.TFrame')
        settings_grid.pack(fill=tk.X)
        
        # 딜레이 설정
        delay_frame = ttk.Frame(settings_grid, style='Card.TFrame')
        delay_frame.pack(fill=tk.X)
        
        # 스크롤 딜레이
        ttk.Label(delay_frame, text="스크롤 딜레이 (초)", style='Body.TLabel').pack(side=tk.LEFT, padx=(0, 8))
        self.scroll_delay_var = tk.StringVar(value="2")
        scroll_delay_entry = ttk.Entry(delay_frame, textvariable=self.scroll_delay_var, 
                                      style='Modern.TEntry', width=6)
        scroll_delay_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # 클릭 딜레이
        ttk.Label(delay_frame, text="클릭 딜레이 (초)", style='Body.TLabel').pack(side=tk.LEFT, padx=(0, 8))
        self.click_delay_var = tk.StringVar(value="1")
        click_delay_entry = ttk.Entry(delay_frame, textvariable=self.click_delay_var, 
                                     style='Modern.TEntry', width=6)
        click_delay_entry.pack(side=tk.LEFT)
    
    def create_control_section(self):
        """제어 섹션 생성"""
        # 제어 카드
        control_card = ttk.Frame(self.scrollable_frame, style='Card.TFrame', padding="15")
        control_card.pack(fill=tk.X, padx=15, pady=10)
        
        # 섹션 제목
        section_title = ttk.Label(control_card, text="자동화 제어", style='Headline.TLabel')
        section_title.pack(anchor=tk.W, pady=(0, 10))
        
        # 버튼 프레임
        button_frame = ttk.Frame(control_card, style='Card.TFrame')
        button_frame.pack(fill=tk.X)
        
        # 시작 버튼
        self.start_button = ttk.Button(button_frame, 
                                      text="선택된 계정 시작", 
                                      command=self.start_selected_accounts,
                                      style='Primary.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 중지 버튼
        self.stop_button = ttk.Button(button_frame, 
                                     text="모든 계정 중지", 
                                     command=self.stop_all_accounts,
                                     style='Secondary.TButton')
        self.stop_button.pack(side=tk.LEFT)
    
    def create_schedule_section(self):
        """스케줄링 섹션 생성"""
        # 스케줄링 카드
        schedule_card = ttk.Frame(self.scrollable_frame, style='Card.TFrame', padding="15")
        schedule_card.pack(fill=tk.X, padx=15, pady=10)
        
        # 섹션 제목
        section_title = ttk.Label(schedule_card, text="스케줄링 설정", style='Headline.TLabel')
        section_title.pack(anchor=tk.W, pady=(0, 15))
        
        # 스케줄링 옵션
        options_frame = ttk.Frame(schedule_card, style='Card.TFrame')
        options_frame.pack(fill=tk.X)
        
        # 스케줄링 활성화 체크박스
        self.schedule_enabled = tk.BooleanVar(value=False)
        schedule_check = ttk.Checkbutton(options_frame, text="스케줄링 활성화", 
                                       variable=self.schedule_enabled, style='Modern.TCheckbutton')
        schedule_check.pack(anchor=tk.W, pady=(0, 10))
        
        # 스케줄링 설정 프레임
        schedule_settings_frame = ttk.Frame(options_frame, style='Card.TFrame')
        schedule_settings_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 간격 설정
        interval_frame = ttk.Frame(schedule_settings_frame, style='Card.TFrame')
        interval_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(interval_frame, text="실행 간격 (시간)", style='Body.TLabel').pack(side=tk.LEFT, padx=(0, 8))
        self.interval_var = tk.StringVar(value="24")
        interval_entry = ttk.Entry(interval_frame, textvariable=self.interval_var, 
                                  style='Modern.TEntry', width=8)
        interval_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # 특정 시간 설정
        time_frame = ttk.Frame(schedule_settings_frame, style='Card.TFrame')
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(time_frame, text="특정 시간 (HH:MM, 쉼표로 구분)", style='Body.TLabel').pack(anchor=tk.W)
        self.specific_times_var = tk.StringVar(value="09:00, 18:00")
        time_entry = ttk.Entry(time_frame, textvariable=self.specific_times_var, 
                              style='Modern.TEntry')
        time_entry.pack(fill=tk.X, pady=(5, 0))
        
        # 요일 설정
        days_frame = ttk.Frame(schedule_settings_frame, style='Card.TFrame')
        days_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(days_frame, text="실행 요일", style='Body.TLabel').pack(anchor=tk.W)
        
        days_check_frame = ttk.Frame(days_frame, style='Card.TFrame')
        days_check_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 요일 체크박스들
        self.days_vars = {}
        days = ["월", "화", "수", "목", "금", "토", "일"]
        days_en = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for i, (day_ko, day_en) in enumerate(zip(days, days_en)):
            var = tk.BooleanVar(value=True)
            self.days_vars[day_en] = var
            check = ttk.Checkbutton(days_check_frame, text=day_ko, variable=var, 
                                   style='Modern.TCheckbutton')
            check.pack(side=tk.LEFT, padx=(0, 8))
        
        # 스케줄링 상태 표시
        status_frame = ttk.Frame(schedule_card, style='Card.TFrame')
        status_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.schedule_status_var = tk.StringVar(value="스케줄러 비활성화")
        status_label = ttk.Label(status_frame, textvariable=self.schedule_status_var, 
                                style='Secondary.TLabel')
        status_label.pack(anchor=tk.W)
        
        # 스케줄링 버튼들
        button_frame = ttk.Frame(schedule_card, style='Card.TFrame')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_scheduler_btn = ttk.Button(button_frame, text="🚀 스케줄러 시작", 
                                            command=self.start_scheduler, 
                                            style='Primary.TButton')
        self.start_scheduler_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_scheduler_btn = ttk.Button(button_frame, text="⏹️ 스케줄러 중단", 
                                           command=self.stop_scheduler, state='disabled', 
                                           style='Secondary.TButton')
        self.stop_scheduler_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_schedule_btn = ttk.Button(button_frame, text="💾 스케줄 저장", 
                                          command=self.save_schedule_config, 
                                          style='Secondary.TButton')
        self.save_schedule_btn.pack(side=tk.LEFT)
    
    def create_progress_section(self):
        """진행 상황 섹션 생성"""
        # 진행 상황 카드
        progress_card = ttk.Frame(self.scrollable_frame, style='Card.TFrame', padding="15")
        progress_card.pack(fill=tk.X, padx=15, pady=10)
        
        # 섹션 제목
        section_title = ttk.Label(progress_card, text="진행 상황", style='Headline.TLabel')
        section_title.pack(anchor=tk.W, pady=(0, 10))
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_card, 
                                           variable=self.progress_var, 
                                           maximum=100, 
                                           style='Modern.Horizontal.TProgressbar')
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))
        
        # 상태 정보 프레임
        status_frame = ttk.Frame(progress_card, style='Card.TFrame')
        status_frame.pack(fill=tk.X)
        
        # 상태 라벨
        self.status_var = tk.StringVar(value="대기 중...")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, style='Body.TLabel')
        status_label.pack(side=tk.LEFT)
        
        # 통계 라벨
        self.stats_var = tk.StringVar(value="공감: 0개, 건너뜀: 0개, 페이지: 1")
        stats_label = ttk.Label(status_frame, textvariable=self.stats_var, style='Secondary.TLabel')
        stats_label.pack(side=tk.RIGHT)
    
    def create_log_section(self):
        """로그 섹션 생성"""
        # 로그 카드
        log_card = ttk.Frame(self.scrollable_frame, style='Card.TFrame', padding="15")
        log_card.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # 섹션 제목
        section_title = ttk.Label(log_card, text="실행 로그", style='Headline.TLabel')
        section_title.pack(anchor=tk.W, pady=(0, 10))
        
        # 로그 텍스트 영역
        self.log_text = scrolledtext.ScrolledText(log_card, 
                                                 height=12, 
                                                 bg=Colors.CARD,
                                                 fg=Colors.PRIMARY_TEXT,
                                                 font=Fonts.get_font('SUBHEAD_WIN'),
                                                 relief='flat',
                                                 borderwidth=1,
                                                 wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 계정별 로그 탭들을 저장할 딕셔너리
        self.account_log_frames = {}
        self.account_log_texts = {}
        
    def update_account_list_display(self):
        """계정 목록 표시 업데이트 (테이블 기반에서는 불필요)"""
        # 테이블 기반 UI에서는 이 메서드가 필요하지 않음
        # 계정 정보는 테이블에서 직접 관리됨
        pass
    
    def toggle_account_selection(self, event):
        """계정 선택 상태 토글 (테이블 기반에서는 불필요)"""
        # 테이블 기반 UI에서는 체크박스를 직접 클릭하여 토글
        pass
    
    def update_account_selection(self):
        """계정 선택 상태 업데이트 (테이블 기반에서는 불필요)"""
        # 테이블 기반 UI에서는 이 메서드가 필요하지 않음
        pass
    
    def select_all_accounts(self):
        """모든 계정 선택 (테이블 기반)"""
        for i in range(1, 4):  # 계정 1, 2, 3
            check_var = getattr(self, f'account{i}_check', None)
            if check_var:
                check_var.set(True)
    
    def deselect_all_accounts(self):
        """모든 계정 선택 해제 (테이블 기반)"""
        for i in range(1, 4):  # 계정 1, 2, 3
            check_var = getattr(self, f'account{i}_check', None)
            if check_var:
                check_var.set(False)
    
    def get_selected_accounts(self):
        """선택된 계정들을 반환 (테이블 기반)"""
        selected_accounts = []
        for i in range(1, 4):  # 계정 1, 2, 3
            check_var = getattr(self, f'account{i}_check', None)
            id_entry = getattr(self, f'account{i}_id', None)
            pw_entry = getattr(self, f'account{i}_pw', None)
            url_entry = getattr(self, f'account{i}_url', None)
            start_page_entry = getattr(self, f'account{i}_start_page', None)
            end_page_entry = getattr(self, f'account{i}_end_page', None)
            
            if all([check_var, id_entry, pw_entry, url_entry, start_page_entry, end_page_entry]):
                if check_var.get():  # 체크박스가 선택된 경우
                    account_data = {
                        'id': id_entry.get().strip(),  # account_automation_worker에서 사용
                        'user_id': id_entry.get().strip(),
                        'password': pw_entry.get().strip(),
                        'blog_url': url_entry.get().strip(),
                        'start_page': int(start_page_entry.get()) if start_page_entry.get().strip() else 1,
                        'end_page': int(end_page_entry.get()) if end_page_entry.get().strip() else None,
                        'selected': True,
                        'is_running': False,  # 새로 시작하는 계정이므로 False로 설정
                        'current_page': int(start_page_entry.get()) if start_page_entry.get().strip() else 1,
                        'liked_count': 0,
                        'skipped_count': 0,
                        'driver': None,  # WebDriver 인스턴스
                        'wait': None,   # WebDriverWait 인스턴스
                        'status': '대기중'
                    }
                    if account_data['user_id'] and account_data['password']:  # 아이디와 비밀번호가 있는 경우만
                        selected_accounts.append(account_data)
        return selected_accounts
    
    def start_selected_accounts(self):
        """선택된 계정들만 시작"""
        self.log_message("선택된 계정 시작 버튼 클릭됨")
        selected_accounts = self.get_selected_accounts()
        self.log_message(f"선택된 계정 수: {len(selected_accounts)}")
        
        if not selected_accounts:
            messagebox.showwarning("경고", "시작할 계정을 선택해주세요.")
            self.log_message("선택된 계정이 없습니다.")
            return
        
        self.log_message(f"선택된 계정들: {[acc['user_id'] for acc in selected_accounts]}")
        
        # 선택된 계정들만 5초 간격으로 시작
        start_thread = threading.Thread(target=self.start_selected_accounts_with_delay, 
                                      args=(selected_accounts,), daemon=True)
        start_thread.start()
        self.log_message("계정 시작 스레드가 시작되었습니다.")
    
    def start_scheduler(self):
        """스케줄러 시작"""
        try:
            if self.scheduler_running:
                messagebox.showwarning("경고", "스케줄러가 이미 실행 중입니다.")
                return
            
            # 스케줄링 활성화 확인 및 자동 활성화
            if not self.schedule_enabled.get():
                self.log_message("⚠️ 스케줄링이 비활성화되어 있습니다. 자동으로 활성화합니다.")
                self.schedule_enabled.set(True)
            
            # 활성화된 계정 확인
            enabled_accounts = []
            for i in range(1, 4):  # 계정 1, 2, 3
                check_var = getattr(self, f'account{i}_check', None)
                id_entry = getattr(self, f'account{i}_id', None)
                pw_entry = getattr(self, f'account{i}_pw', None)
                
                if check_var and id_entry and pw_entry:
                    if check_var.get() and id_entry.get().strip() and pw_entry.get().strip():
                        enabled_accounts.append(f"계정 {i}")
            
            if not enabled_accounts:
                self.log_message("❌ 활성화된 계정이 없습니다.")
                messagebox.showerror("오류", "스케줄러를 시작하려면 최소 하나의 계정을 활성화하고 아이디/비밀번호를 입력해야 합니다.")
                return
            
            self.log_message(f"✅ 활성화된 계정: {', '.join(enabled_accounts)}")
            
            # 스케줄 설정 저장
            self.save_schedule_config()
            
            # 스케줄러 시작 (간단한 구현)
            self.scheduler_running = True
            self.schedule_status_var.set("스케줄러 실행 중...")
            self.start_scheduler_btn.config(state='disabled')
            self.stop_scheduler_btn.config(state='normal')
            
            # 스케줄 설정 정보 로그
            interval = self.interval_var.get()
            times = self.specific_times_var.get()
            enabled_days = [day for day, var in self.days_vars.items() if var.get()]
            
            self.log_message("🚀 스케줄러가 시작되었습니다.")
            self.log_message(f"📋 설정 정보:")
            self.log_message(f"   - 실행 간격: {interval}시간")
            self.log_message(f"   - 특정 시간: {times}")
            self.log_message(f"   - 실행 요일: {', '.join(enabled_days)}")
            
            messagebox.showinfo("성공", "스케줄러가 시작되었습니다!")
            
            # 스케줄러 스레드 시작
            scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
            scheduler_thread.start()
            
        except Exception as e:
            self.log_message(f"스케줄러 시작 중 오류: {e}")
            messagebox.showerror("오류", f"스케줄러 시작 중 오류가 발생했습니다: {e}")
    
    def stop_scheduler(self):
        """스케줄러 중단"""
        try:
            if not self.scheduler_running:
                messagebox.showwarning("경고", "스케줄러가 실행 중이 아닙니다.")
                return
            
            self.scheduler_running = False
            self.schedule_status_var.set("스케줄러 중단됨")
            self.start_scheduler_btn.config(state='normal')
            self.stop_scheduler_btn.config(state='disabled')
            self.log_message("⏹️ 스케줄러가 중단되었습니다.")
            messagebox.showinfo("완료", "스케줄러가 중단되었습니다.")
            
        except Exception as e:
            self.log_message(f"스케줄러 중단 중 오류: {e}")
            messagebox.showerror("오류", f"스케줄러 중단 중 오류가 발생했습니다: {e}")
    
    def scheduler_loop(self):
        """스케줄러 메인 루프"""
        self.log_message("🔄 스케줄러 루프가 시작되었습니다.")
        
        # 초기 디버깅 로그
        self.log_message("🔧 스케줄러 초기화 중...")
        
        while self.scheduler_running:
            try:
                # 현재 시간 확인
                now = time.time()
                current_time = time.strftime("%H:%M")
                current_weekday_korean = time.strftime("%A")
                
                # 한국어 요일을 영어로 변환
                weekday_map = {
                    '월요일': 'monday',
                    '화요일': 'tuesday', 
                    '수요일': 'wednesday',
                    '목요일': 'thursday',
                    '금요일': 'friday',
                    '토요일': 'saturday',
                    '일요일': 'sunday'
                }
                current_weekday = weekday_map.get(current_weekday_korean, current_weekday_korean.lower())
                
                # 요일 확인
                day_var = self.days_vars.get(current_weekday)
                if day_var is None:
                    time.sleep(60)
                    continue
                
                if not day_var.get():
                    time.sleep(60)
                    continue
                
                # 특정 시간 확인
                specific_times_str = self.specific_times_var.get()
                specific_times = [t.strip() for t in specific_times_str.split(',') if t.strip()]
                
                if current_time in specific_times:
                    # 중복 실행 방지: 마지막 실행 시간 확인
                    if not hasattr(self, 'last_scheduled_run') or (now - self.last_scheduled_run) > 300:  # 5분 이상 차이
                        self.log_message(f"⏰ 스케줄된 시간 {current_time}에 자동화를 시작합니다.")
                        self.start_selected_accounts()
                        self.last_scheduled_run = now
                    else:
                        self.log_message(f"⏰ 스케줄된 시간 {current_time}이지만 최근에 실행되어 건너뜁니다.")
                    time.sleep(60)  # 1분 대기 (같은 시간에 중복 실행 방지)
                
                # 간격 기반 실행 (24시간마다)
                interval_hours = int(self.interval_var.get()) if self.interval_var.get().isdigit() else 24
                if not hasattr(self, 'last_run_time'):
                    self.last_run_time = now
                
                if now - self.last_run_time >= interval_hours * 3600:  # 시간을 초로 변환
                    # 중복 실행 방지: 마지막 실행 시간 확인
                    if not hasattr(self, 'last_interval_run') or (now - self.last_interval_run) > 300:  # 5분 이상 차이
                        self.log_message(f"⏰ {interval_hours}시간 간격으로 자동화를 시작합니다.")
                        self.start_selected_accounts()
                        self.last_interval_run = now
                    else:
                        self.log_message(f"⏰ {interval_hours}시간 간격이지만 최근에 실행되어 건너뜁니다.")
                    self.last_run_time = now
                
                time.sleep(60)  # 1분마다 체크
                
            except Exception as e:
                self.log_message(f"❌ 스케줄러 루프 오류: {e}")
                import traceback
                self.log_message(f"❌ 상세 오류: {traceback.format_exc()}")
                time.sleep(60)
    
    def save_schedule_config(self):
        """스케줄 설정 저장"""
        try:
            # 현재 config.json 로드 (기존 데이터 보존)
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                config_data = {}
            
            # 스케줄 설정 업데이트 (기존 accounts, automation_settings는 그대로 유지)
            config_data['automation_schedule'] = {
                'enabled': self.schedule_enabled.get(),
                'interval_hours': int(self.interval_var.get()) if self.interval_var.get().isdigit() else 24,
                'specific_times': [t.strip() for t in self.specific_times_var.get().split(',') if t.strip()],
                'days': {day: var.get() for day, var in self.days_vars.items()}
            }
            
            # config.json에 저장 (기존 데이터는 그대로 유지)
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.log_message("💾 스케줄 설정이 저장되었습니다.")
            
        except Exception as e:
            self.log_message(f"스케줄 설정 저장 중 오류: {e}")
            messagebox.showerror("오류", f"스케줄 설정 저장 중 오류가 발생했습니다: {e}")
    
    def start_selected_accounts_with_delay(self, selected_accounts):
        """선택된 계정들을 5초 간격으로 시작"""
        started_count = 0
        
        # 이미 실행 중인 계정이 있는지 확인
        already_running = []
        for account in selected_accounts:
            if account['user_id'] in self.running_accounts:
                already_running.append(account['user_id'])
        
        if already_running:
            self.log_message(f"⚠️ 이미 실행 중인 계정이 있습니다: {already_running}")
            return
        
        for i, account in enumerate(selected_accounts):
            # 첫 번째 계정이 아닌 경우 5초 대기
            if i > 0:
                self.log_message(f"다음 계정 시작까지 5초 대기 중...")
                time.sleep(5)
            
            # 실행 중인 계정 목록에 추가
            self.running_accounts.add(account['user_id'])
            
            # 각 계정을 독립적인 스레드에서 실행
            thread = threading.Thread(target=self.account_automation_worker, 
                                    args=(account,), daemon=True)
            thread.start()
            self.account_threads.append(thread)
            account['is_running'] = True
            started_count += 1
            self.log_message(f"계정 {account['user_id']} 시작됨 (독립 세션)")
        
        if started_count > 0:
            self.log_message(f"{started_count}개 계정이 5초 간격으로 독립 실행되었습니다.")
        else:
            self.log_message("시작할 수 있는 계정이 없습니다.")
    
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
    
    def load_config(self):
        """config.json에서 설정을 불러옵니다 (테이블 기반)."""
        try:
            if not os.path.exists('config.json'):
                self.log_message("config.json 파일이 없습니다. 기본 설정을 사용합니다.")
                self.initialize_default_table_values()
                return
            
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self.log_message("config.json에서 설정을 불러왔습니다.")
            
            # 테이블에 계정 데이터 로드
            if 'accounts' in self.config:
                for i, account_data in enumerate(self.config['accounts'][:3]):  # 최대 3개 계정
                    row = i + 1
                    
                    # 체크박스 설정
                    check_var = getattr(self, f'account{row}_check', None)
                    if check_var:
                        check_var.set(account_data.get('enabled', True))
                    
                    # 아이디 설정
                    id_entry = getattr(self, f'account{row}_id', None)
                    if id_entry:
                        id_entry.delete(0, tk.END)
                        id_entry.insert(0, account_data.get('id', ''))
                    
                    # 비밀번호 설정
                    pw_entry = getattr(self, f'account{row}_pw', None)
                    if pw_entry:
                        pw_entry.delete(0, tk.END)
                        pw_entry.insert(0, account_data.get('password', ''))
                    
                    # 블로그 URL 설정
                    url_entry = getattr(self, f'account{row}_url', None)
                    if url_entry:
                        url_entry.delete(0, tk.END)
                        url_entry.insert(0, account_data.get('blog_url', 'https://blog.naver.com/'))
                    
                    # 시작 페이지 설정
                    start_page_entry = getattr(self, f'account{row}_start_page', None)
                    if start_page_entry:
                        start_page_entry.delete(0, tk.END)
                        start_page_entry.insert(0, str(account_data.get('start_page', 1)))
                    
                    # 끝 페이지 설정
                    end_page_entry = getattr(self, f'account{row}_end_page', None)
                    if end_page_entry:
                        end_page_entry.delete(0, tk.END)
                        end_page_entry.insert(0, str(account_data.get('end_page', '')))
            
            # 자동화 설정 불러오기
            if 'automation_settings' in self.config:
                settings = self.config['automation_settings']
                self.scroll_delay_var.set(str(settings.get('scroll_delay', 2)))
                self.click_delay_var.set(str(settings.get('click_delay', 1)))
            
            # 스케줄 설정 불러오기
            if 'automation_schedule' in self.config:
                schedule = self.config['automation_schedule']
                self.schedule_enabled.set(schedule.get('enabled', False))
                self.interval_var.set(str(schedule.get('interval_hours', 24)))
                
                # specific_times 처리 (리스트 또는 문자열)
                specific_times = schedule.get('specific_times', ['09:00', '18:00'])
                if isinstance(specific_times, list):
                    self.specific_times_var.set(', '.join(specific_times))
                else:
                    self.specific_times_var.set(specific_times)
                
                # 요일 설정 불러오기
                days_config = schedule.get('days', {})
                for day, var in self.days_vars.items():
                    var.set(days_config.get(day, True))
                
                self.log_message(f"스케줄 설정 불러옴: 활성화={schedule.get('enabled')}, 간격={schedule.get('interval_hours')}시간, 시간={specific_times}")
            
            messagebox.showinfo("불러오기 완료", "설정을 config.json에서 불러왔습니다.")
            
        except Exception as e:
            self.log_message(f"설정 파일 불러오기 중 오류: {e}")
            messagebox.showerror("불러오기 오류", f"설정 불러오기 중 오류가 발생했습니다: {e}")
            # 기본값으로 초기화 (add_default_accounts 대신 테이블 직접 초기화)
            self.initialize_default_table_values()
            
        # 계정 목록 표시 업데이트
        self.update_account_list_display()
    
    def initialize_default_table_values(self):
        """테이블을 기본값으로 초기화"""
        try:
            # 기본 계정 데이터
            default_accounts = [
                {
                    'id': 'cms045757',
                    'password': '!7476458aA',
                    'blog_url': 'https://blog.naver.com/',
                    'start_page': 1,
                    'end_page': None,
                    'enabled': True
                },
                {
                    'id': 'chldudwns645',
                    'password': '981749aA',
                    'blog_url': 'https://blog.naver.com/',
                    'start_page': 1,
                    'end_page': None,
                    'enabled': False
                },
                {
                    'id': 'minaci_',
                    'password': '민아4376!',
                    'blog_url': 'https://blog.naver.com/',
                    'start_page': 1,
                    'end_page': None,
                    'enabled': False
                }
            ]
            
            # 테이블에 기본값 설정
            for i, account_data in enumerate(default_accounts):
                row = i + 1
                
                # 체크박스 설정
                check_var = getattr(self, f'account{row}_check', None)
                if check_var:
                    check_var.set(account_data.get('enabled', False))
                
                # 아이디 설정
                id_entry = getattr(self, f'account{row}_id', None)
                if id_entry:
                    id_entry.delete(0, tk.END)
                    id_entry.insert(0, account_data.get('id', ''))
                
                # 비밀번호 설정
                pw_entry = getattr(self, f'account{row}_pw', None)
                if pw_entry:
                    pw_entry.delete(0, tk.END)
                    pw_entry.insert(0, account_data.get('password', ''))
                
                # 블로그 URL 설정
                url_entry = getattr(self, f'account{row}_url', None)
                if url_entry:
                    url_entry.delete(0, tk.END)
                    url_entry.insert(0, account_data.get('blog_url', 'https://blog.naver.com/'))
                
                # 시작 페이지 설정
                start_page_entry = getattr(self, f'account{row}_start_page', None)
                if start_page_entry:
                    start_page_entry.delete(0, tk.END)
                    start_page_entry.insert(0, str(account_data.get('start_page', 1)))
                
                # 끝 페이지 설정
                end_page_entry = getattr(self, f'account{row}_end_page', None)
                if end_page_entry:
                    end_page_entry.delete(0, tk.END)
                    end_page_entry.insert(0, str(account_data.get('end_page', '')))
            
            self.log_message("기본 계정 설정으로 초기화되었습니다.")
            
        except Exception as e:
            self.log_message(f"기본값 초기화 중 오류: {e}")
    
    def save_config(self):
        """현재 설정을 config.json 파일에 저장합니다."""
        try:
            config = {
                "accounts": [],
                "settings": {
                    "window_title": "네이버 블로그 공감 자동화 프로그램",
                    "window_size": "1200x800",
                    "log_height": 15,
                    "log_width": 80
                }
            }
            
            # 계정 정보 저장
            for account in self.accounts:
                account_config = {
                    "enabled": True,
                    "id": account['user_id'],
                    "password": account['password'],
                    "blog_url": account['blog_url'],
                    "start_page": account['start_page'],
                    "end_page": account.get('end_page')
                }
                config["accounts"].append(account_config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.log_message(f"설정 파일 저장 완료: {self.config_file}")
            
        except Exception as e:
            self.log_message(f"설정 파일 저장 중 오류: {e}")
            messagebox.showerror("저장 오류", f"설정 저장 중 오류가 발생했습니다: {e}")
    
    def save_config_manual(self):
        """설정을 config.json에 저장 (테이블 기반)"""
        try:
            # 기존 config.json 로드 (모든 데이터 보존)
            config_data = {}
            if os.path.exists('config.json'):
                try:
                    with open('config.json', 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    self.log_message("기존 config.json을 로드했습니다.")
                except Exception as load_e:
                    self.log_message(f"기존 config.json 로드 실패: {load_e}")
                    config_data = {}
            
            # 테이블에서 계정 데이터 수집
            accounts = []
            for i in range(1, 4):  # 계정 1, 2, 3
                check_var = getattr(self, f'account{i}_check', None)
                id_entry = getattr(self, f'account{i}_id', None)
                pw_entry = getattr(self, f'account{i}_pw', None)
                url_entry = getattr(self, f'account{i}_url', None)
                start_page_entry = getattr(self, f'account{i}_start_page', None)
                end_page_entry = getattr(self, f'account{i}_end_page', None)
                
                if all([check_var, id_entry, pw_entry, url_entry, start_page_entry, end_page_entry]):
                    # 빈 값이 아닌 계정만 저장
                    if id_entry.get().strip() and pw_entry.get().strip():
                        account_data = {
                            'id': id_entry.get().strip(),
                            'password': pw_entry.get().strip(),
                            'blog_url': url_entry.get().strip(),
                            'start_page': int(start_page_entry.get()) if start_page_entry.get().strip() else 1,
                            'end_page': int(end_page_entry.get()) if end_page_entry.get().strip() else None,
                            'enabled': check_var.get()
                        }
                        accounts.append(account_data)
            
            # 계정 데이터 업데이트
            config_data['accounts'] = accounts
            
            # 자동화 설정 업데이트
            config_data['automation_settings'] = {
                'scroll_delay': float(self.scroll_delay_var.get()) if self.scroll_delay_var.get() else 2.0,
                'click_delay': float(self.click_delay_var.get()) if self.click_delay_var.get() else 1.0
            }
            
            # config.json 파일에 저장 (기존 automation_schedule 등은 그대로 유지)
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.log_message(f"설정 저장 완료: 계정 {len(accounts)}개, 자동화 설정, 기존 스케줄 설정 유지")
            messagebox.showinfo("성공", "설정이 config.json에 저장되었습니다.")
            
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 중 오류가 발생했습니다: {str(e)}")
            self.log_message(f"설정 저장 오류: {str(e)}")
    
    def reset_config(self):
        """설정을 초기화합니다."""
        if messagebox.askyesno("설정 초기화", "모든 계정 설정을 초기화하시겠습니까?"):
            # 테이블의 모든 입력 필드 초기화
            for i in range(1, 4):  # 계정 1, 2, 3
                # 체크박스 초기화
                check_var = getattr(self, f'account{i}_check', None)
                if check_var:
                    check_var.set(i == 1)  # 첫 번째 계정만 체크
                
                # 아이디 초기화
                id_entry = getattr(self, f'account{i}_id', None)
                if id_entry:
                    id_entry.delete(0, tk.END)
                    id_entry.insert(0, f'아이디{i}')
                
                # 비밀번호 초기화
                pw_entry = getattr(self, f'account{i}_pw', None)
                if pw_entry:
                    pw_entry.delete(0, tk.END)
                    pw_entry.insert(0, f'비밀번호{i}')
                
                # 블로그 URL 초기화
                url_entry = getattr(self, f'account{i}_url', None)
                if url_entry:
                    url_entry.delete(0, tk.END)
                    url_entry.insert(0, 'https://blog.naver.com/')
                
                # 시작 페이지 초기화
                start_page_entry = getattr(self, f'account{i}_start_page', None)
                if start_page_entry:
                    start_page_entry.delete(0, tk.END)
                    start_page_entry.insert(0, '1')
                
                # 끝 페이지 초기화
                end_page_entry = getattr(self, f'account{i}_end_page', None)
                if end_page_entry:
                    end_page_entry.delete(0, tk.END)
            
            self.log_message("설정이 초기화되었습니다.")
    
    def add_account_from_config(self, account_data):
        """config에서 계정 정보를 추가합니다."""
        try:
            account_id = f"{account_data['id']}_{len(self.accounts)}"
            
            # 계정 정보 저장
            account = {
                'id': account_id,
                'user_id': account_data['id'],
                'password': account_data['password'],
                'blog_url': account_data.get('blog_url', 'https://blog.naver.com/'),
                'start_page': account_data.get('start_page', 1),
                'end_page': account_data.get('end_page', None),
                'is_running': False,
                'driver': None,
                'wait': None,
                'like_count': 0,
                'skipped_count': 0,
                'current_page': 1
            }
            self.accounts.append(account)
            
            # 계정별 로그 탭 생성
            self.create_account_log_tab(account_id, account_data['id'])
            
            self.log_message(f"계정 로드됨: {account_data['id']} (시작 페이지: {account['start_page']})")
            
            # 계정 목록 표시 업데이트
            self.update_account_list_display()
            
        except Exception as e:
            self.log_message(f"계정 로드 중 오류: {e}")
    
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
                'blog_url': account_info.get('blog_url', 'https://blog.naver.com/'),
                'start_page': account_info.get('start_page', 1),
                'end_page': account_info.get('end_page', None),
                'is_running': False,
                'driver': None,
                'wait': None,
                'like_count': 0,
                'skipped_count': 0,
                'current_page': 1
            }
            self.accounts.append(account_data)
            
            # 계정별 로그 탭 생성
            self.create_account_log_tab(account_id, account_info['id'])
            
            self.log_message(f"계정 추가됨: {account_info['id']} (시작 페이지: {account_info.get('start_page', 1)})")
            
            # 계정 목록 표시 업데이트
            self.update_account_list_display()
            
            # 설정 자동 저장
            self.save_config()
    
    def update_account_status(self, account, status):
        """계정 상태 업데이트"""
        try:
            # 계정 목록 표시 전체 업데이트
            self.update_account_list_display()
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
        
        # 로그 탭 삭제
        account_id = account['id']
        if account_id in self.account_log_frames:
            # 탭 삭제 (실제 구현에서는 notebook에서 탭을 제거해야 함)
            del self.account_log_frames[account_id]
            del self.account_log_texts[account_id]
        
        self.log_message(f"계정 삭제됨: {account['user_id']}")
        
        # 계정 목록 표시 업데이트
        self.update_account_list_display()
        
        # 설정 자동 저장
        self.save_config()
    
    def edit_account(self):
        """선택된 계정 편집"""
        selection = self.account_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "편집할 계정을 선택해주세요.")
            return
        
        index = selection[0]
        account = self.accounts[index]
        
        # 실행 중인 계정인지 확인
        if account.get('is_running', False):
            messagebox.showwarning("경고", "실행 중인 계정은 편집할 수 없습니다.")
            return
        
        # 편집 다이얼로그 열기
        dialog = AccountEditDialog(self.root, account)
        if dialog.result:
            # 계정 정보 업데이트
            account['user_id'] = dialog.result['id']
            account['password'] = dialog.result['password']
            account['blog_url'] = dialog.result['blog_url']
            account['start_page'] = dialog.result['start_page']
            account['end_page'] = dialog.result.get('end_page', None)
            
            self.log_message(f"계정 편집됨: {account['user_id']} (시작 페이지: {account['start_page']})")
            
            # 계정 목록 표시 업데이트
            self.update_account_list_display()
            
            self.save_config()
    
    def create_account_log_tab(self, account_id, user_id):
        """계정별 로그 탭 생성"""
        # 실제로는 notebook에 새 탭을 추가해야 하지만, 
        # 현재는 기본 로그에 계정별로 구분해서 표시
        self.account_log_frames[account_id] = None
        self.account_log_texts[account_id] = None
    
    
    def account_automation_worker_sequential(self, account):
        """계정별 자동화 작업 (순차 실행용)"""
        try:
            account['is_running'] = True
            account_id = account['id']
            
            self.log_message(f"계정 {account['user_id']} 자동화 시작", account_id)
            self.log_message(f"계정 정보 - ID: {account['user_id']}, URL: {account['blog_url']}", account_id)
            
            # WebDriver 설정
            if not self.setup_account_driver(account):
                return
            
            # 로그인 (보안문자 포함)
            if not self.login_account_to_naver_sequential(account):
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
            # 실행 중인 계정 목록에서 제거
            if account['user_id'] in self.running_accounts:
                self.running_accounts.remove(account['user_id'])
                self.log_message(f"계정 {account['user_id']} 실행 완료 및 목록에서 제거됨", account_id)
            
            if account['driver']:
                try:
                    account['driver'].quit()
                except:
                    pass
                account['driver'] = None
    
    def stop_all_accounts(self):
        """모든 계정 중지"""
        stopped_count = 0
        
        # 실행 중인 계정 목록 초기화
        if self.running_accounts:
            self.log_message(f"실행 중인 계정들을 중지합니다: {list(self.running_accounts)}")
            self.running_accounts.clear()
        
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
        account_id = account.get('id', account.get('user_id', 'unknown'))
        try:
            account['is_running'] = True
            
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
                
                # 끝 페이지 체크
                if account.get('end_page') and account['current_page'] >= account['end_page']:
                    self.log_message(f"설정한 끝 페이지({account['end_page']})에 도달했습니다.", account_id)
                    break
                
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
            # 실행 중인 계정 목록에서 제거
            if account['user_id'] in self.running_accounts:
                self.running_accounts.remove(account['user_id'])
                self.log_message(f"계정 {account['user_id']} 실행 완료 및 목록에서 제거됨", account_id)
            
            if account['driver']:
                try:
                    account['driver'].quit()
                except:
                    pass
                account['driver'] = None
        
    def setup_account_driver(self, account):
        """계정별 Chrome WebDriver 설정 (독립 세션)"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # 각 계정별로 독립적인 WebDriver 인스턴스 생성
            account['driver'] = webdriver.Chrome(options=chrome_options)
            account['driver'].execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            account['wait'] = WebDriverWait(account['driver'], 10)
            
            self.log_message(f"계정 {account['user_id']} 독립 WebDriver 세션 생성 완료", account['id'])
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
            
            # 네이버 로그인 페이지 접속
            account['driver'].get("https://nid.naver.com/nidlogin.login")
            time.sleep(2)
            
            user_id = account['user_id']
            password = account['password']
            
            # ID 입력
            self.log_message(f"계정 {account['user_id']} 아이디 입력 중...", account['id'])
            id_input = WebDriverWait(account['driver'], 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#id"))
            )
            pyperclip.copy(user_id)
            id_input.click()
            time.sleep(0.5)
            id_input.send_keys(Keys.CONTROL + 'v')
            time.sleep(1)
            
            # 비밀번호 입력
            self.log_message(f"계정 {account['user_id']} 비밀번호 입력 중...", account['id'])
            pw_input = account['driver'].find_element(By.CSS_SELECTOR, "#pw")
            pyperclip.copy(password)
            pw_input.click()
            time.sleep(0.5)
            pw_input.send_keys(Keys.CONTROL + 'v')
            time.sleep(1)
            
            # 로그인 버튼 클릭
            self.log_message(f"계정 {account['user_id']} 로그인 버튼 클릭 중...", account['id'])
            login_button = account['driver'].find_element(By.CSS_SELECTOR, "#log\\.login")
            login_button.click()
            time.sleep(3)
            
            # 로그인 결과 확인
            current_url = account['driver'].current_url
            self.log_message(f"계정 {account['user_id']} 현재 URL: {current_url}", account['id'])
            
            if "naver.com" not in current_url:
                self.log_message(f"계정 {account['user_id']} 로그인 실패!", account['id'])
                return False
            
            self.log_message(f"계정 {account['user_id']} 네이버 로그인 성공!", account['id'])
            return True
                
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} 로그인 중 오류: {e}", account['id'])
            return False
    
    def login_account_to_naver_sequential(self, account):
        """계정별 네이버 로그인 (순차 실행용 - 보안문자 완료까지 대기)"""
        try:
            self.log_message(f"계정 {account['user_id']} 네이버 로그인 시작...", account['id'])
            self.log_message(f"사용할 ID: {account['user_id']}, 비밀번호: {'*' * len(account['password'])}", account['id'])
            
            # 네이버 로그인 페이지 접속
            account['driver'].get("https://nid.naver.com/nidlogin.login")
            time.sleep(2)
            
            user_id = account['user_id']
            password = account['password']
            
            # ID 입력
            self.log_message(f"계정 {account['user_id']} 아이디 입력 중...", account['id'])
            id_input = WebDriverWait(account['driver'], 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#id"))
            )
            pyperclip.copy(user_id)
            id_input.click()
            time.sleep(0.5)
            id_input.send_keys(Keys.CONTROL + 'v')
            time.sleep(1)
            
            # 비밀번호 입력
            self.log_message(f"계정 {account['user_id']} 비밀번호 입력 중...", account['id'])
            pw_input = account['driver'].find_element(By.CSS_SELECTOR, "#pw")
            pyperclip.copy(password)
            pw_input.click()
            time.sleep(0.5)
            pw_input.send_keys(Keys.CONTROL + 'v')
            time.sleep(1)
            
            # 로그인 버튼 클릭
            self.log_message(f"계정 {account['user_id']} 로그인 버튼 클릭 중...", account['id'])
            login_button = account['driver'].find_element(By.CSS_SELECTOR, "#log\\.login")
            login_button.click()
            time.sleep(3)
            
            # 로그인 결과 확인
            current_url = account['driver'].current_url
            self.log_message(f"계정 {account['user_id']} 현재 URL: {current_url}", account['id'])
            
            if "naver.com" not in current_url:
                self.log_message(f"계정 {account['user_id']} 로그인 실패!", account['id'])
                return False
            
            self.log_message(f"계정 {account['user_id']} 네이버 로그인 성공!", account['id'])
            return True
                
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} 로그인 중 오류: {e}", account['id'])
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
    
    def wait_for_login_success_sequential(self, account):
        """로그인 성공까지 대기 (순차 실행용 - 보안문자 완료까지 대기)"""
        try:
            account_id = account['id']
            max_wait_time = 600  # 최대 10분 대기 (보안문자 입력 시간 고려)
            check_interval = 2   # 2초마다 확인
            waited_time = 0
            
            self.log_message(f"계정 {account['user_id']} 로그인 결과 확인 중... (보안문자 입력을 기다립니다)", account_id)
            
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
            self.log_message(f"계정 {account['user_id']} 로그인 대기 시간 초과 (10분)", account_id)
            return False
            
        except Exception as e:
            self.log_message(f"계정 {account['user_id']} 로그인 대기 중 오류: {e}", account_id)
            return False
            
    def login_to_naver(self):
        """네이버 로그인"""
        try:
            self.log_message("네이버 로그인 시작...")
            
            # 네이버 로그인 페이지 접속
            self.driver.get("https://nid.naver.com/nidlogin.login")
            time.sleep(2)
            
            user_id = self.id_var.get()
            password = self.pw_var.get()
            
            # ID 입력
            self.log_message("아이디 입력 중...")
            id_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#id"))
            )
            pyperclip.copy(user_id)
            id_input.click()
            time.sleep(0.5)
            id_input.send_keys(Keys.CONTROL + 'v')
            time.sleep(1)
            
            # 비밀번호 입력
            self.log_message("비밀번호 입력 중...")
            pw_input = self.driver.find_element(By.CSS_SELECTOR, "#pw")
            pyperclip.copy(password)
            pw_input.click()
            time.sleep(0.5)
            pw_input.send_keys(Keys.CONTROL + 'v')
            time.sleep(1)
            
            # 로그인 버튼 클릭
            self.log_message("로그인 버튼 클릭 중...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, "#log\\.login")
            login_button.click()
            time.sleep(3)
            
            # 로그인 결과 확인
            current_url = self.driver.current_url
            self.log_message(f"현재 URL: {current_url}")
            
            if "naver.com" not in current_url:
                self.log_message("로그인 실패!")
                return False
            
            self.log_message("네이버 로그인 성공!")
            return True
                
        except Exception as e:
            self.log_message(f"로그인 중 오류: {e}")
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
            
            # 페이지네이션 영역이 로드될 때까지 대기
            time.sleep(2)
            
            # 시작 페이지 버튼 찾기 (여러 방법 시도)
            start_page_button = None
            
            # 방법 1: 네이버 블로그 URL 구조에 맞게 직접 이동
            try:
                current_url = account['driver'].current_url
                # 네이버 블로그는 currentPage 파라미터를 사용
                if 'currentPage=' in current_url:
                    # 기존 currentPage 파라미터 교체
                    new_url = current_url.replace(re.search(r'currentPage=\d+', current_url).group(), f'currentPage={start_page_num}')
                else:
                    # currentPage 파라미터 추가
                    separator = '&' if '?' in current_url else '?'
                    new_url = f"{current_url}{separator}currentPage={start_page_num}"
                
                self.log_message(f"계정 {account['user_id']} URL로 시작 페이지 이동: {new_url}", account['id'])
                account['driver'].get(new_url)
                time.sleep(3)
                
                # 이동 후 현재 페이지 확인
                actual_page = self.get_account_current_page_number(account)
                if actual_page == start_page_num:
                    account['current_page'] = actual_page
                    self.log_message(f"계정 {account['user_id']} URL 이동 성공! 현재 페이지: {actual_page}", account['id'])
                    return True
                else:
                    self.log_message(f"계정 {account['user_id']} URL 이동 후 페이지 불일치. 예상: {start_page_num}, 실제: {actual_page}", account['id'])
            except Exception as url_e:
                self.log_message(f"계정 {account['user_id']} URL 이동 실패: {url_e}", account['id'])
            
            # 방법 1-2: JavaScript로 페이지 직접 이동 시도
            try:
                self.log_message(f"계정 {account['user_id']} JavaScript로 페이지 {start_page_num}로 이동 시도...", account['id'])
                result = account['driver'].execute_script(f"""
                    // 네이버 블로그의 페이지네이션 함수 호출
                    if (typeof goToPage === 'function') {{
                        goToPage({start_page_num});
                        return true;
                    }}
                    // AngularJS 컨트롤러가 있는 경우
                    if (typeof angular !== 'undefined' && angular.element(document.body).scope()) {{
                        var scope = angular.element(document.body).scope();
                        if (scope && scope.goToPage) {{
                            scope.goToPage({start_page_num});
                            return true;
                        }}
                    }}
                    return false;
                """)
                
                if result:
                    time.sleep(3)
                    actual_page = self.get_account_current_page_number(account)
                    if actual_page == start_page_num:
                        account['current_page'] = actual_page
                        self.log_message(f"계정 {account['user_id']} JavaScript 이동 성공! 현재 페이지: {actual_page}", account['id'])
                        return True
                    else:
                        self.log_message(f"계정 {account['user_id']} JavaScript 이동 후 페이지 불일치. 예상: {start_page_num}, 실제: {actual_page}", account['id'])
                else:
                    self.log_message(f"계정 {account['user_id']} JavaScript 페이지 이동 함수를 찾을 수 없습니다.", account['id'])
            except Exception as js_e:
                self.log_message(f"계정 {account['user_id']} JavaScript 이동 실패: {js_e}", account['id'])
            
            # 방법 2: 순차적 페이지 이동 (가장 확실한 방법)
            if start_page_num > 1:
                try:
                    self.log_message(f"계정 {account['user_id']} 순차적으로 {start_page_num}페이지까지 이동 시도...", account['id'])
                    current_page = 1
                    
                    # 2페이지부터 시작 페이지까지 순차 이동
                    for target_page in range(2, start_page_num + 1):
                        self.log_message(f"계정 {account['user_id']} {target_page}페이지로 이동 중...", account['id'])
                        
                        # 다음 페이지 버튼 찾기
                        next_button = None
                        try:
                            # aria-label로 다음 페이지 버튼 찾기
                            next_button = account['driver'].find_element(By.CSS_SELECTOR, f"a[aria-label='{target_page}페이지']")
                        except NoSuchElementException:
                            try:
                                # 일반적인 다음 페이지 버튼
                                next_button = account['driver'].find_element(By.CSS_SELECTOR, ".button_next")
                            except NoSuchElementException:
                                try:
                                    # JavaScript로 다음 페이지 버튼 찾기
                                    next_button = account['driver'].execute_script("""
                                        var buttons = document.querySelectorAll('a');
                                        for (var i = 0; i < buttons.length; i++) {
                                            if (buttons[i].textContent.trim() === arguments[0]) {
                                                return buttons[i];
                                            }
                                        }
                                        return null;
                                    """, str(target_page))
                                except:
                                    pass
                        
                        if next_button:
                            # 다음 페이지로 이동
                            account['driver'].execute_script("arguments[0].click();", next_button)
                            time.sleep(2)
                            
                            # 이동 확인
                            actual_page = self.get_account_current_page_number(account)
                            if actual_page == target_page:
                                current_page = actual_page
                                self.log_message(f"계정 {account['user_id']} {target_page}페이지 이동 성공!", account['id'])
                            else:
                                self.log_message(f"계정 {account['user_id']} {target_page}페이지 이동 실패. 현재: {actual_page}", account['id'])
                                break
                        else:
                            self.log_message(f"계정 {account['user_id']} {target_page}페이지 버튼을 찾을 수 없습니다.", account['id'])
                            break
                    
                    # 최종 페이지 확인
                    final_page = self.get_account_current_page_number(account)
                    if final_page == start_page_num:
                        account['current_page'] = final_page
                        self.log_message(f"계정 {account['user_id']} 순차 이동 성공! 최종 페이지: {final_page}", account['id'])
                        return True
                    else:
                        self.log_message(f"계정 {account['user_id']} 순차 이동 실패. 목표: {start_page_num}, 실제: {final_page}", account['id'])
                        
                except Exception as seq_e:
                    self.log_message(f"계정 {account['user_id']} 순차 이동 중 오류: {seq_e}", account['id'])
            
            # 방법 3: 페이지 번호 링크로 직접 이동
            try:
                start_page_button = account['driver'].find_element(By.LINK_TEXT, str(start_page_num))
                self.log_message(f"계정 {account['user_id']} 시작 페이지 {start_page_num} 링크를 찾았습니다.", account['id'])
            except NoSuchElementException:
                # 방법 4: CSS 셀렉터로 페이지 번호 찾기
                try:
                    start_page_button = account['driver'].find_element(By.CSS_SELECTOR, f"a[href*='page={start_page_num}']")
                    self.log_message(f"계정 {account['user_id']} 시작 페이지 {start_page_num} 링크를 CSS로 찾았습니다.", account['id'])
                except NoSuchElementException:
                    # 방법 5: JavaScript로 페이지 번호 링크 찾기
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
                
                return actual_page == start_page_num
            else:
                self.log_message(f"계정 {account['user_id']} 시작 페이지 {start_page_num} 링크를 찾을 수 없습니다.", account['id'])
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
                # 설정 자동 저장
                self.save_config()
                self.root.destroy()
        else:
            if self.driver:
                self.driver.quit()
            # 설정 자동 저장
            self.save_config()
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
        page_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(page_frame, text="시작 페이지:").pack(side=tk.LEFT, padx=(0, 10))
        self.start_page_var = tk.StringVar(value="1")
        page_entry = ttk.Entry(page_frame, textvariable=self.start_page_var, width=10)
        page_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # 끝 페이지 입력
        ttk.Label(page_frame, text="끝 페이지:").pack(side=tk.LEFT, padx=(0, 10))
        self.end_page_var = tk.StringVar(value="")
        end_page_entry = ttk.Entry(page_frame, textvariable=self.end_page_var, width=10)
        end_page_entry.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(page_frame, text="(비우면 끝까지)").pack(side=tk.LEFT)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="추가", command=self.add_account).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="취소", command=self.cancel).pack(side=tk.RIGHT)

class AccountEditDialog:
    """계정 편집 다이얼로그"""
    def __init__(self, parent, account):
        self.result = None
        self.account = account
        
        # 다이얼로그 창 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("계정 편집")
        self.dialog.geometry("450x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=Colors.BACKGROUND)
        
        # 중앙 정렬
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui()
        
        # 다이얼로그가 닫힐 때까지 대기
        self.dialog.wait_window()
    
    def setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너
        main_container = tk.Frame(self.dialog, bg=Colors.BACKGROUND)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 제목 카드
        title_card = tk.Frame(main_container, bg=Colors.CARD, relief='flat', bd=0)
        title_card.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(title_card, 
                              text="계정 정보 편집", 
                              font=Fonts.get_font('HEADLINE_WIN'),
                              bg=Colors.CARD,
                              fg=Colors.PRIMARY_TEXT)
        title_label.pack(pady=15)
        
        # 입력 폼 카드
        form_card = tk.Frame(main_container, bg=Colors.CARD, relief='flat', bd=0)
        form_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # ID 입력
        id_frame = tk.Frame(form_card, bg=Colors.CARD)
        id_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        tk.Label(id_frame, text="ID", 
                font=Fonts.get_font('BODY_WIN'),
                bg=Colors.CARD, fg=Colors.PRIMARY_TEXT).pack(anchor=tk.W)
        
        self.id_var = tk.StringVar(value=self.account['user_id'])
        id_entry = tk.Entry(id_frame, textvariable=self.id_var, 
                           font=Fonts.get_font('BODY_WIN'),
                           bg=Colors.CARD, fg=Colors.PRIMARY_TEXT,
                           relief='flat', bd=1, highlightthickness=1)
        id_entry.pack(fill=tk.X, pady=(5, 0))
        
        # 비밀번호 입력
        pw_frame = tk.Frame(form_card, bg=Colors.CARD)
        pw_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(pw_frame, text="비밀번호", 
                font=Fonts.get_font('BODY_WIN'),
                bg=Colors.CARD, fg=Colors.PRIMARY_TEXT).pack(anchor=tk.W)
        
        self.pw_var = tk.StringVar(value=self.account['password'])
        pw_entry = tk.Entry(pw_frame, textvariable=self.pw_var, show="*",
                           font=Fonts.get_font('BODY_WIN'),
                           bg=Colors.CARD, fg=Colors.PRIMARY_TEXT,
                           relief='flat', bd=1, highlightthickness=1)
        pw_entry.pack(fill=tk.X, pady=(5, 0))
        
        # 블로그 URL 입력
        url_frame = tk.Frame(form_card, bg=Colors.CARD)
        url_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(url_frame, text="블로그 URL", 
                font=Fonts.get_font('BODY_WIN'),
                bg=Colors.CARD, fg=Colors.PRIMARY_TEXT).pack(anchor=tk.W)
        
        self.url_var = tk.StringVar(value=self.account['blog_url'])
        url_entry = tk.Entry(url_frame, textvariable=self.url_var,
                            font=Fonts.get_font('BODY_WIN'),
                            bg=Colors.CARD, fg=Colors.PRIMARY_TEXT,
                            relief='flat', bd=1, highlightthickness=1)
        url_entry.pack(fill=tk.X, pady=(5, 0))
        
        # 페이지 설정 프레임
        page_frame = tk.Frame(form_card, bg=Colors.CARD)
        page_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(page_frame, text="페이지 설정", 
                font=Fonts.get_font('BODY_WIN'),
                bg=Colors.CARD, fg=Colors.PRIMARY_TEXT).pack(anchor=tk.W)
        
        # 페이지 입력 서브프레임
        page_input_frame = tk.Frame(page_frame, bg=Colors.CARD)
        page_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 시작 페이지
        start_frame = tk.Frame(page_input_frame, bg=Colors.CARD)
        start_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Label(start_frame, text="시작 페이지", 
                font=Fonts.get_font('SUBHEAD_WIN'),
                bg=Colors.CARD, fg=Colors.SECONDARY_TEXT).pack(anchor=tk.W)
        
        self.start_page_var = tk.StringVar(value=str(self.account['start_page']))
        start_page_entry = tk.Entry(start_frame, textvariable=self.start_page_var,
                                   font=Fonts.get_font('BODY_WIN'),
                                   bg=Colors.CARD, fg=Colors.PRIMARY_TEXT,
                                   relief='flat', bd=1, highlightthickness=1,
                                   width=8)
        start_page_entry.pack(anchor=tk.W, pady=(2, 0))
        
        # 끝 페이지
        end_frame = tk.Frame(page_input_frame, bg=Colors.CARD)
        end_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(end_frame, text="끝 페이지", 
                font=Fonts.get_font('SUBHEAD_WIN'),
                bg=Colors.CARD, fg=Colors.SECONDARY_TEXT).pack(anchor=tk.W)
        
        self.end_page_var = tk.StringVar(value=str(self.account.get('end_page', '')))
        end_page_entry = tk.Entry(end_frame, textvariable=self.end_page_var,
                                 font=Fonts.get_font('BODY_WIN'),
                                 bg=Colors.CARD, fg=Colors.PRIMARY_TEXT,
                                 relief='flat', bd=1, highlightthickness=1,
                                 width=8)
        end_page_entry.pack(anchor=tk.W, pady=(2, 0))
        
        # 안내 텍스트
        tk.Label(page_frame, text="(끝 페이지를 비우면 끝까지 진행)", 
                font=Fonts.get_font('FOOTNOTE_WIN'),
                bg=Colors.CARD, fg=Colors.SECONDARY_TEXT).pack(anchor=tk.W, pady=(5, 0))
        
        # 버튼 카드
        button_card = tk.Frame(main_container, bg=Colors.CARD, relief='flat', bd=0)
        button_card.pack(fill=tk.X)
        
        button_frame = tk.Frame(button_card, bg=Colors.CARD)
        button_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 취소 버튼
        cancel_btn = tk.Button(button_frame, text="취소", command=self.cancel,
                              font=Fonts.get_font('BODY_WIN'),
                              bg=Colors.CARD, fg=Colors.ACTION_BLUE,
                              relief='flat', bd=1, highlightthickness=0,
                              padx=20, pady=8)
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 저장 버튼
        save_btn = tk.Button(button_frame, text="저장", command=self.save_account,
                            font=Fonts.get_font('BODY_WIN'),
                            bg=Colors.ACTION_BLUE, fg='white',
                            relief='flat', bd=0, highlightthickness=0,
                            padx=20, pady=8)
        save_btn.pack(side=tk.RIGHT)
    
    def save_account(self):
        """계정 저장"""
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
        
        # 끝 페이지 검증
        end_page = None
        end_page_str = self.end_page_var.get().strip()
        if end_page_str:
            try:
                end_page = int(end_page_str)
                if end_page < start_page:
                    messagebox.showerror("오류", "끝 페이지는 시작 페이지보다 크거나 같아야 합니다.")
                    return
            except ValueError:
                messagebox.showerror("오류", "끝 페이지는 숫자로만 입력해주세요.")
            return
        
        self.result = {
            'id': self.id_var.get(),
            'password': self.pw_var.get(),
            'blog_url': self.url_var.get(),
            'start_page': start_page,
            'end_page': end_page
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """취소"""
        self.dialog.destroy()

if __name__ == "__main__":
    app = BlogLikeAutomationGUI()
    app.run()
