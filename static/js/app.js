let currentCard = null;
let notes = [];

// ==================== 账目模块 ====================
let accountCategories = { expense: [], income: [] };
let currentAccountTab = 'expense';

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
        } else if (cardName === 'account') {
            loadAccountData();
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
    
    // 账目日期默认本月
    const firstDay = new Date();
    firstDay.setDate(1);
    document.getElementById('account-start-date').value = firstDay.toISOString().split('T')[0];
    document.getElementById('account-end-date').value = today;
    
    // 默认显示对话
    showChat();
    
    if (Notification.permission === "default") {
        Notification.requestPermission();
    }
};

// ==================== 账目模块 ====================

async function loadAccountData() {
    const startDate = document.getElementById('account-start-date').value;
    const endDate = document.getElementById('account-end-date').value;
    
    try {
        // 加载类别
        const catRes = await fetch('/account/categories');
        const categories = await catRes.json();
        accountCategories = { expense: [], income: [] };
        categories.forEach(c => {
            accountCategories[c.type].push(c);
        });
        
        // 加载汇总
        const sumRes = await fetch(`/account/summary?start_date=${startDate}&end_date=${endDate}`);
        const summary = await sumRes.json();
        
        document.getElementById('summary-income').textContent = `¥${(summary.total_income / 100).toFixed(2)}`;
        document.getElementById('summary-expense').textContent = `¥${(summary.total_expense / 100).toFixed(2)}`;
        document.getElementById('summary-balance').textContent = `¥${(summary.balance / 100).toFixed(2)}`;
        
        // 加载支出列表
        const expRes = await fetch(`/account/expenses?start_date=${startDate}&end_date=${endDate}`);
        const expenses = await expRes.json();
        renderAccountItems(expenses, 'expense');
        
        // 加载收入列表
        const incRes = await fetch(`/account/incomes?start_date=${startDate}&end_date=${endDate}`);
        const incomes = await incRes.json();
        renderAccountItems(incomes, 'income');
        
        // 渲染图表
        renderChart(summary);
        
    } catch (error) {
        console.error('加载账目数据失败:', error);
    }
}

function renderAccountItems(items, type) {
    const container = document.getElementById(`${type}-items`);
    if (items.length === 0) {
        container.innerHTML = `<p class="text-gray-500 text-center py-4">暂无${type === 'expense' ? '支出' : '收入'}记录</p>`;
        return;
    }
    
    container.innerHTML = items.map(item => `
        <div class="account-item">
            <div class="flex items-center">
                <div class="account-item-icon" style="background: ${item.category?.color || '#9CA3AF'}20;">
                    ${item.category?.icon || '💰'}
                </div>
                <div class="account-item-info">
                    <div class="account-item-category">${item.category?.name || '未分类'}</div>
                    <div class="account-item-desc">${item.description || '-'}</div>
                    <div class="account-item-date">${item.date}</div>
                </div>
            </div>
            <div class="text-right">
                <div class="account-item-amount ${type}">${type === 'expense' ? '-' : '+'}¥${(item.amount / 100).toFixed(2)}</div>
                <div class="account-item-actions">
                    <button class="btn-edit" onclick="editAccount(${item.id}, '${type}')">编辑</button>
                    <button class="btn-delete" onclick="deleteAccount(${item.id}, '${type}')">删除</button>
                </div>
            </div>
        </div>
    `).join('');
}

function renderChart(summary) {
    // 支出分布
    const expContainer = document.getElementById('expense-categories');
    if (summary.expense_by_category.length === 0) {
        expContainer.innerHTML = '<p class="text-gray-500 text-sm">暂无数据</p>';
    } else {
        expContainer.innerHTML = summary.expense_by_category.map(cat => `
            <div class="category-pill" style="background: ${cat.color};">
                ${cat.name} <span>¥${(cat.amount / 100).toFixed(2)}</span>
            </div>
        `).join('');
    }
    
    // 收入分布
    const incContainer = document.getElementById('income-categories');
    if (summary.income_by_category.length === 0) {
        incContainer.innerHTML = '<p class="text-gray-500 text-sm">暂无数据</p>';
    } else {
        incContainer.innerHTML = summary.income_by_category.map(cat => `
            <div class="category-pill" style="background: ${cat.color};">
                ${cat.name} <span>¥${(cat.amount / 100).toFixed(2)}</span>
            </div>
        `).join('');
    }
}

function switchAccountTab(tab) {
    currentAccountTab = tab;
    document.querySelectorAll('.account-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.account-tab[data-tab="${tab}"]`).classList.add('active');
    
    document.querySelectorAll('.account-tab-content').forEach(c => c.classList.add('hidden'));
    document.getElementById(`${tab}-list`).classList.remove('hidden');
    if (tab === 'chart') {
        document.getElementById('chart-content').classList.remove('hidden');
    }
}

function showAccountModal(type, id = null) {
    document.getElementById('account-modal-title').textContent = id 
        ? (type === 'expense' ? '编辑支出' : '编辑收入') 
        : (type === 'expense' ? '新建支出' : '新建收入');
    document.getElementById('account-type').value = type;
    document.getElementById('account-id').value = id || '';
    document.getElementById('account-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('account-amount').value = '';
    document.getElementById('account-description').value = '';
    
    // 加载类别
    const select = document.getElementById('account-category');
    select.innerHTML = accountCategories[type].map(c => 
        `<option value="${c.id}">${c.icon} ${c.name}</option>`
    ).join('');
    
    document.getElementById('account-modal').classList.remove('hidden');
}

function closeAccountModal() {
    document.getElementById('account-modal').classList.add('hidden');
}

async function editAccount(id, type) {
    const endpoint = type === 'expense' ? `/account/expenses/${id}` : `/account/incomes/${id}`;
    try {
        const res = await fetch(endpoint);
        const data = await res.json();
        
        showAccountModal(type, id);
        document.getElementById('account-amount').value = (data.amount / 100).toFixed(2);
        document.getElementById('account-date').value = data.date;
        document.getElementById('account-description').value = data.description || '';
        
        if (data.category_id) {
            document.getElementById('account-category').value = data.category_id;
        }
    } catch (error) {
        alert('获取记录失败');
    }
}

async function deleteAccount(id, type) {
    if (!confirm(`确定要删除这条${type === 'expense' ? '支出' : '收入'}记录吗？`)) return;
    
    const endpoint = type === 'expense' ? `/account/expenses/${id}` : `/account/incomes/${id}`;
    try {
        const res = await fetch(endpoint, { method: 'DELETE' });
        if (!res.ok) throw new Error('删除失败');
        loadAccountData();
    } catch (error) {
        alert(error.message);
    }
}

document.getElementById('account-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('account-id').value;
    const type = document.getElementById('account-type').value;
    const amount = Math.round(parseFloat(document.getElementById('account-amount').value) * 100);
    const date = document.getElementById('account-date').value;
    const category_id = parseInt(document.getElementById('account-category').value);
    const description = document.getElementById('account-description').value;
    
    const payload = { amount, date, category_id, description };
    
    try {
        const url = id 
            ? `/${type === 'expense' ? 'account/expenses' : 'account/incomes'}/${id}`
            : `/${type === 'expense' ? 'account/expenses' : 'account/incomes'}`;
        const method = id ? 'PUT' : 'POST';
        
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '保存失败');
        }
        
        closeAccountModal();
        loadAccountData();
    } catch (error) {
        alert(error.message);
    }
});

// ==================== 智能对话模块 ====================

let currentConversationId = null;
let conversations = [];

// 切换到对话视图
function showChat() {
    document.getElementById('chat-view').classList.remove('hidden');
    document.getElementById('chat-view').style.display = 'flex';
    document.getElementById('panel-view').classList.remove('active');
    
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector('.sidebar-item:first-child').classList.add('active');
}

// 切换到面板视图
function showPanel(panelName) {
    document.getElementById('chat-view').classList.add('hidden');
    document.getElementById('chat-view').style.display = 'none';
    document.getElementById('panel-view').classList.add('active');
    
    // 显示对应面板
    document.querySelectorAll('#panel-view .panel').forEach(p => p.style.display = 'none');
    const panel = document.getElementById(`${panelName}-panel`);
    if (panel) {
        panel.style.display = 'block';
    }
    
    // 更新侧边栏
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 加载数据
    if (panelName === 'weather') {
        if (!document.getElementById('weather-city').value) {
            document.getElementById('weather-city').value = '北京';
        }
        getWeather();
    } else if (panelName === 'notes') {
        loadNotes();
    } else if (panelName === 'today') {
        loadTodayNotes();
    } else if (panelName === 'recycle') {
        loadRecycleNotes();
    } else if (panelName === 'account') {
        loadAccountData();
    } else if (panelName === 'tags') {
        loadTags();
    }
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    
    // 显示用户消息
    addMessageToChat('user', message);
    input.value = '';
    
    // 显示加载状态
    document.getElementById('typing-indicator').classList.add('active');
    document.getElementById('send-btn').disabled = true;
    
    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId
            })
        });
        
        if (!res.ok) throw new Error('发送失败');
        
        const data = await res.json();
        
        currentConversationId = data.conversation_id;
        document.getElementById('chat-title').textContent = message.slice(0, 20) + (message.length > 20 ? '...' : '');
        
        // 显示助手回复
        document.getElementById('typing-indicator').classList.remove('active');
        addMessageToChat('assistant', data.response);
        
    } catch (error) {
        document.getElementById('typing-indicator').classList.remove('active');
        addMessageToChat('assistant', '抱歉，出了点问题: ' + error.message);
    }
    
    document.getElementById('send-btn').disabled = false;
}

function addMessageToChat(role, content) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `
        <div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div>
        <div class="message-content">${escapeHtml(content)}</div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 表单提交
document.getElementById('chat-form').addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage();
});

// 会话列表
async function loadConversations() {
    try {
        const res = await fetch('/chat/conversations');
        const data = await res.json();
        conversations = data.conversations || [];
        renderConversationList();
    } catch (error) {
        console.error('加载会话失败:', error);
    }
}

function renderConversationList() {
    const container = document.getElementById('conversation-list');
    if (conversations.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-4">暂无历史会话</p>';
        return;
    }
    
    container.innerHTML = conversations.map(c => `
        <div class="conversation-item ${c.id === currentConversationId ? 'active' : ''}" onclick="loadConversation(${c.id})">
            <div class="font-medium">${escapeHtml(c.title)}</div>
            <div class="text-xs text-gray-500">${new Date(c.updated_at).toLocaleString()}</div>
        </div>
    `).join('');
}

async function loadConversation(id) {
    try {
        const res = await fetch(`/chat/conversations/${id}`);
        const data = await res.json();
        
        currentConversationId = id;
        document.getElementById('chat-title').textContent = data.title;
        
        // 显示消息
        const container = document.getElementById('chat-messages');
        container.innerHTML = '';
        
        data.messages.forEach(m => {
            addMessageToChat(m.role, m.content);
        });
        
        hideConversationModal();
        showChat();
    } catch (error) {
        alert('加载会话失败');
    }
}

function showConversationModal() {
    loadConversations();
    document.getElementById('conversation-modal').classList.add('active');
}

function hideConversationModal() {
    document.getElementById('conversation-modal').classList.remove('active');
}

async function createNewConversation() {
    try {
        const res = await fetch('/chat/conversations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: '新对话' })
        });
        const data = await res.json();
        
        currentConversationId = data.id;
        document.getElementById('chat-title').textContent = '新对话';
        
        // 清空消息
        document.getElementById('chat-messages').innerHTML = `
            <div class="message assistant">
                <div class="message-avatar">🤖</div>
                <div class="message-content">你好！我是你的智能生活助手。有什么可以帮你的吗？</div>
            </div>
        `;
        
        hideConversationModal();
    } catch (error) {
        alert('创建会话失败');
    }
}

// ==================== 标签管理模块 ====================

async function loadTags() {
    try {
        const res = await fetch('/tags');
        const tags = await res.json();
        renderTags(tags);
    } catch (error) {
        console.error('加载标签失败:', error);
    }
}

function renderTags(tags) {
    const container = document.getElementById('tags-list');
    if (tags.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-4">暂无标签</p>';
        return;
    }
    
    container.innerHTML = tags.map(tag => `
        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center gap-3">
                <span class="w-4 h-4 rounded-full" style="background: ${tag.color}"></span>
                <span class="font-medium">${escapeHtml(tag.name)}</span>
            </div>
            <button onclick="deleteTag(${tag.id})" class="text-red-500 hover:text-red-700 text-sm">
                删除
            </button>
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
        const res = await fetch('/tags', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, color })
        });
        
        if (!res.ok) throw new Error('创建失败');
        
        document.getElementById('new-tag-name').value = '';
        loadTags();
    } catch (error) {
        alert(error.message);
    }
}

async function deleteTag(id) {
    if (!confirm('确定要删除这个标签吗？')) return;
    
    try {
        const res = await fetch(`/tags/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('删除失败');
        loadTags();
    } catch (error) {
        alert(error.message);
    }
}
