// Modal Functions
function openCreateFolderModal() {
    document.getElementById('createFolderModal').style.display = 'flex';
}

function closeCreateFolderModal() {
    document.getElementById('createFolderModal').style.display = 'none';
}

function openUploadModal() {
    document.getElementById('uploadModal').style.display = 'flex';
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
}

function openCreateNoteModal() {
    document.getElementById('createNoteModal').style.display = 'flex';
}

function closeCreateNoteModal() {
    document.getElementById('createNoteModal').style.display = 'none';
}

function openCreateLabelModal() {
    document.getElementById('createLabelModal').style.display = 'flex';
}

function closeCreateLabelModal() {
    document.getElementById('createLabelModal').style.display = 'none';
}

function openAddLabelModal() {
    document.getElementById('addLabelModal').style.display = 'flex';
}

function closeAddLabelModal() {
    document.getElementById('addLabelModal').style.display = 'none';
}

// Folder Functions
function openFolder(folderId) {
    window.location.href = `/dashboard?folder=${folderId}`;
}

function deleteFolder(folderId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce dossier ?')) {
        fetch(`/delete_folder/${folderId}`, {
            method: 'POST'
        }).then(() => {
            window.location.reload();
        });
    }
}

// File Functions
function downloadFile(filename) {
    window.location.href = `/download/${filename}`;
}

function deleteFile(fileId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce fichier ?')) {
        fetch(`/delete_file/${fileId}`, {
            method: 'POST'
        }).then(() => {
            window.location.reload();
        });
    }
}

// Note Functions
function editNote(noteId, title, content) {
    // Open modal with existing values
    openCreateNoteModal();
    document.getElementById('note_title').value = title;
    document.getElementById('note_content').value = content;
    
    const form = document.querySelector('#createNoteModal form');
    form.action = `/edit_note/${noteId}`;
}

function deleteNote(noteId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette note ?')) {
        fetch(`/delete_note/${noteId}`, {
            method: 'POST'
        }).then(() => {
            window.location.reload();
        });
    }
}

// Label Functions
function addLabelToFolder(folderId) {
    document.getElementById('modal_folder_id').value = folderId;
    openAddLabelModal();
}

function removeLabelFromFolder(folderId, labelId) {
    fetch(`/remove_label_from_folder/${folderId}/${labelId}`, {
        method: 'POST'
    }).then(() => {
        window.location.reload();
    });
}

// Search Function
function searchFiles() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toLowerCase();
    const allItems = document.querySelectorAll('.item-card');
    
    allItems.forEach(item => {
        const name = item.querySelector('.item-name, .note-title');
        if (name) {
            const txtValue = name.textContent || name.innerText;
            if (txtValue.toLowerCase().indexOf(filter) > -1) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        }
    });
}

// View Toggle
document.querySelectorAll('.view-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        // Remove active class from all buttons
        document.querySelectorAll('.view-btn').forEach(b => {
            b.classList.remove('bg-indigo-100', 'dark:bg-indigo-900/30', 'text-indigo-600', 'dark:text-indigo-400');
        });
        
        // Add active class to clicked button
        this.classList.add('bg-indigo-100', 'dark:bg-indigo-900/30', 'text-indigo-600', 'dark:text-indigo-400');
        
        const view = this.getAttribute('data-view');
        const grids = document.querySelectorAll('#foldersGrid, #filesGrid, #notesGrid');
        
        if (view === 'list') {
            grids.forEach(grid => {
                grid.classList.remove('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3', 'xl:grid-cols-4');
                grid.classList.add('grid-cols-1');
            });
        } else {
            grids.forEach(grid => {
                grid.classList.remove('grid-cols-1');
                grid.classList.add('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3', 'xl:grid-cols-4');
            });
        }
    });
});

// Close modals on click outside
document.querySelectorAll('.modal, .fixed').forEach(modal => {
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            this.style.display = 'none';
        }
    });
});
