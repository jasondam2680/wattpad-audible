// Wattpad AI Audiobook - Reader Window Script

const readerState = {
  storyId: null,
  chapterId: null,
  chapterData: null,
  fontSize: 18,
  fontFamily: 'sans', // 'sans' | 'serif'
  theme: 'dark', // 'dark' | 'sepia' | 'light'
  isPlayingAudio: false
};

const broadcast = typeof BroadcastChannel !== 'undefined' ? new BroadcastChannel('wattpad_channel') : null;

// DOM Elements
const el = {
  btnReaderClose: document.getElementById('btn-reader-close'),
  readerStoryTitle: document.getElementById('reader-story-title'),
  readerChapterTitleTop: document.getElementById('reader-chapter-title-top'),
  btnTopPrevChapter: document.getElementById('btn-top-prev-chapter'),
  selectTopChapter: document.getElementById('select-top-chapter'),
  btnTopNextChapter: document.getElementById('btn-top-next-chapter'),
  btnToggleFavChapter: document.getElementById('btn-toggle-fav-chapter'),
  iconFavChapter: document.getElementById('icon-fav-chapter'),
  readerAudioBadgeContainer: document.getElementById('reader-audio-badge-container'),
  btnToggleSettings: document.getElementById('btn-toggle-settings'),
  readerSettingsPanel: document.getElementById('reader-settings-panel'),
  btnFontDec: document.getElementById('btn-font-dec'),
  btnFontInc: document.getElementById('btn-font-inc'),
  labelFontSize: document.getElementById('label-font-size'),
  btnFontSans: document.getElementById('btn-font-sans'),
  btnFontSerif: document.getElementById('btn-font-serif'),
  btnThemeDark: document.getElementById('btn-theme-dark'),
  btnThemeSepia: document.getElementById('btn-theme-sepia'),
  btnThemeLight: document.getElementById('btn-theme-light'),

  readerLoadingState: document.getElementById('reader-loading-state'),
  readerErrorState: document.getElementById('reader-error-state'),
  readerErrorMsg: document.getElementById('reader-error-msg'),
  btnReaderRetry: document.getElementById('btn-reader-retry'),

  readerContentCard: document.getElementById('reader-content-card'),
  readerMetaStoryTitle: document.getElementById('reader-meta-story-title'),
  readerWordCount: document.getElementById('reader-word-count'),
  readerReadTime: document.getElementById('reader-read-time'),
  readerChapterTitle: document.getElementById('reader-chapter-title'),
  readerInlineAudioBox: document.getElementById('reader-inline-audio-box'),
  readerBodyText: document.getElementById('reader-body-text'),

  btnBottomPrev: document.getElementById('btn-bottom-prev'),
  btnBottomPromptAudio: document.getElementById('btn-bottom-prompt-audio'),
  btnBottomAudioLabel: document.getElementById('btn-bottom-audio-label'),
  btnBottomNext: document.getElementById('btn-bottom-next'),

  readerAudioPlayer: document.getElementById('reader-audio-player')
};

// ------------------- KHỞI TẠO -------------------

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();

  // Đọc tham số URL
  const params = new URLSearchParams(window.location.search);
  readerState.storyId = params.get('story_id');
  readerState.chapterId = parseInt(params.get('chapter_id'), 10);

  if (!readerState.storyId || isNaN(readerState.chapterId)) {
    showError('Không tìm thấy thông tin truyện hoặc chương cần đọc.');
    return;
  }

  // Tải cài đặt giao diện đã lưu
  loadPreferences();

  // Gắn sự kiện
  setupEventListeners();

  // Tải nội dung chương
  loadChapter(readerState.storyId, readerState.chapterId);
  requestScreenWakeLock();
});

// ------------------- SCREEN WAKE LOCK (GIỮ MÀN HÌNH SÁNG KHI ĐỌC) -------------------
let wakeLockSentinel = null;

async function requestScreenWakeLock() {
  // 1. Android Native Bridge
  if (window.AndroidBridge && typeof window.AndroidBridge.setKeepScreenOn === 'function') {
    try {
      window.AndroidBridge.setKeepScreenOn(true);
    } catch (e) {
      console.warn('AndroidBridge keepScreenOn error:', e);
    }
  }

  // 2. Standard Web Screen Wake Lock API
  if ('wakeLock' in navigator && document.visibilityState === 'visible') {
    try {
      wakeLockSentinel = await navigator.wakeLock.request('screen');
      console.log('[Reader] Screen Wake Lock đã kích hoạt - Màn hình sẽ không tắt khi đọc');
      wakeLockSentinel.addEventListener('release', () => {
        console.log('[Reader] Screen Wake Lock đã nhả');
      });
    } catch (err) {
      console.warn('[Reader] Không thể kích hoạt Screen Wake Lock:', err);
    }
  }
}

function releaseScreenWakeLock() {
  if (window.AndroidBridge && typeof window.AndroidBridge.setKeepScreenOn === 'function') {
    try {
      window.AndroidBridge.setKeepScreenOn(false);
    } catch (e) {
      console.warn('AndroidBridge keepScreenOn error:', e);
    }
  }
  if (wakeLockSentinel) {
    try {
      wakeLockSentinel.release();
    } catch (e) {}
    wakeLockSentinel = null;
  }
}

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && !wakeLockSentinel) {
    requestScreenWakeLock();
  }
});

// Gửi thông báo khi người dùng đóng cửa sổ đọc
function notifyReaderClosed() {
  releaseScreenWakeLock();
  if (broadcast && readerState.chapterData) {
    try {
      broadcast.postMessage({
        type: 'READER_CLOSED',
        storyId: readerState.storyId,
        chapterId: readerState.chapterId,
        chapterTitle: readerState.chapterData.chapter_title || '',
        isConverted: Boolean(readerState.chapterData.is_converted)
      });
    } catch (e) {
      console.error('Error posting reader closed message:', e);
    }
  }
}

window.addEventListener('beforeunload', notifyReaderClosed);
window.addEventListener('pagehide', notifyReaderClosed);


// ------------------- TẢI NỘI DUNG CHƯƠNG -------------------

async function loadChapter(storyId, chapterId) {
  setLoading(true);

  try {
    const res = await fetch(`/api/story/${encodeURIComponent(storyId)}/chapter/${chapterId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Không thể tải nội dung chương.');
    }

    const data = await res.json();
    readerState.chapterData = data;
    readerState.chapterId = chapterId;

    // Cập nhật URL trình duyệt (không reload)
    const newUrl = `/reader.html?story_id=${encodeURIComponent(storyId)}&chapter_id=${chapterId}`;
    window.history.replaceState({ storyId, chapterId }, '', newUrl);

    // Ghi nhận lịch sử đọc truyện theo người dùng
    saveReadingHistory(storyId, data.story_title, data.story_cover, data.chapter_id, data.chapter_title);

    renderChapter(data);
  } catch (err) {
    showError(err.message || 'Lỗi kết nối khi tải nội dung chương.');
  } finally {
    setLoading(false);
  }
}

async function saveReadingHistory(storyId, storyTitle, storyCover, chapterId, chapterTitle) {
  const token = localStorage.getItem('wattpad_auth_token');
  try {
    await fetch('/api/user/history/read', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({
        story_id: storyId,
        story_title: storyTitle || 'Truyện Wattpad',
        story_cover: storyCover || null,
        chapter_id: chapterId,
        chapter_title: chapterTitle || `Chương ${chapterId}`,
        timestamp: Date.now() / 1000,
        progress_percent: 0
      })
    });
  } catch (e) {
    console.debug('Không thể lưu lịch sử đọc:', e);
  }

  if (broadcast) {
    try {
      broadcast.postMessage({
        type: 'READ_HISTORY_UPDATED',
        storyId,
        storyTitle,
        chapterId,
        chapterTitle
      });
    } catch (e) {}
  }
}


function renderChapter(data) {
  document.title = `${data.chapter_title} - ${data.story_title || 'Wattpad'}`;

  // Cập nhật tiêu đề
  el.readerStoryTitle.textContent = data.story_title || 'Wattpad Story';
  el.readerChapterTitleTop.textContent = data.chapter_title || `Chương ${data.chapter_id}`;
  el.readerMetaStoryTitle.innerHTML = `<i data-lucide="book" class="w-3.5 h-3.5"></i><span>${data.story_title || 'Wattpad Story'}</span>`;
  el.readerChapterTitle.textContent = data.chapter_title || `Chương ${data.chapter_id}`;

  // Đếm từ và thời gian đọc
  const words = data.text ? data.text.trim().split(/\s+/).filter(Boolean).length : 0;
  const readMins = Math.max(1, Math.ceil(words / 220));
  el.readerWordCount.innerHTML = `<i data-lucide="file-text" class="w-3.5 h-3.5 text-indigo-400"></i><span>${words.toLocaleString('vi-VN')} từ</span>`;
  el.readerReadTime.innerHTML = `<i data-lucide="clock" class="w-3.5 h-3.5 text-pink-400"></i><span>~${readMins} phút đọc</span>`;

  // Format các đoạn văn bản
  if (!data.text || data.text.trim().length === 0) {
    el.readerBodyText.innerHTML = `
      <div class="py-12 text-center text-slate-400">
        <p>Nội dung chương này trống hoặc đang được bảo vệ bởi Wattpad.</p>
      </div>
    `;
  } else {
    const rawParagraphs = data.text.split(/\n\s*\n|\r\n\s*\r\n/);
    const formattedHtml = rawParagraphs
      .map(p => p.trim())
      .filter(p => p.length > 0)
      .map(p => `<p class="paragraph-item">${escapeHtml(p).replace(/\n/g, '<br>')}</p>`)
      .join('');
    el.readerBodyText.innerHTML = formattedHtml;
  }

  // Danh sách dropdown chuyển chương
  if (Array.isArray(data.parts) && data.parts.length > 0) {
    el.selectTopChapter.innerHTML = data.parts.map(p => 
      `<option value="${p.id}" ${p.id === data.chapter_id ? 'selected' : ''}>${escapeHtml(p.title || `Chương ${p.id}`)}</option>`
    ).join('');
    el.selectTopChapter.classList.remove('hidden');
  }

  // Cập nhật nút Trước / Sau
  el.btnTopPrevChapter.disabled = !data.prev_chapter_id;
  el.btnBottomPrev.disabled = !data.prev_chapter_id;
  el.btnTopNextChapter.disabled = !data.next_chapter_id;
  el.btnBottomNext.disabled = !data.next_chapter_id;

  // Trạng thái audio & nút thao tác
  updateAudioControls(data);

  // Trạng thái yêu thích
  updateFavoriteButton();

  // Cuộn lên đầu trang đọc
  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (window.lucide) lucide.createIcons();
}

function updateAudioControls(data) {
  // Dọn dẹp audio player nếu đang phát chương cũ
  if (readerState.isPlayingAudio) {
    el.readerAudioPlayer.pause();
    readerState.isPlayingAudio = false;
  }

  if (data.is_converted) {
    // Đã có audio: Nút nghe nhanh trên topbar và trong thẻ
    el.readerAudioBadgeContainer.innerHTML = `
      <button id="btn-reader-play-audio" class="px-3 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-400/40 text-emerald-300 text-xs font-semibold flex items-center space-x-1.5 transition">
        <i data-lucide="play" id="icon-reader-play" class="w-3.5 h-3.5 fill-current"></i>
        <span id="label-reader-play">Nghe Audio</span>
      </button>
    `;

    el.readerInlineAudioBox.innerHTML = `
      <div class="inline-flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-400/30 text-emerald-300 text-xs font-medium">
        <i data-lucide="mic" class="w-4 h-4 text-emerald-400"></i>
        <span>Chương này đã có sẵn bản Sách nói AI (${escapeHtml(data.audio_voice || 'Thái Sơn')})</span>
      </div>
    `;

    el.btnBottomPromptAudio.className = 'w-full sm:w-auto px-6 py-3 rounded-2xl bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-400/40 text-emerald-200 text-xs font-bold flex items-center justify-center space-x-2 transition';
    el.btnBottomPromptAudio.innerHTML = `
      <i data-lucide="headphones" class="w-4 h-4"></i>
      <span>Nghe bản Audio chương này</span>
    `;

    // Gắn sự kiện play/pause
    const playBtn = document.getElementById('btn-reader-play-audio');
    if (playBtn) {
      playBtn.addEventListener('click', toggleReaderAudio);
    }
    el.btnBottomPromptAudio.onclick = toggleReaderAudio;

  } else {
    // Chưa có audio: Nút yêu cầu tạo
    el.readerAudioBadgeContainer.innerHTML = `
      <button id="btn-reader-req-audio" class="px-2.5 py-1.5 rounded-xl bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-400/30 text-indigo-200 text-xs font-medium flex items-center space-x-1 transition" title="Tạo sách nói cho chương này">
        <i data-lucide="sparkles" class="w-3.5 h-3.5 text-amber-300"></i>
        <span class="hidden sm:inline">Tạo Audio</span>
      </button>
    `;

    el.readerInlineAudioBox.innerHTML = `
      <div class="inline-flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-white/[0.04] border border-white/10 text-slate-300 text-xs">
        <i data-lucide="info" class="w-3.5 h-3.5 text-cyan-400"></i>
        <span>Chương này chưa được chuyển đổi thành sách nói.</span>
      </div>
    `;

    el.btnBottomPromptAudio.className = 'w-full sm:w-auto px-6 py-3 rounded-2xl liquid-btn-primary text-xs font-bold text-white flex items-center justify-center space-x-2 shadow-lg shadow-indigo-500/30 transition';
    el.btnBottomPromptAudio.innerHTML = `
      <i data-lucide="sparkles" class="w-4 h-4 text-amber-300"></i>
      <span>Tạo Sách nói AI cho chương này</span>
    `;

    const reqBtn = document.getElementById('btn-reader-req-audio');
    if (reqBtn) {
      reqBtn.addEventListener('click', promptConvertCurrentChapter);
    }
    el.btnBottomPromptAudio.onclick = promptConvertCurrentChapter;
  }
}

function toggleReaderAudio() {
  if (!readerState.chapterData || !readerState.chapterData.is_converted) return;

  if (readerState.isPlayingAudio) {
    el.readerAudioPlayer.pause();
    readerState.isPlayingAudio = false;
    updateReaderAudioPlayIcon(false);
  } else {
    el.readerAudioPlayer.src = `/api/audio/${encodeURIComponent(readerState.storyId)}/${readerState.chapterId}`;
    el.readerAudioPlayer.play()
      .then(() => {
        readerState.isPlayingAudio = true;
        updateReaderAudioPlayIcon(true);
      })
      .catch(err => {
        console.error('Audio play error:', err);
        alert('Không thể phát file audio này.');
      });
  }
}

function updateReaderAudioPlayIcon(isPlaying) {
  const icon = document.getElementById('icon-reader-play');
  const label = document.getElementById('label-reader-play');
  if (icon && label) {
    if (isPlaying) {
      icon.setAttribute('data-lucide', 'pause');
      label.textContent = 'Tạm dừng';
    } else {
      icon.setAttribute('data-lucide', 'play');
      label.textContent = 'Nghe Audio';
    }
    if (window.lucide) lucide.createIcons();
  }
}

// Báo về cửa sổ chính yêu cầu tạo audio cho chương này
function promptConvertCurrentChapter() {
  if (broadcast && readerState.chapterData) {
    broadcast.postMessage({
      type: 'REQUEST_CONVERT_CHAPTER',
      storyId: readerState.storyId,
      chapterId: readerState.chapterId,
      chapterTitle: readerState.chapterData.chapter_title || ''
    });
  }
  // Đóng cửa sổ đọc và chuyển tiêu điểm về tab chính
  window.close();
}

// ------------------- YÊU THÍCH CHƯƠNG -------------------

function getFavoriteChapters() {
  try {
    return JSON.parse(localStorage.getItem('wattpad_favorite_chapters') || '[]');
  } catch (e) {
    return [];
  }
}

function isChapterFavorite(storyId, chapterId) {
  const favs = getFavoriteChapters();
  return favs.some(f => f.storyId === storyId && f.chapterId === chapterId);
}

function toggleFavoriteChapter() {
  if (!readerState.chapterData) return;

  let favs = getFavoriteChapters();
  const existsIndex = favs.findIndex(f => f.storyId === readerState.storyId && f.chapterId === readerState.chapterId);

  if (existsIndex >= 0) {
    favs.splice(existsIndex, 1);
  } else {
    favs.unshift({
      storyId: readerState.storyId,
      storyTitle: readerState.chapterData.story_title || 'Wattpad Story',
      chapterId: readerState.chapterId,
      chapterTitle: readerState.chapterData.chapter_title || `Chương ${readerState.chapterId}`,
      addedAt: Date.now()
    });
  }

  localStorage.setItem('wattpad_favorite_chapters', JSON.stringify(favs));
  updateFavoriteButton();

  // Báo qua BroadcastChannel để trang chính cập nhật
  if (broadcast) {
    broadcast.postMessage({
      type: 'FAVORITES_UPDATED',
      storyId: readerState.storyId,
      chapterId: readerState.chapterId
    });
  }
}

function updateFavoriteButton() {
  const isFav = isChapterFavorite(readerState.storyId, readerState.chapterId);
  if (isFav) {
    el.btnToggleFavChapter.className = 'p-2 rounded-xl bg-rose-500/20 border border-rose-400/50 text-rose-400 shadow-md shadow-rose-500/20 transition';
    el.btnToggleFavChapter.title = 'Bỏ yêu thích chương';
    el.iconFavChapter.setAttribute('data-lucide', 'heart');
    el.iconFavChapter.classList.add('fill-current');
  } else {
    el.btnToggleFavChapter.className = 'p-2 rounded-xl liquid-btn-secondary text-slate-300 hover:text-rose-400 transition';
    el.btnToggleFavChapter.title = 'Đánh dấu chương yêu thích';
    el.iconFavChapter.setAttribute('data-lucide', 'heart');
    el.iconFavChapter.classList.remove('fill-current');
  }
  if (window.lucide) lucide.createIcons();
}

// ------------------- TÙY BIẾN ĐỌC (FONT, SIZE, THEME) -------------------

function loadPreferences() {
  readerState.fontSize = parseInt(localStorage.getItem('reader_font_size') || '18', 10);
  readerState.fontFamily = localStorage.getItem('reader_font_family') || 'sans';
  readerState.theme = localStorage.getItem('reader_theme') || 'dark';

  applyTypography();
  applyTheme(readerState.theme);
}

function applyTypography() {
  el.labelFontSize.textContent = `${readerState.fontSize}px`;
  el.readerBodyText.style.fontSize = `${readerState.fontSize}px`;
  el.readerBodyText.style.lineHeight = `${readerState.fontSize >= 20 ? 1.85 : 1.75}`;

  if (readerState.fontFamily === 'serif') {
    el.readerBodyText.classList.remove('font-sans');
    el.readerBodyText.classList.add('font-serif');
    el.btnFontSerif.classList.add('active-font-opt');
    el.btnFontSans.classList.remove('active-font-opt');
  } else {
    el.readerBodyText.classList.remove('font-serif');
    el.readerBodyText.classList.add('font-sans');
    el.btnFontSans.classList.add('active-font-opt');
    el.btnFontSerif.classList.remove('active-font-opt');
  }
}

function applyTheme(theme) {
  readerState.theme = theme;
  localStorage.setItem('reader_theme', theme);
  document.documentElement.setAttribute('data-theme', theme);

  const body = document.body;
  body.classList.remove('theme-dark', 'theme-sepia', 'theme-light');
  body.classList.add(`theme-${theme}`);

  // Highlight active theme button
  [el.btnThemeDark, el.btnThemeSepia, el.btnThemeLight].forEach(btn => btn?.classList.remove('ring-2', 'ring-indigo-400'));
  if (theme === 'dark') el.btnThemeDark?.classList.add('ring-2', 'ring-indigo-400');
  if (theme === 'sepia') el.btnThemeSepia?.classList.add('ring-2', 'ring-indigo-400');
  if (theme === 'light') el.btnThemeLight?.classList.add('ring-2', 'ring-indigo-400');
}

// ------------------- GẮN SỰ KIỆN -------------------

function setupEventListeners() {
  // Nút đóng cửa sổ
  el.btnReaderClose.addEventListener('click', () => {
    notifyReaderClosed();
    window.close();
  });

  // Chuyển chương bằng dropdown
  el.selectTopChapter.addEventListener('change', (e) => {
    const nextId = parseInt(e.target.value, 10);
    if (nextId && nextId !== readerState.chapterId) {
      loadChapter(readerState.storyId, nextId);
    }
  });

  // Nút chương trước/sau
  const goPrev = () => {
    if (readerState.chapterData?.prev_chapter_id) {
      loadChapter(readerState.storyId, readerState.chapterData.prev_chapter_id);
    }
  };
  const goNext = () => {
    if (readerState.chapterData?.next_chapter_id) {
      loadChapter(readerState.storyId, readerState.chapterData.next_chapter_id);
    }
  };

  el.btnTopPrevChapter.addEventListener('click', goPrev);
  el.btnBottomPrev.addEventListener('click', goPrev);
  el.btnTopNextChapter.addEventListener('click', goNext);
  el.btnBottomNext.addEventListener('click', goNext);

  // Yêu thích
  el.btnToggleFavChapter.addEventListener('click', toggleFavoriteChapter);

  // Mở / Đóng panel cài đặt
  el.btnToggleSettings.addEventListener('click', (e) => {
    e.stopPropagation();
    el.readerSettingsPanel.classList.toggle('hidden');
  });
  document.addEventListener('click', (e) => {
    if (!el.readerSettingsPanel.contains(e.target) && !el.btnToggleSettings.contains(e.target)) {
      el.readerSettingsPanel.classList.add('hidden');
    }
  });

  // Tăng giảm font
  el.btnFontDec.addEventListener('click', () => {
    if (readerState.fontSize > 14) {
      readerState.fontSize -= 2;
      localStorage.setItem('reader_font_size', readerState.fontSize);
      applyTypography();
    }
  });
  el.btnFontInc.addEventListener('click', () => {
    if (readerState.fontSize < 30) {
      readerState.fontSize += 2;
      localStorage.setItem('reader_font_size', readerState.fontSize);
      applyTypography();
    }
  });

  // Chọn font sans/serif
  el.btnFontSans.addEventListener('click', () => {
    readerState.fontFamily = 'sans';
    localStorage.setItem('reader_font_family', 'sans');
    applyTypography();
  });
  el.btnFontSerif.addEventListener('click', () => {
    readerState.fontFamily = 'serif';
    localStorage.setItem('reader_font_family', 'serif');
    applyTypography();
  });

  // Chọn Theme
  el.btnThemeDark.addEventListener('click', () => applyTheme('dark'));
  el.btnThemeSepia.addEventListener('click', () => applyTheme('sepia'));
  el.btnThemeLight.addEventListener('click', () => applyTheme('light'));

  // Nút thử lại khi lỗi
  el.btnReaderRetry.addEventListener('click', () => {
    loadChapter(readerState.storyId, readerState.chapterId);
  });

  // Sự kiện kết thúc phát audio
  el.readerAudioPlayer.addEventListener('ended', () => {
    readerState.isPlayingAudio = false;
    updateReaderAudioPlayIcon(false);
  });
}

function setLoading(isLoading) {
  if (isLoading) {
    el.readerLoadingState.classList.remove('hidden');
    el.readerContentCard.classList.add('hidden');
    el.readerErrorState.classList.add('hidden');
  } else {
    el.readerLoadingState.classList.add('hidden');
    el.readerContentCard.classList.remove('hidden');
  }
}

function showError(msg) {
  el.readerLoadingState.classList.add('hidden');
  el.readerContentCard.classList.add('hidden');
  el.readerErrorState.classList.remove('hidden');
  el.readerErrorMsg.textContent = msg;
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}
