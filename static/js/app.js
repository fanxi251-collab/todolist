let currentCard = null;
let tags = [];
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
            loadTags();
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
    const tagId = document.getElementById('filter-tag').value;
    
    let url = '/notes?';
    if (search) url += `search=${encodeURIComponent(search)}&`;
    if (tagId) url += `tag_id=${tagId}&`;
    
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
        <div class="note-card">
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <p class="text-gray-800 whitespace-pre-wrap">${note.content || '(无内容)'}</p>
                    ${note.image_path ? `<img src="${note.image_path}" class="note-image" alt="便签图片">` : ''}
                    <div class="note-tags">
                        ${note.tags.map(t => `<span class="tag" style="background-color: ${t.color}">${t.name}</span>`).join('')}
                    </div>
                </div>
                <span class="note-date">${note.reminder_date || '无日期'}</span>
            </div>
            <div class="note-actions">
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
                        <div class="note-tags">
                            ${note.tags.map(t => `<span class="tag" style="background-color: ${t.color}">${t.name}</span>`).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载今日待办失败:', error);
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

async function loadTags() {
    try {
        const response = await fetch('/tags');
        tags = await response.json();
        
        const filterSelect = document.getElementById('filter-tag');
        filterSelect.innerHTML = '<option value="">全部标签</option>' + 
            tags.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
        
        renderTagSelect();
    } catch (error) {
        console.error('加载标签失败:', error);
    }
}

function renderTagSelect() {
    const container = document.getElementById('tag-select');
    container.innerHTML = tags.map(tag => `
        <label class="tag-checkbox" style="background-color: ${tag.color}20; color: ${tag.color}" 
               data-id="${tag.id}">
            <input type="checkbox" value="${tag.id}" class="hidden">${tag.name}
        </label>
    `).join('') + `
        <button class="btn-manage-tags" onclick="showTagModal()">管理标签</button>
    `;
    
    document.querySelectorAll('.tag-checkbox').forEach(el => {
        el.addEventListener('click', function() {
            this.classList.toggle('selected');
            this.querySelector('input').checked = this.classList.contains('selected');
        });
    });
}

function showCreateNoteModal() {
    document.getElementById('modal-title').textContent = '新建便签';
    document.getElementById('note-id').value = '';
    document.getElementById('note-form').reset();
    document.getElementById('current-image').classList.add('hidden');
    document.getElementById('note-modal').classList.remove('hidden');
    
    loadTags();
}

function editNote(id) {
    const note = notes.find(n => n.id === id);
    if (!note) return;
    
    document.getElementById('modal-title').textContent = '编辑便签';
    document.getElementById('note-id').value = note.id;
    document.getElementById('note-content').value = note.content || '';
    document.getElementById('note-date').value = note.reminder_date || '';
    
    if (note.image_path) {
        document.getElementById('current-image').classList.remove('hidden');
        document.getElementById('preview-image').src = note.image_path;
    } else {
        document.getElementById('current-image').classList.add('hidden');
    }
    
    loadTags();
    
    setTimeout(() => {
        document.querySelectorAll('.tag-checkbox').forEach(el => {
            const tagId = parseInt(el.dataset.id);
            const isSelected = note.tags.some(t => t.id === tagId);
            if (isSelected) {
                el.classList.add('selected');
                el.querySelector('input').checked = true;
            } else {
                el.classList.remove('selected');
                el.querySelector('input').checked = false;
            }
        });
    }, 100);
    
    document.getElementById('note-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('note-modal').classList.add('hidden');
}

function removeImage() {
    document.getElementById('current-image').classList.add('hidden');
    document.getElementById('note-image').value = '';
}

document.getElementById('note-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('note-id').value;
    const content = document.getElementById('note-content').value;
    const reminderDate = document.getElementById('note-date').value;
    const imageFile = document.getElementById('note-image').files[0];
    
    const tagCheckboxes = document.querySelectorAll('.tag-checkbox input:checked');
    const tagIds = Array.from(tagCheckboxes).map(cb => cb.value).join(',');
    
    const formData = new FormData();
    if (id) formData.append('content', content);
    else formData.append('content', content);
    if (reminderDate) formData.append('reminder_date', reminderDate);
    if (tagIds) formData.append('tag_ids', tagIds);
    if (imageFile) formData.append('image', imageFile);
    
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

function showTagModal() {
    renderTagList();
    document.getElementById('tag-modal').classList.remove('hidden');
}

function closeTagModal() {
    document.getElementById('tag-modal').classList.add('hidden');
}

function renderTagList() {
    const container = document.getElementById('tag-list');
    container.innerHTML = tags.map(tag => `
        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span class="flex items-center gap-2">
                <span class="w-4 h-4 rounded" style="background-color: ${tag.color}"></span>
                ${tag.name}
            </span>
            <button class="text-red-500 text-sm" onclick="deleteTag(${tag.id})">删除</button>
        </div>
    `).join('');
}

async function createTag() {
    const name = document.getElementById('new-tag-name').value.trim();
    const color = document.getElementById('new-tag-color').value;
    
    if (!name) {
        alert('请输入标签名称');
        return;
    }
    
    try {
        const response = await fetch('/tags', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, color })
        });
        
        if (!response.ok) throw new Error('创建标签失败');
        
        document.getElementById('new-tag-name').value = '';
        loadTags();
        renderTagList();
    } catch (error) {
        alert(error.message);
    }
}

async function deleteTag(id) {
    if (!confirm('确定要删除这个标签吗？')) return;
    
    try {
        const response = await fetch(`/tags/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('删除标签失败');
        loadTags();
        renderTagList();
    } catch (error) {
        alert(error.message);
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
};
