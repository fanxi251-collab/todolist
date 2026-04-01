let currentCard = null;
let notes = [];

function toggleCard(cardName) {
    const panel = document.getElementById(`${cardName}-panel`);
    const isHidden = panel.classList.contains('hidden');
    
    document.querySelectorAll('.panel').forEach(p => p.classList.add('hidden'));
    
    if (isHidden) {
        panel.classList.remove('hidden');
        currentCard = cardName;
        
        if (cardName === 'weather') {
            if (!document.getElementById('weather-city').value) {
                document.getElementById('weather-city').value = '北京';
            }
            getWeather();
        } else if (cardName === 'notes') {
            loadNotes();
        } else if (cardName === 'today') {
            loadTodayNotes();
        } else if (cardName === 'recycle') {
            loadRecycleNotes();
        }
    } else {
        currentCard = null;
    }
}

async function getWeather() {
    const city = document.getElementById('weather-city').value.trim() || '北京';
    const resultDiv = document.getElementById('weather-result');
    resultDiv.innerHTML = '<p class="text-gray-500">加载中...</p>';
    
    try {
        const response = await fetch(`/weather?city=${encodeURIComponent(city)}&days=3`);
        if (!response.ok) throw new Error('获取天气失败');
        const data = await response.json();
        
        resultDiv.innerHTML = data.map((w, i) => `
            <div class="weather-card ${i === 0 ? 'today' : ''}">
                <div class="weather-date">${i === 0 ? '今天' : w.date}</div>
                <div class="weather-icon">${getWeatherIcon(w.weather)}</div>
                <div class="weather-temp">${w.temperature}</div>
                <div class="weather-desc">${w.weather} · ${w.wind}</div>
            </div>
        `).join('');
    } catch (error) {
        resultDiv.innerHTML = `<p class="text-red-500">${error.message}</p>`;
    }
}

function getWeatherIcon(weather) {
    const map = {
        '晴': '☀️', '多云': '⛅', '阴': '☁️', '小雨': '🌧️', '中雨': '🌧️',
        '大雨': '🌧️', '雷阵雨': '⛈️', '雪': '❄️', '雾': '🌫️', '霾': '🌫️'
    };
    for (let key in map) {
        if (weather.includes(key)) return map[key];
    }
    return '🌤️';
}

async function loadNotes() {
    const search = document.getElementById('search-notes').value;
    
    let url = '/notes?';
    if (search) url += `search=${encodeURIComponent(search)}&`;
    
    try {
        const response = await fetch(url);
        notes = await response.json();
        renderNotes();
    } catch (error) {
        console.error('加载便签失败:', error);
    }
}

function renderNotes() {
    const container = document.getElementById('notes-list');
    if (notes.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">暂无便签</p>';
        return;
    }
    
    container.innerHTML = notes.map(note => `
        <div class="note-card ${note.is_pinned ? 'pinned' : ''}">
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    ${note.is_pinned ? '<span class="text-xs bg-yellow-400 text-yellow-800 px-2 py-0.5 rounded">置顶</span>' : ''}
                    <p class="text-gray-800 whitespace-pre-wrap">${note.content || '(无内容)'}</p>
                    ${note.image_path ? `<img src="${note.image_path}" class="note-image" alt="便签图片">` : ''}
                    ${note.attachment_path ? `
                        <div class="mt-2 flex items-center gap-2">
                            <a href="${note.attachment_path}" target="_blank" class="text-blue-500 text-sm flex items-center gap-1 hover:underline">
                                📎 查看附件
                            </a>
                        </div>
                    ` : ''}
                </div>
                <span class="note-date">${note.reminder_date || '无日期'}</span>
            </div>
            <div class="note-actions">
                <button class="btn-pin ${note.is_pinned ? 'btn-unpin' : ''}" onclick="togglePin(${note.id}, ${!note.is_pinned})">
                    ${note.is_pinned ? '取消置顶' : '置顶'}
                </button>
                <button class="btn-edit" onclick="editNote(${note.id})">编辑</button>
                <button class="btn-delete" onclick="deleteNote(${note.id})">删除</button>
            </div>
        </div>
    `).join('');
}

async function loadTodayNotes() {
    try {
        const response = await fetch('/notes/today');
        const todayNotes = await response.json();
        
        const container = document.getElementById('today-list');
        if (todayNotes.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8">暂无今日待办</p>';
            return;
        }
        
        container.innerHTML = todayNotes.map(note => `
            <div class="note-card">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <p class="text-gray-800 whitespace-pre-wrap">${note.content || '(无内容)'}</p>
                        ${note.image_path ? `<img src="${note.image_path}" class="note-image" alt="便签图片">` : ''}
                        ${note.attachment_path ? `
                            <div class="mt-2 flex items-center gap-2">
                                <a href="${note.attachment_path}" target="_blank" class="text-blue-500 text-sm flex items-center gap-1 hover:underline">
                                    📎 查看附件
                                </a>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
        
        if (todayNotes.length > 0) {
            showTodayNotification(todayNotes);
        }
    } catch (error) {
        console.error('加载今日待办失败:', error);
    }
}

function showTodayNotification(notes) {
    if (!("Notification" in window)) return;
    
    if (Notification.permission === "granted") {
        new Notification("今日待办", {
            body: `您今天有 ${notes.length} 条待办事项`,
            icon: "📝"
        });
    } else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(permission => {
            if (permission === "granted") {
                new Notification("今日待办", {
                    body: `您今天有 ${notes.length} 条待办事项`,
                    icon: "📝"
                });
            }
        });
    }
}

async function loadRecycleNotes() {
    try {
        const response = await fetch('/recycle');
        const recycleNotes = await response.json();
        
        const container = document.getElementById('recycle-list');
        if (recycleNotes.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8">回收站是空的</p>';
            return;
        }
        
        container.innerHTML = recycleNotes.map(note => `
            <div class="note-card">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <p class="text-gray-800 whitespace-pre-wrap">${note.content || '(无内容)'}</p>
                        <div class="deleted-info">删除于: ${note.deleted_at || '未知时间'}</div>
                    </div>
                </div>
                <div class="note-actions">
                    <button class="btn-restore" onclick="restoreNote(${note.id})">恢复</button>
                    <button class="btn-destroy" onclick="destroyNote(${note.id})">彻底删除</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载回收站失败:', error);
    }
}

function showCreateNoteModal() {
    document.getElementById('modal-title').textContent = '新建便签';
    document.getElementById('note-id').value = '';
    document.getElementById('note-form').reset();
    document.getElementById('current-image').classList.add('hidden');
    document.getElementById('current-attachment').classList.add('hidden');
    document.getElementById('note-pinned').checked = false;
    document.getElementById('note-modal').classList.remove('hidden');
}

function editNote(id) {
    const note = notes.find(n => n.id === id);
    if (!note) return;
    
    document.getElementById('modal-title').textContent = '编辑便签';
    document.getElementById('note-id').value = note.id;
    document.getElementById('note-content').value = note.content || '';
    document.getElementById('note-date').value = note.reminder_date || '';
    document.getElementById('note-pinned').checked = note.is_pinned || false;
    
    if (note.image_path) {
        document.getElementById('current-image').classList.remove('hidden');
        document.getElementById('preview-image').src = note.image_path;
    } else {
        document.getElementById('current-image').classList.add('hidden');
    }
    
    if (note.attachment_path) {
        document.getElementById('current-attachment').classList.remove('hidden');
        document.getElementById('attachment-name').textContent = note.attachment_path.split('/').pop();
    } else {
        document.getElementById('current-attachment').classList.add('hidden');
    }
    
    document.getElementById('note-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('note-modal').classList.add('hidden');
}

function removeImage() {
    document.getElementById('current-image').classList.add('hidden');
    document.getElementById('note-image').value = '';
}

function removeAttachment() {
    document.getElementById('current-attachment').classList.add('hidden');
    document.getElementById('note-attachment').value = '';
}

async function togglePin(id, isPinned) {
    try {
        const response = await fetch(`/notes/${id}/pin?is_pinned=${isPinned}`, { method: 'PATCH' });
        if (!response.ok) throw new Error('置顶失败');
        loadNotes();
        if (currentCard === 'today') loadTodayNotes();
    } catch (error) {
        alert(error.message);
    }
}

document.getElementById('note-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('note-id').value;
    const content = document.getElementById('note-content').value;
    const reminderDate = document.getElementById('note-date').value;
    const isPinned = document.getElementById('note-pinned').checked;
    const imageFile = document.getElementById('note-image').files[0];
    const attachmentFile = document.getElementById('note-attachment').files[0];
    const removeImage = document.getElementById('current-image').classList.contains('hidden') && document.getElementById('preview-image').src;
    const removeAttachment = document.getElementById('current-attachment').classList.contains('hidden') && document.getElementById('attachment-name').textContent;
    
    const formData = new FormData();
    if (id) formData.append('content', content);
    else formData.append('content', content);
    if (reminderDate) formData.append('reminder_date', reminderDate);
    formData.append('is_pinned', isPinned);
    if (imageFile) formData.append('image', imageFile);
    if (attachmentFile) formData.append('attachment', attachmentFile);
    if (removeImage) formData.append('remove_image', 'true');
    if (removeAttachment) formData.append('remove_attachment', 'true');
    
    try {
        const url = id ? `/notes/${id}` : '/notes';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            body: formData
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || '保存失败');
        }
        
        closeModal();
        loadNotes();
        if (currentCard === 'today') loadTodayNotes();
    } catch (error) {
        alert(error.message);
    }
});

async function deleteNote(id) {
    if (!confirm('确定要删除这条便签吗？')) return;
    
    try {
        const response = await fetch(`/notes/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('删除失败');
        loadNotes();
        if (currentCard === 'today') loadTodayNotes();
    } catch (error) {
        alert(error.message);
    }
}

async function restoreNote(id) {
    try {
        const response = await fetch(`/recycle/${id}/restore`, { method: 'POST' });
        if (!response.ok) throw new Error('恢复失败');
        loadRecycleNotes();
    } catch (error) {
        alert(error.message);
    }
}

async function destroyNote(id) {
    if (!confirm('确定要彻底删除这条便签吗？此操作不可恢复！')) return;
    
    try {
        const response = await fetch(`/recycle/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('删除失败');
        loadRecycleNotes();
    } catch (error) {
        alert(error.message);
    }
}

async function cleanupOldNotes() {
    if (!confirm('确定要清理7天前的便签吗？')) return;
    
    try {
        const response = await fetch('/recycle/cleanup?days=7', { method: 'POST' });
        const result = await response.json();
        alert(result.message);
        loadRecycleNotes();
    } catch (error) {
        alert(error.message);
    }
}

async function exportNotes(format) {
    try {
        const response = await fetch(`/notes/export?format=${format}`, { method: 'POST' });
        const data = await response.json();
        
        if (format === 'json') {
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `todolist_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
        }
    } catch (error) {
        alert('导出失败: ' + error.message);
    }
}

document.getElementById('search-notes').addEventListener('input', debounce(loadNotes, 300));

function debounce(fn, delay) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

window.onload = () => {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('note-date').min = today;
    
    if (Notification.permission === "default") {
        Notification.requestPermission();
    }
};
