document.addEventListener('DOMContentLoaded', function() {
    loadTasks();
    loadVideos();
    loadStorageInfo();
    checkMigrationStatus();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('download-form').addEventListener('submit', handleDownloadSubmit);
    document.getElementById('change-storage-btn').addEventListener('click', handleChangeStorage);
    document.getElementById('search-btn').addEventListener('click', handleSearch);
    document.getElementById('search-input').addEventListener('input', handleRealTimeSearch);
    
    document.getElementById('login-bilibili-btn').addEventListener('click', () => handleLogin('bilibili'));
    document.getElementById('login-douyin-btn').addEventListener('click', () => handleLogin('douyin'));
    document.getElementById('login-toutiao-btn').addEventListener('click', () => handleLogin('toutiao'));
    
    setupDragAndDrop();
}

function handleDownloadSubmit(e) {
    e.preventDefault();
    
    const url = document.getElementById('video-url').value.trim();
    
    if (!url) {
        alert('请输入视频链接');
        return;
    }
    
    addTask(url);
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
            alert('下载任务已添加到队列');
            document.getElementById('video-url').value = '';
            loadTasks();
        } else {
            alert('添加任务失败：' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('网络错误，请稍后重试');
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
            </div>` : '';
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
            alert('操作失败：' + data.message);
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
            alert('操作失败：' + data.message);
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
            alert('操作失败：' + data.message);
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
            alert('操作失败：' + data.message);
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
            alert('操作失败：' + data.message);
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
            alert('移动失败：' + data.message);
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
    alert('正在调用访达进行地址选择...\n\n在实际应用中，这里会调用访达API打开目录选择对话框。');
    
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
            alert('选择目录失败：' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('Error selecting directory:', error);
        alert('网络错误，请稍后重试');
    });
}

function selectDirectoryWindows() {
    alert('正在调用文件资源管理器进行地址选择...\n\n在实际应用中，这里会调用Windows文件资源管理器API打开目录选择对话框。');
    
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
            alert('选择目录失败：' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('Error selecting directory:', error);
        alert('网络错误，请稍后重试');
    });
}

function selectDirectoryLinux() {
    alert('正在调用系统目录选择器...\n\n在实际应用中，这里会调用Webkit目录选择API。');
    
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
            alert('选择目录失败：' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('Error selecting directory:', error);
        alert('网络错误，请稍后重试');
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
        alert('请选择一种迁移方式');
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
            alert('迁移失败：' + data.message);
            closeMigrationModal();
        }
    })
    .catch(error => {
        console.error('Error migrating storage:', error);
        alert('网络错误，请稍后重试');
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
                alert('存储目录已更新，文件迁移完成！');
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
            alert('已取消未完成的迁移。');
        }
    });
}

function handleLogin(platform) {
    const platformNames = {
        'bilibili': 'Bilibili',
        'douyin': '抖音',
        'toutiao': '今日头条'
    };
    
    alert(`正在打开${platformNames[platform]}登录页面...\n\n在实际应用中，这里会打开对应平台的登录页面，用户完成登录后自动保存Cookie。`);
    
    fetch(`/api/auth/login/${platform}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateLoginStatus(platform, true);
            alert(`${platformNames[platform]}登录成功`);
        } else {
            alert(`${platformNames[platform]}登录失败：${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error logging in:', error);
        alert('网络错误，请稍后重试');
    });
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
                alert('打开目录失败：' + data.message);
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