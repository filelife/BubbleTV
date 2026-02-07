document.addEventListener('DOMContentLoaded', function() {
    loadTasks();
    loadVideos();
    loadStorageInfo();
    checkMigrationStatus();
    setupEventListeners();
    createMessageModal();
    
    setInterval(() => {
        loadTasks();
    }, 2000);
});

function createMessageModal() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'messageModal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-hidden', 'true');
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="messageModalTitle">提示</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="alert alert-info">
                        <div id="messageModalContent" style="white-space: pre-wrap; word-break: break-word;"></div>
                    </div>
                    <div class="text-center mt-3">
                        <button class="btn btn-outline-primary btn-sm" onclick="copyMessageContent()">
                            <i class="fa fa-copy"></i> 复制内容
                        </button>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
                        <i class="fa fa-check"></i> 确定
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    modal.addEventListener('hidden.bs.modal', function() {
        document.getElementById('messageModalContent').textContent = '';
    });
}

function showMessage(title, message) {
    const modal = document.getElementById('messageModal');
    const titleElement = document.getElementById('messageModalTitle');
    const contentElement = document.getElementById('messageModalContent');
    
    titleElement.textContent = title;
    contentElement.textContent = message;
    
    let bsModal = bootstrap.Modal.getInstance(modal);
    if (!bsModal) {
        bsModal = new bootstrap.Modal(modal);
    }
    bsModal.show();
}

function copyMessageContent() {
    const content = document.getElementById('messageModalContent').textContent;
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(content).then(() => {
            showMessage('复制成功', '内容已复制到剪贴板');
        }).catch(err => {
            console.error('Clipboard API failed:', err);
            fallbackCopy(content);
        });
    } else {
        fallbackCopy(content);
    }
}

function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    textarea.style.top = '0';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    textarea.setSelectionRange(0, 99999);
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showMessage('复制成功', '内容已复制到剪贴板');
        } else {
            showMessage('复制失败', '无法复制内容，请手动选择文本复制');
        }
    } catch (err) {
        console.error('Copy failed:', err);
        showMessage('复制失败', '无法复制内容，请手动选择文本复制');
    }
    
    document.body.removeChild(textarea);
}

function setupEventListeners() {
    document.getElementById('download-form').addEventListener('submit', handleDownloadSubmit);
    document.getElementById('change-storage-btn').addEventListener('click', handleChangeStorage);
    document.getElementById('search-btn').addEventListener('click', handleSearch);
    document.getElementById('search-input').addEventListener('input', handleRealTimeSearch);
    document.getElementById('scan-videos-btn').addEventListener('click', handleScanVideos);
    
    document.getElementById('login-bilibili-btn').addEventListener('click', () => handleLogin('bilibili', 'auto'));
    document.getElementById('login-douyin-btn').addEventListener('click', () => handleLogin('douyin', 'auto'));
    document.getElementById('login-toutiao-btn').addEventListener('click', () => handleLogin('toutiao', 'auto'));
    
    document.getElementById('save-bilibili-cookie-btn').addEventListener('click', () => handleManualLogin('bilibili'));
    document.getElementById('save-douyin-cookie-btn').addEventListener('click', () => handleManualLogin('douyin'));
    document.getElementById('save-toutiao-cookie-btn').addEventListener('click', () => handleManualLogin('toutiao'));
    
    document.getElementById('copyMessageBtn').addEventListener('click', copyMessageContent);
    
    setupDragAndDrop();
}

function handleDownloadSubmit(e) {
    e.preventDefault();
    
    let url = document.getElementById('video-url').value.trim();
    
    if (!url) {
        showMessage('提示', '请输入视频链接');
        return;
    }
    
    const extractedUrl = extractUrl(url);
    if (!extractedUrl) {
        showMessage('错误', '无法识别有效的视频链接，请检查输入内容');
        return;
    }
    
    if (extractedUrl !== url) {
        showMessage('提示', '已从输入内容中提取视频链接');
        document.getElementById('video-url').value = extractedUrl;
    }
    
    addTask(extractedUrl);
}

function extractUrl(text) {
    const urlPattern = /(https?:\/\/[^\s\]\`'"]+)/;
    const match = text.match(urlPattern);
    return match ? match[1] : null;
}

function addTask(url) {
    const taskData = {
        url: url,
        status: 'pending',
        progress: 0,
        created_at: new Date().toISOString()
    };
    
    fetch('/api/tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('成功', '下载任务已添加到队列');
            document.getElementById('video-url').value = '';
            loadTasks();
        } else {
            showMessage('错误', '添加任务失败：' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('网络错误', '网络错误，请稍后重试');
    });
}

function loadTasks() {
    fetch('/api/tasks')
    .then(response => response.json())
    .then(data => {
        displayTasks(data.tasks);
    })
    .catch(error => {
        console.error('Error loading tasks:', error);
    });
}

function handleScanVideos() {
    const btn = document.getElementById('scan-videos-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> 扫描中...';
    
    fetch('/api/videos/scan', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('扫描完成', data.message);
            loadVideos();
        } else {
            showMessage('扫描失败', '扫描失败：' + data.message);
        }
    })
    .catch(error => {
        console.error('Error scanning videos:', error);
        showMessage('网络错误', '网络错误，请稍后重试');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa fa-refresh"></i> 检测资源';
    });
}

function displayTasks(tasks) {
    const container = document.getElementById('task-container');
    
    if (tasks.length === 0) {
        container.innerHTML = '<div class="text-center text-muted"><p>暂无下载任务</p></div>';
        return;
    }
    
    let html = '';
    
    tasks.forEach(task => {
        const statusClass = task.status === 'completed' ? 'completed' : (task.status === 'failed' ? 'failed' : '');
        const statusBadge = getStatusBadge(task.status);
        const progressHtml = task.status === 'downloading' ? 
            `<div class="progress">
                <div class="progress-bar bg-info" style="width: ${task.progress}%"></div>
            </div>
            <small class="text-muted">下载速度: ${task.download_speed || '计算中...'}</small>` : '';
        const actionButtons = getActionButtons(task);
        
        html += `
            <div class="task-item ${statusClass}">
                <div class="d-flex justify-content-between">
                    <h5>${task.title} <span class="auto-detect-badge">自动识别</span></h5>
                    ${statusBadge}
                </div>
                <p class="text-muted">${task.url}</p>
                ${progressHtml}
                ${task.error_message ? `<p class="text-danger">错误信息：${task.error_message}</p>` : ''}
                <div class="mt-2">
                    ${actionButtons}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function getStatusBadge(status) {
    const badges = {
        'pending': '<span class="badge bg-secondary">等待中</span>',
        'downloading': '<span class="badge bg-info">下载中</span>',
        'completed': '<span class="badge bg-success">已完成</span>',
        'failed': '<span class="badge bg-danger">下载失败</span>'
    };
    return badges[status] || '';
}

function getActionButtons(task) {
    if (task.status === 'downloading') {
        return `
            <button class="btn btn-sm btn-secondary" onclick="pauseTask('${task.id}')">
                <i class="fa fa-pause"></i> 暂停
            </button>
            <button class="btn btn-sm btn-danger" onclick="cancelTask('${task.id}')">
                <i class="fa fa-times"></i> 取消
            </button>
        `;
    } else if (task.status === 'completed') {
        return `
            <button class="btn btn-sm btn-primary" onclick="openTask('${task.id}')">
                <i class="fa fa-folder-open"></i> 打开
            </button>
            <button class="btn btn-sm btn-danger" onclick="deleteTask('${task.id}')">
                <i class="fa fa-trash"></i> 删除
            </button>
        `;
    } else if (task.status === 'failed') {
        return `
            <button class="btn btn-sm btn-primary" onclick="retryTask('${task.id}')">
                <i class="fa fa-refresh"></i> 重试
            </button>
            <button class="btn btn-sm btn-danger" onclick="deleteTask('${task.id}')">
                <i class="fa fa-trash"></i> 删除
            </button>
        `;
    }
    return '';
}

function pauseTask(taskId) {
    fetch(`/api/tasks/${taskId}/pause`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTasks();
        } else {
            showMessage('操作失败', '操作失败：' + data.message);
        }
    });
}

function cancelTask(taskId) {
    fetch(`/api/tasks/${taskId}/cancel`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTasks();
        } else {
            showMessage('操作失败', '操作失败：' + data.message);
        }
    });
}

function retryTask(taskId) {
    fetch(`/api/tasks/${taskId}/retry`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTasks();
        } else {
            showMessage('操作失败', '操作失败：' + data.message);
        }
    });
}

function openTask(taskId) {
    fetch(`/api/tasks/${taskId}/open`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.path) {
                openDirectory(data.path);
            }
        } else {
            showMessage('操作失败', '操作失败：' + data.message);
        }
    });
}

function deleteTask(taskId) {
    if (!confirm('确定要删除这个任务吗？')) {
        return;
    }
    
    fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTasks();
        } else {
            showMessage('操作失败', '操作失败：' + data.message);
        }
    });
}

function loadVideos() {
    fetch('/api/videos')
    .then(response => response.json())
    .then(data => {
        displayVideos(data.videos);
    })
    .catch(error => {
        console.error('Error loading videos:', error);
    });
}

function displayVideos(videos) {
    const container = document.getElementById('tree-container');
    
    if (videos.length === 0) {
        container.innerHTML = '<div class="text-center text-muted"><p>暂无已下载资源</p></div>';
        return;
    }
    
    const treeData = buildTreeData(videos);
    const treeHtml = buildTreeHtml(treeData);
    container.innerHTML = treeHtml;
    
    setupTreeInteractions();
}

function buildTreeData(videos) {
    const tree = {};
    
    videos.forEach(video => {
        const path = video.save_path.split('/');
        let current = tree;
        
        path.forEach((part, index) => {
            if (!current[part]) {
                if (index === path.length - 1) {
                    current[part] = {
                        type: 'file',
                        data: video
                    };
                } else {
                    current[part] = {};
                }
                current = current[part];
            }
        });
    });
    
    return tree;
}

function buildTreeHtml(tree, level = 0) {
    let html = '';
    const indent = level * 20;
    
    Object.keys(tree).forEach(key => {
        const node = tree[key];
        const iconClass = node.type === 'folder' ? 'fa-folder' : 'fa-file-video-o';
        const nodeClass = node.type === 'folder' ? 'folder' : 'file';
        const draggable = node.type === 'file' ? 'draggable="true"' : '';
        
        html += `
            <div class="tree-node ${nodeClass} ${draggable}" style="margin-left: ${indent}px" data-path="${node.data ? node.data.save_path : ''}">
                <i class="fa ${iconClass}"></i> ${key}
            </div>
        `;
        
        if (node.type === 'folder' && Object.keys(node).length > 0) {
            html += buildTreeHtml(node, level + 1);
        }
    });
    
    return html;
}

function setupTreeInteractions() {
    document.querySelectorAll('.tree-node.folder').forEach(node => {
        node.addEventListener('click', function(e) {
            if (e.target === this || e.target.tagName === 'I') {
                const children = this.querySelectorAll('.tree-node');
                children.forEach(child => {
                    if (child.style.display === 'none') {
                        child.style.display = 'block';
                    } else {
                        child.style.display = 'none';
                    }
                });
            }
        });
    });
    
    setupDragAndDrop();
}

function setupDragAndDrop() {
    const treeNodes = document.querySelectorAll('.tree-node.draggable');
    const folders = document.querySelectorAll('.tree-node.folder');
    
    let draggedElement = null;
    
    treeNodes.forEach(node => {
        node.addEventListener('dragstart', function(e) {
            draggedElement = this;
            this.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', this.innerHTML);
        });
        
        node.addEventListener('dragend', function(e) {
            this.classList.remove('dragging');
            document.querySelectorAll('.tree-node').forEach(n => {
                n.classList.remove('drag-over');
            });
        });
        
        node.addEventListener('dragenter', function(e) {
            e.preventDefault();
            if (this !== draggedElement && this.classList.contains('folder')) {
                this.classList.add('drag-over');
            }
        });
        
        node.addEventListener('dragleave', function(e) {
            this.classList.remove('drag-over');
        });
        
        node.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            return false;
        });
        
        node.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (this !== draggedElement && this.classList.contains('folder')) {
                this.classList.remove('drag-over');
                
                const nodeName = draggedElement.textContent.trim();
                const targetName = this.textContent.trim();
                
                moveFile(nodeName, targetName);
            }
            
            return false;
        });
    });
}

function moveFile(sourcePath, targetPath) {
    fetch('/api/storage/move', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            source: sourcePath,
            target: targetPath
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadVideos();
        } else {
            showMessage('移动失败', '移动失败：' + data.message);
        }
    });
}

function handleSearch() {
    const searchTerm = document.getElementById('search-input').value.trim();
    
    if (!searchTerm) {
        loadVideos();
        return;
    }
    
    searchVideos(searchTerm);
}

function handleRealTimeSearch(e) {
    const searchTerm = e.target.value.trim();
    
    if (!searchTerm) {
        loadVideos();
        return;
    }
    
    searchVideos(searchTerm);
}

function searchVideos(searchTerm) {
    fetch(`/api/videos/search?q=${encodeURIComponent(searchTerm)}`)
    .then(response => response.json())
    .then(data => {
        displayVideos(data.videos);
    })
    .catch(error => {
        console.error('Error searching videos:', error);
    });
}

function loadStorageInfo() {
    fetch('/api/storage/info')
    .then(response => response.json())
    .then(data => {
        displayStorageInfo(data);
    })
    .catch(error => {
        console.error('Error loading storage info:', error);
    });
}

function displayStorageInfo(info) {
    const pathElement = document.getElementById('current-storage-path');
    pathElement.textContent = info.path || '/Users/username/Downloads/Videos';
}

function handleChangeStorage() {
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    const isWindows = navigator.platform.toUpperCase().indexOf('WIN') >= 0;
    
    if (isMac) {
        selectDirectoryMacos();
    } else if (isWindows) {
        selectDirectoryWindows();
    } else {
        selectDirectoryLinux();
    }
}

function selectDirectoryMacos() {
    showMessage('提示', '正在调用访达进行地址选择...\n\n在实际应用中，这里会调用访达API打开目录选择对话框。');
    
    fetch('/api/storage/select-directory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ platform: 'macos' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.selected_path) {
            showMigrationDialog(data.current_path, data.selected_path);
        } else {
            showMessage('选择目录失败', '选择目录失败：' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('Error selecting directory:', error);
        showMessage('网络错误', '网络错误，请稍后重试');
    });
}

function selectDirectoryWindows() {
    showMessage('提示', '正在调用文件资源管理器进行地址选择...\n\n在实际应用中，这里会调用Windows文件资源管理器API打开目录选择对话框。');
    
    fetch('/api/storage/select-directory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ platform: 'windows' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.selected_path) {
            showMigrationDialog(data.current_path, data.selected_path);
        } else {
            showMessage('选择目录失败', '选择目录失败：' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('Error selecting directory:', error);
        showMessage('网络错误', '网络错误，请稍后重试');
    });
}

function selectDirectoryLinux() {
    showMessage('提示', '正在调用系统目录选择器...\n\n在实际应用中，这里会调用Webkit目录选择API。');
    
    fetch('/api/storage/select-directory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ platform: 'linux' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.selected_path) {
            showMigrationDialog(data.current_path, data.selected_path);
        } else {
            showMessage('选择目录失败', '选择目录失败：' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('Error selecting directory:', error);
        showMessage('网络错误', '网络错误，请稍后重试');
    });
}

function showMigrationDialog(oldPath, newPath) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'migrationModal';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fa fa-exchange"></i> 存储目录迁移
                    </h5>
                    <button type="button" class="btn-close" onclick="closeMigrationModal()" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="alert alert-info">
                        <i class="fa fa-info-circle"></i>
                        <small>
                            旧目录：${oldPath}<br>
                            新目录：${newPath}
                        </small>
                    </div>
                    <h6>请选择迁移方式：</h6>
                    <div class="migration-option" onclick="selectMigrationOption(1, this)">
                        <div class="d-flex align-items-center">
                            <div class="me-3">
                                <i class="fa fa-arrows-alt fa-2x" style="color: #007bff;"></i>
                            </div>
                            <div>
                                <strong>迁移已下载资源</strong>
                                <p class="mb-0 text-muted small">
                                    将旧目录中的所有文件移动到新目录<br>
                                    <span class="text-warning">注意：迁移过程中请不要关闭终端</span>
                                </p>
                            </div>
                        </div>
                    </div>
                    <div class="migration-option" onclick="selectMigrationOption(2, this)">
                        <div class="d-flex align-items-center">
                            <div class="me-3">
                                <i class="fa fa-refresh fa-2x" style="color: #28a745;"></i>
                            </div>
                            <div>
                                <strong>仅更新存储地址</strong>
                                <p class="mb-0 text-muted small">
                                    旧目录中的文件保持不变<br>
                                    新下载的视频将保存到新目录
                                </p>
                            </div>
                        </div>
                    </div>
                    <div class="migration-progress" id="migrationProgress" style="display: none;">
                        <div class="progress">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" id="migrationProgressBar" style="width: 0%"></div>
                        </div>
                        <p class="text-center text-muted small mt-2" id="migrationStatus">
                            正在迁移文件... 0%
                        </p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeMigrationModal()">
                        <i class="fa fa-times"></i> 取消
                    </button>
                    <button type="button" class="btn btn-primary" onclick="confirmMigration('${newPath}')">
                        <i class="fa fa-check"></i> 确认
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'block';
    modal.classList.add('show');
}

function selectMigrationOption(option, element) {
    document.querySelectorAll('.migration-option').forEach(opt => opt.classList.remove('selected'));
    element.classList.add('selected');
    window.selectedMigrationOption = option;
}

function confirmMigration(newPath) {
    if (!window.selectedMigrationOption) {
        showMessage('提示', '请选择一种迁移方式');
        return;
    }
    
    document.querySelectorAll('.migration-option').forEach(opt => opt.style.display = 'none');
    document.getElementById('migrationProgress').style.display = 'block';
    
    const migrateFiles = window.selectedMigrationOption === 1;
    
    fetch('/api/storage/migrate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            new_path: newPath,
            migrate_files: migrateFiles
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            simulateMigrationProgress(data.total_files);
        } else {
            showMessage('迁移失败', '迁移失败：' + data.message);
            closeMigrationModal();
        }
    })
    .catch(error => {
        console.error('Error migrating storage:', error);
        showMessage('网络错误', '网络错误，请稍后重试');
        closeMigrationModal();
    });
}

function simulateMigrationProgress(totalFiles) {
    let progress = 0;
    const interval = setInterval(() => {
        progress += 10;
        document.getElementById('migrationProgressBar').style.width = progress + '%';
        document.getElementById('migrationStatus').textContent = `正在迁移文件... ${progress}%`;
        
        if (progress >= 100) {
            clearInterval(interval);
            document.getElementById('migrationStatus').textContent = '迁移完成！';
            
            setTimeout(() => {
                closeMigrationModal();
                loadStorageInfo();
                showMessage('成功', '存储目录已更新，文件迁移完成！');
            }, 1000);
        }
    }, 500);
}

function closeMigrationModal() {
    const modal = document.getElementById('migrationModal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 300);
    }
}

function checkMigrationStatus() {
    fetch('/api/storage/migration-status')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'in_progress') {
            if (confirm('检测到上次有未完成的文件迁移。\n\n是否继续完成文件传输？')) {
                continueMigration(data.new_path);
            } else {
                cancelMigration();
            }
        }
    })
    .catch(error => {
        console.error('Error checking migration status:', error);
    });
}

function cancelMigration() {
    fetch('/api/storage/cancel-migration', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('取消成功', '已取消未完成的迁移。');
        }
    });
}

function handleLogin(platform, loginType) {
    const platformNames = {
        'bilibili': 'Bilibili',
        'douyin': '抖音',
        'toutiao': '今日头条'
    };
    
    if (loginType === 'auto') {
        showMessage('提示', `正在打开${platformNames[platform]}登录页面...\n\n在实际应用中，这里会打开对应平台的登录页面，用户完成登录后自动保存Cookie。`);
    
        fetch(`/api/auth/login/${platform}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ login_type: 'auto' })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateLoginStatus(platform, true, 'auto');
                showMessage('登录成功', `${platformNames[platform]}登录成功`);
            } else {
                showMessage('登录失败', `${platformNames[platform]}登录失败：${data.message}`);
            }
        })
        .catch(error => {
            console.error('Error logging in:', error);
            showMessage('网络错误', '网络错误，请稍后重试');
        });
    }
}

function handleManualLogin(platform) {
    const platformNames = {
        'bilibili': 'Bilibili',
        'douyin': '抖音',
        'toutiao': '今日头条'
    };
    
    let cookieString = '';
    
    if (platform === 'bilibili') {
        cookieString = document.getElementById('bilibili-cookie').value.trim();
    } else if (platform === 'douyin') {
        cookieString = document.getElementById('douyin-cookie').value.trim();
    } else if (platform === 'toutiao') {
        cookieString = document.getElementById('toutiao-cookie').value.trim();
    }
    
    if (!cookieString) {
        showMessage('提示', '请输入Cookie字符串');
        return;
    }
    
    showMessage('提示', `正在保存${platformNames[platform]} Cookie...`);
    
    fetch(`/api/auth/login/${platform}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            login_type: 'manual',
            cookie_string: cookieString 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateLoginStatus(platform, true, 'manual');
            showMessage('保存成功', `${platformNames[platform]} Cookie已保存`);
            
            if (platform === 'bilibili') {
                document.getElementById('bilibili-cookie').value = '';
            } else if (platform === 'douyin') {
                document.getElementById('douyin-cookie').value = '';
            } else if (platform === 'toutiao') {
                document.getElementById('toutiao-cookie').value = '';
            }
        } else {
            showMessage('保存失败', `${platformNames[platform]} Cookie保存失败：${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error saving cookie:', error);
        showMessage('网络错误', '网络错误，请稍后重试');
    });
}

function updateLoginStatus(platform, isLoggedIn, loginType) {
    const autoStatusElement = document.getElementById(`${platform}-status`);
    const manualStatusElement = document.getElementById(`${platform}-manual-status`);
    
    if (isLoggedIn) {
        if (loginType === 'auto') {
            autoStatusElement.className = 'login-status logged-in';
            autoStatusElement.innerHTML = '<i class="fa fa-check-circle"></i> 已登录';
            manualStatusElement.className = 'login-status logged-out';
            manualStatusElement.innerHTML = '<i class="fa fa-times-circle"></i> 未登录';
        } else {
            manualStatusElement.className = 'login-status logged-in';
            manualStatusElement.innerHTML = '<i class="fa fa-check-circle"></i> 已登录';
            autoStatusElement.className = 'login-status logged-out';
            autoStatusElement.innerHTML = '<i class="fa fa-times-circle"></i> 未登录';
        }
    } else {
        autoStatusElement.className = 'login-status logged-out';
        autoStatusElement.innerHTML = '<i class="fa fa-times-circle"></i> 未登录';
        manualStatusElement.className = 'login-status logged-out';
        manualStatusElement.innerHTML = '<i class="fa fa-times-circle"></i> 未登录';
    }
}

function updateLoginStatus(platform, isLoggedIn) {
    const statusElement = document.getElementById(`${platform}-status`);
    
    if (isLoggedIn) {
        statusElement.className = 'login-status logged-in';
        statusElement.innerHTML = '<i class="fa fa-check-circle"></i> 已登录';
    } else {
        statusElement.className = 'login-status logged-out';
        statusElement.innerHTML = '<i class="fa fa-times-circle"></i> 未登录';
    }
}

function openDirectory(path) {
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    const isWindows = navigator.platform.toUpperCase().indexOf('WIN') >= 0;
    
    if (isMac) {
        const script = `tell application "Finder" to open POSIX file "${path}"`;
        
        fetch('/api/storage/open-directory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: path, platform: 'macos' })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                showMessage('打开目录失败', '打开目录失败：' + data.message);
            }
        });
    } else if (isWindows) {
        window.open(`file:///${path.replace(/\\/g, '/')}`);
    } else {
        window.open(`file://${path}`);
    }
}

function loadLoginStatus() {
    fetch('/api/auth/status')
    .then(response => response.json())
    .then(data => {
        if (data.status) {
            Object.keys(data.status).forEach(platform => {
                updateLoginStatus(platform, data.status[platform].logged_in);
            });
        }
    })
    .catch(error => {
        console.error('Error loading login status:', error);
    });
}