// State management
let isLoading = false;
let validationTimeout = null;

// DOM elements
const keyInput = document.getElementById('keyInput');
const fetchButton = document.getElementById('fetchButton');
const resultDisplay = document.getElementById('result');
const loadingOverlay = document.getElementById('loading-overlay');
const toastContainer = document.getElementById('toast-container');
const inputValidation = document.querySelector('.input-validation');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    animateInitialElements();
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Key input events
    keyInput.addEventListener('input', handleKeyInput);
    keyInput.addEventListener('keypress', handleKeyPress);
    keyInput.addEventListener('focus', handleInputFocus);
    keyInput.addEventListener('blur', handleInputBlur);
    
    // Button events
    fetchButton.addEventListener('click', fetchCode);
    
    // Global keyboard shortcuts
    document.addEventListener('keydown', handleGlobalKeydown);
}

/**
 * Animate initial elements on page load
 */
function animateInitialElements() {
    // Add subtle entrance animations to particles
    const particles = document.querySelectorAll('.particle');
    particles.forEach((particle, index) => {
        particle.style.animationDelay = `${index * 2}s`;
    });
}

/**
 * Handle key input changes with real-time validation
 */
function handleKeyInput(event) {
    const key = event.target.value.trim();
    
    // Clear previous validation timeout
    if (validationTimeout) {
        clearTimeout(validationTimeout);
    }
    
    // Reset input styling
    keyInput.classList.remove('valid', 'invalid');
    inputValidation.classList.remove('show', 'valid', 'invalid');
    
    // Don't validate empty input
    if (!key) {
        return;
    }
    
    // Debounce validation
    validationTimeout = setTimeout(() => {
        validateKey(key);
    }, 500);
}

/**
 * Handle enter key press in input field
 */
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        if (!isLoading && keyInput.value.trim()) {
            fetchCode();
        }
    }
}

/**
 * Handle input focus
 */
function handleInputFocus() {
    keyInput.parentElement.classList.add('focused');
}

/**
 * Handle input blur
 */
function handleInputBlur() {
    keyInput.parentElement.classList.remove('focused');
}

/**
 * Handle global keyboard shortcuts
 */
function handleGlobalKeydown(event) {
    // Escape key to clear input
    if (event.key === 'Escape') {
        keyInput.value = '';
        keyInput.focus();
        resetInputValidation();
        resetResultDisplay();
    }
}

/**
 * Validate key in real-time
 */
async function validateKey(key) {
    try {
        const response = await fetch('/validate-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key })
        });
        
        const data = await response.json();
        
        // Update input styling based on validation
        if (data.valid) {
            keyInput.classList.add('valid');
            inputValidation.classList.add('show', 'valid');
            inputValidation.querySelector('.validation-message').textContent = data.message;
        } else {
            keyInput.classList.add('invalid');
            inputValidation.classList.add('show', 'invalid');
            inputValidation.querySelector('.validation-message').textContent = data.message;
        }
        
    } catch (error) {
        console.error('Validation error:', error);
        showToast('Validation failed. Please try again.', 'error');
    }
}

/**
 * Main function to fetch Netflix code
 */
async function fetchCode() {
    const key = keyInput.value.trim();
    
    // Validation
    if (!key) {
        showToast('Please enter your access key', 'error');
        keyInput.focus();
        return;
    }
    
    if (isLoading) {
        return;
    }
    
    // Start loading state
    setLoadingState(true);
    
    try {
        const response = await fetch('/get-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            displayCode(data.code);
            showToast('Netflix code retrieved successfully!', 'success');
        } else {
            displayError(data.error || 'Failed to fetch code');
            showToast(data.error || 'Failed to fetch Netflix code', 'error');
        }
        
    } catch (error) {
        console.error('Fetch error:', error);
        displayError('Network error. Please check your connection.');
        showToast('Network error. Please try again.', 'error');
    } finally {
        setLoadingState(false);
    }
}

/**
 * Set loading state for the application
 */
function setLoadingState(loading) {
    isLoading = loading;
    
    if (loading) {
        fetchButton.classList.add('loading');
        fetchButton.disabled = true;
        keyInput.disabled = true;
        loadingOverlay.classList.add('show');
    } else {
        fetchButton.classList.remove('loading');
        fetchButton.disabled = false;
        keyInput.disabled = false;
        loadingOverlay.classList.remove('show');
    }
}

/**
 * Display Netflix code with animation
 */
function displayCode(code) {
    resultDisplay.className = 'result-display result-code';
    
    const codeContent = document.createElement('div');
    codeContent.className = 'code-content';
    
    codeContent.innerHTML = `
        <div class="code-label">
            <i class="fas fa-ticket-alt"></i>
            Your Netflix Code
        </div>
        <div class="code-value" id="codeValue"></div>
        <button class="copy-button" onclick="copyCode('${code}')">
            <i class="fas fa-copy"></i>
            Copy Code
        </button>
    `;
    
    resultDisplay.innerHTML = '';
    resultDisplay.appendChild(codeContent);
    
    // Typewriter effect for the code
    typewriterEffect(document.getElementById('codeValue'), code);
}

/**
 * Display error message with animation
 */
function displayError(message) {
    resultDisplay.className = 'result-display result-error';
    
    resultDisplay.innerHTML = `
        <div class="error-content">
            <i class="fas fa-exclamation-triangle"></i>
            <div class="error-message">${message}</div>
            <button class="retry-button" onclick="retryFetch()">
                <i class="fas fa-redo"></i>
                Try Again
            </button>
        </div>
    `;
}

/**
 * Reset result display to initial state
 */
function resetResultDisplay() {
    resultDisplay.className = 'result-display';
    resultDisplay.innerHTML = `
        <div class="result-placeholder">
            <i class="fas fa-ticket-alt"></i>
            <span>Your Netflix code will appear here</span>
        </div>
    `;
}

/**
 * Reset input validation state
 */
function resetInputValidation() {
    keyInput.classList.remove('valid', 'invalid');
    inputValidation.classList.remove('show', 'valid', 'invalid');
}

/**
 * Typewriter effect for displaying code
 */
function typewriterEffect(element, text) {
    element.style.width = '0';
    element.style.borderRight = '2px solid hsl(var(--netflix-red-bright))';
    element.style.whiteSpace = 'nowrap';
    element.style.overflow = 'hidden';
    
    let i = 0;
    const typeInterval = setInterval(() => {
        element.textContent = text.slice(0, i + 1);
        element.style.width = 'auto';
        i++;
        
        if (i >= text.length) {
            clearInterval(typeInterval);
            // Remove cursor after animation
            setTimeout(() => {
                element.style.borderRight = 'none';
            }, 500);
        }
    }, 100);
}

/**
 * Copy code to clipboard
 */
async function copyCode(code) {
    try {
        await navigator.clipboard.writeText(code);
        showToast('Code copied to clipboard!', 'success');
        
        // Visual feedback on copy button
        const copyButton = document.querySelector('.copy-button');
        const originalText = copyButton.innerHTML;
        copyButton.innerHTML = '<i class="fas fa-check"></i> Copied!';
        copyButton.style.background = 'hsl(var(--success))';
        
        setTimeout(() => {
            copyButton.innerHTML = originalText;
            copyButton.style.background = '';
        }, 2000);
        
    } catch (error) {
        console.error('Copy failed:', error);
        showToast('Failed to copy code', 'error');
    }
}

/**
 * Retry fetching code
 */
function retryFetch() {
    resetResultDisplay();
    keyInput.focus();
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle',
        warning: 'fas fa-exclamation-triangle'
    };
    
    toast.innerHTML = `
        <div class="toast-content">
            <i class="toast-icon ${iconMap[type] || iconMap.info}"></i>
            <div class="toast-message">${message}</div>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove toast after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease-out reverse';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 5000);
    
    // Click to dismiss
    toast.addEventListener('click', () => {
        toast.style.animation = 'slideInRight 0.3s ease-out reverse';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    });
}

/**
 * Utility function to debounce function calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Initialize error handling for unhandled promise rejections
 */
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('An unexpected error occurred', 'error');
});

/**
 * Handle network status changes
 */
window.addEventListener('online', function() {
    showToast('Connection restored', 'success');
});

window.addEventListener('offline', function() {
    showToast('Connection lost. Please check your internet.', 'warning');
});
