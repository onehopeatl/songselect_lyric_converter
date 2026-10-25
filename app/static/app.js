// Dark Mode Toggle Functionality
class ThemeManager {
    constructor() {
        this.theme = this.getStoredTheme() || this.getPreferredTheme();
        this.init();
    }

    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    getPreferredTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    setStoredTheme(theme) {
        localStorage.setItem('theme', theme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.updateToggleButton(theme);
    }

    updateToggleButton(theme) {
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');

        if (theme === 'dark') {
            themeIcon.textContent = '☀️';
            themeText.textContent = 'Light';
        } else {
            themeIcon.textContent = '🌙';
            themeText.textContent = 'Dark';
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        this.setStoredTheme(newTheme);
        this.setTheme(newTheme);
        this.theme = newTheme;
    }

    init() {
        this.setTheme(this.theme);

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!this.getStoredTheme()) {
                const newTheme = e.matches ? 'dark' : 'light';
                this.setTheme(newTheme);
                this.theme = newTheme;
            }
        });

        // Add click listener to toggle button
        document.getElementById('theme-toggle').addEventListener('click', () => {
            this.toggleTheme();
        });
    }
}

// Initialize theme manager
const themeManager = new ThemeManager();

// File management functions
function clearFiles() {
    const fileInput = document.getElementById('files');
    const fileList = document.getElementById('file-list');
    const fileListContainer = document.getElementById('file-list-container');

    // Clear the file input
    fileInput.value = '';

    // Reset UI elements
    document.getElementById('file-label').textContent = 'Click or Drag-and-Drop files here...';
    document.getElementById('selected-files').textContent = '0';
    document.getElementById('file-count').style.display = 'none';

    // Clear and hide file list
    fileList.innerHTML = '';
    fileListContainer.style.display = 'none';
}

document.getElementById('clear-btn').addEventListener('click', clearFiles);

document.getElementById('files').addEventListener('change', function() {
    const fileCount = this.files.length;
    const fileList = document.getElementById('file-list');
    const fileListContainer = document.getElementById('file-list-container');

    // document.getElementById('selected-files').textContent = fileCount;
    // document.getElementById('file-count').style.display = 'block';

    // Clear previous file list
    fileList.innerHTML = '';

    if (fileCount > 0) {
        if (fileCount === 1) {
            document.getElementById('file-label').textContent = this.files[0].name;
        } else {
            document.getElementById('file-label').textContent = fileCount + ' files selected';
        }

        // Show file list and populate it
        fileListContainer.style.display = 'block';
        for (let i = 0; i < fileCount; i++) {
            const li = document.createElement('li');
            li.textContent = this.files[i].name;
            fileList.appendChild(li);
        }
    } else {
        document.getElementById('file-label').textContent = 'Click or Drag-and-Drop files here...';
        fileListContainer.style.display = 'none';
    }

    // Check if more than 10 files are selected
    if (fileCount > 10) {
        alert('You can only upload up to 10 files at a time.');
        clearFiles(); // Use the clear function for consistency
    }
});

document.querySelector('form').addEventListener('submit', function(e) {
    const form = e.target;

    // Clear files after form submission completes
    setTimeout(function() {
        // Check if we're still on the same page (no redirect occurred)
        // This suggests the form submission was processed
        clearFiles();
    }, 1500);
});
