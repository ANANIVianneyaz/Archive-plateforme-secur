// Application JavaScript pour Archive Platform

// Configuration globale
const APP_CONFIG = {
    searchDelay: 300,
    animationDuration: 200
};

// Utilitaires
const utils = {
    // Debounce function pour les recherches
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Formatter la taille des fichiers
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Animer les éléments
    animate(element, animation, duration = APP_CONFIG.animationDuration) {
        element.style.animation = `${animation} ${duration}ms ease`;
        setTimeout(() => {
            element.style.animation = '';
        }, duration);
    }
};

// Gestion des modales
class ModalManager {
    constructor() {
        this.activeModal = null;
        this.init();
    }

    init() {
        // Fermer les modales avec Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.close(this.activeModal);
            }
        });

        // Fermer en cliquant en dehors
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.close(e.target);
            }
        });
    }

    open(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'flex';
            this.activeModal = modal;
            document.body.style.overflow = 'hidden';
            
            // Focus sur le premier input
            const firstInput = modal.querySelector('input');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }
    }

    close(modal) {
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            this.activeModal = null;
            document.body.style.overflow = '';
        }
    }
}

// Gestion des fichiers et dossiers
class FileManager {
    constructor() {
        this.currentView = 'grid';
        this.init();
    }

    init() {
        this.setupViewToggle();
        this.setupDragAndDrop();
        this.setupFileInput();
    }

    setupViewToggle() {
        const viewButtons = document.querySelectorAll('.view-btn');
        viewButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                viewButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentView = btn.dataset.view;
                this.updateView();
            });
        });
    }

    updateView() {
        const grids = document.querySelectorAll('.items-grid');
        grids.forEach(grid => {
            if (this.currentView === 'list') {
                grid.style.gridTemplateColumns = '1fr';
                grid.querySelectorAll('.item-card').forEach(card => {
                    card.style.flexDirection = 'row';
                });
            } else {
                grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(280px, 1fr))';
                grid.querySelectorAll('.item-card').forEach(card => {
                    card.style.flexDirection = 'row';
                });
            }
        });
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');
        if (!uploadArea) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            }, false);
        });

        uploadArea.addEventListener('drop', this.handleDrop.bind(this), false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        const fileInput = document.getElementById('file');
        
        if (fileInput && files.length > 0) {
            fileInput.files = files;
            this.updateFileInputDisplay(files[0]);
        }
    }

    setupFileInput() {
        const fileInput = document.getElementById('file');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.updateFileInputDisplay(e.target.files[0]);
                }
            });
        }
    }

    updateFileInputDisplay(file) {
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            const iconElement = uploadArea.querySelector('.upload-icon i');
            const titleElement = uploadArea.querySelector('h3');
            const descElement = uploadArea.querySelector('p');
            
            if (iconElement) iconElement.className = 'fas fa-file-check';
            if (titleElement) titleElement.textContent = file.name;
            if (descElement) descElement.textContent = `Taille: ${utils.formatFileSize(file.size)}`;
            
            uploadArea.style.borderColor = 'var(--secondary-color)';
            uploadArea.style.background = 'rgba(52, 168, 83, 0.05)';
        }
    }
}

// Gestion des recherches
class SearchManager {
    constructor() {
        this.searchInput = document.getElementById('searchInput');
        this.init();
    }

    init() {
        if (!this.searchInput) return;
        
        const debouncedSearch = utils.debounce(this.performSearch.bind(this), APP_CONFIG.searchDelay);
        this.searchInput.addEventListener('input', debouncedSearch);
    }

    async performSearch(e) {
        const query = e.target.value.trim();
        
        if (query.length === 0) {
            this.clearSearchResults();
            return;
        }

        if (query.length < 2) return;

        try {
            const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            this.displaySearchResults(data.files, query);
        } catch (error) {
            console.error('Erreur de recherche:', error);
            this.showSearchError();
        }
    }

    displaySearchResults(files, query) {
        const filesGrid = document.getElementById('filesGrid');
        if (!filesGrid) return;

        // Cacher les autres sections pendant la recherche
        const foldersGrid = document.getElementById('foldersGrid');
        if (foldersGrid) {
            foldersGrid.parentElement.style.display = 'none';
        }

        // Afficher les résultats
        if (files.length === 0) {
            filesGrid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fas fa-search"></i>
                    </div>
                    <h3>Aucun résultat</h3>
                    <p>Aucun fichier ne correspond à "${query}"</p>
                </div>
            `;
        } else {
            const fileItems = files.map(file => this.createFileItem(file)).join('');
            filesGrid.innerHTML = fileItems;
        }
    }

    createFileItem(file) {
        const extension = file[3].split('.').pop().toLowerCase();
        const iconClass = this.getFileIconClass(extension);
        const fileSize = utils.formatFileSize(file[5]);
        
        return `
            <div class="item-card file-item">
                <div class="item-icon">
                    <i class="${iconClass}"></i>
                </div>
                <div class="item-content">
                    <h4 class="item-name">${file[3]}</h4>
                    <p class="item-meta">${fileSize}</p>
                </div>
                <div class="item-actions">
                    <button class="action-btn" onclick="downloadFile('${file[2]}')">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="action-btn" onclick="deleteFile(${file[0]})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }

    getFileIconClass(extension) {
        const iconMap = {
            'jpg': 'fas fa-image text-green',
            'jpeg': 'fas fa-image text-green',
            'png': 'fas fa-image text-green',
            'gif': 'fas fa-image text-green',
            'webp': 'fas fa-image text-green',
            'pdf': 'fas fa-file-pdf text-red',
            'doc': 'fas fa-file-word text-blue',
            'docx': 'fas fa-file-word text-blue',
            'txt': 'fas fa-file-alt text-gray'
        };
        return iconMap[extension] || 'fas fa-file text-gray';
    }

    clearSearchResults() {
        // Remettre l'affichage normal
        location.reload(); // Solution simple pour remettre l'affichage normal
    }

    showSearchError() {
        const filesGrid = document.getElementById('filesGrid');
        if (filesGrid) {
            filesGrid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <h3>Erreur de recherche</h3>
                    <p>Une erreur s'est produite lors de la recherche</p>
                </div>
            `;
        }
    }
}

// Gestion des notifications
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: var(--spacing-md);
            box-shadow: var(--shadow-lg);
            max-width: 300px;
            animation: slideIn 0.3s ease;
        `;
        
        const icon = this.getIcon(type);
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: var(--spacing-sm);">
                <i class="${icon}" style="color: ${this.getColor(type)};"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="margin-left: auto; background: none; border: none; cursor: pointer;">&times;</button>
            </div>
        `;
        
        this.container.appendChild(notification);
        
        // Auto-remove
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }

    getIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    getColor(type) {
        const colors = {
            success: 'var(--secondary-color)',
            error: 'var(--danger-color)',
            warning: 'var(--warning-color)',
            info: 'var(--primary-color)'
        };
        return colors[type] || colors.info;
    }
}

// Instances globales
const modalManager = new ModalManager();
const fileManager = new FileManager();
const searchManager = new SearchManager();
const notificationManager = new NotificationManager();

// Fonctions globales pour les événements
function openCreateFolderModal() {
    modalManager.open('createFolderModal');
}

function closeCreateFolderModal() {
    modalManager.close(document.getElementById('createFolderModal'));
}

function openUploadModal() {
    modalManager.open('uploadModal');
}

function closeUploadModal() {
    modalManager.close(document.getElementById('uploadModal'));
}

function openFolder(folderId) {
    window.location.href = `/dashboard?folder_id=${folderId}`;
}

function downloadFile(filename) {
    window.location.href = `/download/${filename}`;
}

function deleteFile(fileId) {
    if (confirm('Voulez-vous vraiment supprimer ce fichier ?')) {
        // Créer un formulaire pour envoyer la requête POST
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/delete_file/${fileId}`;
        document.body.appendChild(form);
        form.submit();
    }
}

function deleteFolder(folderId) {
    if (confirm('Voulez-vous vraiment supprimer ce dossier et tout son contenu ?')) {
        // Créer un formulaire pour envoyer la requête POST
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/delete_folder/${folderId}`;
        document.body.appendChild(form);
        form.submit();
    }
}

// Fonction de recherche (appelée depuis le HTML)
function searchFiles() {
    // Gérée par SearchManager
}

// Animations CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
`;
document.head.appendChild(style);

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Animer l'apparition des éléments
    const items = document.querySelectorAll('.item-card');
    items.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        setTimeout(() => {
            item.style.transition = 'all 0.3s ease';
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, index * 50);
    });
    
    // Message de bienvenue pour les nouveaux utilisateurs
    const dashboardTitle = document.querySelector('.dashboard-title h1');
    if (dashboardTitle && document.querySelectorAll('.item-card').length === 0) {
        setTimeout(() => {
            notificationManager.show('Bienvenue ! Commencez par télécharger vos premiers fichiers.', 'info', 7000);
        }, 1000);
    }
    
    console.log('Archive Platform - Application chargée avec succès');
});

// ============================================
// NOUVELLES FONCTIONNALITÉS JAVASCRIPT
// ============================================

// 1. Gestionnaire de thème sombre/clair
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.setupToggleButton();
    }

    setupToggleButton() {
        const toggleBtn = document.getElementById('themeToggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.toggle();
            });
        }
    }

    toggle() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.currentTheme);
        localStorage.setItem('theme', this.currentTheme);
    }

    applyTheme(theme) {
        const body = document.body;
        if (theme === 'dark') {
            body.classList.add('dark-theme');
        } else {
            body.classList.remove('dark-theme');
        }
    }

    getCurrentTheme() {
        return this.currentTheme;
    }
}

// 2. Gestionnaire de notes
class NotesManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Écouter les clics sur les boutons de création de note
        document.addEventListener('click', (e) => {
            if (e.target.matches('.create-note-btn') || e.target.closest('.create-note-btn')) {
                this.openCreateNoteModal();
            }
            if (e.target.matches('.edit-note-btn') || e.target.closest('.edit-note-btn')) {
                const noteId = e.target.closest('.edit-note-btn').dataset.noteId;
                this.openEditNoteModal(noteId);
            }
            if (e.target.matches('.delete-note-btn') || e.target.closest('.delete-note-btn')) {
                const noteId = e.target.closest('.delete-note-btn').dataset.noteId;
                this.deleteNote(noteId);
            }
        });
    }

    openCreateNoteModal() {
        modalManager.open('createNoteModal');
    }

    openEditNoteModal(noteId) {
        // Implémentation pour éditer une note
        // Pour la démo, on utilise une modal simple
        const title = prompt('Éditer le titre:');
        const content = prompt('Éditer le contenu:');
        
        if (title !== null && content !== null) {
            this.updateNote(noteId, title, content);
        }
    }

    updateNote(noteId, title, content) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/edit_note/${noteId}`;
        
        const titleInput = document.createElement('input');
        titleInput.type = 'hidden';
        titleInput.name = 'note_title';
        titleInput.value = title;
        
        const contentInput = document.createElement('input');
        contentInput.type = 'hidden';
        contentInput.name = 'note_content';
        contentInput.value = content;
        
        form.appendChild(titleInput);
        form.appendChild(contentInput);
        document.body.appendChild(form);
        form.submit();
    }

    deleteNote(noteId) {
        if (confirm('Voulez-vous vraiment supprimer cette note ?')) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/delete_note/${noteId}`;
            document.body.appendChild(form);
            form.submit();
        }
    }
}

// 3. Gestionnaire d'étiquettes
class LabelsManager {
    constructor() {
        this.userLabels = [];
        this.init();
    }

    init() {
        this.loadUserLabels();
        this.setupEventListeners();
    }

    async loadUserLabels() {
        try {
            const response = await fetch('/get_labels');
            const data = await response.json();
            this.userLabels = data.labels;
        } catch (error) {
            console.error('Erreur lors du chargement des étiquettes:', error);
        }
    }

    setupEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('.create-label-btn') || e.target.closest('.create-label-btn')) {
                this.openCreateLabelModal();
            }
            if (e.target.matches('.add-label-btn') || e.target.closest('.add-label-btn')) {
                const folderId = e.target.closest('.add-label-btn').dataset.folderId;
                this.openAddLabelModal(folderId);
            }
            if (e.target.matches('.remove-label-btn') || e.target.closest('.remove-label-btn')) {
                const folderId = e.target.closest('.remove-label-btn').dataset.folderId;
                const labelId = e.target.closest('.remove-label-btn').dataset.labelId;
                this.removeLabel(folderId, labelId);
            }
        });
    }

    openCreateLabelModal() {
        modalManager.open('createLabelModal');
    }

    openAddLabelModal(folderId) {
        // Implémentation simplifiée avec prompt
        const labelName = prompt('Étiquette à ajouter:');
        if (labelName) {
            // Trouver l'étiquette correspondante
            const label = this.userLabels.find(l => l[1].toLowerCase() === labelName.toLowerCase());
            if (label) {
                this.addLabelToFolder(folderId, label[0]);
            } else {
                alert('Étiquette non trouvée');
            }
        }
    }

    addLabelToFolder(folderId, labelId) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/add_label_to_folder';
        
        const folderInput = document.createElement('input');
        folderInput.type = 'hidden';
        folderInput.name = 'folder_id';
        folderInput.value = folderId;
        
        const labelInput = document.createElement('input');
        labelInput.type = 'hidden';
        labelInput.name = 'label_id';
        labelInput.value = labelId;
        
        form.appendChild(folderInput);
        form.appendChild(labelInput);
        document.body.appendChild(form);
        form.submit();
    }

    removeLabel(folderId, labelId) {
        if (confirm('Retirer cette étiquette du dossier ?')) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/remove_label_from_folder';
            
            const folderInput = document.createElement('input');
            folderInput.type = 'hidden';
            folderInput.name = 'folder_id';
            folderInput.value = folderId;
            
            const labelInput = document.createElement('input');
            labelInput.type = 'hidden';
            labelInput.name = 'label_id';
            labelInput.value = labelId;
            
            form.appendChild(folderInput);
            form.appendChild(labelInput);
            document.body.appendChild(form);
            form.submit();
        }
    }
}

// Instances globales des nouvelles fonctionnalités
const themeManager = new ThemeManager();
const notesManager = new NotesManager();
const labelsManager = new LabelsManager();

// Fonctions globales pour les nouvelles fonctionnalités
function toggleTheme() {
    themeManager.toggle();
}

function openCreateNoteModal() {
    modalManager.open('createNoteModal');
}

function closeCreateNoteModal() {
    modalManager.close(document.getElementById('createNoteModal'));
}

function openCreateLabelModal() {
    modalManager.open('createLabelModal');
}

function closeCreateLabelModal() {
    modalManager.close(document.getElementById('createLabelModal'));
}

function editNote(noteId, currentTitle, currentContent) {
    notesManager.openEditNoteModal(noteId);
}

function deleteNote(noteId) {
    notesManager.deleteNote(noteId);
}

function addLabelToFolder(folderId) {
    // Ouvrir le modal d'ajout d'étiquette
    const modal = document.getElementById('addLabelModal');
    const folderIdInput = document.getElementById('modal_folder_id');
    if (folderIdInput) {
        folderIdInput.value = folderId;
    }
    modalManager.open('addLabelModal');
}

function closeAddLabelModal() {
    modalManager.close(document.getElementById('addLabelModal'));
}

function removeLabelFromFolder(folderId, labelId) {
    labelsManager.removeLabel(folderId, labelId);
}

// Mise à jour de l'initialisation DOMContentLoaded existante
document.addEventListener('DOMContentLoaded', function() {
    // Appliquer le thème sauvé
    if (typeof themeManager !== 'undefined') {
        themeManager.applyTheme(themeManager.getCurrentTheme());
    }
    
    // Charger les étiquettes utilisateur
    if (typeof labelsManager !== 'undefined') {
        labelsManager.loadUserLabels();
    }
    
    console.log('🎆 Archive Platform - Nouvelles fonctionnalités activées!');
    console.log('⚠️ Application éducative avec vulnérabilités intentionnelles');
});

// Gestion des erreurs globales
window.addEventListener('error', function(e) {
    console.error('Erreur JavaScript:', e.error);
    notificationManager.show('Une erreur inattendue s\'est produite', 'error');
});

// Export pour utilisation modulaire si nécessaire
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        modalManager,
        fileManager,
        searchManager,
        notificationManager,
        utils
    };
}