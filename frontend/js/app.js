// Wattpad AI Audiobook Frontend Application

// State quản lý toàn bộ ứng dụng
const state = {
  engines: [],
  vieneuVoices: [],
  vieneuCues: [],
  edgeVoices: [],
  edgeEmotions: {},
  voices: [],
  emotions: {},
  currentStory: null,
  selectedChapterIds: new Set(),
  activeTaskId: null,
  taskPollInterval: null,
  taskStatus: 'idle', // 'idle' | 'processing' | 'paused' | 'completed' | 'failed' | 'cancelled'
  
  // Voice configuration
  voiceConfig: {
    engine: "vieneu",
    voice: "Thái Sơn",
    emotion_cue: "",
    emotion: "neutral",
    pitch: "+0Hz",
    rate: "+0%",
    volume: "+0%"
  },

  // Cấu hình dịch thuật văn học AI
  translationConfig: {
    enabled: true,
    source_language: "auto",
    target_language: "vi",
    prompt_version: "literary_vi_v1"
  },

  // Audio Player State
  currentPlayingChapterId: null,
  isPlaying: false,
  playbackRates: [1.0, 1.25, 1.5, 1.75, 2.0],
  currentRateIndex: 0,
  
  // PWA Install prompt
  deferredPrompt: null,

  // Phiên bản 1.8: Device ID, Auth & User Data
  deviceId: null,
  currentUser: null,
  authToken: localStorage.getItem('wattpad_auth_token') || null,
  activeLibraryTab: 'stories', // 'stories' | 'audiobooks' | 'read' | 'listen'
  libraryData: {
    stories: [],
    audiobooks: [],
    read_history: [],
    listen_history: []
  },

  // Reader & Favorites
  chapterFilter: 'all', // 'all' | 'favorites' | 'unconverted'
  lastClosedReaderInfo: null,
  activeReaderWindow: null,
  readerCheckInterval: null
};

// DOM Elements
const elements = {
  formFetchStory: document.getElementById('form-fetch-story'),
  inputStoryUrl: document.getElementById('input-story-url'),
  btnClearInput: document.getElementById('btn-clear-input'),
  btnSubmitFetch: document.getElementById('btn-submit-fetch'),
  btnDemoStory: document.getElementById('btn-demo-story'),
  btnEmptyDemo: document.getElementById('btn-empty-demo'),
  btnInstallPwa: document.getElementById('btn-install-pwa'),

  // Phiên bản 1.8: Auth & Profile Elements
  profileCapsuleBtn: document.getElementById('profile-capsule-btn'),
  sidebarUserAvatar: document.getElementById('sidebar-user-avatar'),
  sidebarUserName: document.getElementById('sidebar-user-name'),
  sidebarUserRole: document.getElementById('sidebar-user-role'),
  btnSidebarAuthAction: document.getElementById('btn-sidebar-auth-action'),
  iconSidebarAuth: document.getElementById('icon-sidebar-auth'),
  btnAndroidUserModal: document.getElementById('btn-android-user-modal'),
  androidUserStatusText: document.getElementById('android-user-status-text'),

  // Modal Login
  modalLogin: document.getElementById('modal-login'),
  btnCloseLoginModal: document.getElementById('btn-close-login-modal'),
  formLogin: document.getElementById('form-login'),
  loginUsername: document.getElementById('login-username'),
  loginPassword: document.getElementById('login-password'),
  loginRemember: document.getElementById('login-remember'),
  loginErrorMsg: document.getElementById('login-error-msg'),
  loginErrorText: document.getElementById('login-error-text'),
  btnQuickFillLogin: document.getElementById('btn-quick-fill-login'),
  btnSubmitLogin: document.getElementById('btn-submit-login'),

  // Phiên bản 1.8: User Library & History (4 Tabs)
  btnOpenFavorites: document.getElementById('btn-open-favorites'),
  badgeFavCount: document.getElementById('badge-fav-count'),
  btnToggleFavStory: document.getElementById('btn-toggle-fav-story'),
  iconFavStory: document.getElementById('icon-fav-story'),
  labelFavStory: document.getElementById('label-fav-story'),
  chapterFiltersGroup: document.getElementById('chapter-filters-group'),
  filterCountAll: document.getElementById('filter-count-all'),
  filterCountFav: document.getElementById('filter-count-fav'),
  filterCountUnconv: document.getElementById('filter-count-unconv'),

  modalFavorites: document.getElementById('modal-favorites'),
  btnCloseFavoritesModal: document.getElementById('btn-close-favorites-modal'),
  tabFavStories: document.getElementById('tab-fav-stories'),
  tabLibAudiobooks: document.getElementById('tab-lib-audiobooks'),
  tabLibReadHistory: document.getElementById('tab-lib-read-history'),
  tabLibListenHistory: document.getElementById('tab-lib-listen-history'),
  badgeFavStoriesCount: document.getElementById('badge-fav-stories-count'),
  badgeLibAudiobooksCount: document.getElementById('badge-lib-audiobooks-count'),
  badgeLibReadCount: document.getElementById('badge-lib-read-count'),
  badgeLibListenCount: document.getElementById('badge-lib-listen-count'),
  containerFavStories: document.getElementById('container-fav-stories'),
  containerLibAudiobooks: document.getElementById('container-lib-audiobooks'),
  containerLibReadHistory: document.getElementById('container-lib-read-history'),
  containerLibListenHistory: document.getElementById('container-lib-listen-history'),

  // Modal Audio Prompt
  modalAudioPrompt: document.getElementById('modal-audio-prompt'),
  promptChapterTitle: document.getElementById('prompt-chapter-title'),
  btnPromptConvertThis: document.getElementById('btn-prompt-convert-this'),
  btnPromptConvertAll: document.getElementById('btn-prompt-convert-all'),
  btnPromptDismiss: document.getElementById('btn-prompt-dismiss'),
  
  // Custom Story Modal
  btnOpenCustomModal: document.getElementById('btn-open-custom-modal'),
  modalCustomStory: document.getElementById('modal-custom-story'),
  btnCloseCustomModal: document.getElementById('btn-close-custom-modal'),
  btnCancelCustom: document.getElementById('btn-cancel-custom'),
  formCustomStory: document.getElementById('form-custom-story'),


  // Sections
  emptyState: document.getElementById('empty-state'),
  storyContentSection: document.getElementById('story-content-section'),
  conversionProgressBanner: document.getElementById('conversion-progress-banner'),
  
  // Progress Banner & Task Controls
  taskStatusText: document.getElementById('task-status-text'),
  taskOverallProgress: document.getElementById('task-overall-progress'),
  taskProgressBar: document.getElementById('task-progress-bar'),
  taskChapterDetail: document.getElementById('task-chapter-detail'),
  taskPulseDot: document.getElementById('task-pulse-dot'),
  btnPauseResumeTask: document.getElementById('btn-pause-resume-task'),
  iconTaskPause: document.getElementById('icon-task-pause'),
  iconTaskResume: document.getElementById('icon-task-resume'),
  labelTaskPauseResume: document.getElementById('label-task-pause-resume'),
  btnCancelTask: document.getElementById('btn-cancel-task'),

  // Story Info
  storyCover: document.getElementById('story-cover'),
  storyTitle: document.getElementById('story-title'),
  storyAuthor: document.getElementById('story-author'),
  storyChapterCount: document.getElementById('story-chapter-count'),
  storyConvertedCount: document.getElementById('story-converted-count'),
  storyDescription: document.getElementById('story-description'),
  badgeStoryLang: document.getElementById('badge-story-lang'),

  // Translation UI Elements
  sectionTranslationControls: document.getElementById('section-translation-controls'),
  checkboxEnableTranslation: document.getElementById('checkbox-enable-translation'),
  badgePromptVersion: document.getElementById('badge-prompt-version'),
  translationDescText: document.getElementById('translation-desc-text'),
  translationStatusHint: document.getElementById('translation-status-hint'),
  btnOpenPreviewTranslation: document.getElementById('btn-open-preview-translation'),
  modalTranslationPreview: document.getElementById('modal-translation-preview'),
  btnCloseTranslationModal: document.getElementById('btn-close-translation-modal'),
  previewSourceText: document.getElementById('preview-source-text'),
  previewTranslatedBox: document.getElementById('preview-translated-box'),
  previewCachedTag: document.getElementById('preview-cached-tag'),
  previewLatencyText: document.getElementById('preview-latency-text'),
  btnSubmitPreviewTranslate: document.getElementById('btn-submit-preview-translate'),

  // Voice Studio (Engine Switcher, VieNeu & Edge-TTS)
  btnEngineVieneu: document.getElementById('btn-engine-vieneu'),
  btnEngineEdge: document.getElementById('btn-engine-edge'),
  badgeEngineTag: document.getElementById('badge-engine-tag'),
  labelVoiceDetails: document.getElementById('label-voice-details'),
  sectionVieneuCues: document.getElementById('section-vieneu-cues'),
  vieneuCuesGrid: document.getElementById('vieneu-cues-grid'),
  currentCueLabel: document.getElementById('current-cue-label'),
  sectionEdgeControls: document.getElementById('section-edge-controls'),
  selectVoice: document.getElementById('select-voice'),
  currentEmotionLabel: document.getElementById('current-emotion-label'),
  emotionPresetsGrid: document.getElementById('emotion-presets-grid'),
  sliderPitch: document.getElementById('slider-pitch'),
  pitchValueBadge: document.getElementById('pitch-value-badge'),
  sliderRate: document.getElementById('slider-rate'),
  rateValueBadge: document.getElementById('rate-value-badge'),
  btnPreviewSample: document.getElementById('btn-preview-sample'),
  previewSampleText: document.getElementById('preview-sample-text'),
  sampleAudioPlayer: document.getElementById('sample-audio-player'),

  // Chapter List
  checkboxSelectAll: document.getElementById('checkbox-select-all'),
  btnDownloadAllZip: document.getElementById('btn-download-all-zip'),
  btnStartConvert: document.getElementById('btn-start-convert'),
  convertBtnLabel: document.getElementById('convert-btn-label'),
  chapterListContainer: document.getElementById('chapter-list-container'),

  // Audiobook Player Bar
  audiobookPlayer: document.getElementById('audiobook-player'),
  mainAudio: document.getElementById('main-audio'),
  playerMiniCover: document.getElementById('player-mini-cover'),
  playerChapterTitle: document.getElementById('player-chapter-title'),
  playerStoryTitle: document.getElementById('player-story-title'),
  playerEqualizer: document.getElementById('player-equalizer'),
  btnPlayerPlayPause: document.getElementById('btn-player-play-pause'),
  playerPlayIconSlot: document.getElementById('player-play-icon-slot'),
  iconPlayerPlay: document.getElementById('icon-player-play'),
  iconPlayerPause: document.getElementById('icon-player-pause'),
  btnPlayerRewind: document.getElementById('btn-player-rewind'),
  btnPlayerForward: document.getElementById('btn-player-forward'),
  btnPlayerPrev: document.getElementById('btn-player-prev'),
  btnPlayerNext: document.getElementById('btn-player-next'),
  playerProgressContainer: document.getElementById('player-progress-container'),
  playerProgressBar: document.getElementById('player-progress-bar'),
  playerCurrentTime: document.getElementById('player-current-time'),
  playerTotalTime: document.getElementById('player-total-time'),
  btnPlaybackRate: document.getElementById('btn-playback-rate'),
  btnPlayerDownload: document.getElementById('btn-player-download')
};

// ------------------- KHỞI TẠO ỨNG DỤNG (PHIÊN BẢN 1.8) -------------------

document.addEventListener('DOMContentLoaded', async () => {
  if (window.lucide) lucide.createIcons();

  // 1. Khởi tạo mã định danh thiết bị đầu cuối duy nhất
  initDeviceId();

  // 2. Đăng ký Service Worker cho PWA
  registerServiceWorker();

  // 3. Bắt sự kiện cài đặt app Android
  setupPwaInstall();

  // 4. Khởi tạo BroadcastChannel và đồng bộ giữa các cửa sổ
  initBroadcastChannel();

  // 5. Khởi tạo xác thực người dùng (tự động nhận diện tài khoản jason)
  await initAuth();

  // 6. Tải dữ liệu thư viện truyện, sách nói và lịch sử theo người dùng
  await loadUserLibrary();

  // 7. Tải danh sách giọng đọc và preset biểu cảm AI
  await loadVoicesAndEmotions();

  // 8. Gắn các trình lắng nghe sự kiện UI
  setupEventListeners();

  // 9. Kiểm tra phiên chuyển đổi đang dang dở từ thiết bị này để tiếp tục tự động
  await checkActiveDeviceTask();
});


// Đăng ký Service Worker
function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then(() => console.log('Service Worker đã kích hoạt thành công'))
      .catch((err) => console.warn('Lỗi Service Worker:', err));
  }
}

// Bắt sự kiện cài đặt PWA trên Android
function setupPwaInstall() {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    state.deferredPrompt = e;
    elements.btnInstallPwa.classList.remove('hidden');
    elements.btnInstallPwa.classList.add('inline-flex');
  });

  elements.btnInstallPwa.addEventListener('click', async () => {
    if (!state.deferredPrompt) return;
    state.deferredPrompt.prompt();
    const { outcome } = await state.deferredPrompt.userChoice;
    console.log(`PWA install outcome: ${outcome}`);
    state.deferredPrompt = null;
    elements.btnInstallPwa.classList.add('hidden');
  });
}

// ------------------- TẢI DỮ LIỆU BAN ĐẦU -------------------

async function loadVoicesAndEmotions() {
  try {
    const res = await fetch('/api/voices');
    if (!res.ok) throw new Error('Không thể tải danh sách giọng đọc');
    const data = await res.json();
    state.engines = data.engines || [];
    state.vieneuVoices = data.vieneu_voices || [];
    state.vieneuCues = data.vieneu_cues || [];
    state.edgeVoices = data.edge_voices || [];
    state.edgeEmotions = data.edge_emotions || {};
    state.voices = data.voices || data.edge_voices || [];
    state.emotions = data.emotions || data.edge_emotions || {};

    // Khởi tạo giao diện theo engine mặc định (VieNeu-TTS)
    switchEngine(state.voiceConfig.engine);
    renderVieneuCues();
    renderEmotionButtons();
  } catch (err) {
    console.error('Lỗi load voices:', err);
  }
}

function switchEngine(engine) {
  state.voiceConfig.engine = engine;

  if (engine === 'vieneu') {
    // Cập nhật tab active
    elements.btnEngineVieneu.className = 'py-2 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5 bg-rose-600 text-white shadow-sm';
    elements.btnEngineEdge.className = 'py-2 px-3 rounded-xl text-xs font-semibold transition flex items-center justify-center space-x-1.5 text-slate-600 hover:text-slate-900 bg-transparent';

    // Tag badge & voice count
    elements.badgeEngineTag.textContent = '48kHz AI Neural';
    elements.badgeEngineTag.className = 'text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-300 font-bold';
    elements.labelVoiceDetails.textContent = `${state.vieneuVoices.length} giọng đọc`;

    // Hiển thị phần VieNeu, ẩn phần Edge controls
    elements.sectionVieneuCues.classList.remove('hidden');
    elements.sectionEdgeControls.classList.add('hidden');

    // Nếu giọng hiện tại không nằm trong VieNeu, chọn Thái Sơn
    const exists = state.vieneuVoices.some(v => v.id === state.voiceConfig.voice);
    if (!exists) {
      state.voiceConfig.voice = (state.vieneuVoices.length > 0) ? state.vieneuVoices[0].id : 'Thái Sơn';
    }
  } else {
    // Edge-TTS
    elements.btnEngineEdge.className = 'py-2 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5 bg-rose-600 text-white shadow-sm';
    elements.btnEngineVieneu.className = 'py-2 px-3 rounded-xl text-xs font-semibold transition flex items-center justify-center space-x-1.5 text-slate-600 hover:text-slate-900 bg-transparent';

    elements.badgeEngineTag.textContent = '24kHz Cloud Edge';
    elements.badgeEngineTag.className = 'text-[11px] px-2.5 py-0.5 rounded-full bg-cyan-50 text-cyan-800 border border-cyan-300 font-bold';
    elements.labelVoiceDetails.textContent = `${state.edgeVoices.length} giọng đọc`;

    // Ẩn VieNeu, hiển thị Edge controls
    elements.sectionVieneuCues.classList.add('hidden');
    elements.sectionEdgeControls.classList.remove('hidden');

    // Nếu giọng hiện tại không nằm trong Edge, chọn Hoài My
    const exists = state.edgeVoices.some(v => v.id === state.voiceConfig.voice);
    if (!exists) {
      state.voiceConfig.voice = (state.edgeVoices.length > 0) ? state.edgeVoices[0].id : 'vi-VN-HoaiMyNeural';
    }
  }

  renderVoiceOptions();
  if (window.lucide) lucide.createIcons();
}

function renderVoiceOptions() {
  elements.selectVoice.innerHTML = '';

  if (state.voiceConfig.engine === 'vieneu') {
    // Gom nhóm theo phong cách giọng đọc
    const groups = {};
    state.vieneuVoices.forEach(v => {
      const styleName = v.style || 'Khác';
      if (!groups[styleName]) groups[styleName] = [];
      groups[styleName].push(v);
    });

    Object.entries(groups).forEach(([groupName, voices]) => {
      const optgroup = document.createElement('optgroup');
      optgroup.label = `--- Phong cách: ${groupName} ---`;
      voices.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = `${v.name} (${v.accent}) - ${v.desc}`;
        optgroup.appendChild(opt);
      });
      elements.selectVoice.appendChild(optgroup);
    });
  } else {
    // Edge-TTS
    state.edgeVoices.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.textContent = `${v.name} - ${v.desc}`;
      elements.selectVoice.appendChild(opt);
    });
  }

  elements.selectVoice.value = state.voiceConfig.voice;
}

function renderVieneuCues() {
  if (!elements.vieneuCuesGrid) return;
  elements.vieneuCuesGrid.innerHTML = '';

  state.vieneuCues.forEach(cue => {
    const btn = document.createElement('button');
    btn.type = 'button';
    const isSelected = (state.voiceConfig.emotion_cue || '') === cue.tag;
    btn.className = `p-2.5 rounded-2xl text-left transition flex flex-col justify-between ${
      isSelected
        ? 'liquid-tile-active'
        : 'liquid-tile'
    }`;

    btn.innerHTML = `
      <div class="flex items-center justify-between mb-1">
        <span class="font-bold text-xs text-slate-900">${cue.label}</span>
        ${cue.tag ? `<code class="text-[10px] text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded-md border border-rose-200 font-mono font-bold">${cue.tag}</code>` : ''}
      </div>
      <span class="text-[10.5px] text-slate-600 font-medium line-clamp-1">${cue.desc}</span>
    `;

    btn.addEventListener('click', () => {
      state.voiceConfig.emotion_cue = cue.tag;
      elements.currentCueLabel.textContent = cue.label;
      renderVieneuCues();
    });

    elements.vieneuCuesGrid.appendChild(btn);
  });
}

function renderEmotionButtons() {
  if (!elements.emotionPresetsGrid) return;
  elements.emotionPresetsGrid.innerHTML = '';
  const entries = Object.entries(state.edgeEmotions);

  entries.forEach(([key, emo]) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    const isSelected = key === state.voiceConfig.emotion;
    btn.className = `p-2.5 rounded-2xl text-left transition flex flex-col justify-between ${
      isSelected 
        ? 'liquid-tile-active' 
        : 'liquid-tile'
    }`;
    btn.dataset.emotionKey = key;

    btn.innerHTML = `
      <div class="flex items-center space-x-1.5 mb-1">
        <i data-lucide="${emo.icon || 'sparkles'}" class="w-3.5 h-3.5 ${isSelected ? 'text-rose-600' : 'text-slate-500'}"></i>
        <span class="font-bold text-xs text-slate-900 truncate">${emo.label.split(' ')[0]}</span>
      </div>
      <span class="text-[10.5px] text-slate-600 font-medium line-clamp-1">${emo.desc}</span>
    `;

    btn.addEventListener('click', () => selectEmotion(key));
    elements.emotionPresetsGrid.appendChild(btn);
  });

  if (window.lucide) lucide.createIcons();
}

function selectEmotion(key) {
  const emo = state.edgeEmotions[key];
  if (!emo) return;

  state.voiceConfig.emotion = key;
  state.voiceConfig.pitch = emo.pitch;
  state.voiceConfig.rate = emo.rate;
  state.voiceConfig.volume = emo.volume || "+0%";

  elements.currentEmotionLabel.textContent = emo.label;

  // Cập nhật giá trị thanh slider
  const pitchVal = parseInt(emo.pitch.replace('Hz', '').replace('+', '')) || 0;
  elements.sliderPitch.value = pitchVal;
  updatePitchBadge(pitchVal);

  const rateVal = parseInt(emo.rate.replace('%', '').replace('+', '')) || 0;
  elements.sliderRate.value = rateVal;
  updateRateBadge(rateVal);

  // Cập nhật trạng thái active của các nút biểu cảm
  renderEmotionButtons();
}

function updatePitchBadge(val) {
  const sign = val > 0 ? `+${val}` : `${val}`;
  let desc = 'Tiêu chuẩn';
  if (val < -5) desc = 'Trầm ấm';
  if (val > 5) desc = 'Trong trẻo / Cao';
  elements.pitchValueBadge.textContent = `${sign}Hz (${desc})`;
  state.voiceConfig.pitch = `${sign}Hz`;
}

function updateRateBadge(val) {
  const factor = (1 + val / 100).toFixed(2);
  let desc = 'Chuẩn';
  if (val < -10) desc = 'Chậm';
  if (val > 10) desc = 'Nhanh';
  elements.rateValueBadge.textContent = `${factor}x (${desc})`;
  const sign = val >= 0 ? `+${val}` : `${val}`;
  state.voiceConfig.rate = `${sign}%`;
}

// ------------------- XỬ LÝ SỰ KIỆN GIAO DIỆN -------------------

function setupEventListeners() {
  // Input Story URL
  elements.inputStoryUrl.addEventListener('input', (e) => {
    if (e.target.value.trim().length > 0) {
      elements.btnClearInput.classList.remove('hidden');
    } else {
      elements.btnClearInput.classList.add('hidden');
    }
  });

  elements.btnClearInput.addEventListener('click', () => {
    elements.inputStoryUrl.value = '';
    elements.btnClearInput.classList.add('hidden');
    elements.inputStoryUrl.focus();
  });

  // Tải truyện từ Wattpad URL
  elements.formFetchStory.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = elements.inputStoryUrl.value.trim();
    if (url) await fetchStory(url);
  });

  // Nút Thử truyện mẫu
  const demoUrl = 'https://www.wattpad.com/story/151007312-transfic-ongniel-drabble-collar-full';
  elements.btnDemoStory.addEventListener('click', () => {
    elements.inputStoryUrl.value = demoUrl;
    elements.btnClearInput.classList.remove('hidden');
    fetchStory(demoUrl);
  });
  elements.btnEmptyDemo.addEventListener('click', () => {
    elements.inputStoryUrl.value = demoUrl;
    elements.btnClearInput.classList.remove('hidden');
    fetchStory(demoUrl);
  });

  // Custom Story Modal Events
  elements.btnOpenCustomModal.addEventListener('click', () => {
    elements.modalCustomStory.classList.remove('hidden');
  });
  elements.btnCloseCustomModal.addEventListener('click', () => {
    elements.modalCustomStory.classList.add('hidden');
  });
  elements.btnCancelCustom.addEventListener('click', () => {
    elements.modalCustomStory.classList.add('hidden');
  });
  elements.formCustomStory.addEventListener('submit', async (e) => {
    e.preventDefault();
    await createCustomStory();
  });

  // Voice Studio Inputs & Engine Switcher
  if (elements.btnEngineVieneu) {
    elements.btnEngineVieneu.addEventListener('click', () => switchEngine('vieneu'));
  }
  if (elements.btnEngineEdge) {
    elements.btnEngineEdge.addEventListener('click', () => switchEngine('edge-tts'));
  }

  elements.selectVoice.addEventListener('change', (e) => {
    state.voiceConfig.voice = e.target.value;
  });

  elements.sliderPitch.addEventListener('input', (e) => {
    updatePitchBadge(parseInt(e.target.value));
  });

  elements.sliderRate.addEventListener('input', (e) => {
    updateRateBadge(parseInt(e.target.value));
  });

  // Nghe thử giọng đọc mẫu
  elements.btnPreviewSample.addEventListener('click', previewVoiceSample);

  // Điều khiển tác vụ chuyển đổi (Tạm dừng, Tiếp tục, Hủy)
  if (elements.btnPauseResumeTask) {
    elements.btnPauseResumeTask.addEventListener('click', handlePauseResumeTask);
  }
  if (elements.btnCancelTask) {
    elements.btnCancelTask.addEventListener('click', handleCancelTask);
  }

  // Bộ chọn chương
  elements.checkboxSelectAll.addEventListener('change', (e) => {
    toggleSelectAll(e.target.checked);
  });

  elements.btnStartConvert.addEventListener('click', startBatchConversion);

  elements.btnDownloadAllZip.addEventListener('click', (e) => {
    e.preventDefault();
    if (!state.currentStory) return;
    const url = `/api/audio/${state.currentStory.id}/download-all`;
    downloadFile(url, `${state.currentStory.title} - Sách nói AI.zip`);
  });

  // Player Controls
  setupPlayerControls();

  // Phiên bản 1.5: Yêu thích truyện
  if (elements.btnToggleFavStory) {
    elements.btnToggleFavStory.addEventListener('click', () => {
      if (state.currentStory) {
        toggleFavoriteStory(state.currentStory);
      }
    });
  }

  // Mở & Đóng Modal Yêu thích
  if (elements.btnOpenFavorites) {
    elements.btnOpenFavorites.addEventListener('click', openFavoritesModal);
  }
  if (elements.btnCloseFavoritesModal) {
    elements.btnCloseFavoritesModal.addEventListener('click', closeFavoritesModal);
  }
  if (elements.modalFavorites) {
    elements.modalFavorites.addEventListener('click', (e) => {
      if (e.target === elements.modalFavorites) closeFavoritesModal();
    });
  }

  // Tab chuyển đổi trong Modal Tủ sách & Lịch sử cá nhân (4 Tabs)
  if (elements.tabFavStories) {
    elements.tabFavStories.addEventListener('click', () => switchFavoritesTab('stories'));
  }
  if (elements.tabLibAudiobooks) {
    elements.tabLibAudiobooks.addEventListener('click', () => switchFavoritesTab('audiobooks'));
  }
  if (elements.tabLibReadHistory) {
    elements.tabLibReadHistory.addEventListener('click', () => switchFavoritesTab('read'));
  }
  if (elements.tabLibListenHistory) {
    elements.tabLibListenHistory.addEventListener('click', () => switchFavoritesTab('listen'));
  }

  const btnViewAllHistory = document.getElementById('btn-view-all-history');
  if (btnViewAllHistory) {
    btnViewAllHistory.addEventListener('click', () => {
      openFavoritesModal();
      switchFavoritesTab('listen');
    });
  }

  // Phiên bản 1.8: Sự kiện Modal Đăng nhập & Profile thành viên
  if (elements.btnSidebarAuthAction) {
    elements.btnSidebarAuthAction.addEventListener('click', handleSidebarAuthAction);
  }
  if (elements.profileCapsuleBtn) {
    elements.profileCapsuleBtn.addEventListener('click', () => {
      if (!state.currentUser) openLoginModal();
      else openFavoritesModal();
    });
  }
  if (elements.btnAndroidUserModal) {
    elements.btnAndroidUserModal.addEventListener('click', () => {
      if (!state.currentUser) openLoginModal();
      else openFavoritesModal();
    });
  }
  if (elements.btnCloseLoginModal) {
    elements.btnCloseLoginModal.addEventListener('click', closeLoginModal);
  }
  if (elements.modalLogin) {
    elements.modalLogin.addEventListener('click', (e) => {
      if (e.target === elements.modalLogin) closeLoginModal();
    });
  }
  if (elements.formLogin) {
    elements.formLogin.addEventListener('submit', handleLoginSubmit);
  }
  if (elements.btnQuickFillLogin) {
    elements.btnQuickFillLogin.addEventListener('click', () => {
      if (elements.loginUsername) elements.loginUsername.value = 'jason';
      if (elements.loginPassword) elements.loginPassword.value = '1987';
    });
  }

  // Phiên bản 2.0: Dịch thuật AI & Dịch thử trực tiếp
  if (elements.checkboxEnableTranslation) {
    elements.checkboxEnableTranslation.addEventListener('change', (e) => {
      state.translationConfig.enabled = e.target.checked;
    });
  }
  if (elements.btnOpenPreviewTranslation) {
    elements.btnOpenPreviewTranslation.addEventListener('click', openTranslationPreviewModal);
  }
  if (elements.btnCloseTranslationModal) {
    elements.btnCloseTranslationModal.addEventListener('click', closeTranslationPreviewModal);
  }
  if (elements.modalTranslationPreview) {
    elements.modalTranslationPreview.addEventListener('click', (e) => {
      if (e.target === elements.modalTranslationPreview) closeTranslationPreviewModal();
    });
  }
  if (elements.btnSubmitPreviewTranslate) {
    elements.btnSubmitPreviewTranslate.addEventListener('click', handlePreviewTranslation);
  }

  // Tự động kiểm tra và kết nối lại phiên chuyển đổi khi người dùng quay lại app từ màn hình Home Android
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      checkActiveDeviceTask();
    }
  });
  window.addEventListener('pageshow', () => checkActiveDeviceTask());
  window.addEventListener('focus', () => checkActiveDeviceTask());


  // Bộ lọc danh sách chương (Tất cả / Yêu thích / Chưa chuyển)
  if (elements.chapterFiltersGroup) {
    elements.chapterFiltersGroup.addEventListener('click', (e) => {
      const btn = e.target.closest('.chapter-filter-btn');
      if (!btn) return;
      const filter = btn.dataset.filter;
      if (filter && filter !== state.chapterFilter) {
        state.chapterFilter = filter;
        elements.chapterFiltersGroup.querySelectorAll('.chapter-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderChapterList();
      }
    });
  }

  // Modal nhắc nhở tạo Audio (Khi đóng cửa sổ đọc chi tiết)
  if (elements.btnPromptConvertThis) {
    elements.btnPromptConvertThis.addEventListener('click', () => {
      elements.modalAudioPrompt.classList.add('hidden');
      if (state.lastClosedReaderInfo && state.currentStory) {
        const cid = state.lastClosedReaderInfo.chapterId;
        state.selectedChapterIds.clear();
        state.selectedChapterIds.add(cid);
        renderChapterList();
        updateConvertButton();
        elements.btnStartConvert.scrollIntoView({ behavior: 'smooth', block: 'center' });
        elements.btnStartConvert.classList.add('animate-pulse');
        setTimeout(() => elements.btnStartConvert.classList.remove('animate-pulse'), 2500);
      }
    });
  }

  if (elements.btnPromptConvertAll) {
    elements.btnPromptConvertAll.addEventListener('click', () => {
      elements.modalAudioPrompt.classList.add('hidden');
      if (state.currentStory) {
        state.selectedChapterIds.clear();
        state.currentStory.parts.forEach(p => {
          if (!p.is_converted) state.selectedChapterIds.add(p.id);
        });
        renderChapterList();
        updateConvertButton();
        elements.btnStartConvert.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  }

  if (elements.btnPromptDismiss) {
    elements.btnPromptDismiss.addEventListener('click', () => {
      elements.modalAudioPrompt.classList.add('hidden');
    });
  }
  if (elements.modalAudioPrompt) {
    elements.modalAudioPrompt.addEventListener('click', (e) => {
      if (e.target === elements.modalAudioPrompt) elements.modalAudioPrompt.classList.add('hidden');
    });
  }
}

// Hàm hỗ trợ tải file an toàn trên cả Web và Android PWA / WebView
function downloadFile(url, fallbackFilename = '') {
  try {
    const a = document.createElement('a');
    a.href = url;
    if (fallbackFilename) {
      a.setAttribute('download', fallbackFilename);
    } else {
      a.setAttribute('download', '');
    }
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      if (document.body.contains(a)) {
        document.body.removeChild(a);
      }
    }, 500);
  } catch (err) {
    console.error('Lỗi khi kích hoạt tải file:', err);
    window.location.href = url;
  }
}

// ------------------- TẢI & HIỂN THỊ TRUYỆN -------------------

async function fetchStory(url) {
  setLoadingFetch(true);
  try {
    const res = await fetch('/api/story/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Không thể tải truyện từ Wattpad');
    }

    const story = await res.json();
    renderStory(story);
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  } finally {
    setLoadingFetch(false);
  }
}

async function createCustomStory() {
  const title = document.getElementById('custom-story-title').value.trim();
  const author = document.getElementById('custom-story-author').value.trim() || 'Tác giả ẩn danh';
  const chapTitle = document.getElementById('custom-chapter-title').value.trim();
  const chapContent = document.getElementById('custom-chapter-content').value.trim();

  if (!title || !chapTitle || !chapContent) {
    alert('Vui lòng điền đầy đủ tiêu đề và nội dung.');
    return;
  }

  try {
    const res = await fetch('/api/story/custom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        author,
        chapters: [{ title: chapTitle, content: chapContent }]
      })
    });

    if (!res.ok) throw new Error('Không thể tạo truyện tùy chỉnh');
    const story = await res.json();
    elements.modalCustomStory.classList.add('hidden');
    renderStory(story);
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
}

function setLoadingFetch(isLoading) {
  elements.btnSubmitFetch.disabled = isLoading;
  if (isLoading) {
    elements.btnSubmitFetch.innerHTML = `<div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div><span>Đang lấy...</span>`;
  } else {
    elements.btnSubmitFetch.innerHTML = `<i data-lucide="search" class="w-4 h-4"></i><span>Tải truyện</span>`;
    if (window.lucide) lucide.createIcons();
  }
}

function renderStory(story) {
  state.currentStory = story;
  state.selectedChapterIds.clear();

  // Hiện khu vực nội dung truyện, ẩn empty state
  elements.emptyState.classList.add('hidden');
  elements.storyContentSection.classList.remove('hidden');

  // Cập nhật thông tin truyện
  elements.storyCover.src = story.cover || 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80';
  elements.storyTitle.textContent = story.title;
  elements.storyAuthor.innerHTML = `<i data-lucide="user" class="w-3.5 h-3.5"></i><span>${story.author}</span>`;
  elements.storyDescription.textContent = story.description || 'Không có tóm tắt.';
  elements.storyChapterCount.innerHTML = `<i data-lucide="list" class="w-3.5 h-3.5 text-indigo-400"></i><span>${story.numParts} chương</span>`;

  // Cập nhật nhãn ngôn ngữ & trạng thái dịch tự động
  const detectedLang = (story.detected_language || story.language || 'vi').toLowerCase();
  if (elements.badgeStoryLang) {
    if (detectedLang === 'vi' || detectedLang === 'vietnamese') {
      elements.badgeStoryLang.textContent = '🇻🇳 Tiếng Việt';
      elements.badgeStoryLang.className = 'inline-block px-2.5 py-0.5 rounded-full text-[10.5px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80 mb-1.5 ml-1';
      if (elements.translationStatusHint) {
        elements.translationStatusHint.innerHTML = `<i data-lucide="check-check" class="w-3 h-3 text-emerald-600"></i> Truyện gốc là Tiếng Việt (Không cần dịch)`;
      }
      if (elements.checkboxEnableTranslation) {
        elements.checkboxEnableTranslation.checked = false;
        state.translationConfig.enabled = false;
      }
    } else if (detectedLang === 'en' || detectedLang === 'english') {
      elements.badgeStoryLang.textContent = '🇺🇸 English';
      elements.badgeStoryLang.className = 'inline-block px-2.5 py-0.5 rounded-full text-[10.5px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/80 mb-1.5 ml-1';
      if (elements.translationStatusHint) {
        elements.translationStatusHint.innerHTML = `<i data-lucide="sparkles" class="w-3 h-3 text-indigo-600"></i> Tự động dịch sang Tiếng Việt chuẩn văn học`;
      }
      if (elements.checkboxEnableTranslation) {
        elements.checkboxEnableTranslation.checked = true;
        state.translationConfig.enabled = true;
      }
    } else {
      elements.badgeStoryLang.textContent = `🌐 ${detectedLang.toUpperCase()}`;
      elements.badgeStoryLang.className = 'inline-block px-2.5 py-0.5 rounded-full text-[10.5px] font-semibold bg-amber-50 text-amber-700 border border-amber-200/80 mb-1.5 ml-1';
    }
  }

  // Cập nhật trạng thái nút Yêu thích truyện
  updateStoryFavButton();

  // Mặc định chọn tất cả các chương chưa chuyển đổi
  story.parts.forEach(p => {
    if (!p.is_converted) {
      state.selectedChapterIds.add(p.id);
    }
  });

  renderChapterList();
  updateStoryStats();

  if (window.lucide) lucide.createIcons();
}

function updateStoryStats() {
  if (!state.currentStory) return;
  const converted = state.currentStory.parts.filter(p => p.is_converted).length;
  elements.storyConvertedCount.innerHTML = `<i data-lucide="check-circle" class="w-3.5 h-3.5"></i><span>${converted} đã chuyển</span>`;

  if (converted > 0) {
    elements.btnDownloadAllZip.classList.remove('hidden');
    elements.btnDownloadAllZip.classList.add('inline-flex');
  } else {
    elements.btnDownloadAllZip.classList.add('hidden');
  }

  updateConvertButton();
}

// ------------------- QUẢN LÝ CHƯƠNG YÊU THÍCH -------------------

function getFavoriteChapters() {
  try {
    return JSON.parse(localStorage.getItem('wattpad_favorite_chapters') || '[]');
  } catch (e) {
    return [];
  }
}

function isChapterFavorite(storyId, chapterId) {
  if (!storyId || !chapterId) return false;
  const favs = getFavoriteChapters();
  return favs.some(f => f.storyId === storyId && String(f.chapterId) === String(chapterId));
}

function toggleFavoriteChapter(storyId, part) {
  if (!storyId || !part) return;
  let favs = getFavoriteChapters();
  const existsIndex = favs.findIndex(f => f.storyId === storyId && String(f.chapterId) === String(part.id));

  if (existsIndex >= 0) {
    favs.splice(existsIndex, 1);
  } else {
    favs.unshift({
      storyId: storyId,
      storyTitle: state.currentStory?.title || 'Wattpad Story',
      chapterId: part.id,
      chapterTitle: part.title || `Chương ${part.id}`,
      addedAt: Date.now()
    });
  }

  localStorage.setItem('wattpad_favorite_chapters', JSON.stringify(favs));
  renderChapterList();

  // Báo qua BroadcastChannel để cửa sổ đọc (reader window) cập nhật nếu đang mở
  if (appBroadcast) {
    try {
      appBroadcast.postMessage({
        type: 'FAVORITES_UPDATED',
        storyId: storyId,
        chapterId: part.id
      });
    } catch (e) {}
  }
}

function renderChapterList() {
  if (!state.currentStory) return;

  const allParts = state.currentStory.parts || [];
  const favCount = allParts.filter(p => isChapterFavorite(state.currentStory.id, p.id)).length;
  const unconvCount = allParts.filter(p => !p.is_converted).length;

  if (elements.filterCountAll) elements.filterCountAll.textContent = allParts.length;
  if (elements.filterCountFav) elements.filterCountFav.textContent = favCount;
  if (elements.filterCountUnconv) elements.filterCountUnconv.textContent = unconvCount;

  let displayParts = allParts;
  if (state.chapterFilter === 'favorites') {
    displayParts = allParts.filter(p => isChapterFavorite(state.currentStory.id, p.id));
  } else if (state.chapterFilter === 'unconverted') {
    displayParts = allParts.filter(p => !p.is_converted);
  }

  elements.chapterListContainer.innerHTML = '';

  if (displayParts.length === 0) {
    elements.chapterListContainer.innerHTML = `
      <div class="py-12 text-center text-slate-400 glass-card rounded-2xl p-6 space-y-2">
        <i data-lucide="${state.chapterFilter === 'favorites' ? 'bookmark' : 'check-circle'}" class="w-8 h-8 mx-auto text-slate-500"></i>
        <p class="text-xs sm:text-sm font-medium text-slate-300">
          ${state.chapterFilter === 'favorites' 
            ? 'Chưa có chương nào được đánh dấu yêu thích trong truyện này.' 
            : 'Tất cả các chương đã được tạo bản audio thành công!'}
        </p>
        <p class="text-[11px] text-slate-400">
          ${state.chapterFilter === 'favorites' ? 'Bấm biểu tượng trái tim ở góc mỗi chương để đánh dấu yêu thích.' : ''}
        </p>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  displayParts.forEach((part) => {
    const originalIndex = allParts.findIndex(p => p.id === part.id);
    const indexNumber = originalIndex >= 0 ? originalIndex + 1 : part.id;
    const isSelected = state.selectedChapterIds.has(part.id);
    const isPlaying = state.currentPlayingChapterId === part.id;
    const isFav = isChapterFavorite(state.currentStory.id, part.id);

    const item = document.createElement('div');
    item.className = `p-3 sm:p-3.5 rounded-xl transition flex items-center justify-between gap-3 ${
      isPlaying 
        ? 'liquid-tile-active ring-2 ring-rose-500 shadow-md shadow-rose-500/15' 
        : part.is_converted 
          ? 'chapter-row-item border-slate-200 hover:border-slate-300' 
          : 'chapter-row-item border-slate-200 hover:border-slate-300'
    }`;

    item.innerHTML = `
      <div class="flex items-center space-x-3 min-w-0 flex-1">
        <!-- Checkbox chọn chuyển đổi -->
        <input 
          type="checkbox" 
          class="chapter-checkbox w-4 h-4 rounded text-rose-600 focus:ring-rose-500 border-slate-300 cursor-pointer shrink-0" 
          data-id="${part.id}" 
          ${isSelected ? 'checked' : ''}
        >

        <div class="min-w-0 flex-1">
          <div class="flex items-center space-x-2">
            <span class="text-[11px] font-mono font-bold text-slate-500 shrink-0">#${indexNumber}</span>
            <h4 class="font-bold text-xs sm:text-sm text-slate-900 truncate ${isPlaying ? 'text-rose-700 font-extrabold' : ''}">
              ${part.title}
            </h4>
          </div>
          <div class="flex items-center space-x-2 mt-0.5 text-[11px]">
            ${
              part.is_converted 
                ? `<span class="inline-flex items-center text-emerald-700 font-bold bg-emerald-50/80 px-2 py-0.5 rounded-lg border border-emerald-200/60 shadow-xs">
                     <i data-lucide="mic" class="w-3.5 h-3.5 mr-1 text-emerald-600"></i> Giọng ${escapeHtml(part.audio_voice || 'Thái Sơn')} ${part.audio_size_bytes ? `(${Math.round(part.audio_size_bytes / 1024)} KB)` : ''}
                   </span>`
                : `<span class="text-slate-500 font-medium">Chưa chuyển đổi</span>`
            }
          </div>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="flex items-center space-x-1.5 shrink-0">
        <!-- Nút Đọc chi tiết trong cửa sổ mới -->
        <button 
          class="btn-read-chapter px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-800 text-xs font-semibold flex items-center space-x-1.5 transition shadow-sm"
          data-id="${part.id}"
          title="Đọc chi tiết nội dung chương trong cửa sổ mới"
        >
          <i data-lucide="book-open" class="w-3.5 h-3.5 text-rose-600"></i>
          <span class="hidden sm:inline">Đọc</span>
        </button>

        <!-- Nút Yêu thích chương -->
        <button 
          class="btn-fav-chapter p-2 text-slate-400 hover:text-rose-600 rounded-xl hover:bg-rose-50 transition ${isFav ? 'is-fav' : ''}"
          data-id="${part.id}"
          title="${isFav ? 'Bỏ yêu thích' : 'Yêu thích chương'}"
        >
          <i data-lucide="heart" class="w-4 h-4 ${isFav ? 'fill-current text-rose-600' : ''}"></i>
        </button>

        ${
          part.is_converted
            ? `
              <button 
                class="btn-play-chapter px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center space-x-1.5 transition shadow-sm"
                data-id="${part.id}"
              >
                <i data-lucide="${isPlaying && state.isPlaying ? 'pause' : 'play'}" class="w-3.5 h-3.5 fill-current"></i>
                <span>${isPlaying && state.isPlaying ? 'Tạm dừng' : 'Nghe'}</span>
              </button>

              <button 
                class="btn-download-chapter p-2 text-slate-600 hover:text-slate-900 rounded-xl hover:bg-slate-100 border border-slate-200 transition"
                title="Tải file MP3"
                data-id="${part.id}"
              >
                <i data-lucide="download" class="w-4 h-4"></i>
              </button>
            `
            : `
              <span class="text-xs text-slate-500 font-medium px-1">Chờ chuyển</span>
            `
        }
      </div>
    `;

    // Gắn sự kiện click checkbox
    const checkbox = item.querySelector('.chapter-checkbox');
    checkbox.addEventListener('change', (e) => {
      if (e.target.checked) {
        state.selectedChapterIds.add(part.id);
      } else {
        state.selectedChapterIds.delete(part.id);
      }
      updateConvertButton();
    });

    // Gắn sự kiện nút Đọc chương trong cửa sổ mới
    const readBtn = item.querySelector('.btn-read-chapter');
    if (readBtn) {
      readBtn.addEventListener('click', () => {
        openReaderWindow(state.currentStory.id, part.id);
      });
    }

    // Gắn sự kiện nút Yêu thích chương
    const favBtn = item.querySelector('.btn-fav-chapter');
    if (favBtn) {
      favBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        favBtn.classList.add('heart-pop');
        setTimeout(() => favBtn.classList.remove('heart-pop'), 450);
        toggleFavoriteChapter(state.currentStory.id, part);
      });
    }

    // Gắn sự kiện nút Play chương
    const playBtn = item.querySelector('.btn-play-chapter');
    if (playBtn) {
      playBtn.addEventListener('click', () => {
        playChapter(part.id);
      });
    }

    // Gắn sự kiện nút Tải MP3 chương
    const dlBtn = item.querySelector('.btn-download-chapter');
    if (dlBtn) {
      dlBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const url = `/api/audio/${state.currentStory.id}/${part.id}/download`;
        downloadFile(url, `${part.title}.mp3`);
      });
    }

    elements.chapterListContainer.appendChild(item);
  });

  if (window.lucide) lucide.createIcons();
}

function toggleSelectAll(checked) {
  if (!state.currentStory) return;
  if (checked) {
    state.currentStory.parts.forEach(p => state.selectedChapterIds.add(p.id));
  } else {
    state.selectedChapterIds.clear();
  }
  renderChapterList();
}

function updateConvertButton() {
  const count = state.selectedChapterIds.size;
  if (state.activeTaskId !== null) {
    elements.btnStartConvert.classList.add('hidden');
    elements.conversionProgressBanner.classList.remove('hidden');
  } else {
    elements.conversionProgressBanner.classList.add('hidden');
    elements.btnStartConvert.classList.remove('hidden');
    elements.btnStartConvert.disabled = count === 0;
  }
  elements.convertBtnLabel.textContent = `Chuyển đổi ${count} chương đã chọn thành Sách nói AI`;
  elements.checkboxSelectAll.checked = state.currentStory && count === state.currentStory.parts.length;
}

// ------------------- CHUYỂN ĐỔI SÁCH NÓI & BÁO CÁO TIẾN TRÌNH -------------------

async function startBatchConversion() {
  if (!state.currentStory || state.selectedChapterIds.size === 0) return;

  const chapterIds = Array.from(state.selectedChapterIds);
  elements.btnStartConvert.disabled = true;

  try {
    const headers = {
      'Content-Type': 'application/json',
      ...(state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : {})
    };

    const res = await fetch('/api/tts/convert', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        story_id: state.currentStory.id,
        chapter_ids: chapterIds,
        voice_config: state.voiceConfig,
        translation_config: state.translationConfig,
        device_id: state.deviceId,
        user_id: state.currentUser?.username || null
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Lỗi bắt đầu chuyển đổi');
    }

    const data = await res.json();
    state.activeTaskId = data.task_id;

    if (data.resumed) {
      console.log(`[Wattpad v1.8] Tiếp tục phiên chuyển đổi (${data.task_id}) cho thiết bị ${state.deviceId}`);
      elements.taskStatusText.textContent = data.message || 'Tiếp tục phiên làm việc trước đó...';
    }

    // Kích hoạt Foreground Service trên Android để không bị kill khi thoát ra Home
    notifyAndroidBackgroundStart('Wattpad AI Audiobook', 'Đang chuyển đổi sách nói AI...');

    startTaskPolling(data.task_id);

  } catch (err) {
    alert(`Lỗi: ${err.message}`);
    elements.btnStartConvert.disabled = false;
  }
}

function startTaskPolling(taskId) {
  // Chuyển đổi trạng thái ô hợp nhất: ẩn nút bắt đầu, hiện ô tiến trình
  elements.btnStartConvert.classList.add('hidden');
  elements.conversionProgressBanner.classList.remove('hidden');
  state.taskStatus = 'processing';
  updateTaskStateUI('processing');

  if (state.taskPollInterval) clearInterval(state.taskPollInterval);

  state.taskPollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/tts/task/${taskId}`);
      if (!res.ok) return;
      const task = await res.json();

      updateProgressUI(task);

      // Cập nhật thông báo thanh trạng thái Android
      if (task.status === 'processing') {
        const phaseName = task.current_phase === 'translating' ? 'Đang dịch AI' : 'Đang tạo giọng đọc';
        notifyAndroidBackgroundUpdate(
          'Wattpad AI Audiobook',
          `${phaseName} (${task.completed_chapters}/${task.total_chapters}): ${task.current_chapter_title} (${task.current_chapter_percent}%)`
        );
      }

      if (task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled') {
        clearInterval(state.taskPollInterval);
        state.taskPollInterval = null;
        state.activeTaskId = null;

        // Nếu không phát audio, dừng background service Android
        if (!state.isPlaying) {
          notifyAndroidBackgroundStop();
        }

        // Tải lại thông tin truyện và cập nhật kho Sách nói
        await reloadStory(task.story_id);
        await loadUserLibrary();

        if (task.status === 'completed') {
          elements.taskStatusText.textContent = 'Đã hoàn tất chuyển đổi tất cả các chương!';
          elements.taskPulseDot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-400';
          setTimeout(() => {
            elements.conversionProgressBanner.classList.add('hidden');
            elements.btnStartConvert.classList.remove('hidden');
            elements.btnStartConvert.disabled = false;
            updateConvertButton();
          }, 3000);

          // Tự động phát chương đầu tiên vừa chuyển đổi nếu chưa có gì đang phát
          if (!state.currentPlayingChapterId) {
            const firstConverted = state.currentStory.parts.find(p => p.is_converted);
            if (firstConverted) playChapter(firstConverted.id);
          }
        } else if (task.status === 'cancelled') {
          elements.taskStatusText.textContent = 'Tiến trình chuyển đổi đã bị hủy bỏ.';
          elements.taskPulseDot.className = 'w-2.5 h-2.5 rounded-full bg-rose-500';
          setTimeout(() => {
            elements.conversionProgressBanner.classList.add('hidden');
            elements.btnStartConvert.classList.remove('hidden');
            elements.btnStartConvert.disabled = false;
            updateConvertButton();
          }, 2000);
        } else {
          elements.taskStatusText.textContent = `Lỗi: ${task.error || 'Chuyển đổi thất bại'}`;
          elements.taskPulseDot.className = 'w-2.5 h-2.5 rounded-full bg-rose-500';
          setTimeout(() => {
            elements.conversionProgressBanner.classList.add('hidden');
            elements.btnStartConvert.classList.remove('hidden');
            elements.btnStartConvert.disabled = false;
            updateConvertButton();
          }, 3000);
          alert(`Chuyển đổi thất bại: ${task.error}`);
        }
      }
    } catch (err) {
      console.error('Lỗi kiểm tra tiến trình:', err);
    }
  }, 1000);
}


function updateProgressUI(task) {
  state.taskStatus = task.status;
  updateTaskStateUI(task.status);

  const overallPercent = task.total_chapters > 0 
    ? Math.round(((task.completed_chapters + (task.current_chapter_percent / 100)) / task.total_chapters) * 100)
    : 0;

  elements.taskOverallProgress.textContent = `${overallPercent}%`;
  elements.taskProgressBar.style.width = `${overallPercent}%`;

  let phaseLabel = 'Đang xử lý';
  if (task.current_phase === 'translating') {
    phaseLabel = `Đang dịch văn học AI (${task.translation_percent || task.current_chapter_percent}%)`;
  } else if (task.current_phase === 'synthesizing') {
    phaseLabel = `Đang tạo giọng đọc TTS (${task.tts_percent || task.current_chapter_percent}%)`;
  } else if (task.current_phase === 'scraping') {
    phaseLabel = `Đang trích xuất nội dung`;
  }

  if (task.status === 'paused') {
    elements.taskStatusText.textContent = `Đang tạm dừng (${task.completed_chapters}/${task.total_chapters} chương)`;
  } else {
    elements.taskStatusText.textContent = `${phaseLabel} (${task.completed_chapters}/${task.total_chapters} chương)`;
  }
  elements.taskChapterDetail.textContent = `Chương: ${task.current_chapter_title || 'Đang nạp...'} (${task.current_chapter_percent}%)`;
}

function updateTaskStateUI(status) {
  if (status === 'paused') {
    elements.taskPulseDot.className = 'w-2.5 h-2.5 rounded-full bg-amber-400';
    elements.iconTaskPause.classList.add('hidden');
    elements.iconTaskResume.classList.remove('hidden');
    elements.labelTaskPauseResume.textContent = 'Tiếp tục';
    elements.btnPauseResumeTask.className = 'px-3 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-400/40 text-emerald-300 text-xs font-medium flex items-center space-x-1.5 transition backdrop-blur-md';
  } else if (status === 'processing') {
    elements.taskPulseDot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping';
    elements.iconTaskPause.classList.remove('hidden');
    elements.iconTaskResume.classList.add('hidden');
    elements.labelTaskPauseResume.textContent = 'Tạm dừng';
    elements.btnPauseResumeTask.className = 'px-3 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400/40 text-amber-300 text-xs font-medium flex items-center space-x-1.5 transition backdrop-blur-md';
  }
  if (window.lucide) lucide.createIcons();
}

async function handlePauseResumeTask() {
  if (!state.activeTaskId) return;

  if (state.taskStatus === 'processing') {
    elements.btnPauseResumeTask.disabled = true;
    try {
      const res = await fetch(`/api/tts/task/${state.activeTaskId}/pause`, { method: 'POST' });
      if (res.ok) {
        state.taskStatus = 'paused';
        updateTaskStateUI('paused');
        elements.taskStatusText.textContent = 'Đã tạm dừng chuyển đổi. Bấm "Tiếp tục" để chạy tiếp.';
      }
    } catch (e) {
      console.error('Lỗi khi gửi yêu cầu tạm dừng:', e);
    } finally {
      elements.btnPauseResumeTask.disabled = false;
    }
  } else if (state.taskStatus === 'paused') {
    elements.btnPauseResumeTask.disabled = true;
    try {
      const res = await fetch(`/api/tts/task/${state.activeTaskId}/resume`, { method: 'POST' });
      if (res.ok) {
        state.taskStatus = 'processing';
        updateTaskStateUI('processing');
        elements.taskStatusText.textContent = 'Đang tiếp tục chuyển đổi...';
      }
    } catch (e) {
      console.error('Lỗi khi gửi yêu cầu tiếp tục:', e);
    } finally {
      elements.btnPauseResumeTask.disabled = false;
    }
  }
}

async function handleCancelTask() {
  if (!state.activeTaskId) return;
  if (!confirm('Bạn có chắc chắn muốn hủy bỏ quá trình chuyển đổi audio này không?')) return;

  elements.btnCancelTask.disabled = true;
  try {
    const res = await fetch(`/api/tts/task/${state.activeTaskId}/cancel`, { method: 'POST' });
    if (res.ok) {
      state.taskStatus = 'cancelled';
      if (state.taskPollInterval) {
        clearInterval(state.taskPollInterval);
        state.taskPollInterval = null;
      }
      elements.taskStatusText.textContent = 'Đã hủy tác vụ chuyển đổi.';
      elements.taskPulseDot.className = 'w-2.5 h-2.5 rounded-full bg-rose-500';
      state.activeTaskId = null;

      setTimeout(() => {
        elements.conversionProgressBanner.classList.add('hidden');
        elements.btnStartConvert.classList.remove('hidden');
        elements.btnStartConvert.disabled = false;
        updateConvertButton();
      }, 1800);

      if (state.currentStory) {
        await reloadStory(state.currentStory.id);
      }
    }
  } catch (e) {
    console.error('Lỗi khi hủy tác vụ:', e);
  } finally {
    elements.btnCancelTask.disabled = false;
  }
}

async function reloadStory(storyId) {
  try {
    const res = await fetch(`/api/story/${storyId}`);
    if (res.ok) {
      const updatedStory = await res.json();
      state.currentStory = updatedStory;
      renderChapterList();
      updateStoryStats();
    }
  } catch (err) {
    console.error('Lỗi reload story:', err);
  }
}

// ------------------- NGHE THỬ GIỌNG ĐỌC MẪU -------------------

async function previewVoiceSample() {
  elements.btnPreviewSample.disabled = true;
  elements.previewSampleText.textContent = 'Đang tổng hợp giọng nói...';

  try {
    const res = await fetch('/api/tts/sample', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: "Chào bạn, đây là mẫu giọng đọc của ứng dụng sách nói Wattpad với biểu cảm bạn vừa chọn.",
        voice_config: state.voiceConfig
      })
    });

    if (!res.ok) throw new Error('Không thể tạo mẫu âm thanh');
    const data = await res.json();

    elements.sampleAudioPlayer.src = data.sample_url;
    elements.sampleAudioPlayer.play();

    elements.previewSampleText.textContent = 'Đang phát âm thanh mẫu...';
    elements.sampleAudioPlayer.onended = () => {
      elements.previewSampleText.textContent = 'Nghe thử giọng đọc đã chọn';
      elements.btnPreviewSample.disabled = false;
    };
  } catch (err) {
    alert(`Lỗi nghe thử: ${err.message}`);
    elements.previewSampleText.textContent = 'Nghe thử giọng đọc đã chọn';
    elements.btnPreviewSample.disabled = false;
  }
}

// ------------------- TRÌNH PHÁT SÁCH NÓI & MEDIASESSION -------------------

let lastListenHistorySaveTime = 0;

function setupPlayerControls() {
  const audio = elements.mainAudio;

  // Play / Pause
  elements.btnPlayerPlayPause.addEventListener('click', () => {
    triggerHaptic(20);
    togglePlayPause();
  });

  // Tua 15s trước và sau
  elements.btnPlayerRewind.addEventListener('click', () => {
    triggerHaptic(15);
    audio.currentTime = Math.max(0, audio.currentTime - 15);
  });
  elements.btnPlayerForward.addEventListener('click', () => {
    triggerHaptic(15);
    audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 15);
  });

  // Chuyển chương trước / sau
  elements.btnPlayerPrev.addEventListener('click', () => {
    triggerHaptic(25);
    playPreviousChapter();
  });
  elements.btnPlayerNext.addEventListener('click', () => {
    triggerHaptic(25);
    playNextChapter();
  });

  // Thanh tiến trình (Seek bar)
  elements.playerProgressContainer.addEventListener('click', (e) => {
    if (!audio.duration) return;
    triggerHaptic(10);
    const rect = elements.playerProgressContainer.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    audio.currentTime = pos * audio.duration;
  });

  // Chỉnh tốc độ phát (1x, 1.25x, 1.5x...)
  elements.btnPlaybackRate.addEventListener('click', () => {
    triggerHaptic(15);
    state.currentRateIndex = (state.currentRateIndex + 1) % state.playbackRates.length;
    const rate = state.playbackRates[state.currentRateIndex];
    audio.playbackRate = rate;
    elements.btnPlaybackRate.textContent = `${rate.toFixed(2).replace(/\.00$/, '')}x`;
  });


  // Cập nhật thời gian audio & ghi nhận lịch sử nghe
  audio.addEventListener('timeupdate', () => {
    if (!audio.duration) return;
    const current = audio.currentTime;
    const total = audio.duration;
    elements.playerCurrentTime.textContent = formatTime(current);
    elements.playerTotalTime.textContent = formatTime(total);
    elements.playerProgressBar.style.width = `${(current / total) * 100}%`;

    // Ghi nhận lịch sử nghe định kỳ mỗi 6 giây
    const now = Date.now();
    if (now - lastListenHistorySaveTime > 6000 && state.currentStory && state.currentPlayingChapterId) {
      lastListenHistorySaveTime = now;
      recordCurrentListeningHistory(current, total);
    }
  });

  audio.addEventListener('loadedmetadata', () => {
    elements.playerTotalTime.textContent = formatTime(audio.duration);
  });

  // Tự động chuyển tiếp sang chương kế tiếp khi nghe hết chương hiện tại
  audio.addEventListener('ended', () => {
    if (audio.duration) recordCurrentListeningHistory(audio.duration, audio.duration);
    playNextChapter();
  });

  audio.addEventListener('play', () => {
    state.isPlaying = true;
    updatePlayerUI();
    renderChapterList();
    if (state.currentStory && state.currentPlayingChapterId) {
      const part = state.currentStory.parts.find(p => p.id === state.currentPlayingChapterId);
      notifyAndroidBackgroundStart('Đang phát: ' + (part?.title || 'Sách nói'), state.currentStory.title);
    }
  });

  audio.addEventListener('pause', () => {
    state.isPlaying = false;
    updatePlayerUI();
    renderChapterList();
    if (audio.duration && state.currentStory && state.currentPlayingChapterId) {
      recordCurrentListeningHistory(audio.currentTime, audio.duration);
    }
    if (window.AndroidBridge && !state.activeTaskId) {
      notifyAndroidBackgroundStop();
    }
  });

  // Tải file MP3 của chương đang phát từ player bar
  elements.btnPlayerDownload.addEventListener('click', (e) => {
    e.preventDefault();
    if (!state.currentStory || !state.currentPlayingChapterId) return;
    const part = state.currentStory.parts.find(p => p.id === state.currentPlayingChapterId);
    const url = `/api/audio/${state.currentStory.id}/${state.currentPlayingChapterId}/download`;
    downloadFile(url, part ? `${part.title}.mp3` : 'chapter.mp3');
  });
}

function playChapter(chapterId, initialSeekTime = 0) {
  if (!state.currentStory) return;
  const part = state.currentStory.parts.find(p => p.id === chapterId);
  if (!part || !part.is_converted) {
    alert('Chương này chưa được chuyển đổi sang audio.');
    return;
  }

  state.currentPlayingChapterId = chapterId;
  const audio = elements.mainAudio;
  const audioUrl = `/api/audio/${state.currentStory.id}/${chapterId}?t=${Date.now()}`;

  audio.src = audioUrl;

  if (initialSeekTime > 0) {
    const applySeek = () => {
      audio.currentTime = initialSeekTime;
      audio.removeEventListener('loadedmetadata', applySeek);
    };
    audio.addEventListener('loadedmetadata', applySeek);
  }

  audio.play().catch(e => console.warn('Autoplay prevented:', e));

  // Hiện Player bar ở đáy màn hình
  elements.audiobookPlayer.classList.remove('hidden');

  // Cập nhật thông tin trên player bar
  elements.playerMiniCover.src = state.currentStory.cover;
  elements.playerChapterTitle.textContent = part.title;
  elements.playerStoryTitle.textContent = state.currentStory.title;
  elements.btnPlayerDownload.href = `/api/audio/${state.currentStory.id}/${chapterId}/download`;

  // Thiết lập MediaSession (Điều khiển trên màn hình khóa Android)
  setupMediaSession(part);

  // Kích hoạt Foreground Service trên Android
  notifyAndroidBackgroundStart('Đang phát: ' + part.title, state.currentStory.title);

  state.isPlaying = true;
  renderChapterList();
  updatePlayerUI();
}


function togglePlayPause() {
  const audio = elements.mainAudio;
  if (!audio.src) return;

  if (audio.paused) {
    audio.play().catch(e => console.warn('Lỗi phát âm thanh:', e));
  } else {
    audio.pause();
  }
}

function playPreviousChapter() {
  if (!state.currentStory || !state.currentPlayingChapterId) return;
  const converted = state.currentStory.parts.filter(p => p.is_converted);
  const currentIndex = converted.findIndex(p => p.id === state.currentPlayingChapterId);
  if (currentIndex > 0) {
    playChapter(converted[currentIndex - 1].id);
  }
}

function playNextChapter() {
  if (!state.currentStory || !state.currentPlayingChapterId) return;
  const converted = state.currentStory.parts.filter(p => p.is_converted);
  const currentIndex = converted.findIndex(p => p.id === state.currentPlayingChapterId);
  if (currentIndex >= 0 && currentIndex < converted.length - 1) {
    playChapter(converted[currentIndex + 1].id);
  }
}

function updatePlayerUI() {
  const iconSlot = elements.playerPlayIconSlot || document.getElementById('player-play-icon-slot') || elements.btnPlayerPlayPause;
  if (iconSlot) {
    if (state.isPlaying) {
      iconSlot.innerHTML = '<i data-lucide="pause" class="w-4 h-4 fill-current"></i>';
      if (elements.btnPlayerPlayPause) elements.btnPlayerPlayPause.title = 'Tạm dừng (Phím Cách)';
    } else {
      iconSlot.innerHTML = '<i data-lucide="play" class="w-4 h-4 fill-current ml-0.5"></i>';
      if (elements.btnPlayerPlayPause) elements.btnPlayerPlayPause.title = 'Phát (Phím Cách)';
    }
  }

  if (elements.playerEqualizer) {
    if (state.isPlaying) {
      elements.playerEqualizer.classList.remove('paused');
    } else {
      elements.playerEqualizer.classList.add('paused');
    }
  }
  if (window.lucide) lucide.createIcons();
}

// MediaSession API: Tích hợp hệ thống thông báo và khóa màn hình trên điện thoại Android
function setupMediaSession(part) {
  if ('mediaSession' in navigator && state.currentStory) {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: part.title,
      artist: state.currentStory.author,
      album: state.currentStory.title,
      artwork: [
        { src: state.currentStory.cover, sizes: '96x96', type: 'image/jpeg' },
        { src: state.currentStory.cover, sizes: '192x192', type: 'image/jpeg' },
        { src: state.currentStory.cover, sizes: '512x512', type: 'image/jpeg' }
      ]
    });

    navigator.mediaSession.setActionHandler('play', () => elements.mainAudio.play());
    navigator.mediaSession.setActionHandler('pause', () => elements.mainAudio.pause());
    navigator.mediaSession.setActionHandler('seekbackward', () => {
      elements.mainAudio.currentTime = Math.max(0, elements.mainAudio.currentTime - 15);
    });
    navigator.mediaSession.setActionHandler('seekforward', () => {
      elements.mainAudio.currentTime = Math.min(elements.mainAudio.duration || 0, elements.mainAudio.currentTime + 15);
    });
    navigator.mediaSession.setActionHandler('previoustrack', playPreviousChapter);
    navigator.mediaSession.setActionHandler('nexttrack', playNextChapter);
  }
}

function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return '00:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

// =================== PHIÊN BẢN 1.5: READER CỬA SỔ MỚI & YÊU THÍCH ===================

let appBroadcast = null;

function initBroadcastChannel() {
  if (typeof BroadcastChannel !== 'undefined') {
    try {
      appBroadcast = new BroadcastChannel('wattpad_channel');
      appBroadcast.onmessage = (event) => {
        const data = event.data;
        if (!data) return;

        if (data.type === 'READER_CLOSED') {
          handleReaderClosed(data.storyId, data.chapterId, data.chapterTitle, data.isConverted);
        } else if (data.type === 'READ_HISTORY_UPDATED') {
          loadUserLibrary();
        } else if (data.type === 'REQUEST_CONVERT_CHAPTER') {
          if (state.currentStory && state.currentStory.id === data.storyId) {
            state.selectedChapterIds.clear();
            state.selectedChapterIds.add(data.chapterId);
            renderChapterList();
            updateConvertButton();
            elements.btnStartConvert.scrollIntoView({ behavior: 'smooth', block: 'center' });
            elements.btnStartConvert.classList.add('animate-pulse');
            setTimeout(() => elements.btnStartConvert.classList.remove('animate-pulse'), 2500);
          }
        } else if (data.type === 'FAVORITES_UPDATED') {
          updateFavoritesBadges();
          renderChapterList();
          if (state.currentStory) updateStoryFavButton();
        }
      };
    } catch (e) {
      console.warn('BroadcastChannel not supported or error:', e);
    }
  }
}

// ------------------- CỬA SỔ ĐỌC (READER WINDOW) -------------------

function openReaderWindow(storyId, chapterId) {
  const part = state.currentStory?.parts?.find(p => p.id === chapterId);
  const chapterTitle = part ? part.title : `Chương ${chapterId}`;
  const wasConverted = part ? Boolean(part.is_converted) : false;

  const url = `/reader.html?story_id=${encodeURIComponent(storyId)}&chapter_id=${chapterId}`;
  const w = 960, h = 820;
  const left = Math.max(0, Math.floor((window.screen.width - w) / 2));
  const top = Math.max(0, Math.floor((window.screen.height - h) / 2));

  if (state.readerCheckInterval) {
    clearInterval(state.readerCheckInterval);
    state.readerCheckInterval = null;
  }

  state.activeReaderWindow = window.open(
    url,
    'WattpadReaderWindow',
    `width=${w},height=${h},top=${top},left=${left},resizable=yes,scrollbars=yes,status=no,toolbar=no,menubar=no`
  );

  // Giám sát đóng cửa sổ đọc bằng interval
  state.readerCheckInterval = setInterval(() => {
    if (state.activeReaderWindow && state.activeReaderWindow.closed) {
      clearInterval(state.readerCheckInterval);
      state.readerCheckInterval = null;
      state.activeReaderWindow = null;
      handleReaderClosed(storyId, chapterId, chapterTitle, wasConverted);
    }
  }, 600);
}

function handleReaderClosed(storyId, chapterId, chapterTitle, wasConverted) {
  // Kiểm tra xem chương này đã có audio chưa
  const part = state.currentStory?.parts?.find(p => p.id === chapterId);
  const isConverted = part ? Boolean(part.is_converted) : wasConverted;

  // Nếu chương ĐÃ có audio rồi -> không làm phiền người dùng
  if (isConverted) {
    return;
  }

  // Nếu CHƯA có audio -> Hiển thị Modal nhắc nhở tạo sách nói AI
  state.lastClosedReaderInfo = {
    storyId,
    chapterId,
    chapterTitle: chapterTitle || part?.title || `Chương ${chapterId}`
  };

  if (elements.promptChapterTitle) {
    elements.promptChapterTitle.textContent = state.lastClosedReaderInfo.chapterTitle;
  }
  if (elements.modalAudioPrompt) {
    elements.modalAudioPrompt.classList.remove('hidden');
  }
  if (window.lucide) lucide.createIcons();
}

// ------------------- QUẢN LÝ YÊU THÍCH (FAVORITES) -------------------

// ------------------- PHIÊN BẢN 1.8: ĐỊNH DANH THIẾT BỊ & XÁC THỰC THÀNH VIÊN -------------------

function initDeviceId() {
  let did = localStorage.getItem('wattpad_device_id');
  if (!did) {
    did = 'device_' + Math.random().toString(36).substring(2, 9) + '_' + Date.now().toString(36);
    localStorage.setItem('wattpad_device_id', did);
  }
  state.deviceId = did;
  console.log('[Wattpad v1.8] Thiết bị đầu cuối ID:', state.deviceId);
}

async function initAuth() {
  if (state.authToken) {
    try {
      const res = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${state.authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        state.currentUser = data.user;
      } else {
        state.authToken = null;
        localStorage.removeItem('wattpad_auth_token');
        state.currentUser = null;
      }
    } catch (e) {
      console.warn('Lỗi xác thực phiên đăng nhập:', e);
    }
  }
  updateProfileUI();
}

function updateProfileUI() {
  const user = state.currentUser;
  if (user) {
    if (elements.sidebarUserAvatar) {
      elements.sidebarUserAvatar.textContent = user.avatar || user.name.charAt(0).toUpperCase();
      elements.sidebarUserAvatar.className = 'profile-avatar bg-gradient-to-tr from-indigo-500 to-purple-600 text-white font-bold text-xs shadow-sm';
    }
    if (elements.sidebarUserName) elements.sidebarUserName.textContent = user.name;
    if (elements.sidebarUserRole) elements.sidebarUserRole.textContent = user.role || 'Thành viên chính thức';
    if (elements.iconSidebarAuth) elements.iconSidebarAuth.setAttribute('data-lucide', 'log-out');
    if (elements.btnSidebarAuthAction) elements.btnSidebarAuthAction.title = 'Đăng xuất tài khoản ' + user.name;
    if (elements.androidUserStatusText) elements.androidUserStatusText.textContent = `Thành viên: ${user.name}`;
    if (elements.btnAndroidUserModal) elements.btnAndroidUserModal.title = `Tài khoản: ${user.name}`;
  } else {
    if (elements.sidebarUserAvatar) {
      elements.sidebarUserAvatar.textContent = 'K';
      elements.sidebarUserAvatar.className = 'profile-avatar bg-slate-200 text-slate-600 font-bold text-xs';
    }
    if (elements.sidebarUserName) elements.sidebarUserName.textContent = 'Khách';
    if (elements.sidebarUserRole) elements.sidebarUserRole.textContent = 'Chưa đăng nhập';
    if (elements.iconSidebarAuth) elements.iconSidebarAuth.setAttribute('data-lucide', 'log-in');
    if (elements.btnSidebarAuthAction) elements.btnSidebarAuthAction.title = 'Đăng nhập thành viên';
    if (elements.androidUserStatusText) elements.androidUserStatusText.textContent = 'Chế độ khách';
    if (elements.btnAndroidUserModal) elements.btnAndroidUserModal.title = 'Đăng nhập';
  }
  if (window.lucide) lucide.createIcons();
}

function openLoginModal() {
  if (elements.loginErrorMsg) elements.loginErrorMsg.classList.add('hidden');
  if (elements.loginUsername && !elements.loginUsername.value) {
    elements.loginUsername.value = 'jason';
  }
  if (elements.modalLogin) elements.modalLogin.classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function closeLoginModal() {
  if (elements.modalLogin) elements.modalLogin.classList.add('hidden');
}

// ------------------- MODAL DỊCH THỬ AI VĂN HỌC (PREVIEW) -------------------

function openTranslationPreviewModal() {
  if (!elements.modalTranslationPreview) return;
  
  // Nạp câu mẫu nếu ô đang rỗng
  if (elements.previewSourceText && !elements.previewSourceText.value.trim()) {
    if (state.currentStory && state.currentStory.description) {
      elements.previewSourceText.value = state.currentStory.description.slice(0, 300);
    } else {
      elements.previewSourceText.value = "The cold autumn wind howled through the barren trees as Eleanor pulled her coat tighter, watching the mysterious silhouette vanish into the misty shadows of the old cathedral.";
    }
  }

  elements.modalTranslationPreview.classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function closeTranslationPreviewModal() {
  if (elements.modalTranslationPreview) {
    elements.modalTranslationPreview.classList.add('hidden');
  }
}

async function handlePreviewTranslation() {
  const text = elements.previewSourceText ? elements.previewSourceText.value.trim() : '';
  if (!text) {
    alert('Vui lòng nhập đoạn văn bản nguồn tiếng Anh cần dịch thử.');
    return;
  }

  if (elements.btnSubmitPreviewTranslate) {
    elements.btnSubmitPreviewTranslate.disabled = true;
    elements.btnSubmitPreviewTranslate.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin inline mr-1"></i> Đang dịch AI...`;
  }
  if (elements.previewTranslatedBox) {
    elements.previewTranslatedBox.textContent = 'Đang kết nối Neural Translation Model & xử lý văn phong văn học...';
  }
  if (window.lucide) lucide.createIcons();

  const startTime = Date.now();
  try {
    const res = await fetch('/api/translation/preview', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : {})
      },
      body: JSON.stringify({
        text,
        source_language: 'auto',
        target_language: 'vi',
        story_id: state.currentStory ? state.currentStory.id : null
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Lỗi xử lý dịch thuật');
    }

    const data = await res.json();
    if (elements.previewTranslatedBox) {
      elements.previewTranslatedBox.textContent = data.translated_text || '(Không có kết quả)';
    }
    if (elements.previewCachedTag) {
      if (data.cached) {
        elements.previewCachedTag.classList.remove('hidden');
      } else {
        elements.previewCachedTag.classList.add('hidden');
      }
    }
    if (elements.previewLatencyText) {
      const elapsed = data.latency_ms || (Date.now() - startTime);
      elements.previewLatencyText.textContent = `${elapsed}ms (${data.char_count || text.length} ký tự)`;
    }
  } catch (err) {
    if (elements.previewTranslatedBox) {
      elements.previewTranslatedBox.textContent = `Lỗi dịch thử: ${err.message}`;
    }
  } finally {
    if (elements.btnSubmitPreviewTranslate) {
      elements.btnSubmitPreviewTranslate.disabled = false;
      elements.btnSubmitPreviewTranslate.innerHTML = `<i data-lucide="sparkles" class="w-4 h-4 inline mr-1"></i> Dịch thử ngay`;
    }
    if (window.lucide) lucide.createIcons();
  }
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  const username = elements.loginUsername.value.trim();
  const password = elements.loginPassword.value.trim();
  const remember = elements.loginRemember ? elements.loginRemember.checked : true;

  if (!username || !password) return;

  try {
    elements.btnSubmitLogin.disabled = true;
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      if (elements.loginErrorMsg) {
        elements.loginErrorText.textContent = data.detail || data.message || 'Tên đăng nhập hoặc mật khẩu không chính xác.';
        elements.loginErrorMsg.classList.remove('hidden');
      }
      elements.btnSubmitLogin.disabled = false;
      return;
    }

    state.authToken = data.token;
    state.currentUser = data.user;
    if (remember) {
      localStorage.setItem('wattpad_auth_token', data.token);
    }
    updateProfileUI();
    closeLoginModal();
    await loadUserLibrary();
    alert(`Đăng nhập thành công! Chào mừng ${data.user.name} (Vai trò: ${data.user.role})`);
  } catch (err) {
    if (elements.loginErrorMsg) {
      elements.loginErrorText.textContent = 'Lỗi kết nối: ' + err.message;
      elements.loginErrorMsg.classList.remove('hidden');
    }
  } finally {
    elements.btnSubmitLogin.disabled = false;
    if (window.lucide) lucide.createIcons();
  }
}

async function handleLogout() {
  if (!confirm('Bạn có chắc chắn muốn đăng xuất tài khoản?')) return;
  if (state.authToken) {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${state.authToken}` }
      });
    } catch (e) {}
  }
  state.authToken = null;
  state.currentUser = null;
  localStorage.removeItem('wattpad_auth_token');
  updateProfileUI();
  await loadUserLibrary();
}

function handleSidebarAuthAction() {
  if (state.currentUser) {
    handleLogout();
  } else {
    openLoginModal();
  }
}

// ------------------- QUẢN LÝ THƯ VIỆN & LỊCH SỬ THEO NGƯỜI DÙNG -------------------

async function loadUserLibrary() {
  try {
    const headers = state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : {};
    const res = await fetch('/api/user/library', { headers });
    if (res.ok) {
      const data = await res.json();
      state.libraryData = {
        stories: data.stories || [],
        audiobooks: data.audiobooks || [],
        read_history: data.read_history || [],
        listen_history: data.listen_history || []
      };
    }
  } catch (e) {
    console.warn('Lỗi tải dữ liệu thư viện:', e);
  }
  updateFavoritesBadges();
  updateStoryFavButton();
  renderFavoritesModal();
  updateRecentlyPlayedSection();
}

function isStoryFavorite(storyId) {
  if (!storyId) return false;
  if (state.libraryData && state.libraryData.stories) {
    return state.libraryData.stories.some(s => s.id === storyId);
  }
  try {
    const localFavs = JSON.parse(localStorage.getItem('wattpad_favorite_stories') || '[]');
    return localFavs.some(s => s.id === storyId);
  } catch (e) {
    return false;
  }
}

async function toggleFavoriteStory(story) {
  if (!story) return;
  const isFav = isStoryFavorite(story.id);

  if (isFav) {
    // Xóa khỏi thư viện
    try {
      const headers = state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : {};
      await fetch(`/api/user/library/story/${encodeURIComponent(story.id)}`, {
        method: 'DELETE',
        headers
      });
    } catch (e) {}
    state.libraryData.stories = state.libraryData.stories.filter(s => s.id !== story.id);
  } else {
    // Thêm vào thư viện
    const storyItem = {
      id: story.id,
      title: story.title,
      author: story.author,
      cover: story.cover,
      numParts: story.numParts,
      url: story.url || '',
      added_at: Date.now() / 1000,
      is_custom: Boolean(story.id.startsWith('custom_'))
    };
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : {})
      };
      await fetch('/api/user/library/story', {
        method: 'POST',
        headers,
        body: JSON.stringify(storyItem)
      });
    } catch (e) {}
    state.libraryData.stories.unshift(storyItem);
  }

  // Cập nhật fallback localStorage
  localStorage.setItem('wattpad_favorite_stories', JSON.stringify(state.libraryData.stories));

  updateStoryFavButton();
  updateFavoritesBadges();
  renderFavoritesModal();

  if (elements.btnToggleFavStory) {
    elements.btnToggleFavStory.classList.add('heart-pop');
    setTimeout(() => elements.btnToggleFavStory.classList.remove('heart-pop'), 450);
  }
}

function updateStoryFavButton() {
  if (!state.currentStory || !elements.btnToggleFavStory) return;
  const isFav = isStoryFavorite(state.currentStory.id);

  if (isFav) {
    elements.btnToggleFavStory.className = 'mt-2 inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-xl bg-rose-500/20 border border-rose-400/40 text-rose-300 shadow-sm transition';
    elements.iconFavStory.className = 'w-3.5 h-3.5 fill-current text-rose-500';
    elements.labelFavStory.textContent = 'Đã lưu trong Thư viện';
  } else {
    elements.btnToggleFavStory.className = 'mt-2 inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-xl liquid-btn-secondary text-xs text-slate-200 hover:text-rose-400 transition';
    elements.iconFavStory.className = 'w-3.5 h-3.5 text-slate-400';
    elements.labelFavStory.textContent = 'Lưu vào Thư viện';
  }
  if (window.lucide) lucide.createIcons();
}

function updateFavoritesBadges() {
  const storiesCount = state.libraryData.stories?.length || 0;
  const audiobooksCount = state.libraryData.audiobooks?.length || 0;
  const readCount = state.libraryData.read_history?.length || 0;
  const listenCount = state.libraryData.listen_history?.length || 0;
  const total = storiesCount + audiobooksCount;

  if (elements.badgeFavCount) {
    if (total > 0) {
      elements.badgeFavCount.classList.remove('hidden');
      elements.badgeFavCount.textContent = total;
    } else {
      elements.badgeFavCount.classList.add('hidden');
    }
  }

  if (elements.badgeFavStoriesCount) elements.badgeFavStoriesCount.textContent = storiesCount;
  if (elements.badgeLibAudiobooksCount) elements.badgeLibAudiobooksCount.textContent = audiobooksCount;
  if (elements.badgeLibReadCount) elements.badgeLibReadCount.textContent = readCount;
  if (elements.badgeLibListenCount) elements.badgeLibListenCount.textContent = listenCount;
}

function openFavoritesModal() {
  updateFavoritesBadges();
  renderFavoritesModal();
  if (elements.modalFavorites) {
    elements.modalFavorites.classList.remove('hidden');
  }
  if (window.lucide) lucide.createIcons();
}

function closeFavoritesModal() {
  if (elements.modalFavorites) {
    elements.modalFavorites.classList.add('hidden');
  }
}

function switchFavoritesTab(tabName) {
  state.activeLibraryTab = tabName;
  const tabs = [
    { name: 'stories', btn: elements.tabFavStories, container: elements.containerFavStories },
    { name: 'audiobooks', btn: elements.tabLibAudiobooks, container: elements.containerLibAudiobooks },
    { name: 'read', btn: elements.tabLibReadHistory, container: elements.containerLibReadHistory },
    { name: 'listen', btn: elements.tabLibListenHistory, container: elements.containerLibListenHistory }
  ];

  tabs.forEach(t => {
    if (!t.btn || !t.container) return;
    if (t.name === tabName) {
      t.btn.className = 'px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 transition flex items-center space-x-1.5 shrink-0 shadow-sm';
      t.container.classList.remove('hidden');
    } else {
      t.btn.className = 'px-3 py-1.5 rounded-xl text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition flex items-center space-x-1.5 shrink-0';
      t.container.classList.add('hidden');
    }
  });

  renderFavoritesModal();
  if (window.lucide) lucide.createIcons();
}

function renderFavoritesModal() {
  const stories = state.libraryData.stories || [];
  const audiobooks = state.libraryData.audiobooks || [];
  const readHistory = state.libraryData.read_history || [];
  const listenHistory = state.libraryData.listen_history || [];

  // 1. TAB 1: THƯ VIỆN TRUYỆN
  if (elements.containerFavStories) {
    if (stories.length === 0) {
      elements.containerFavStories.innerHTML = `
        <div class="py-12 text-center text-slate-400 space-y-2">
          <i data-lucide="book-open" class="w-10 h-10 mx-auto text-slate-400/80"></i>
          <p class="text-sm font-semibold text-slate-700">Chưa có truyện nào trong Thư viện.</p>
          <p class="text-xs text-slate-500">Bấm "Lưu vào Thư viện" ở trang thông tin truyện để quản lý dễ dàng.</p>
        </div>
      `;
    } else {
      elements.containerFavStories.innerHTML = stories.map(s => `
        <div class="p-3 rounded-2xl bg-white/70 border border-slate-200/80 hover:border-slate-300 transition flex items-center justify-between gap-3 shadow-xs">
          <div class="flex items-center space-x-3 min-w-0 flex-1">
            <img src="${s.cover || 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80'}" class="w-11 h-15 rounded-xl object-cover border border-slate-200 shrink-0" onerror="this.src='https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80'">
            <div class="min-w-0 flex-1">
              <h4 class="font-bold text-xs sm:text-sm text-slate-900 truncate">${escapeHtml(s.title)}</h4>
              <p class="text-[11px] text-slate-500 truncate mt-0.5">${escapeHtml(s.author || 'Tác giả')} • ${s.numParts || 0} chương</p>
            </div>
          </div>
          <div class="flex items-center space-x-1.5 shrink-0">
            <button class="btn-open-fav-story px-3 py-1.5 rounded-xl btn-primary-desktop text-xs font-semibold flex items-center space-x-1 shadow-sm" data-id="${s.id}" data-url="${s.url || ''}">
              <i data-lucide="book-open" class="w-3.5 h-3.5"></i>
              <span>Mở truyện</span>
            </button>
            <button class="btn-remove-fav-story p-1.5 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition" data-id="${s.id}" title="Xóa khỏi thư viện">
              <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
          </div>
        </div>
      `).join('');

      elements.containerFavStories.querySelectorAll('.btn-open-fav-story').forEach(btn => {
        btn.addEventListener('click', () => {
          loadStoryById(btn.dataset.id, btn.dataset.url);
        });
      });

      elements.containerFavStories.querySelectorAll('.btn-remove-fav-story').forEach(btn => {
        btn.addEventListener('click', () => {
          const sid = btn.dataset.id;
          const storyObj = state.libraryData.stories.find(s => s.id === sid);
          if (storyObj) toggleFavoriteStory(storyObj);
        });
      });
    }
  }

  // 2. TAB 2: KHO SÁCH NÓI (AUDIOBOOKS)
  if (elements.containerLibAudiobooks) {
    if (audiobooks.length === 0) {
      elements.containerLibAudiobooks.innerHTML = `
        <div class="py-12 text-center text-slate-400 space-y-2">
          <i data-lucide="headphones" class="w-10 h-10 mx-auto text-slate-400/80"></i>
          <p class="text-sm font-semibold text-slate-700">Chưa có sách nói nào được tạo.</p>
          <p class="text-xs text-slate-500">Hãy chọn các chương truyện và bấm "Chuyển đổi thành Sách nói AI" để lưu vào kho này.</p>
        </div>
      `;
    } else {
      elements.containerLibAudiobooks.innerHTML = audiobooks.map(a => `
        <div class="p-3 rounded-2xl bg-white/70 border border-slate-200/80 hover:border-slate-300 transition flex items-center justify-between gap-3 shadow-xs">
          <div class="flex items-center space-x-3 min-w-0 flex-1">
            <img src="${a.cover || 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80'}" class="w-11 h-15 rounded-xl object-cover border border-slate-200 shrink-0" onerror="this.src='https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80'">
            <div class="min-w-0 flex-1">
              <div class="flex items-center space-x-1.5 mb-0.5">
                <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                  ${a.converted_count} chương Audio sẵn sàng
                </span>
              </div>
              <h4 class="font-bold text-xs sm:text-sm text-slate-900 truncate">${escapeHtml(a.title)}</h4>
              <p class="text-[11px] text-slate-500 truncate mt-0.5">${escapeHtml(a.author || 'Tác giả')}</p>
            </div>
          </div>
          <div class="flex items-center space-x-1.5 shrink-0">
            <button class="btn-play-audiobook px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center space-x-1 shadow-sm transition" data-id="${a.id}" data-chapter="${a.first_audio_chapter_id}">
              <i data-lucide="play" class="w-3.5 h-3.5 fill-current"></i>
              <span>Nghe ngay</span>
            </button>
            <a href="/api/audio/${a.id}/download-all" class="p-1.5 rounded-xl text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition" title="Tải toàn bộ file ZIP">
              <i data-lucide="download" class="w-4 h-4"></i>
            </a>
          </div>
        </div>
      `).join('');

      elements.containerLibAudiobooks.querySelectorAll('.btn-play-audiobook').forEach(btn => {
        btn.addEventListener('click', async () => {
          const sid = btn.dataset.id;
          const cid = parseInt(btn.dataset.chapter, 10);
          closeFavoritesModal();
          await resumeListening(sid, cid, 0);
        });
      });
    }
  }

  // 3. TAB 3: LỊCH SỬ ĐỌC (READING HISTORY)
  if (elements.containerLibReadHistory) {
    if (readHistory.length === 0) {
      elements.containerLibReadHistory.innerHTML = `
        <div class="py-12 text-center text-slate-400 space-y-2">
          <i data-lucide="book-open" class="w-10 h-10 mx-auto text-slate-400/80"></i>
          <p class="text-sm font-semibold text-slate-700">Chưa có lịch sử đọc truyện.</p>
          <p class="text-xs text-slate-500">Khi bạn mở đọc các chương trong cửa sổ Reader, lịch sử đọc sẽ được tự động ghi nhận tại đây.</p>
        </div>
      `;
    } else {
      elements.containerLibReadHistory.innerHTML = `
        <div class="flex justify-between items-center pb-1 text-xs text-slate-500">
          <span>${readHistory.length} chương đã đọc gần đây</span>
          <button id="btn-clear-read-history" class="text-rose-600 hover:text-rose-800 font-medium">Xóa lịch sử</button>
        </div>
        ${readHistory.map(r => {
          const dateStr = new Date((r.timestamp || Date.now()/1000) * 1000).toLocaleString('vi-VN', {
            hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit'
          });
          return `
            <div class="p-3 rounded-2xl bg-white/70 border border-slate-200/80 hover:border-slate-300 transition flex items-center justify-between gap-3 shadow-xs">
              <div class="min-w-0 flex-1">
                <span class="text-[10px] px-2 py-0.5 rounded-full bg-cyan-50 text-cyan-700 border border-cyan-200 truncate inline-block max-w-[200px] mb-1 font-medium">
                  ${escapeHtml(r.story_title || 'Truyện')}
                </span>
                <h4 class="font-bold text-xs sm:text-sm text-slate-900 truncate">${escapeHtml(r.chapter_title)}</h4>
                <p class="text-[10px] text-slate-400 mt-0.5">Đã đọc lúc: ${dateStr}</p>
              </div>
              <div class="shrink-0">
                <button class="btn-resume-read px-3 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-700 text-white text-xs font-semibold flex items-center space-x-1 shadow-sm transition" data-story="${r.story_id}" data-chapter="${r.chapter_id}">
                  <i data-lucide="book-open" class="w-3.5 h-3.5"></i>
                  <span>Đọc tiếp</span>
                </button>
              </div>
            </div>
          `;
        }).join('')}
      `;

      elements.containerLibReadHistory.querySelectorAll('.btn-resume-read').forEach(btn => {
        btn.addEventListener('click', () => {
          closeFavoritesModal();
          openReaderWindow(btn.dataset.story, parseInt(btn.dataset.chapter, 10));
        });
      });

      const btnClearRead = document.getElementById('btn-clear-read-history');
      if (btnClearRead) {
        btnClearRead.addEventListener('click', async () => {
          if (!confirm('Bạn có chắc chắn muốn xóa toàn bộ lịch sử đọc?')) return;
          try {
            const headers = state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : {};
            await fetch('/api/user/history/read', { method: 'DELETE', headers });
          } catch (e) {}
          state.libraryData.read_history = [];
          updateFavoritesBadges();
          renderFavoritesModal();
        });
      }
    }
  }

  // 4. TAB 4: LỊCH SỬ NGHE (LISTENING HISTORY)
  if (elements.containerLibListenHistory) {
    if (listenHistory.length === 0) {
      elements.containerLibListenHistory.innerHTML = `
        <div class="py-12 text-center text-slate-400 space-y-2">
          <i data-lucide="disc" class="w-10 h-10 mx-auto text-slate-400/80"></i>
          <p class="text-sm font-semibold text-slate-700">Chưa có lịch sử nghe sách nói.</p>
          <p class="text-xs text-slate-500">Khi bạn nghe sách nói, thời lượng và tiến trình nghe sẽ được lưu lại chính xác để tiếp tục nghe bất cứ lúc nào.</p>
        </div>
      `;
    } else {
      elements.containerLibListenHistory.innerHTML = `
        <div class="flex justify-between items-center pb-1 text-xs text-slate-500">
          <span>${listenHistory.length} chương đã nghe gần đây</span>
          <button id="btn-clear-listen-history" class="text-rose-600 hover:text-rose-800 font-medium">Xóa lịch sử</button>
        </div>
        ${listenHistory.map(l => {
          const curTime = l.current_time || 0;
          const durTime = l.duration || 1;
          const percent = Math.min(100, Math.round((curTime / durTime) * 100));
          return `
            <div class="p-3 rounded-2xl bg-white/70 border border-slate-200/80 hover:border-slate-300 transition flex items-center justify-between gap-3 shadow-xs">
              <div class="min-w-0 flex-1">
                <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 truncate inline-block max-w-[200px] mb-1 font-medium">
                  ${escapeHtml(l.story_title || 'Truyện')}
                </span>
                <h4 class="font-bold text-xs sm:text-sm text-slate-900 truncate">${escapeHtml(l.chapter_title)}</h4>
                <div class="flex items-center space-x-2 mt-1">
                  <div class="w-24 sm:w-36 h-1.5 rounded-full bg-slate-200 overflow-hidden shrink-0">
                    <div class="h-full bg-emerald-500 rounded-full" style="width: ${percent}%"></div>
                  </div>
                  <span class="text-[10px] text-slate-500 font-mono">${formatTime(curTime)} / ${formatTime(durTime)}</span>
                </div>
              </div>
              <div class="shrink-0">
                <button class="btn-resume-listen px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center space-x-1 shadow-sm transition" data-story="${l.story_id}" data-chapter="${l.chapter_id}" data-seek="${curTime}">
                  <i data-lucide="play" class="w-3.5 h-3.5 fill-current"></i>
                  <span>Tiếp tục nghe</span>
                </button>
              </div>
            </div>
          `;
        }).join('')}
      `;

      elements.containerLibListenHistory.querySelectorAll('.btn-resume-listen').forEach(btn => {
        btn.addEventListener('click', async () => {
          const sid = btn.dataset.story;
          const cid = parseInt(btn.dataset.chapter, 10);
          const seek = parseFloat(btn.dataset.seek) || 0;
          closeFavoritesModal();
          await resumeListening(sid, cid, seek);
        });
      });

      const btnClearListen = document.getElementById('btn-clear-listen-history');
      if (btnClearListen) {
        btnClearListen.addEventListener('click', async () => {
          if (!confirm('Bạn có chắc chắn muốn xóa toàn bộ lịch sử nghe?')) return;
          try {
            const headers = state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : {};
            await fetch('/api/user/history/listen', { method: 'DELETE', headers });
          } catch (e) {}
          state.libraryData.listen_history = [];
          updateFavoritesBadges();
          renderFavoritesModal();
        });
      }
    }
  }

  if (window.lucide) lucide.createIcons();
}

// ------------------- TIẾP TỤC PHÁT ÂM THANH TỪ LỊCH SỬ -------------------

async function recordCurrentListeningHistory(currentTime, duration) {
  if (!state.currentStory || !state.currentPlayingChapterId) return;
  const part = state.currentStory.parts?.find(p => p.id === state.currentPlayingChapterId);
  const chapterTitle = part ? part.title : `Chương ${state.currentPlayingChapterId}`;

  const item = {
    story_id: state.currentStory.id,
    story_title: state.currentStory.title,
    story_cover: state.currentStory.cover,
    chapter_id: state.currentPlayingChapterId,
    chapter_title: chapterTitle,
    current_time: currentTime,
    duration: duration,
    timestamp: Date.now() / 1000
  };

  // Cập nhật state cục bộ
  const hist = state.libraryData.listen_history || [];
  state.libraryData.listen_history = [
    item,
    ...hist.filter(h => !(h.story_id === item.story_id && h.chapter_id === item.chapter_id))
  ].slice(0, 50);

  // Cập nhật giao diện Đã nghe gần đây
  updateRecentlyPlayedSection();

  try {
    const headers = {
      'Content-Type': 'application/json',
      ...(state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : {})
    };
    await fetch('/api/user/history/listen', {
      method: 'POST',
      headers,
      body: JSON.stringify(item)
    });
  } catch (e) {}
}

async function resumeListening(storyId, chapterId, seekSeconds = 0) {
  if (!state.currentStory || state.currentStory.id !== storyId) {
    setLoadingFetch(true);
    try {
      const res = await fetch(`/api/story/${encodeURIComponent(storyId)}`);
      if (res.ok) {
        const story = await res.json();
        renderStory(story);
      }
    } catch (e) {
      console.warn('Lỗi load story resume:', e);
    } finally {
      setLoadingFetch(false);
    }
  }

  playChapter(chapterId, seekSeconds);
}

// ------------------- TỰ ĐỘNG TIẾP TỤC TÁC VỤ DANG DỞ (REQUIREMENT 3) -------------------

async function checkActiveDeviceTask() {
  if (!state.deviceId) return;
  try {
    const storyParam = state.currentStory ? `&story_id=${encodeURIComponent(state.currentStory.id)}` : '';
    const res = await fetch(`/api/tts/active-task?device_id=${encodeURIComponent(state.deviceId)}${storyParam}`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.has_active_task && data.task) {
      const task = data.task;
      console.log(`[Wattpad v1.8] Tiếp nối phiên chuyển đổi ${task.task_id} của thiết bị ${state.deviceId}`);
      state.activeTaskId = task.task_id;
      if (!state.currentStory || state.currentStory.id !== task.story_id) {
        await reloadStory(task.story_id);
      }
      startTaskPolling(task.task_id);
    }
  } catch (e) {
    console.debug('Lỗi kiểm tra tác vụ nền:', e);
  }
}

// ------------------- CẦU NỐI CHẠY NGẦM & NATIVE ANDROID -------------------

// Phản hồi rung xúc giác (Haptic Feedback) cho điện thoại di động
function triggerHaptic(durationMs = 25) {
  try {
    if (window.AndroidBridge && typeof window.AndroidBridge.vibrate === 'function') {
      window.AndroidBridge.vibrate(durationMs);
      return;
    }
    if ('vibrate' in navigator && typeof navigator.vibrate === 'function') {
      navigator.vibrate(durationMs);
    }
  } catch (e) {
    // Thiết bị không hỗ trợ rung
  }
}

function openAndroidServerConfig() {
  if (window.AndroidBridge && typeof window.AndroidBridge.openServerConfig === 'function') {
    try {
      window.AndroidBridge.openServerConfig();
    } catch (e) {
      console.warn('AndroidBridge openServerConfig error:', e);
    }
  }
}

function notifyAndroidBackgroundStart(title, message) {
  if (window.AndroidBridge && typeof window.AndroidBridge.startBackground === 'function') {
    try {
      window.AndroidBridge.startBackground(title, message);
    } catch (e) {
      console.warn('AndroidBridge error:', e);
    }
  }
}

function notifyAndroidBackgroundUpdate(title, message) {
  if (window.AndroidBridge && typeof window.AndroidBridge.updateBackground === 'function') {
    try {
      window.AndroidBridge.updateBackground(title, message);
    } catch (e) {
      console.warn('AndroidBridge error:', e);
    }
  }
}

function notifyAndroidBackgroundStop() {
  if (window.AndroidBridge && typeof window.AndroidBridge.stopBackground === 'function') {
    try {
      window.AndroidBridge.stopBackground();
    } catch (e) {
      console.warn('AndroidBridge error:', e);
    }
  }
}


// Tra cứu ảnh bìa truyện từ bộ nhớ đệm thư viện hoặc lịch sử
function getStoryCover(storyId, fallbackCover) {
  if (fallbackCover && fallbackCover.trim() !== '') return fallbackCover;
  if (state.currentStory && state.currentStory.id === storyId && state.currentStory.cover) {
    return state.currentStory.cover;
  }
  const libStory = (state.libraryData.stories || []).find(s => s.id === storyId);
  if (libStory && libStory.cover) return libStory.cover;
  const audioStory = (state.libraryData.audiobooks || []).find(a => a.id === storyId);
  if (audioStory && audioStory.cover) return audioStory.cover;
  const listenItem = (state.libraryData.listen_history || []).find(l => l.story_id === storyId && l.story_cover);
  if (listenItem && listenItem.story_cover) return listenItem.story_cover;
  return 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80';
}

// Cập nhật khu vực "Đã nghe gần đây" trên trang chủ theo cả lịch sử nghe và lịch sử đọc
function updateRecentlyPlayedSection() {
  const container = document.getElementById('recent-played-scroll');
  if (!container) return;

  const listenItems = (state.libraryData.listen_history || []).map(item => ({
    ...item,
    history_type: 'listen',
    sort_time: item.timestamp || 0
  }));

  const readItems = (state.libraryData.read_history || []).map(item => ({
    ...item,
    history_type: 'read',
    sort_time: item.timestamp || 0
  }));

  // Gộp cả 2 danh sách lịch sử và sắp xếp theo mốc thời gian mới nhất
  const combined = [...listenItems, ...readItems]
    .sort((a, b) => b.sort_time - a.sort_time)
    .slice(0, 12);

  if (combined.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-8 px-6 text-center text-slate-400 bg-white/50 backdrop-blur-sm rounded-2xl border border-slate-200/80 shadow-xs">
        <i data-lucide="history" class="w-8 h-8 mx-auto mb-2 text-slate-400"></i>
        <p class="text-sm font-semibold text-slate-700">Chưa có lịch sử nghe hoặc đọc gần đây</p>
        <p class="text-xs text-slate-500 mt-1">Khi bạn nghe sách nói hoặc đọc truyện, các chương truyện sẽ tự động xuất hiện tại đây để tiếp tục bất cứ lúc nào.</p>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  container.innerHTML = combined.map(item => {
    const isListen = item.history_type === 'listen';
    const coverUrl = getStoryCover(item.story_id, item.story_cover);
    
    if (isListen) {
      const curTime = item.current_time || 0;
      const durTime = item.duration || 0;
      const timeLabel = durTime > 0 
        ? `${formatTime(curTime)} / ${formatTime(durTime)}` 
        : (curTime > 0 ? formatTime(curTime) : 'Đã nghe');

      return `
        <div class="recent-album-card group cursor-pointer" data-type="listen" data-story="${escapeHtml(item.story_id)}" data-chapter="${escapeHtml(item.chapter_id)}" data-seek="${curTime}">
          <div class="recent-art-wrapper relative">
            <img src="${escapeHtml(coverUrl)}" alt="${escapeHtml(item.story_title)}" class="recent-art-img" onerror="this.src='https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80'">
            <div class="absolute top-2 left-2 z-10 pointer-events-none">
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-600/90 text-white backdrop-blur shadow-sm flex items-center gap-1">
                <i data-lucide="headphones" class="w-2.5 h-2.5"></i> Nghe
              </span>
            </div>
            <div class="recent-play-hover">
              <div class="play-hover-circle text-emerald-600">
                <i data-lucide="play" class="w-5 h-5 fill-current ml-0.5"></i>
              </div>
            </div>
          </div>
          <h4 class="recent-title" title="${escapeHtml(item.story_title)}">${escapeHtml(item.story_title)}</h4>
          <p class="recent-author text-emerald-600 font-medium truncate" title="${escapeHtml(item.chapter_title)} • ${timeLabel}">
            ${escapeHtml(item.chapter_title)} • ${timeLabel}
          </p>
        </div>
      `;
    } else {
      return `
        <div class="recent-album-card group cursor-pointer" data-type="read" data-story="${escapeHtml(item.story_id)}" data-chapter="${escapeHtml(item.chapter_id)}">
          <div class="recent-art-wrapper relative">
            <img src="${escapeHtml(coverUrl)}" alt="${escapeHtml(item.story_title)}" class="recent-art-img" onerror="this.src='https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400&q=80'">
            <div class="absolute top-2 left-2 z-10 pointer-events-none">
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-600/90 text-white backdrop-blur shadow-sm flex items-center gap-1">
                <i data-lucide="book-open" class="w-2.5 h-2.5"></i> Đọc
              </span>
            </div>
            <div class="recent-play-hover">
              <div class="play-hover-circle bg-cyan-600 text-white">
                <i data-lucide="book-open" class="w-4 h-4"></i>
              </div>
            </div>
          </div>
          <h4 class="recent-title" title="${escapeHtml(item.story_title)}">${escapeHtml(item.story_title)}</h4>
          <p class="recent-author text-cyan-600 font-medium truncate" title="${escapeHtml(item.chapter_title)} • Đang đọc">
            ${escapeHtml(item.chapter_title)} • Đang đọc
          </p>
        </div>
      `;
    }
  }).join('');

  // Gắn sự kiện chuyển tiếp đến tiếp tục nghe hoặc tiếp tục đọc
  container.querySelectorAll('.recent-album-card').forEach(el => {
    el.addEventListener('click', () => {
      const type = el.dataset.type;
      const storyId = el.dataset.story;
      const chapterId = parseInt(el.dataset.chapter, 10);
      if (type === 'listen') {
        const seek = parseFloat(el.dataset.seek) || 0;
        resumeListening(storyId, chapterId, seek);
      } else {
        openReaderWindow(storyId, chapterId);
      }
    });
  });

  if (window.lucide) lucide.createIcons();
}

async function loadStoryById(storyId, fallbackUrl) {
  setLoadingFetch(true);
  try {
    const res = await fetch(`/api/story/${encodeURIComponent(storyId)}`);
    if (res.ok) {
      const story = await res.json();
      closeFavoritesModal();
      renderStory(story);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
  } catch (e) {
    console.warn('loadStoryById cache failed, trying fallback:', e);
  }

  if (fallbackUrl || storyId) {
    closeFavoritesModal();
    await fetchStory(fallbackUrl || storyId);
  }
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

