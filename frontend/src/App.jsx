import React, { useState, useEffect, useRef } from 'react';
import { 
  LayoutDashboard, 
  Mail, 
  FolderOpen, 
  History, 
  Search, 
  Play, 
  Square, 
  RefreshCw, 
  Trash2, 
  Eye, 
  EyeOff, 
  LogOut, 
  Download, 
  BookOpen, 
  CheckCircle,
  AlertTriangle,
  Info,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  FolderSync,
  Settings,
  Bookmark,
  Star,
  ChevronDown,
  User,
  X
} from 'lucide-react';

// Safe API Bridge Helper for pywebview
const callApi = (method, ...args) => {
  return new Promise((resolve, reject) => {
    if (window.pywebview && window.pywebview.api && window.pywebview.api[method]) {
      window.pywebview.api[method](...args)
        .then(resolve)
        .catch(reject);
    } else {
      const onReady = () => {
        window.pywebview.api[method](...args)
          .then(resolve)
          .catch(reject);
      };
      window.addEventListener('pywebviewready', onReady, { once: true });
      setTimeout(() => {
        window.removeEventListener('pywebviewready', onReady);
        reject(new Error("Python API 连接超时，请确保程序已正确启动！"));
      }, 10000);
    }
  });
};

const DEFAULT_CHINESE_BOOKS = [
  {
    id: 5225442,
    title: "三体 (全集)",
    author: "刘慈欣",
    extension: "epub",
    filesizeString: "2.1 MB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/25bcf8e0a3597b8d8df6f3cf8c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  },
  {
    id: 5581420,
    title: "活着",
    author: "余华",
    extension: "epub",
    filesizeString: "512 KB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/3b6346b9a3597b8d8df6f3cf8c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  },
  {
    id: 5285211,
    title: "你当像鸟飞往你的山",
    author: "塔拉·韦斯特弗",
    extension: "epub",
    filesizeString: "571 KB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/d298aa327f2a87873719d0bb6c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  },
  {
    id: 5731855,
    title: "被讨厌的勇气",
    author: "岸见一郎",
    extension: "epub",
    filesizeString: "4.7 MB",
    cover: "https://covers.1lib.sk/covers299/collections/userbooks/09d56417a36781520aed51632632175c49537f6b2127184c3dcf677734331aff.jpg"
  },
  {
    id: 5411413,
    title: "红楼梦",
    author: "曹雪芹",
    extension: "epub",
    filesizeString: "1.8 MB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/25728e84dca6ab1a24fd76ac46fc6bdb759cdfc3fecd00053e5c3a72e64fcdfc.jpg"
  },
  {
    id: 5321894,
    title: "百年孤独",
    author: "加西亚·马尔克斯",
    extension: "epub",
    filesizeString: "980 KB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/ab49f6b9a3597b8d8df6f3cf8c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  },
  {
    id: 5129481,
    title: "白夜行",
    author: "东野圭吾",
    extension: "epub",
    filesizeString: "1.2 MB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/ee9b0bb9a3597b8d8df6f3cf8c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  },
  {
    id: 5211878,
    title: "明朝那些事儿 (全集)",
    author: "当年明月",
    extension: "epub",
    filesizeString: "4.5 MB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/f1fe83b9a3597b8d8df6f3cf8c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  }
];

const DEFAULT_ENGLISH_BOOKS = [
  {
    id: 5221001,
    title: "The Great Gatsby",
    author: "F. Scott Fitzgerald",
    extension: "epub",
    filesizeString: "320 KB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/d68b0bb9a3597b8d8df6f3cf8c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  },
  {
    id: 5221002,
    title: "1984",
    author: "George Orwell",
    extension: "epub",
    filesizeString: "450 KB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/1984b9a3597b8d8df6f3cf8c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  },
  {
    id: 5221003,
    title: "To Kill a Mockingbird",
    author: "Harper Lee",
    extension: "epub",
    filesizeString: "820 KB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/tkm0bb9a3597b8d8df6f3cf8c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  },
  {
    id: 5221004,
    title: "Pride and Prejudice",
    author: "Jane Austen",
    extension: "epub",
    filesizeString: "670 KB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/pap0bb9a3597b8d8df6f3cf8c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  },
  {
    id: 5221005,
    title: "The Hobbit",
    author: "J.R.R. Tolkien",
    extension: "epub",
    filesizeString: "1.2 MB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/th0bb9a3597b8d8df6f3cf8c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  },
  {
    id: 5221006,
    title: "The Little Prince",
    author: "Antoine de Saint-Exupéry",
    extension: "epub",
    filesizeString: "540 KB",
    cover: "https://covers.1lib.sk/covers299/collections/genesis/tlp0bb9a3597b8d8df6f3cf8c1561f634ca291aa7b608c34d2419b18041f37.jpg"
  }
];

const Spinner = () => (
  <svg className="spinner" viewBox="0 0 50 50">
    <circle className="path" cx="25" cy="25" r="20" fill="none" strokeWidth="4"></circle>
  </svg>
);

export default function App() {
  const [activeTab, setActiveTab] = useState('zlib');
  const [config, setConfig] = useState(null);
  const [logs, setLogs] = useState([]);
  const [serviceRunning, setServiceRunning] = useState(false);
  const [history, setHistory] = useState([]);

  // My Library state
  const [savedBooks, setSavedBooks] = useState([]);
  const [savedBooksLoading, setSavedBooksLoading] = useState(false);
  const [savedBooksError, setSavedBooksError] = useState(null);
  const [unsavingBooks, setUnsavingBooks] = useState({});

  // Profile state
  const [profileData, setProfileData] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);

  // Theme state — initialized from localStorage, will sync from backend config once loaded
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('kindlefly_theme') || 'dark';
  });
  
  // SMTP Test state
  const [smtpTesting, setSmtpTesting] = useState(false);
  const [smtpTestResult, setSmtpTestResult] = useState(null);
  const [showSmtpPassword, setShowSmtpPassword] = useState(false);

  // Guide state
  const [guideTab, setGuideTab] = useState('gmail');

  // Z-Library states
  const [zlibStatus, setZlibStatus] = useState({
    logged_in: false,
    user: null,
    domain: '',
    loading: true,
    error: null
  });
  
  // Recommendations states
  const [recommendations, setRecommendations] = useState(null);
  const [recLoading, setRecLoading] = useState(false);
  const [recError, setRecError] = useState(null);

  const [zlibQuery, setZlibQuery] = useState('');
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const userDropdownRef = useRef(null);
  const [zlibFilters, setZlibFilters] = useState({
    extension: 'all',
    language: 'all'
  });
  const [zlibResults, setZlibResults] = useState(null);
  const [zlibPage, setZlibPage] = useState(1);
  const [zlibLoading, setZlibLoading] = useState(false);
  const [zlibError, setZlibError] = useState(null);
  const [covers, setCovers] = useState({});
  const [pushingBooks, setPushingBooks] = useState({}); // { bookId: 'downloading' | 'pushing' | 'success' | 'error' | message }

  // Refs for debouncing / concurrency control
  const profileCheckTimerRef = useRef(null);
  const coverLoadingRef = useRef(new Set()); // tracks in-flight cover requests

  // Book detail states
  const [activeBookDetail, setActiveBookDetail] = useState(null);
  const [bookDetailLoading, setBookDetailLoading] = useState(false);
  const [bookDetailError, setBookDetailError] = useState(null);
  const [bookDetailActiveTab, setBookDetailActiveTab] = useState('desc'); // 'desc' | 'meta'
  const [bookmarkToggling, setBookmarkToggling] = useState(false);

  // Warning dialog states
  const [formatWarningBook, setFormatWarningBook] = useState(null);

  // Endless recommendations loading states
  const [displayedRecommendations, setDisplayedRecommendations] = useState([]);
  const [recPage, setRecPage] = useState(1);
  const [loadMoreLoading, setLoadMoreLoading] = useState(false);

  // Book comments & notes states
  const [comments, setComments] = useState([]);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [newCommentText, setNewCommentText] = useState('');
  const [newCommentUsername, setNewCommentUsername] = useState('');

  // Book format dropdown states
  const [availableFormats, setAvailableFormats] = useState([]);
  const [selectedFormat, setSelectedFormat] = useState(null);

  const [zlibEmail, setZlibEmail] = useState('');
  const [zlibPassword, setZlibPassword] = useState('');
  const [showZlibPassword, setShowZlibPassword] = useState(false);
  const [zlibTokenUserid, setZlibTokenUserid] = useState('');
  const [zlibTokenUserkey, setZlibTokenUserkey] = useState('');
  const [loginMethod, setLoginMethod] = useState('credentials'); // 'credentials' | 'token'
  const [loginSubmitting, setLoginSubmitting] = useState(false);
  const [loginError, setLoginError] = useState(null);
  const [domainRefreshing, setDomainRefreshing] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

  const consoleEndRef = useRef(null);

  // Apply theme classes to body
  useEffect(() => {
    if (theme === 'light') {
      document.body.classList.add('light-theme');
      document.body.classList.remove('dark-theme');
    } else {
      document.body.classList.add('dark-theme');
      document.body.classList.remove('light-theme');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => {
      const next = prev === 'dark' ? 'light' : 'dark';
      localStorage.setItem('kindlefly_theme', next);
      // Also persist to backend config so it survives reinstalls / profile resets
      callApi('save_config', { app_theme: next }).catch(() => {});
      return next;
    });
  };

  // 1. Initial configuration loading and listeners
  useEffect(() => {
    // Expose log listener to global window so python can push messages
    window.addLog = (msg, level = 'info') => {
      setLogs(prev => [...prev.slice(-199), { text: msg, type: level }]);
    };
    
    window.onServiceStatusChanged = (isRunning) => {
      setServiceRunning(isRunning);
    };

    // Load initial configurations
    const loadInitialData = async () => {
      try {
        const cfg = await callApi('get_config');
        setConfig(cfg);
        setZlibEmail(cfg.zlib_email || '');
        setZlibTokenUserid(cfg.zlib_remix_userid || '');
        setZlibTokenUserkey(cfg.zlib_remix_userkey || '');
        
        const status = await callApi('get_service_status');
        setServiceRunning(status);

        const hist = await callApi('get_history');
        setHistory(hist);

        // Apply saved theme from backend config (overrides localStorage default)
        if (cfg.app_theme && cfg.app_theme !== localStorage.getItem('kindlefly_theme')) {
          localStorage.setItem('kindlefly_theme', cfg.app_theme);
          setTheme(cfg.app_theme);
        }

        // Run Zlib status check asynchronously — don’t block render
        setTimeout(() => checkZlibProfile(), 0);
      } catch (err) {
        console.error("Error loading initial backend data:", err);
      }
    };

    loadInitialData();

    return () => {
      delete window.addLog;
      delete window.onServiceStatusChanged;
    };
  }, []);

  // Auto-scroll logs panel
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Handle outside clicks to close user dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userDropdownRef.current && !userDropdownRef.current.contains(event.target)) {
        setShowUserDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Refresh data when switching to certain tabs
  useEffect(() => {
    if (activeTab === 'history') {
      callApi('get_history').then(hist => setHistory(hist)).catch(err => console.error(err));
    }
    if (activeTab === 'library') {
      if (!zlibStatus.logged_in) return;
      setSavedBooksLoading(true);
      setSavedBooksError(null);
      callApi('zlib_get_saved_books', 1, 20)
        .then(res => {
          const books = res.books || [];
          setSavedBooks(books);
          loadCoversInBackground(books);
        })
        .catch(err => setSavedBooksError(err.message))
        .finally(() => setSavedBooksLoading(false));
    }
    if (activeTab === 'profile') {
      if (!zlibStatus.logged_in) return;
      setProfileLoading(true);
      Promise.all([
        callApi('zlib_get_profile'),
        callApi('zlib_get_saved_books', 1, 5),
      ]).then(([prof, saved]) => {
        const books = saved.books || [];
        setProfileData({ user: prof.user, recentSaved: books });
        loadCoversInBackground(books);
      }).catch(console.error)
        .finally(() => setProfileLoading(false));
    }
  }, [activeTab]);

  // Debounced version — waits 400 ms between rapid consecutive calls
  const checkZlibProfile = (forceRefreshDomain = false) => {
    if (profileCheckTimerRef.current) clearTimeout(profileCheckTimerRef.current);
    profileCheckTimerRef.current = setTimeout(async () => {
      setZlibStatus(prev => ({ ...prev, loading: true }));
      try {
        const domain = await callApi('get_zlib_domain', forceRefreshDomain);
        const res = await callApi('zlib_check_status');
        setZlibStatus({
          logged_in: res.logged_in,
          user: res.user || null,
          domain: domain,
          error: res.error || null,
          loading: false
        });
      } catch (err) {
        setZlibStatus(prev => ({
          ...prev,
          loading: false,
          error: err.message
        }));
      }
    }, 400);
  };

  const handleRefreshDomain = async () => {
    setDomainRefreshing(true);
    await checkZlibProfile(true);
    setDomainRefreshing(false);
  };

  const fetchRecommendations = async () => {
    setRecLoading(true);
    setRecError(null);
    try {
      const res = await callApi('zlib_get_recommendations');
      if (res.success && res.data && res.data.books) {
        setRecommendations(res.data.books);
        setDisplayedRecommendations(res.data.books);
        setRecPage(1);
        // Load covers in background
        loadCoversInBackground(res.data.books);
      } else {
        setRecError(res.message || "获取推荐失败");
      }
    } catch (err) {
      setRecError(err.message);
    } finally {
      setRecLoading(false);
    }
  };

  const handleLoadMoreRecommendations = async () => {
    setLoadMoreLoading(true);
    try {
      const pageToFetch = Math.floor((recPage - 1) / 2) + 1;
      const isPopular = recPage % 2 === 1;
      const langParam = zlibFilters.language;
      
      let res;
      if (isPopular) {
        res = await callApi('zlib_get_popular', langParam, pageToFetch);
      } else {
        res = await callApi('zlib_get_recently', langParam, pageToFetch);
      }

      if (res.success && res.data && res.data.books) {
        const newBooks = res.data.books;
        setDisplayedRecommendations(prev => {
          const existingIds = new Set(prev.map(b => b.id));
          const filteredNew = newBooks.filter(b => !existingIds.has(b.id));
          return [...prev, ...filteredNew];
        });
        loadCoversInBackground(newBooks);
        setRecPage(prev => prev + 1);
      } else {
        alert(res.message || "加载更多书籍失败");
      }
    } catch (err) {
      alert(`加载更多异常: ${err.message}`);
    } finally {
      setLoadMoreLoading(false);
    }
  };
  useEffect(() => {
    if (zlibStatus.logged_in) {
      fetchRecommendations();
    } else {
      const guestBooks = zlibFilters.language === 'english' ? DEFAULT_ENGLISH_BOOKS : DEFAULT_CHINESE_BOOKS;
      setRecommendations(guestBooks);
      setDisplayedRecommendations(guestBooks);
      setRecPage(1);
    }
  }, [zlibStatus.logged_in, zlibFilters.language]);
  // ----------------------------------------------------
  // Configuration handlers
  // ----------------------------------------------------
  const handleConfigChange = (key, value) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleCheckboxChange = (ext, checked) => {
    let list = [...(config.allowed_extensions || [])];
    if (checked) {
      if (!list.includes(ext)) {
        list.push(ext);
        if (ext === '.mobi') list.push('.azw');
        if (ext === '.docx') list.push('.doc');
      }
    } else {
      list = list.filter(item => {
        if (ext === '.mobi') return item !== '.mobi' && item !== '.azw';
        if (ext === '.docx') return item !== '.docx' && item !== '.doc';
        return item !== ext;
      });
    }
    handleConfigChange('allowed_extensions', list);
  };

  const handlePresetChange = (preset) => {
    const updates = { ...config };
    if (preset === 'Gmail') {
      updates.smtp_server = 'smtp.gmail.com';
      updates.smtp_port = 587;
      updates.smtp_use_ssl = false;
      setGuideTab('gmail');
    } else if (preset === 'QQ 邮箱') {
      updates.smtp_server = 'smtp.qq.com';
      updates.smtp_port = 465;
      updates.smtp_use_ssl = true;
      setGuideTab('qq');
    } else if (preset === '网易 163 邮箱') {
      updates.smtp_server = 'smtp.163.com';
      updates.smtp_port = 465;
      updates.smtp_use_ssl = true;
      setGuideTab('163');
    }
    setConfig(updates);
  };

  const handleSaveConfig = async () => {
    if (!config.sender_email || !config.sender_email.includes('@')) {
      alert("请填写有效的发信电子邮箱！");
      return;
    }
    if (!config.smtp_password) {
      alert("请填写邮箱授权码！");
      return;
    }
    if (activeTab === 'folder_kindle') {
      if (!config.kindle_email || !config.kindle_email.includes('@')) {
        alert("请填写正确的 Kindle 接收端邮箱！");
        return;
      }
      if (!config.scan_folder) {
        alert("请配置本地扫描目录！");
        return;
      }
      if (!config.allowed_extensions || config.allowed_extensions.length === 0) {
        alert("请至少勾选一种支持的电子书格式！");
        return;
      }
    }

    try {
      const res = await callApi('save_config', config);
      if (res.success) {
        alert(res.message);
      } else {
        alert(res.message);
      }
    } catch (err) {
      alert("保存失败: " + err.message);
    }
  };

  const handleTestSmtp = async () => {
    setSmtpTesting(true);
    setSmtpTestResult(null);
    try {
      const res = await callApi('test_smtp_connection', config);
      setSmtpTestResult(res);
    } catch (err) {
      setSmtpTestResult({ success: false, message: err.message });
    } finally {
      setSmtpTesting(false);
    }
  };

  const handleBrowseFolder = async () => {
    try {
      const selected = await callApi('browse_folder');
      if (selected) {
        handleConfigChange('scan_folder', selected);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // ----------------------------------------------------
  // Service Control handlers
  // ----------------------------------------------------
  const handleToggleService = async (checked) => {
    try {
      const res = await callApi('toggle_service', checked);
      if (!res.success) {
        alert(res.message);
        setServiceRunning(false);
      } else {
        setServiceRunning(checked);
      }
    } catch (err) {
      alert(err.message);
      setServiceRunning(!checked);
    }
  };

  const handleManualScan = async () => {
    try {
      await callApi('manual_scan_now');
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenScanFolder = async () => {
    try {
      const res = await callApi('open_scan_folder');
      if (!res.success) {
        alert(res.message);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm("这会清空本地数据库的发送记录。\n清空后，若本地目录中的电子书依然存在，它们会被再次推送。\n\n确认清空全部历史记录吗？")) {
      try {
        const res = await callApi('clear_history');
        if (res.success) {
          setHistory([]);
        }
      } catch (err) {
        alert(err.message);
      }
    }
  };

  // ----------------------------------------------------
  // Z-Library Operations
  // ----------------------------------------------------
  const handleZlibLogin = async (e) => {
    e.preventDefault();
    setLoginSubmitting(true);
    setLoginError(null);
    try {
      let res;
      if (loginMethod === 'credentials') {
        if (!zlibEmail || !zlibPassword) {
          throw new Error("请填写邮箱账号和密码！");
        }
        res = await callApi('zlib_login', zlibEmail, zlibPassword);
      } else {
        if (!zlibTokenUserid || !zlibTokenUserkey) {
          throw new Error("请填写 remix_userid 和 remix_userkey！");
        }
        res = await callApi('zlib_login_token', zlibTokenUserid, zlibTokenUserkey);
      }

      if (res.success) {
        // Reload Zlib config & status
        const cfg = await callApi('get_config');
        setConfig(cfg);
        setShowLoginModal(false);
        checkZlibProfile();
      } else {
        setLoginError(res.message);
      }
    } catch (err) {
      setLoginError(err.message);
    } finally {
      setLoginSubmitting(false);
    }
  };

  const handleZlibLogout = async () => {
    try {
      await callApi('zlib_logout');
      // Clear local states
      setZlibPassword('');
      setZlibResults(null);
      checkZlibProfile();
    } catch (err) {
      console.error(err);
    }
  };
  const handleZlibSearch = async (pageVal = 1) => {
    if (!zlibQuery.trim()) return;
    if (!zlibStatus.logged_in) {
      setShowLoginModal(true);
      return;
    }
    setZlibLoading(true);
    setZlibError(null);
    setZlibPage(pageVal);
    try {
      const res = await callApi('zlib_search', zlibQuery, zlibFilters.extension, zlibFilters.language, pageVal);
      if (res.success) {
        setZlibResults(res.data);
        // Async load cover thumbnails in the background
        if (res.data && res.data.books) {
          loadCoversInBackground(res.data.books);
        }
      } else {
        setZlibError(res.message);
      }
    } catch (err) {
      setZlibError(err.message);
    } finally {
      setZlibLoading(false);
    }
  };

  // Concurrency-limited cover loader (max 4 simultaneous requests)
  const MAX_CONCURRENT_COVERS = 4;
  const loadCoversInBackground = (books) => {
    books.forEach(async (book) => {
      if (!book.cover || covers[book.id] || coverLoadingRef.current.has(book.id)) return;

      // Wait until we have a free slot
      while (coverLoadingRef.current.size >= MAX_CONCURRENT_COVERS) {
        await new Promise(r => setTimeout(r, 100));
      }

      coverLoadingRef.current.add(book.id);
      try {
        const url = await callApi('get_book_cover_base64', book.cover);
        if (url) {
          setCovers(prev => ({ ...prev, [book.id]: url }));
        }
      } catch (e) {
        console.error('Cover load error:', e);
      } finally {
        coverLoadingRef.current.delete(book.id);
      }
    });
  };

  const executePushBook = async (book) => {
    const bookId = book.id;
    setPushingBooks(prev => ({ ...prev, [bookId]: 'downloading' }));
    
    try {
      const res = await callApi('zlib_push', book);
      if (res.success) {
        setPushingBooks(prev => ({ ...prev, [bookId]: 'success' }));
        callApi('get_history').then(hist => setHistory(hist)).catch(e => console.error(e));
      } else {
        setPushingBooks(prev => ({ ...prev, [bookId]: { status: 'error', message: res.message } }));
        alert(`推送失败：${res.message}`);
      }
    } catch (err) {
      setPushingBooks(prev => ({ ...prev, [bookId]: { status: 'error', message: err.message } }));
      alert(`推送异常：${err.message}`);
    }
  };

  const handleCheckAndPushBook = (book) => {
    if (!zlibStatus.logged_in) {
      setShowLoginModal(true);
      return;
    }
    const targetBook = selectedFormat && (selectedFormat.title === book.title) ? selectedFormat : book;
    const ext = (targetBook.extension || '').toLowerCase();
    if (ext && ext !== 'epub') {
      setFormatWarningBook(targetBook);
    } else {
      executePushBook(targetBook);
    }
  };

  const handleOpenBookDetails = async (book) => {
    const initialFormat = {
      id: book.id,
      hash: book.hash,
      extension: book.extension,
      filesizeString: book.filesizeString,
      title: book.title,
      author: book.author || '未知作者',
      cover: book.cover
    };
    setSelectedFormat(initialFormat);
    setAvailableFormats([initialFormat]);
    setComments([]);
    
    // Set minimal info first so modal shows up immediately with basic data (title, author, format)
    setActiveBookDetail({
      id: book.id,
      hash: book.hash,
      title: book.title,
      author: book.author,
      cover: book.cover,
      extension: book.extension,
      filesizeString: book.filesizeString
    });
    setBookDetailLoading(true);
    setBookDetailError(null);
    setBookDetailActiveTab('desc');

    // Load real Z-Library comments + local notes (pass hash so backend can query EAPI)
    setCommentsLoading(true);
    callApi('get_book_comments', book.id, book.hash || '')
      .then(data => setComments(Array.isArray(data) ? data : []))
      .catch(err => console.error('Error loading comments:', err))
      .finally(() => setCommentsLoading(false));

    // Guest mode: skip server-side Z-Library API fetches, just show local data
    if (!zlibStatus.logged_in) {
      setBookDetailLoading(false);
      return;
    }

    try {
      const res = await callApi('zlib_get_book_info', book.id, book.hash);
      if (res.success) {
        setActiveBookDetail(res.book);
        
        setSelectedFormat(prev => ({
          ...prev,
          title: res.book.title,
          author: res.book.author || '未知作者',
          cover: res.book.cover,
          extension: prev.extension || res.book.extension,
          filesizeString: prev.filesizeString || res.book.filesizeString
        }));

        setAvailableFormats(prev => {
          if (prev.length > 0) {
            const updated = [...prev];
            updated[0] = {
              ...updated[0],
              extension: updated[0].extension || res.book.extension,
              filesizeString: updated[0].filesizeString || res.book.filesizeString,
              title: res.book.title,
              author: res.book.author || '未知作者',
              cover: res.book.cover
            };
            return updated;
          }
          return prev;
        });

        if (res.book.cover && !covers[res.book.id]) {
          try {
            const base64 = await callApi('get_book_cover_base64', res.book.cover);
            if (base64) {
              setCovers(prev => ({ ...prev, [res.book.id]: base64 }));
            }
          } catch (e) {
            console.error("Error loading detail cover base64:", e);
          }
        }
        
        // 3. Fetch other formats
        callApi('zlib_get_book_formats', book.id, book.hash).then(formatsRes => {
          if (formatsRes.success && formatsRes.formats) {
            setAvailableFormats(prev => {
              const existingIds = new Set(prev.map(f => f.id));
              const enriched = formatsRes.formats
                .filter(f => !existingIds.has(f.id))
                .map(f => ({
                  ...f,
                  title: res.book.title,
                  author: res.book.author || '未知作者',
                  cover: res.book.cover
                }));
              return [...prev, ...enriched];
            });
          }
        }).catch(err => console.error("Error fetching formats:", err));
        
      } else {
        setBookDetailError(res.message);
      }
    } catch (err) {
      setBookDetailError(err.message);
    } finally {
      setBookDetailLoading(false);
    }
  };

  const handleToggleBookmark = async (bookId) => {
    if (!activeBookDetail) return;
    if (!zlibStatus.logged_in) {
      setShowLoginModal(true);
      return;
    }
    const isCurrentlySaved = !!activeBookDetail._isUserSavedBook;
    setBookmarkToggling(true);
    try {
      const apiMethod = isCurrentlySaved ? 'zlib_unsave_book' : 'zlib_save_book';
      const res = await callApi(apiMethod, bookId);
      if (res.success) {
        setActiveBookDetail(prev => ({
          ...prev,
          _isUserSavedBook: !isCurrentlySaved
        }));
      } else {
        alert(res.message || "收藏操作失败");
      }
    } catch (err) {
      alert(`收藏操作异常: ${err.message}`);
    } finally {
      setBookmarkToggling(false);
    }
  };

  const handleDownloadOnly = async (book) => {
    if (!zlibStatus.logged_in) {
      setShowLoginModal(true);
      return;
    }
    // Respect selectedFormat in details modal if it corresponds to the same book title
    const targetBook = selectedFormat && (selectedFormat.title === book.title) ? selectedFormat : book;
    const bookId = targetBook.id;
    setPushingBooks(prev => ({ ...prev, [bookId]: 'downloading' }));

    try {
      const res = await callApi('zlib_download_only', targetBook);
      if (res.success) {
        setPushingBooks(prev => ({ ...prev, [bookId]: 'success' }));
        alert(res.message);
        callApi('get_history').then(hist => setHistory(hist)).catch(e => console.error(e));
      } else {
        setPushingBooks(prev => ({ ...prev, [bookId]: { status: 'error', message: res.message } }));
        alert(`下载失败：${res.message}`);
      }
    } catch (err) {
      setPushingBooks(prev => ({ ...prev, [bookId]: { status: 'error', message: err.message } }));
      alert(`下载异常：${err.message}`);
    }
  };

  const handleSubmitComment = async (e) => {
    if (e) e.preventDefault();
    if (!newCommentText.trim() || !activeBookDetail) return;
    try {
      const nameVal = newCommentUsername.trim() || '我';
      const res = await callApi('add_book_comment', activeBookDetail.id, nameVal, newCommentText.trim());
      setComments(res || []);
      setNewCommentText('');
    } catch (err) {
      alert(`评论保存失败: ${err.message}`);
    }
  };

  if (!config) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', alignItems: 'center', justifyContent: 'center', gap: '16px', background: '#0a0a0f' }}>
        <Spinner />
        <span style={{ fontSize: '14px', color: '#9ca3af', fontWeight: 500, fontFamily: 'Outfit' }}>正在连接 KindleFly 后端发信系统...</span>
      </div>
    );
  }

  return (
    <div className="app-container" style={{ flexDirection: 'column' }}>
      {/* Top Navbar */}
      <header className="top-navbar">
        <div className="navbar-logo-section" onClick={() => { setZlibResults(null); setZlibQuery(''); setActiveTab('zlib'); }} style={{ cursor: 'pointer' }}>
          <FolderSync className="navbar-logo-icon" />
          <h1 className="navbar-logo-text">KindleFly</h1>
        </div>

        <nav className="navbar-menu">
          <div className={`nav-item ${activeTab === 'zlib' ? 'active' : ''}`} onClick={() => setActiveTab('zlib')}>
            <Search className="nav-icon" />
            <span>找书主页</span>
          </div>

          <div className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            <LayoutDashboard className="nav-icon" />
            <span>扫描监控</span>
          </div>

          <div className={`nav-item ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>
            <History className="nav-icon" />
            <span>推送历史</span>
          </div>

          <div className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
            <Settings className="nav-icon" />
            <span>设置中心</span>
          </div>
        </nav>

        <div className="navbar-actions">
          {/* Theme switcher */}
          <button className="theme-toggle-btn" onClick={toggleTheme} title={theme === 'dark' ? "切换为明亮主题" : "切换为暗黑主题"}>
            {theme === 'dark' ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '16px', height: '16px' }}><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '16px', height: '16px' }}><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
            )}
          </button>

          {/* User profile dropdown or login button */}
          {zlibStatus.logged_in ? (
            <div className="navbar-user-container" ref={userDropdownRef}>
              <div className="navbar-user-card" onClick={() => setShowUserDropdown(!showUserDropdown)} style={{ cursor: 'pointer' }}>
                <div className="user-avatar-mini">
                  {(zlibStatus.user?.name || zlibStatus.user?.email || 'Z').charAt(0).toUpperCase()}
                </div>
                <div className="user-info-mini">
                  <span className="username" title={zlibStatus.user?.name || 'Zlib 用户'}>{zlibStatus.user?.name || 'Zlib 用户'}</span>
                  <span className="downloads-today">今日额度: {Math.max(0, (zlibStatus.user?.downloads_limit || 10) - (zlibStatus.user?.downloads_today || 0))} / {zlibStatus.user?.downloads_limit || 10}</span>
                </div>
                <ChevronDown style={{ width: '12px', height: '12px', opacity: 0.6, marginLeft: '2px', transform: showUserDropdown ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
              </div>
              
              {showUserDropdown && (
                <div className="user-dropdown-menu">
                  <div className="dropdown-header">
                    <span className="dropdown-user-name">{zlibStatus.user?.name || 'Zlib 用户'}</span>
                    <span className="dropdown-user-email">{zlibStatus.user?.email}</span>
                  </div>
                  <div className="dropdown-divider" />
                  <div 
                    className={`dropdown-item ${activeTab === 'profile' ? 'active' : ''}`}
                    onClick={() => {
                      setActiveTab('profile');
                      setShowUserDropdown(false);
                    }}
                  >
                    <User style={{ width: '14px', height: '14px' }} />
                    <span>我的主页</span>
                  </div>
                  <div 
                    className={`dropdown-item ${activeTab === 'library' ? 'active' : ''}`}
                    onClick={() => {
                      setActiveTab('library');
                      setShowUserDropdown(false);
                    }}
                  >
                    <BookOpen style={{ width: '14px', height: '14px' }} />
                    <span>我的书库</span>
                  </div>
                  <div className="dropdown-divider" />
                  <div 
                    className="dropdown-item logout"
                    onClick={() => {
                      handleZlibLogout();
                      setShowUserDropdown(false);
                    }}
                  >
                    <LogOut style={{ width: '14px', height: '14px' }} />
                    <span>退出登录</span>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <button
              className="btn btn-primary"
              style={{ fontSize: '12px', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => setShowLoginModal(true)}
            >
              登录 Z-Library
            </button>
          )}
        </div>
      </header>

      {/* Main View Container */}
      <main className="content-panel">
        
        {/* TAB 1: Z-Library Tab (Home View & Search view combined) */}
        {activeTab === 'zlib' && (
          <div className="view-container" style={{ overflowY: 'auto' }}>
            
            {/* Search results view */}
            {zlibResults ? (
              <div className="zlib-results-container">
                <div className="results-back-row">
                  <button className="btn btn-secondary" onClick={() => { setZlibResults(null); setZlibQuery(''); }} style={{ padding: '6px 12px', fontSize: '12px' }}>
                    ← 返回主页
                  </button>
                  <span className="results-info-text">
                    关于 “<strong>{zlibQuery}</strong>” 的搜索结果 (第 {zlibPage} 页)
                  </span>
                  
                  <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {zlibStatus.domain && (
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        API 网关: <strong style={{ color: 'var(--accent-green)' }}>{zlibStatus.domain}</strong>
                      </span>
                    )}
                    <button className="btn btn-secondary" onClick={handleRefreshDomain} disabled={domainRefreshing} style={{ padding: '4px 8px', fontSize: '11px' }}>
                      <RefreshCw className={`btn-icon ${domainRefreshing ? 'spinner' : ''}`} style={{ width: '12px', height: '12px' }} /> 域名检测
                    </button>
                  </div>
                </div>

                <div className="search-bar-card results-search-bar" style={{ padding: '12px', marginTop: '10px' }}>
                  <input 
                    type="text" 
                    className="form-input zlib-search-input" 
                    placeholder="键入书名、作者、ISBN..."
                    value={zlibQuery}
                    onChange={(e) => setZlibQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleZlibSearch(1)}
                  />
                  <div className="search-filters-row">
                    <select 
                      className="filter-select"
                      value={zlibFilters.extension}
                      onChange={(e) => setZlibFilters(prev => ({ ...prev, extension: e.target.value }))}
                    >
                      <option value="all">任意格式</option>
                      <option value="epub">EPUB</option>
                      <option value="pdf">PDF</option>
                      <option value="mobi">MOBI</option>
                      <option value="azw3">AZW3</option>
                      <option value="txt">TXT</option>
                    </select>

                    <select 
                      className="filter-select"
                      value={zlibFilters.language}
                      onChange={(e) => setZlibFilters(prev => ({ ...prev, language: e.target.value }))}
                    >
                      <option value="all">任意语言</option>
                      <option value="chinese">中文 (Chinese)</option>
                      <option value="english">英文 (English)</option>
                    </select>
                  </div>

                  <button className="btn btn-primary" onClick={() => handleZlibSearch(1)} disabled={zlibLoading || !zlibQuery.trim()}>
                    {zlibLoading ? <Spinner /> : <Search className="btn-icon" />}
                    <span>检索</span>
                  </button>
                </div>

                {zlibLoading ? (
                  <div style={{ display: 'flex', minHeight: '300px', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                    <Spinner />
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>正在检索书籍列表...</span>
                  </div>
                ) : zlibError ? (
                  <div style={{ display: 'flex', minHeight: '300px', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', color: 'var(--accent-red)' }}>
                    <AlertTriangle style={{ width: '36px', height: '36px' }} />
                    <span style={{ fontSize: '14px', fontWeight: 500 }}>检索失败: {zlibError}</span>
                    <button className="btn btn-secondary" onClick={() => handleZlibSearch(zlibPage)}>重新加载</button>
                  </div>
                ) : zlibResults.books && zlibResults.books.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', marginTop: '16px' }}>
                    <div className="books-grid">
                      {zlibResults.books.map((book) => {
                        const bookId = book.id;
                        const pushingState = pushingBooks[bookId];
                        return (
                          <div key={bookId} className="book-card">
                            <div className="book-cover" onClick={() => handleOpenBookDetails(book)} style={{ cursor: 'pointer' }}>
                              {covers[bookId] ? (
                                <img src={covers[bookId]} alt={book.title} />
                              ) : (
                                <BookOpen style={{ width: '28px', height: '28px', opacity: 0.3 }} />
                              )}
                            </div>
                            <div className="book-info-container">
                              <div onClick={() => handleOpenBookDetails(book)} style={{ display: 'flex', flexDirection: 'column', minWidth: 0, cursor: 'pointer' }}>
                                <span className="book-title" title={book.title}>{book.title}</span>
                                <span className="book-author" title={book.author}>{book.author || '未知作者'}</span>
                                <div className="book-meta">
                                  <span className="badge badge-format">{book.extension}</span>
                                  <span className="badge badge-size">{book.filesizeString || '未知大小'}</span>
                                  {book.language && <span className="badge badge-lang">{book.language}</span>}
                                </div>
                              </div>
                              <div className="push-btn-container">
                                {pushingState === 'downloading' && (
                                  <button className="btn btn-secondary" style={{ width: '100%', fontSize: '11px', padding: '5px 0' }} disabled>
                                    <Spinner /> 下载中...
                                  </button>
                                )}
                                {pushingState === 'pushing' && (
                                  <button className="btn btn-secondary" style={{ width: '100%', fontSize: '11px', padding: '5px 0' }} disabled>
                                    <Spinner /> 推送中...
                                  </button>
                                )}
                                {pushingState === 'success' && (
                                  <button className="btn btn-secondary" style={{ width: '100%', fontSize: '11px', padding: '5px 0', border: '1px solid rgba(16, 185, 129, 0.4)', color: 'var(--accent-green)' }} disabled>
                                    <CheckCircle style={{ width: '12px', height: '12px' }} /> 已送达
                                  </button>
                                )}
                                {(!pushingState || pushingState.status === 'error') && (
                                  <button 
                                    className="btn btn-primary" 
                                    style={{ width: '100%', fontSize: '11px', padding: '5px 0' }} 
                                    onClick={() => handleCheckAndPushBook(book)}
                                  >
                                    <Download style={{ width: '12px', height: '12px' }} /> 一键推送
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div className="pagination-container" style={{ marginTop: '16px' }}>
                      <button className="btn btn-secondary" disabled={zlibPage <= 1 || zlibLoading} onClick={() => handleZlibSearch(zlibPage - 1)}>
                        <ChevronLeft style={{ width: '16px', height: '16px' }} /> 上一页
                      </button>
                      <span className="page-num">第 {zlibPage} 页</span>
                      <button className="btn btn-secondary" disabled={zlibResults.books.length < 15 || zlibLoading} onClick={() => handleZlibSearch(zlibPage + 1)}>
                        下一页 <ChevronRight style={{ width: '16px', height: '16px' }} />
                      </button>
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', minHeight: '300px', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
                    <BookOpen style={{ width: '32px', height: '32px', opacity: 0.5 }} />
                    <span style={{ fontSize: '13px' }}>未搜索到匹配的电子书，请换个词试试？</span>
                  </div>
                )}
              </div>
            ) : (
              /* Z-Library Styled Home view */
              <div className="zlib-home-layout">
                {/* Center logo and slogan */}
                <div className="zlib-home-header">
                  <div className="zlib-logo">
                    <span className="logo-z">z</span>
                    <span className="logo-library">library</span>
                  </div>
                  <p className="zlib-slogan">Your gateway to knowledge and culture. Accessible for everyone.</p>
                </div>

                {/* Big center search box */}
                <div className="zlib-home-search-container">
                  <div className="search-tabs">
                    <span className="search-tab active">常规检索</span>
                    <span className="search-tab" style={{ opacity: 0.4, cursor: 'not-allowed' }}>全文检索</span>
                  </div>

                  <div className="search-bar-card home-search-bar">
                    <input 
                      type="text" 
                      className="form-input zlib-search-input-large" 
                      placeholder="输入书名、作者、ISBN、出版社或 md5 码..."
                      value={zlibQuery}
                      onChange={(e) => setZlibQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleZlibSearch(1)}
                    />
                    <button className="btn btn-primary btn-large" onClick={() => handleZlibSearch(1)} disabled={zlibLoading || !zlibQuery.trim()}>
                      <Search className="btn-icon" style={{ width: '18px', height: '18px' }} />
                      <span style={{ fontSize: '15px' }}>搜索</span>
                    </button>
                  </div>

                  {/* Filters row immediately below input */}
                  <div className="home-search-filters">
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <select 
                        className="filter-select"
                        value={zlibFilters.extension}
                        onChange={(e) => setZlibFilters(prev => ({ ...prev, extension: e.target.value }))}
                      >
                        <option value="all">任意格式</option>
                        <option value="epub">EPUB</option>
                        <option value="pdf">PDF</option>
                        <option value="mobi">MOBI</option>
                        <option value="azw3">AZW3</option>
                        <option value="txt">TXT</option>
                      </select>

                      <select 
                        className="filter-select"
                        value={zlibFilters.language}
                        onChange={(e) => setZlibFilters(prev => ({ ...prev, language: e.target.value }))}
                      >
                        <option value="all">任意语言</option>
                        <option value="chinese">中文 (Chinese)</option>
                        <option value="english">英文 (English)</option>
                      </select>
                    </div>

                    <div className="gateway-status">
                      {zlibStatus.domain ? (
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          API 网关: <strong style={{ color: 'var(--accent-green)' }}>{zlibStatus.domain}</strong>
                        </span>
                      ) : (
                        <span style={{ fontSize: '11px', color: 'var(--accent-red)' }}>未能连接 Zlib 服务</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Unified recommendations section — shown for all users */}
                <div className="zlib-home-recommendations">
                  <div className="section-title-container">
                    <h3 className="section-title" style={{ margin: 0 }}>
                      {zlibStatus.logged_in ? '猜你喜欢 / 账户个人推荐' : '热门推荐书籍'}
                    </h3>
                    {zlibStatus.logged_in && (
                      <button className="refresh-rec-btn" onClick={fetchRecommendations} title="刷新推荐" disabled={recLoading}>
                        <RefreshCw className={`btn-icon ${recLoading ? 'spinner' : ''}`} style={{ width: '14px', height: '14px' }} />
                      </button>
                    )}
                  </div>

                  {/* Guest mode banner */}
                  {!zlibStatus.logged_in && (
                    <div className="guest-mode-banner">
                      <span>以下为热门经典书籍展示。登录后可获取个人推荐、搜索及一键推送功能。</span>
                      <button className="btn-link" onClick={() => setShowLoginModal(true)}>立即登录</button>
                    </div>
                  )}

                  {recLoading && (!displayedRecommendations || displayedRecommendations.length === 0) ? (
                    <div className="rec-loading-grid">
                      {[1, 2, 3, 4].map(i => (
                        <div key={i} className="book-card skeleton-card">
                          <div className="book-cover skeleton-element" />
                          <div className="book-info-container">
                            <div className="skeleton-line title" />
                            <div className="skeleton-line author" />
                            <div className="skeleton-line meta" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : recError ? (
                    <div className="rec-error-box">
                      <span>获取推荐图书失败：{recError}</span>
                      {zlibStatus.logged_in && (
                        <button className="btn btn-secondary" onClick={fetchRecommendations} style={{ padding: '4px 10px', fontSize: '11px' }}>
                          重试
                        </button>
                      )}
                    </div>
                  ) : displayedRecommendations && displayedRecommendations.length > 0 ? (
                    <div className="recommendations-scroll-container">
                      <div className="recommendations-grid">
                        {displayedRecommendations.map((book) => {
                          const bookId = book.id;
                          const pushingState = pushingBooks[bookId];
                          return (
                            <div key={bookId} className="book-card rec-book-card">
                              <div className="book-cover" onClick={() => handleOpenBookDetails(book)} style={{ cursor: 'pointer' }}>
                                {covers[bookId] ? (
                                  <img src={covers[bookId]} alt={book.title} />
                                ) : book.cover ? (
                                  <img src={book.cover} alt={book.title} onError={(e) => { e.target.style.display = 'none'; }} />
                                ) : (
                                  <BookOpen style={{ width: '24px', height: '24px', opacity: 0.3 }} />
                                )}
                              </div>
                              <div className="book-info-container">
                                <div onClick={() => handleOpenBookDetails(book)} style={{ display: 'flex', flexDirection: 'column', minWidth: 0, cursor: 'pointer' }}>
                                  <span className="book-title" title={book.title}>{book.title}</span>
                                  <span className="book-author" title={book.author}>{book.author || '未知'}</span>
                                  <div className="book-meta">
                                    <span className="badge badge-format">{book.extension}</span>
                                    <span className="badge badge-size">{book.filesizeString || '未知'}</span>
                                  </div>
                                </div>
                                <div className="push-btn-container" style={{ marginTop: '6px' }}>
                                  {!zlibStatus.logged_in ? (
                                    <button
                                      className="btn btn-secondary"
                                      style={{ width: '100%', fontSize: '10px', padding: '4px 0' }}
                                      onClick={() => setShowLoginModal(true)}
                                    >
                                      登录后操作
                                    </button>
                                  ) : (
                                    <>
                                      {pushingState === 'downloading' && (
                                        <button className="btn btn-secondary" style={{ width: '100%', fontSize: '10px', padding: '4px 0' }} disabled>
                                          <Spinner /> 下载中
                                        </button>
                                      )}
                                      {pushingState === 'pushing' && (
                                        <button className="btn btn-secondary" style={{ width: '100%', fontSize: '10px', padding: '4px 0' }} disabled>
                                          <Spinner /> 推送中
                                        </button>
                                      )}
                                      {pushingState === 'success' && (
                                        <button className="btn btn-secondary" style={{ width: '100%', fontSize: '10px', padding: '4px 0', border: '1px solid rgba(16, 185, 129, 0.4)', color: 'var(--accent-green)' }} disabled>
                                          <CheckCircle style={{ width: '10px', height: '10px' }} /> 已推送
                                        </button>
                                      )}
                                      {(!pushingState || pushingState.status === 'error') && (
                                        <button
                                          className="btn btn-primary"
                                          style={{ width: '100%', fontSize: '10px', padding: '4px 0' }}
                                          onClick={() => handleCheckAndPushBook(book)}
                                        >
                                          <Download style={{ width: '10px', height: '10px' }} /> 推送 Kindle
                                        </button>
                                      )}
                                    </>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Load More button — only for logged-in users */}
                      {zlibStatus.logged_in && (
                        <div className="load-more-container">
                          <button className="btn-load-more" onClick={handleLoadMoreRecommendations} disabled={loadMoreLoading}>
                            {loadMoreLoading ? <Spinner /> : null}
                            {loadMoreLoading ? '正在加载...' : '显示更多推荐与热门图书'}
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="rec-empty-box">
                      <span>暂无书籍数据。</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Dashboard/Watcher */}
        {activeTab === 'dashboard' && (
          <div className="view-container">
            <div className="view-header">
              <h2 className="view-title">自动扫描服务监控</h2>
              <div className="service-toggle-card" style={{ padding: '6px 12px' }}>
                <div className="toggle-info" style={{ marginRight: '14px' }}>
                  <span className="toggle-desc" style={{ fontSize: '11px', fontWeight: 'bold' }}>{serviceRunning ? '守护运行中' : '服务已停止'}</span>
                </div>
                <label className="switch" style={{ width: '38px', height: '20px' }}>
                  <input 
                    type="checkbox" 
                    checked={serviceRunning}
                    onChange={(e) => handleToggleService(e.target.checked)}
                  />
                  <span className="slider" style={{ borderRadius: '20px' }}></span>
                </label>
              </div>
            </div>
            
            <div className="stats-grid">
              <div className="glass-card">
                <div className={`card-icon-container ${serviceRunning ? 'green' : 'yellow'}`}>
                  {serviceRunning ? <Play className="btn-icon" /> : <Square className="btn-icon" />}
                </div>
                <div className="card-content">
                  <span className="card-label">自动扫描监控状态</span>
                  <span className="card-value" style={{ color: serviceRunning ? 'var(--accent-green)' : 'var(--accent-yellow)' }}>
                    {serviceRunning ? '运行中' : '已停止'}
                  </span>
                  <span className="card-subtext" title={config.scan_folder}>
                    {serviceRunning ? `目录: ${config.scan_folder ? config.scan_folder.split(/[\\/]/).pop() : '未命名'}` : '定时扫描目录未激活'}
                  </span>
                </div>
              </div>

              <div className="glass-card">
                <div className="card-icon-container blue">
                  <History className="btn-icon" />
                </div>
                <div className="card-content">
                  <span className="card-label">成功推送书籍数</span>
                  <span className="card-value">{history.length} 本</span>
                  <span className="card-subtext">
                    {history.length > 0 ? `最后推送: ${history[0].sent_at || ''}` : '防重复过滤器运行中'}
                  </span>
                </div>
              </div>
            </div>

            <div className="console-card">
              <div className="console-header">
                <div className="console-title">
                  <History style={{ width: '16px', height: '16px', color: 'var(--accent-blue)' }} />
                  <span>实时运行日志</span>
                </div>
                <div className="console-actions">
                  <button className="btn btn-secondary" onClick={handleOpenScanFolder} style={{ padding: '6px 12px' }}>
                    打开本地目录
                  </button>
                  <button className="btn btn-primary" onClick={handleManualScan} style={{ padding: '6px 12px' }}>
                    立即扫描推送
                  </button>
                </div>
              </div>
              <div className="console-body">
                {logs.length === 0 ? (
                  <div style={{ color: '#6b7280', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                    等待后台服务日志输出...
                  </div>
                ) : (
                  logs.map((log, idx) => (
                    <div key={idx} className={`log-item ${log.type}`}>
                      {log.text}
                    </div>
                  ))
                )}
                <div ref={consoleEndRef} />
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: History */}
        {activeTab === 'history' && (
          <div className="view-container">
            <div className="view-header">
              <h2 className="view-title">电子书推送历史记录</h2>
              <button className="btn btn-danger" onClick={handleClearHistory} disabled={history.length === 0} style={{ padding: '6px 12px' }}>
                <Trash2 style={{ width: '14px', height: '14px' }} /> 清空全部历史
              </button>
            </div>

            <div className="history-table-container">
              <div className="history-header-row">
                <span>书籍名称</span>
                <span style={{ textAlign: 'center' }}>大小</span>
                <span style={{ textAlign: 'center' }}>状态</span>
                <span style={{ textAlign: 'right' }}>操作时间</span>
              </div>
              <div className="history-scroll">
                {history.length === 0 ? (
                  <div className="history-empty">
                    <Info style={{ width: '20px', height: '20px', display: 'block', margin: '0 auto 8px', color: 'var(--text-muted)' }} />
                    暂无推送/下载记录。在本地目录放入电子书，开启自动扫描或直接从 Z-Library 推送！
                  </div>
                ) : (
                  history.map((record, index) => (
                    <div key={index} className="history-row">
                      <span className="book-title-cell" title={record.file_name}>{record.file_name}</span>
                      <span style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>{record.file_size || '未知'}</span>
                      <span style={{ textAlign: 'center' }}>
                        <span className={`status-badge ${record.status === 'downloaded' ? 'status-downloaded' : 'status-sent'}`}>
                          {record.status === 'downloaded' ? '仅下载' : '已推送'}
                        </span>
                      </span>
                      <span style={{ textAlign: 'right', color: 'var(--text-muted)' }}>{record.sent_at || ''}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB: 我的书库 — Saved Books from Z-Library */}
        {activeTab === 'library' && (
          <div className="view-container" style={{ overflowY: 'auto' }}>
            <div className="view-header">
              <h2 className="view-title">我的书库</h2>
              <span className="view-subtitle">在 Z-Library 上收藏的书籍</span>
            </div>

            {!zlibStatus.logged_in ? (
              <div className="guest-mode-banner" style={{ margin: '40px auto', maxWidth: '480px', flexDirection: 'column', gap: '12px', textAlign: 'center' }}>
                <span style={{ fontSize: '14px' }}>请先登录 Z-Library 账号，才能查看您的收藏书单</span>
                <button className="btn btn-primary" onClick={() => setShowLoginModal(true)}>登录 Z-Library</button>
              </div>
            ) : savedBooksLoading ? (
              <div className="books-grid">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="book-card skeleton-card">
                    <div className="book-cover skeleton-element" />
                    <div className="book-info-container">
                      <div className="skeleton-line title skeleton-element" />
                      <div className="skeleton-line author skeleton-element" />
                      <div className="skeleton-line meta skeleton-element" style={{ width: '40%' }} />
                      <div style={{ display: 'flex', gap: '6px', marginTop: 'auto' }}>
                        <div className="skeleton-element" style={{ flex: 1, height: '28px', borderRadius: '6px' }} />
                        <div className="skeleton-element" style={{ width: '50px', height: '28px', borderRadius: '6px' }} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : savedBooksError ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--accent-red)' }}>
                <AlertTriangle style={{ width: '36px', height: '36px', display: 'block', margin: '0 auto 12px' }} />
                <span>{savedBooksError}</span>
              </div>
            ) : savedBooks.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: '48px', marginBottom: '12px' }}>📚</div>
                <p>您还没有收藏任何书籍。</p>
                <p style={{ fontSize: '13px' }}>在找书主页中，点击「加入收藏」按钮即可收藏。</p>
              </div>
            ) : (
              <div className="books-grid">
                {savedBooks.map((book) => {
                  const bookId = book.id;
                  const pushingState = pushingBooks[bookId];
                  return (
                    <div key={bookId} className="book-card">
                      <div className="book-cover" onClick={() => handleOpenBookDetails(book)} style={{ cursor: 'pointer' }}>
                        {covers[bookId] ? (
                          <img src={covers[bookId]} alt={book.title} />
                        ) : (
                          <BookOpen style={{ width: '28px', height: '28px', opacity: 0.3 }} />
                        )}
                      </div>
                      <div className="book-info-container">
                        <div onClick={() => handleOpenBookDetails(book)} style={{ display: 'flex', flexDirection: 'column', minWidth: 0, cursor: 'pointer' }}>
                          <span className="book-title" title={book.title}>{book.title}</span>
                          <span className="book-author" title={book.author}>{book.author || '未知作者'}</span>
                          <div className="book-meta">
                            <span className="badge badge-format">{book.extension}</span>
                            <span className="badge badge-size">{book.filesizeString || '未知大小'}</span>
                          </div>
                        </div>
                        <div className="push-btn-container" style={{ gap: '6px', marginTop: 'auto' }}>
                          {pushingState === 'downloading' && (
                            <button className="btn btn-secondary" style={{ flex: 1, fontSize: '11px', padding: '5px 0' }} disabled>
                              <Spinner /> 下载中...
                            </button>
                          )}
                          {pushingState === 'pushing' && (
                            <button className="btn btn-secondary" style={{ flex: 1, fontSize: '11px', padding: '5px 0' }} disabled>
                              <Spinner /> 推送中...
                            </button>
                          )}
                          {pushingState === 'success' && (
                            <button className="btn btn-secondary" style={{ flex: 1, fontSize: '11px', padding: '5px 0', border: '1px solid rgba(16, 185, 129, 0.4)', color: 'var(--accent-green)' }} disabled>
                              <CheckCircle style={{ width: '12px', height: '12px' }} /> 已送达
                            </button>
                          )}
                          {(!pushingState || pushingState.status === 'error') && (
                            <button
                              className="btn btn-primary"
                              style={{ flex: 1, fontSize: '11px', padding: '5px 0' }}
                              onClick={e => { e.stopPropagation(); executePushBook(book); }}
                            >
                              <Download style={{ width: '12px', height: '12px' }} /> 推送 Kindle
                            </button>
                          )}
                          <button
                            className="btn btn-secondary"
                            style={{ fontSize: '11px', padding: '5px 8px', color: 'var(--accent-red)' }}
                            disabled={unsavingBooks[bookId]}
                            onClick={async e => {
                              e.stopPropagation();
                              setUnsavingBooks(p => ({ ...p, [bookId]: true }));
                              try {
                                await callApi('zlib_unsave_book', bookId);
                                setSavedBooks(prev => prev.filter(b => b.id !== bookId));
                              } catch(err) { console.error(err); }
                              setUnsavingBooks(p => { const n={...p}; delete n[bookId]; return n; });
                            }}
                          >
                            {unsavingBooks[bookId] ? '…' : '取消'}
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            {savedBooks.length > 0 && !savedBooksLoading && (
              <div style={{ textAlign: 'center', padding: '16px', color: 'var(--text-muted)', fontSize: '12px' }}>
                共 {savedBooks.length} 本收藏书籍（显示最近 {savedBooks.length} 本）
              </div>
            )}
          </div>
        )}

        {/* TAB: 我的主页 — Profile */}
        {activeTab === 'profile' && (
          <div className="view-container" style={{ overflowY: 'auto' }}>
            <div className="view-header">
              <h2 className="view-title">我的主页</h2>
              <span className="view-subtitle">Z-Library 账号概览</span>
            </div>

            {!zlibStatus.logged_in ? (
              <div className="guest-mode-banner" style={{ margin: '40px auto', maxWidth: '480px', flexDirection: 'column', gap: '12px', textAlign: 'center' }}>
                <span style={{ fontSize: '14px' }}>请先登录 Z-Library 账号</span>
                <button className="btn btn-primary" onClick={() => setShowLoginModal(true)}>登录 Z-Library</button>
              </div>
            ) : profileLoading ? (
              <div className="profile-container">
                {/* Profile Card Skeleton */}
                <div className="glass-card profile-card">
                  <div className="skeleton-element" style={{ width: '72px', height: '72px', borderRadius: '50%', flexShrink: 0 }} />
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div className="skeleton-element" style={{ width: '150px', height: '20px', borderRadius: '4px' }} />
                    <div className="skeleton-element" style={{ width: '220px', height: '14px', borderRadius: '4px' }} />
                    <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
                      <div className="skeleton-element" style={{ width: '80px', height: '20px', borderRadius: '10px' }} />
                      <div className="skeleton-element" style={{ width: '60px', height: '20px', borderRadius: '10px' }} />
                    </div>
                  </div>
                </div>

                {/* Quota Card Skeleton */}
                <div className="glass-card quota-card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div className="skeleton-element" style={{ width: '100px', height: '14px', borderRadius: '4px' }} />
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div className="skeleton-element" style={{ flex: 1, height: '8px', borderRadius: '4px' }} />
                    <div className="skeleton-element" style={{ width: '50px', height: '18px', borderRadius: '4px' }} />
                  </div>
                  <div className="skeleton-element" style={{ width: '140px', height: '12px', borderRadius: '4px' }} />
                </div>

                {/* Recent Saves Skeleton */}
                <div className="glass-card recent-saves-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div className="skeleton-element" style={{ width: '80px', height: '14px', borderRadius: '4px' }} />
                    <div className="skeleton-element" style={{ width: '60px', height: '14px', borderRadius: '4px' }} />
                  </div>
                  <div className="recent-saves-list">
                    {[1, 2, 3].map(i => (
                      <div key={i} style={{ display: 'flex', gap: '12px', alignItems: 'center', padding: '8px 0' }}>
                        <div className="skeleton-element" style={{ width: '36px', height: '48px', borderRadius: '4px', flexShrink: 0 }} />
                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          <div className="skeleton-element" style={{ width: '60%', height: '13px', borderRadius: '4px' }} />
                          <div className="skeleton-element" style={{ width: '40%', height: '11px', borderRadius: '4px' }} />
                        </div>
                        <div className="skeleton-element" style={{ width: '40px', height: '16px', borderRadius: '8px', flexShrink: 0 }} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : profileData ? (
              <div className="profile-container">

                {/* Profile Card */}
                <div className="glass-card profile-card">
                  <div className="profile-avatar">
                    {(profileData.user?.name || profileData.user?.email || 'Z')[0].toUpperCase()}
                  </div>
                  <div className="profile-details">
                    <div className="profile-name">
                      {profileData.user?.name || '未知用户'}
                    </div>
                    <div className="profile-email">
                      {profileData.user?.email}
                    </div>
                    <div className="profile-badges-row">
                      <span className={profileData.user?.isPremium ? 'badge-premium' : 'badge-guest'}>
                        {profileData.user?.isPremium ? '⭐ Premium' : '免费用户'}
                      </span>
                      {profileData.user?.confirmed ? (
                        <span className="badge-verified">✓ 已验证</span>
                      ) : null}
                    </div>
                  </div>
                </div>

                {/* Download Quota */}
                <div className="glass-card quota-card">
                  <div className="quota-title">今日下载配额</div>
                  <div className="quota-progress-container">
                    <div className="quota-progress-track">
                      <div 
                        className="quota-progress-bar" 
                        style={{ width: `${Math.min(100, ((profileData.user?.downloads_today || 0) / (profileData.user?.downloads_limit || 10)) * 100)}%` }} 
                      />
                    </div>
                    <div className="quota-value">
                      {profileData.user?.downloads_today || 0} / {profileData.user?.downloads_limit || 10}
                    </div>
                  </div>
                  <div className="quota-remaining">
                    今日还剩 <strong>{Math.max(0, (profileData.user?.downloads_limit || 10) - (profileData.user?.downloads_today || 0))}</strong> 次下载
                  </div>
                </div>

                {/* Recent Saves */}
                {profileData.recentSaved?.length > 0 && (
                  <div className="glass-card recent-saves-card">
                    <div className="recent-saves-header">
                      <div className="quota-title" style={{ margin: 0 }}>最近收藏</div>
                      <button className="btn-link" onClick={() => setActiveTab('library')} style={{ fontSize: '12px', color: 'var(--accent-blue)' }}>查看全部 →</button>
                    </div>
                    <div className="recent-saves-list">
                      {profileData.recentSaved.map(book => (
                        <div key={book.id} onClick={() => handleOpenBookDetails(book)} className="recent-save-item">
                          {covers[book.id] ? (
                            <img src={covers[book.id]} alt="" className="recent-save-cover" />
                          ) : (
                            <div className="recent-save-cover-placeholder">
                              <span>{(book.title||'?')[0]}</span>
                            </div>
                          )}
                          <div className="recent-save-info">
                            <div className="recent-save-title">{book.title}</div>
                            <div className="recent-save-author">{book.author}</div>
                          </div>
                          <span className="recent-save-badge">
                            {(book.extension||'').toUpperCase()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Kindle Email */}
                {profileData.user?.kindle_email && (
                  <div className="glass-card email-card">
                    <div className="email-card-title">绑定的 Kindle 邮箱</div>
                    <div className="email-card-value">{profileData.user.kindle_email}</div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>加载失败，请重试</div>
            )}
          </div>
        )}

        {/* TAB 4: Unified Settings */}
        {activeTab === 'settings' && (
          <div className="view-container">
            <div className="view-header">
              <h2 className="view-title">系统设置中心</h2>
            </div>

            <div className="settings-grid-layout">
              {/* Card 1: SMTP Send config */}
              <div className="glass-card settings-card" style={{ display: 'block' }}>
                <h3 className="settings-card-title" style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Mail style={{ color: 'var(--accent-blue)', width: '18px', height: '18px' }} />
                  <span>发信邮箱配置 (SMTP)</span>
                </h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '14px' }}>
                  <div className="form-group">
                    <label className="form-label">常用邮箱服务商预设</label>
                    <select 
                      className="filter-select"
                      value={config.smtp_server === 'smtp.gmail.com' ? 'Gmail' : config.smtp_server === 'smtp.qq.com' ? 'QQ 邮箱' : config.smtp_server === 'smtp.163.com' ? '网易 163 邮箱' : '自定义 SMTP'}
                      onChange={(e) => handlePresetChange(e.target.value)}
                    >
                      <option value="Gmail">Gmail</option>
                      <option value="QQ 邮箱">QQ 邮箱</option>
                      <option value="网易 163 邮箱">网易 163 邮箱</option>
                      <option value="自定义 SMTP">自定义 SMTP</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">发信人电子邮箱</label>
                    <input 
                      type="email" 
                      className="form-input" 
                      placeholder="example@domain.com"
                      value={config.sender_email || ''} 
                      onChange={(e) => handleConfigChange('sender_email', e.target.value.trim())}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">邮箱授权码/应用专用密码</label>
                    <div className="input-with-button">
                      <input 
                        type={showSmtpPassword ? "text" : "password"} 
                        className="form-input"
                        placeholder="16位授权码或发信密码"
                        value={config.smtp_password || ''}
                        onChange={(e) => handleConfigChange('smtp_password', e.target.value.trim())}
                      />
                      <button className="btn btn-secondary" style={{ padding: '10px' }} onClick={() => setShowSmtpPassword(!showSmtpPassword)}>
                        {showSmtpPassword ? <EyeOff style={{ width: '16px', height: '16px' }} /> : <Eye style={{ width: '16px', height: '16px' }} />}
                      </button>
                    </div>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">SMTP 服务器地址</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        value={config.smtp_server || ''}
                        onChange={(e) => handleConfigChange('smtp_server', e.target.value.trim())}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">端口</label>
                      <input 
                        type="number" 
                        className="form-input" 
                        value={config.smtp_port || 587}
                        onChange={(e) => handleConfigChange('smtp_port', parseInt(e.target.value) || 587)}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">安全协议</label>
                    <div className="radio-group">
                      <label className="radio-label">
                        <input 
                          type="radio" 
                          name="smtp_use_ssl" 
                          checked={config.smtp_use_ssl === false} 
                          onChange={() => {
                            handleConfigChange('smtp_use_ssl', false);
                            handleConfigChange('smtp_port', 587);
                          }}
                        />
                        <span>TLS (默认 587)</span>
                      </label>
                      <label className="radio-label">
                        <input 
                          type="radio" 
                          name="smtp_use_ssl" 
                          checked={config.smtp_use_ssl === true} 
                          onChange={() => {
                            handleConfigChange('smtp_use_ssl', true);
                            handleConfigChange('smtp_port', 465);
                          }}
                        />
                        <span>SSL (默认 465)</span>
                      </label>
                    </div>
                  </div>

                  <button className="btn btn-secondary" onClick={handleTestSmtp} disabled={smtpTesting} style={{ marginTop: '8px' }}>
                    {smtpTesting ? <Spinner /> : null}
                    {smtpTesting ? '连接测试中...' : '测试 SMTP 连接'}
                  </button>

                  {smtpTestResult && (
                    <div className="guide-box" style={{ 
                      padding: '10px 14px',
                      borderColor: smtpTestResult.success ? 'var(--accent-green)' : 'var(--accent-red)',
                      background: smtpTestResult.success ? 'rgba(16, 185, 129, 0.05)' : 'rgba(239, 68, 68, 0.05)'
                    }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: smtpTestResult.success ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                        {smtpTestResult.success ? '✅ 测试通过' : '❌ 连接失败'}
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>
                        {smtpTestResult.message}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Card 2: Folder & Kindle Receiver */}
              <div className="glass-card settings-card" style={{ display: 'block' }}>
                <h3 className="settings-card-title" style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FolderOpen style={{ color: 'var(--accent-purple)', width: '18px', height: '18px' }} />
                  <span>本地监控与 Kindle 接收端</span>
                </h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '14px' }}>
                  <div className="form-group">
                    <label className="form-label">Kindle 专属接收邮箱</label>
                    <input 
                      type="email" 
                      className="form-input" 
                      placeholder="xxx@kindle.com"
                      value={config.kindle_email || ''} 
                      onChange={(e) => handleConfigChange('kindle_email', e.target.value.trim())}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">自动监控的本地文件夹目录</label>
                    <div className="input-with-button">
                      <input 
                        type="text" 
                        className="form-input" 
                        value={config.scan_folder || ''} 
                        onChange={(e) => handleConfigChange('scan_folder', e.target.value)}
                      />
                      <button className="btn btn-secondary" style={{ flexShrink: 0 }} onClick={handleBrowseFolder}>
                        选择
                      </button>
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">扫描间隔: <strong style={{ color: 'var(--accent-blue)' }}>{config.scan_interval_minutes || 10} 分钟</strong></label>
                    <input 
                      type="range" 
                      min="1" 
                      max="60" 
                      style={{ accentColor: 'var(--accent-blue)', cursor: 'pointer' }}
                      value={config.scan_interval_minutes || 10}
                      onChange={(e) => handleConfigChange('scan_interval_minutes', parseInt(e.target.value) || 10)}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">允许扫描推送的文件格式</label>
                    <div className="checkbox-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', padding: '10px' }}>
                      {['.epub', '.pdf', '.mobi', '.azw3', '.txt', '.docx'].map(ext => (
                        <label key={ext} className="checkbox-label" style={{ fontSize: '11px' }}>
                          <input 
                            type="checkbox" 
                            checked={(config.allowed_extensions || []).includes(ext)}
                            onChange={(e) => handleCheckboxChange(ext, e.target.checked)}
                          />
                          <span>{ext.substring(1).toUpperCase()}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Card 3: Network Proxy & Custom domain */}
              <div className="glass-card settings-card" style={{ display: 'block' }}>
                <h3 className="settings-card-title" style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Settings style={{ color: 'var(--accent-green)', width: '18px', height: '18px' }} />
                  <span>代理与 API 域名设置</span>
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '14px' }}>
                  <div className="form-group">
                    <label className="checkbox-label" style={{ padding: '4px 0' }}>
                      <input 
                        type="checkbox" 
                        checked={config.proxy_enabled || false}
                        onChange={(e) => handleConfigChange('proxy_enabled', e.target.checked)}
                      />
                      <span>启用代理服务 (支持本地 Clash/Socks 代理)</span>
                    </label>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">代理类型</label>
                      <select 
                        className="filter-select"
                        disabled={!config.proxy_enabled}
                        value={config.proxy_type || 'SOCKS5'}
                        onChange={(e) => handleConfigChange('proxy_type', e.target.value)}
                      >
                        <option value="SOCKS5">SOCKS5</option>
                        <option value="HTTP">HTTP</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">端口</label>
                      <input 
                        type="number" 
                        className="form-input" 
                        disabled={!config.proxy_enabled}
                        value={config.proxy_port || 7890}
                        onChange={(e) => handleConfigChange('proxy_port', parseInt(e.target.value) || 7890)}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">代理服务器地址</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      disabled={!config.proxy_enabled}
                      value={config.proxy_host || '127.0.0.1'}
                      onChange={(e) => handleConfigChange('proxy_host', e.target.value.trim())}
                    />
                  </div>

                  <div style={{ margin: '6px 0', height: '1px', backgroundColor: 'var(--border-color)' }} />

                  <div className="form-group">
                    <label className="form-label">自定义 Z-Library API 域名 (可选)</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="例如: z-library.sk"
                      value={config.zlib_custom_domain || ''} 
                      onChange={(e) => handleConfigChange('zlib_custom_domain', e.target.value.trim())}
                    />
                  </div>
                </div>
              </div>

              {/* Card 4: System guide and run settings */}
              <div className="glass-card settings-card" style={{ display: 'block' }}>
                <h3 className="settings-card-title" style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Info style={{ color: 'var(--accent-yellow)', width: '18px', height: '18px' }} />
                  <span>辅助设置与授权指南</span>
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '14px' }}>
                  <div className="form-group">
                    <label className="checkbox-label">
                      <input 
                        type="checkbox" 
                        checked={config.minimize_to_tray !== false}
                        onChange={(e) => handleConfigChange('minimize_to_tray', e.target.checked)}
                      />
                      <span>关闭窗口时最小化到系统托盘，后台监控</span>
                    </label>
                  </div>

                  <div className="form-group">
                    <label className="checkbox-label">
                      <input 
                        type="checkbox" 
                        checked={config.auto_start_service || false}
                        onChange={(e) => handleConfigChange('auto_start_service', e.target.checked)}
                      />
                      <span>程序启动时自动开启自动监控服务</span>
                    </label>
                  </div>

                  <div className="guide-box" style={{ padding: '10px 14px', fontSize: '11px', marginTop: '6px', maxHeight: '180px', overflowY: 'auto' }}>
                    <strong>📧 常用发信参数指南：</strong><br/>
                    • <strong>Gmail</strong>: SMTP 地址 为 <code>smtp.gmail.com</code>，安全协议 TLS 端口 <code>587</code>。需开启谷歌账号两步验证并使用【应用专用密码】。<br/>
                    • <strong>QQ 邮箱</strong>: SMTP 地址 为 <code>smtp.qq.com</code>，安全协议 SSL 端口 <code>465</code>。需在网页设置中启用并生成【发信授权码】。<br/>
                    • <strong>163 邮箱</strong>: SMTP 地址 为 <code>smtp.163.com</code>，安全协议 SSL 端口 <code>465</code>。
                  </div>
                </div>
              </div>
            </div>

            <div style={{ marginTop: '20px', display: 'flex', gap: '12px' }}>
              <button className="btn btn-primary" onClick={handleSaveConfig} style={{ padding: '12px 24px' }}>
                保存全部设置
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer Status Bar */}
      <footer className="status-bar">
        <div className="status-left">
          <span className="status-dot green" />
          <span>发信邮箱: <strong>{config.sender_email || '未配置'}</strong></span>
        </div>
        <div className="status-right">
          <span>Kindle 接收端: <strong>{config.kindle_email || '未配置'}</strong></span>
          <span style={{ margin: '0 4px', color: 'rgba(255,255,255,0.1)' }}>|</span>
          <span>扫描频率: <strong>{config.scan_interval_minutes || 10} 分钟/次</strong></span>
        </div>
      </footer>

      {/* Book Details Modal */}
      {activeBookDetail && (
        <div className="modal-backdrop" onClick={() => setActiveBookDetail(null)}>
          <div className="book-detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title-text">
                <BookOpen style={{ width: '18px', height: '18px', color: 'var(--accent-blue)' }} />
                书籍详情 (Book Details)
              </span>
              <button className="modal-close-btn" onClick={() => setActiveBookDetail(null)}>
                <X style={{ width: '18px', height: '18px' }} />
              </button>
            </div>

            <div className="book-detail-split">
              {/* Left sidebar: Cover + metadata badges + format dropdown */}
              <div className="book-detail-left">
                <div className="book-detail-cover">
                  {covers[activeBookDetail.id] ? (
                    <img src={covers[activeBookDetail.id]} alt={activeBookDetail.title} />
                  ) : activeBookDetail.cover ? (
                    <img src={activeBookDetail.cover} alt={activeBookDetail.title} />
                  ) : (
                    <BookOpen style={{ width: '48px', height: '48px', opacity: 0.2 }} />
                  )}
                </div>

                <div className="book-detail-badges">
                  <div className="badge-row">
                    <span className="badge-label">格式:</span>
                    <span className="badge-val" style={{ textTransform: 'uppercase', color: 'var(--accent-blue)' }}>
                      {(selectedFormat || activeBookDetail).extension || '加载中'}
                    </span>
                  </div>
                  <div className="badge-row">
                    <span className="badge-label">大小:</span>
                    <span className="badge-val">{(selectedFormat || activeBookDetail).filesizeString || '加载中'}</span>
                  </div>
                  <div className="badge-row">
                    <span className="badge-label">评分:</span>
                    <span className="badge-val" style={{ color: 'var(--accent-yellow)' }}>
                      ★ {activeBookDetail.interestScore || '无'}
                    </span>
                  </div>
                </div>

                {/* Available formats select dropdown */}
                {availableFormats.length > 1 && (
                  <div className="formats-select-container">
                    <span className="formats-label">选择其他版本/格式:</span>
                    <select 
                      className="formats-dropdown"
                      value={selectedFormat ? selectedFormat.id : ''}
                      onChange={(e) => {
                        const targetId = parseInt(e.target.value);
                        const found = availableFormats.find(f => f.id === targetId);
                        if (found) {
                          setSelectedFormat(found);
                        }
                      }}
                    >
                      {availableFormats.map(f => (
                        <option key={f.id} value={f.id}>
                          {(f.extension || '').toUpperCase()} ({f.filesizeString || '加载中'})
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* Right panel: Title + Actions + Tabs + Tab content */}
              <div className="book-detail-right">
                <div className="book-detail-meta-header">
                  <h2 className="detail-title" title={activeBookDetail.title}>{activeBookDetail.title}</h2>
                  <span className="detail-author">{activeBookDetail.author || '未知作者'}</span>
                </div>

                <div className="book-detail-actions">
                  {/* Push button */}
                  {pushingBooks[selectedFormat ? selectedFormat.id : activeBookDetail.id] === 'downloading' && (
                    <button className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '12px' }} disabled>
                      <Spinner /> 下载中...
                    </button>
                  )}
                  {pushingBooks[selectedFormat ? selectedFormat.id : activeBookDetail.id] === 'pushing' && (
                    <button className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '12px' }} disabled>
                      <Spinner /> 推送中...
                    </button>
                  )}
                  {pushingBooks[selectedFormat ? selectedFormat.id : activeBookDetail.id] === 'success' && (
                    <button className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '12px', border: '1px solid rgba(16, 185, 129, 0.4)', color: 'var(--accent-green)' }} disabled>
                      <CheckCircle style={{ width: '14px', height: '14px' }} /> 已发送至 Kindle
                    </button>
                  )}
                  {(!pushingBooks[selectedFormat ? selectedFormat.id : activeBookDetail.id] || pushingBooks[selectedFormat ? selectedFormat.id : activeBookDetail.id].status === 'error') && (
                    <button className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '12px' }} onClick={() => handleCheckAndPushBook(activeBookDetail)}>
                      <Download style={{ width: '14px', height: '14px' }} /> 一键推送至 Kindle
                    </button>
                  )}

                  {/* Download button */}
                  <button className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '12px' }} onClick={() => handleDownloadOnly(activeBookDetail)}>
                    <Download style={{ width: '14px', height: '14px', color: 'var(--accent-blue)' }} /> 仅下载到本地
                  </button>

                  {/* Bookmark button */}
                  <button 
                    className="btn btn-secondary" 
                    style={{ padding: '8px 16px', fontSize: '12px', color: activeBookDetail._isUserSavedBook ? 'var(--accent-yellow)' : 'var(--text-primary)' }} 
                    onClick={() => handleToggleBookmark(activeBookDetail.id)}
                    disabled={bookmarkToggling || bookDetailLoading}
                  >
                    {bookmarkToggling ? (
                      <Spinner />
                    ) : activeBookDetail._isUserSavedBook ? (
                      <Star style={{ width: '14px', height: '14px', fill: 'currentColor' }} />
                    ) : (
                      <Star style={{ width: '14px', height: '14px' }} />
                    )}
                    <span>{activeBookDetail._isUserSavedBook ? '已收藏' : '加入收藏'}</span>
                  </button>
                </div>

                {/* Tabs */}
                <div className="book-detail-tabs">
                  <button 
                    className={`book-detail-tab-btn ${bookDetailActiveTab === 'desc' ? 'active' : ''}`} 
                    onClick={() => setBookDetailActiveTab('desc')}
                  >
                    内容简介 (About Book)
                  </button>
                  <button 
                    className={`book-detail-tab-btn ${bookDetailActiveTab === 'meta' ? 'active' : ''}`} 
                    onClick={() => setBookDetailActiveTab('meta')}
                  >
                    图书元数据
                  </button>
                  <button 
                    className={`book-detail-tab-btn ${bookDetailActiveTab === 'comments' ? 'active' : ''}`} 
                    onClick={() => setBookDetailActiveTab('comments')}
                  >
                    用户评论
                  </button>
                </div>

                {/* Tab content */}
                <div className="book-detail-tab-content">
                  {bookDetailLoading ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 0', gap: '10px', color: 'var(--text-secondary)' }}>
                      <Spinner />
                      <span>正在从 Z-Library 加载详细元数据...</span>
                    </div>
                  ) : bookDetailError ? (
                    <div style={{ color: 'var(--accent-red)', padding: '20px 0', textAlign: 'center' }}>
                      ⚠️ 元数据加载失败: {bookDetailError}
                    </div>
                  ) : bookDetailActiveTab === 'desc' ? (
                    activeBookDetail.description ? (
                      <div className="book-desc-content" dangerouslySetInnerHTML={{ __html: activeBookDetail.description }} />
                    ) : (
                      <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', padding: '20px 0' }}>暂无该图书的内容简介。</div>
                    )
                  ) : bookDetailActiveTab === 'comments' ? (
                    <div className="comments-section-container">
                      {commentsLoading ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px 0', gap: '8px', color: 'var(--text-secondary)' }}>
                          <Spinner />
                          <span>正在加载评论与笔记...</span>
                        </div>
                      ) : (
                        <>
                          <div className="comments-list">
                            {/* API limitation notice + open in browser */}
                            <div style={{
                              background: 'rgba(99,179,237,0.07)', border: '1px solid rgba(99,179,237,0.2)',
                              borderRadius: '10px', padding: '12px 14px', marginBottom: '12px',
                              display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12.5px', color: 'var(--text-secondary)'
                            }}>
                              <span style={{ fontSize: '16px', flexShrink: 0 }}>ℹ️</span>
                              <div style={{ flex: 1 }}>Z-Library 用户评论仅限网页版读取，无法通过 API 获取。</div>
                              {activeBookDetail?.href && (
                                <button
                                  className="btn btn-ghost"
                                  style={{ fontSize: '11px', padding: '5px 10px', whiteSpace: 'nowrap', border: '1px solid rgba(99,179,237,0.3)', color: 'var(--accent-blue)', flexShrink: 0 }}
                                  onClick={() => callApi('open_url_in_browser', activeBookDetail.href)}
                                >
                                  🌐 浏览器中查看评论
                                </button>
                              )}
                            </div>

                            {!Array.isArray(comments) || comments.length === 0 ? (
                              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', padding: '16px 0', fontSize: '13px', textAlign: 'center' }}>
                                暂无读书笔记，在下方写下第一条！
                              </div>
                            ) : (
                              comments.map((comment, idx) => comment ? (
                                <div key={idx} className={`comment-item${comment.is_local ? ' comment-local' : ''}`}>
                                  <div className="comment-avatar">
                                    {comment.avatar_char || (comment.username || '?')[0].toUpperCase()}
                                  </div>
                                  <div className="comment-body">
                                    <div className="comment-user-meta">
                                      <span className="comment-username">{comment.username || '匿名'}</span>
                                      {comment.is_local && (
                                        <span className="comment-local-badge">我的笔记</span>
                                      )}
                                      <span className="comment-date">{comment.created_at || ''}</span>
                                    </div>
                                    <div className="comment-text">{comment.content || ''}</div>
                                  </div>
                                </div>
                              ) : null)
                            )}
                          </div>

                          <form className="comment-form-container" onSubmit={handleSubmitComment}>
                            <span className="comment-form-title">添加我的书评与读书笔记:</span>
                            <div className="comment-form-inputs">
                              <input 
                                type="text" 
                                className="form-input comment-username-input" 
                                placeholder="署名 (选填)"
                                value={newCommentUsername}
                                onChange={(e) => setNewCommentUsername(e.target.value)}
                              />
                              <input 
                                type="text" 
                                className="form-input comment-text-input" 
                                placeholder="写下你的读书感悟或笔记..."
                                value={newCommentText}
                                onChange={(e) => setNewCommentText(e.target.value)}
                                required
                              />
                              <button type="submit" className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '13px' }}>
                                提交
                              </button>
                            </div>
                          </form>
                        </>
                      )}
                    </div>
                  ) : (
                    <div className="book-meta-grid">
                      <div className="book-meta-item">
                        <span className="meta-label">出版社</span>
                        <span className="meta-value">{activeBookDetail.publisher || '未知'}</span>
                      </div>
                      <div className="book-meta-item">
                        <span className="meta-label">年份</span>
                        <span className="meta-value">{activeBookDetail.year || '未知'}</span>
                      </div>
                      <div className="book-meta-item">
                        <span className="meta-label">页数</span>
                        <span className="meta-value">{activeBookDetail.pages || '未知'}</span>
                      </div>
                      <div className="book-meta-item">
                        <span className="meta-label">语言</span>
                        <span className="meta-value">{activeBookDetail.language || '未知'}</span>
                      </div>
                      <div className="book-meta-item" style={{ gridColumn: 'span 2' }}>
                        <span className="meta-label">ISBN 号码</span>
                        <span className="meta-value">{activeBookDetail.identifier || '未知'}</span>
                      </div>
                      <div className="book-meta-item" style={{ gridColumn: 'span 2' }}>
                        <span className="meta-label">图书分类</span>
                        <span className="meta-value">
                          {activeBookDetail.categories && activeBookDetail.categories.length > 0 
                            ? activeBookDetail.categories.map(c => typeof c === 'object' ? c.name : c).join(', ') 
                            : '未知'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Kindle Push Non-EPUB Warning Dialog */}
      {formatWarningBook && (
        <div className="warning-dialog-backdrop">
          <div className="warning-dialog">
            <div className="warning-dialog-header">
              <AlertTriangle style={{ width: '20px', height: '20px' }} />
              <span>Kindle 推送格式预警</span>
            </div>
            <div className="warning-dialog-body">
              亚马逊 Kindle 官方目前<strong>仅正式支持 EPUB 格式</strong>的邮箱推送，当前您选择的书籍格式为 <strong style={{ color: 'var(--accent-yellow)', textTransform: 'uppercase' }}>{(formatWarningBook.extension || '').toUpperCase()}</strong>。
              <br /><br />
              推送非 EPUB 文件可能导致 Kindle 邮箱服务拒收并发送报错退信，或者在您的电子书阅读器上显示排版失效、乱码。
              <br /><br />
              建议您选择<strong>“仅下载到本地”</strong>，随后通过 USB 数据线手动拷贝至 Kindle，或将其转换为 EPUB 格式后再进行推送。
            </div>
            <div className="warning-dialog-actions">
              <button className="btn btn-secondary" onClick={() => setFormatWarningBook(null)}>
                取消
              </button>
              <button className="btn btn-secondary" onClick={() => { handleDownloadOnly(formatWarningBook); setFormatWarningBook(null); }} style={{ color: 'var(--accent-blue)' }}>
                改为仅下载
              </button>
              <button className="btn btn-primary" onClick={() => { executePushBook(formatWarningBook); setFormatWarningBook(null); }} style={{ backgroundColor: 'var(--accent-yellow)', border: 'none' }}>
                坚持推送
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Login Modal Overlay */}
      {showLoginModal && (
        <div className="modal-backdrop" onClick={() => setShowLoginModal(false)}>
          <div className="login-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title-text">登录 Z-Library</span>
              <button className="modal-close-btn" onClick={() => setShowLoginModal(false)}>
                <X style={{ width: '18px', height: '18px' }} />
              </button>
            </div>

            <div className="guide-tabs" style={{ marginBottom: '16px', justifyContent: 'center' }}>
              <div className={`guide-tab ${loginMethod === 'credentials' ? 'active' : ''}`} onClick={() => setLoginMethod('credentials')}>账号密码登录</div>
              <div className={`guide-tab ${loginMethod === 'token' ? 'active' : ''}`} onClick={() => setLoginMethod('token')}>Cookie 凭证登录</div>
            </div>

            <form onSubmit={handleZlibLogin} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {loginMethod === 'credentials' ? (
                <>
                  <input
                    type="email"
                    className="form-input"
                    placeholder="Z-Library 注册邮箱"
                    value={zlibEmail}
                    onChange={(e) => setZlibEmail(e.target.value.trim())}
                  />
                  <div className="input-with-button">
                    <input
                      type={showZlibPassword ? 'text' : 'password'}
                      className="form-input"
                      placeholder="密码"
                      value={zlibPassword}
                      onChange={(e) => setZlibPassword(e.target.value.trim())}
                    />
                    <button type="button" className="btn btn-secondary" style={{ padding: '8px' }} onClick={() => setShowZlibPassword(!showZlibPassword)}>
                      {showZlibPassword ? <EyeOff style={{ width: '14px', height: '14px' }} /> : <Eye style={{ width: '14px', height: '14px' }} />}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="remix_userid (Cookie 字段)"
                    value={zlibTokenUserid}
                    onChange={(e) => setZlibTokenUserid(e.target.value.trim())}
                  />
                  <input
                    type="text"
                    className="form-input"
                    placeholder="remix_userkey (Cookie 字段)"
                    value={zlibTokenUserkey}
                    onChange={(e) => setZlibTokenUserkey(e.target.value.trim())}
                  />
                </>
              )}

              {loginError && (
                <div style={{ color: 'var(--accent-red)', fontSize: '12px', textAlign: 'center', padding: '8px', background: 'rgba(239,68,68,0.06)', borderRadius: '6px' }}>
                  {loginError}
                </div>
              )}

              <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '4px' }} disabled={loginSubmitting}>
                {loginSubmitting ? <Spinner /> : null}
                {loginSubmitting ? '正在登录...' : '立即登录'}
              </button>
            </form>

            <p style={{ marginTop: '14px', fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center' }}>
              登录后可获取个人推荐、搜索书籍、一键推送至 Kindle。
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
