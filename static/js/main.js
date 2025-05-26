// Set global configuration
window.STATIC_URL = document.currentScript.getAttribute('data-static-url') || '/static/';
window.DEBUG = document.currentScript.getAttribute('data-debug') === 'true';

// Debug information
if (window.DEBUG) {
    console.log('Static URL set to:', window.STATIC_URL);
    console.log('Debug mode:', window.DEBUG);
}

// Main initialization
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const themeToggle = document.getElementById('theme-toggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const userMenuButton = document.getElementById('user-menu-button');
    const userDropdown = document.querySelector('.user-dropdown');
    const html = document.documentElement;
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

    // Toggle sidebar on mobile
    function toggleSidebar() {
        if (sidebar) {
            sidebar.classList.toggle('open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('open');
            }
        }
    }

    // Close sidebar when clicking outside
    function closeSidebar(e) {
        if (sidebar && !sidebar.contains(e.target) && sidebarToggle && !sidebarToggle.contains(e.target)) {
            sidebar.classList.remove('open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.remove('open');
            }
        }
    }

    // Toggle user dropdown
    function toggleUserDropdown() {
        if (userDropdown && userMenuButton) {
            userDropdown.classList.toggle('hidden');
            const isExpanded = userMenuButton.getAttribute('aria-expanded') === 'true';
            userMenuButton.setAttribute('aria-expanded', !isExpanded);
        }
    }

    // Close dropdown when clicking outside
    function closeDropdowns(e) {
        if (userDropdown && userMenuButton && 
            !userMenuButton.contains(e.target) && 
            !(userDropdown && userDropdown.contains(e.target))) {
            userDropdown.classList.add('hidden');
            userMenuButton.setAttribute('aria-expanded', 'false');
        }
    }

    // Theme management
    function updateTheme() {
        if (localStorage.theme === 'dark' || (!('theme' in localStorage) && prefersDarkScheme.matches)) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }

    // Event Listeners
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isDark = html.classList.toggle('dark');
            localStorage.theme = isDark ? 'dark' : 'light';
        });
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', toggleSidebar);
    }

    if (userMenuButton) {
        userMenuButton.addEventListener('click', toggleUserDropdown);
    }

    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
        closeSidebar(e);
        closeDropdowns(e);
    });

    // Initialize theme
    updateTheme();
    
    // Watch for system theme changes
    prefersDarkScheme.addListener(updateTheme);
});
