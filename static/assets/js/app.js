document.addEventListener('DOMContentLoaded', () => {
    function autoGrowTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = `${textarea.scrollHeight}px`;
    }

    const textarea = document.querySelector('textarea');
    if (textarea) {
        textarea.empty = true;
        textarea.addEventListener('input', () => autoGrowTextarea(textarea));
        autoGrowTextarea(textarea);
    }

    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const notes = document.querySelectorAll('.note-list li');
            notes.forEach(note => {
                const text = note.textContent.toLowerCase();
                note.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
});