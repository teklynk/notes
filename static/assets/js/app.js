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

    const toggle = document.getElementById('theme-toggle');
    const body = document.body;

    if (!localStorage.getItem('theme')) {
        localStorage.setItem('theme', 'dark-mode');
    }

    body.classList.add(localStorage.getItem('theme'));

    toggle.addEventListener('click', () => {
        if (body.classList.contains('dark-mode')) {
            body.classList.replace('dark-mode', 'light-mode');
            localStorage.setItem('theme', 'light-mode');
        } else {
            body.classList.replace('light-mode', 'dark-mode');
            localStorage.setItem('theme', 'dark-mode');
        }
    });
});