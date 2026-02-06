const API_HOST = window.location.hostname || 'localhost';
const DEFAULT_API_BASE_URL = `http://${API_HOST}:5001`;
const CONFIGURED_API_BASE_URL = (
    window.APP_CONFIG && typeof window.APP_CONFIG.API_BASE_URL === 'string'
        ? window.APP_CONFIG.API_BASE_URL.trim()
        : null
);
const IS_LOCAL_HOST = API_HOST === 'localhost' || API_HOST === '127.0.0.1';
const API_BASE_URL = (
    CONFIGURED_API_BASE_URL === ''
        ? (IS_LOCAL_HOST ? DEFAULT_API_BASE_URL : '')
        : (CONFIGURED_API_BASE_URL || DEFAULT_API_BASE_URL)
).replace(/\/+$/, '');
const API_URL = `${API_BASE_URL}/api`;

// State
let recipes = [];
let currentFilter = 'all';
let currentSearchQuery = '';
let currentSearchMode = 'name';
let isAuthenticated = false;

// DOM Elements
const loginScreen = document.getElementById('login-screen');
const appScreen = document.getElementById('app-screen');
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const logoutBtn = document.getElementById('logout-btn');
const addRecipeForm = document.getElementById('add-recipe-form');
const manualRecipeForm = document.getElementById('manual-recipe-form');
const openManualModalBtn = document.getElementById('open-manual-modal-btn');
const recipeUrlInput = document.getElementById('recipe-url');
const recipeSearchInput = document.getElementById('recipe-search');
const searchModeSelect = document.getElementById('search-mode');
const scrapeStatus = document.getElementById('scrape-status');
const manualStatus = document.getElementById('manual-status');
const recipesContainer = document.getElementById('recipes-container');
const filterBtns = document.querySelectorAll('.filter-btn');
const recipeModal = document.getElementById('recipe-modal');
const recipeModalClose = document.getElementById('recipe-modal-close');
const manualModal = document.getElementById('manual-modal');
const manualModalClose = document.getElementById('manual-modal-close');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateSearchPlaceholder();
    checkAuth();
    setupEventListeners();
});

function setupEventListeners() {
    loginForm.addEventListener('submit', handleLogin);
    logoutBtn.addEventListener('click', handleLogout);
    addRecipeForm.addEventListener('submit', handleAddRecipe);
    manualRecipeForm.addEventListener('submit', handleAddManualRecipe);
    openManualModalBtn.addEventListener('click', openManualModal);
    recipeSearchInput.addEventListener('input', handleSearch);
    searchModeSelect.addEventListener('change', handleSearchModeChange);
    filterBtns.forEach(btn => {
        btn.addEventListener('click', handleFilter);
    });
    recipeModalClose.addEventListener('click', closeModal);
    manualModalClose.addEventListener('click', closeManualModal);
    window.addEventListener('click', (e) => {
        if (e.target === recipeModal) {
            closeModal();
        }
        if (e.target === manualModal) {
            closeManualModal();
        }
    });
}

function updateSearchPlaceholder() {
    recipeSearchInput.placeholder = currentSearchMode === 'ingredient'
        ? 'Search ingredients (e.g., chicken)...'
        : 'Search recipe names...';
}

function parseManualIngredients(rawText) {
    const lines = String(rawText || '')
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);

    const groups = [];
    let currentGroup = { section: 'Ingredients', items: [] };

    for (const rawLine of lines) {
        const line = rawLine.replace(/^[-*]\s+/, '').trim();
        if (!line) {
            continue;
        }

        if (line.endsWith(':') && line.length > 1) {
            if (currentGroup.items.length > 0) {
                groups.push(currentGroup);
            }
            currentGroup = { section: line.slice(0, -1).trim(), items: [] };
            continue;
        }

        currentGroup.items.push(line);
    }

    if (currentGroup.items.length > 0) {
        groups.push(currentGroup);
    }

    return groups;
}

// Authentication
function checkAuth() {
    // Check if session is authenticated
    fetch(`${API_URL}/recipes`, {
        credentials: 'include'
    })
    .then(response => {
        if (response.ok) {
            showApp();
        } else {
            showLogin();
        }
    })
    .catch(() => showLogin());
}

async function handleLogin(e) {
    e.preventDefault();
    const password = document.getElementById('password-input').value;

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ password })
        });

        if (response.ok) {
            showApp();
        } else {
            const data = await response.json().catch(() => ({}));
            if (response.status === 401) {
                loginError.textContent = data.error || 'Invalid password';
            } else {
                loginError.textContent = data.error || `Login failed (API ${response.status})`;
            }
        }
    } catch (error) {
        loginError.textContent = `Connection error (${API_URL})`;
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_URL}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        showLogin();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

function showLogin() {
    loginScreen.classList.add('active');
    appScreen.classList.remove('active');
    isAuthenticated = false;
}

function showApp() {
    loginScreen.classList.remove('active');
    appScreen.classList.add('active');
    isAuthenticated = true;
    loadRecipes();
}

// Recipe Management
async function loadRecipes() {
    try {
        const response = await fetch(`${API_URL}/recipes`, {
            credentials: 'include'
        });

        if (response.ok) {
            recipes = await response.json();
            renderRecipes();
        } else if (response.status === 401) {
            showLogin();
        } else {
            const error = await response.json().catch(() => ({}));
            recipesContainer.innerHTML = `<p class="error">Failed to load recipes: ${error.error || 'Unexpected server error'}</p>`;
        }
    } catch (error) {
        recipesContainer.innerHTML = `<p class="error">Failed to load recipes: ${error.message}</p>`;
    }
}

async function handleAddRecipe(e) {
    e.preventDefault();
    const url = recipeUrlInput.value;

    scrapeStatus.textContent = 'Scraping recipe...';
    scrapeStatus.className = 'status-message';

    try {
        const response = await fetch(`${API_URL}/recipes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ url })
        });

        if (response.ok) {
            scrapeStatus.textContent = 'Recipe added successfully!';
            scrapeStatus.classList.add('success');
            recipeUrlInput.value = '';
            setTimeout(() => {
                scrapeStatus.textContent = '';
                scrapeStatus.className = 'status-message';
            }, 3000);
            loadRecipes();
        } else {
            const error = await response.json();
            scrapeStatus.textContent = error.error || 'Failed to add recipe';
            scrapeStatus.classList.add('error');
        }
    } catch (error) {
        scrapeStatus.textContent = `Error: ${error.message}`;
        scrapeStatus.classList.add('error');
    }
}

async function handleAddManualRecipe(e) {
    e.preventDefault();

    const title = document.getElementById('manual-title').value.trim();
    const ingredientsText = document.getElementById('manual-ingredients').value;
    const instructions = document.getElementById('manual-instructions').value.trim();
    const yields = document.getElementById('manual-yields').value.trim();
    const totalTime = document.getElementById('manual-total-time').value.trim();
    const sourceUrl = document.getElementById('manual-source-url').value.trim();
    const imageUrl = document.getElementById('manual-image-url').value.trim();
    const ingredients = parseManualIngredients(ingredientsText);

    manualStatus.textContent = 'Saving manual recipe...';
    manualStatus.className = 'status-message';

    if (!title || !instructions || ingredients.length === 0) {
        manualStatus.textContent = 'Title, ingredients, and instructions are required.';
        manualStatus.classList.add('error');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/recipes/manual`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                title,
                ingredients,
                instructions,
                yields: yields || null,
                total_time: totalTime || null,
                source_url: sourceUrl || null,
                image_url: imageUrl || null
            })
        });

        if (response.ok) {
            manualStatus.textContent = 'Manual recipe saved!';
            manualStatus.classList.add('success');
            manualRecipeForm.reset();
            loadRecipes();
            setTimeout(() => {
                manualStatus.textContent = '';
                manualStatus.className = 'status-message';
            }, 3000);
            closeManualModal();
        } else {
            const error = await response.json().catch(() => ({}));
            manualStatus.textContent = error.error || 'Failed to save manual recipe';
            manualStatus.classList.add('error');
        }
    } catch (error) {
        manualStatus.textContent = `Error: ${error.message}`;
        manualStatus.classList.add('error');
    }
}

function openManualModal() {
    manualStatus.textContent = '';
    manualStatus.className = 'status-message';
    manualModal.classList.add('active');
}

function closeManualModal() {
    manualModal.classList.remove('active');
}

function handleFilter(e) {
    currentFilter = e.target.dataset.filter;
    filterBtns.forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    renderRecipes();
}

function handleSearch(e) {
    currentSearchQuery = e.target.value.trim().toLowerCase();
    renderRecipes();
}

function handleSearchModeChange(e) {
    currentSearchMode = e.target.value;
    updateSearchPlaceholder();
    renderRecipes();
}

function escapeHtml(value) {
    return String(value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function renderIngredientGroups(ingredients) {
    if (!ingredients) {
        return '<p>No ingredients available</p>';
    }

    let groups = [];
    if (Array.isArray(ingredients) && ingredients.length > 0 && typeof ingredients[0] === 'object' && ingredients[0].items) {
        groups = ingredients.map(group => ({
            section: group.section || 'Ingredients',
            items: Array.isArray(group.items) ? group.items : []
        }));
    } else if (Array.isArray(ingredients)) {
        groups = [{ section: 'Ingredients', items: ingredients }];
    }

    if (!groups.length) {
        return '<p>No ingredients available</p>';
    }

    if (groups.length === 1 && (groups[0].section || '').toLowerCase() === 'ingredients') {
        return `
            <ul>
                ${(groups[0].items || []).map(item => `<li>${escapeHtml(item)}</li>`).join('')}
            </ul>
        `;
    }

    return groups.map(group => `
        <div class="ingredient-group">
            <h4>${escapeHtml(group.section)}</h4>
            <ul>
                ${(group.items || []).map(item => `<li>${escapeHtml(item)}</li>`).join('')}
            </ul>
        </div>
    `).join('');
}

function parseInstructionSteps(instructions) {
    const raw = String(instructions || '').trim();
    if (!raw) {
        return [];
    }

    const steps = [];
    const stepRegex = /Step\s+(\d+)(?::\s*([^\n]+))?\n?([\s\S]*?)(?=\n\nStep\s+\d+|$)/g;
    let match = null;

    while ((match = stepRegex.exec(raw)) !== null) {
        const number = match[1];
        const title = (match[2] || '').trim();
        const body = (match[3] || '').trim();
        steps.push({
            heading: title ? `Step ${number}: ${title}` : `Step ${number}`,
            body
        });
    }

    return steps;
}

function renderInstructions(instructions) {
    const steps = parseInstructionSteps(instructions);
    if (steps.length > 0) {
        return `
            <div class="instructions-list">
                ${steps.map(step => `
                    <section class="instruction-step">
                        <h4>${escapeHtml(step.heading)}</h4>
                        <p>${escapeHtml(step.body)}</p>
                    </section>
                `).join('')}
            </div>
        `;
    }

    if (!instructions) {
        return '<p>No instructions available</p>';
    }
    return `<p>${escapeHtml(instructions)}</p>`;
}

function collectRecipeIngredientText(recipe) {
    const ingredients = recipe.ingredients;
    if (!Array.isArray(ingredients) || ingredients.length === 0) {
        return '';
    }

    // Supports both legacy flat arrays and grouped ingredient payloads.
    if (typeof ingredients[0] === 'object' && ingredients[0] !== null && 'items' in ingredients[0]) {
        const chunks = [];
        for (const group of ingredients) {
            const section = typeof group.section === 'string' ? group.section : '';
            const items = Array.isArray(group.items) ? group.items : [];
            if (section) {
                chunks.push(section);
            }
            for (const item of items) {
                chunks.push(String(item));
            }
        }
        return chunks.join(' ').toLowerCase();
    }

    return ingredients.map(item => String(item)).join(' ').toLowerCase();
}

function recipeMatchesSearch(recipe, query) {
    if (!query) {
        return true;
    }

    const titleText = (recipe.title || '').toLowerCase();
    const ingredientText = collectRecipeIngredientText(recipe);
    if (currentSearchMode === 'ingredient') {
        return ingredientText.includes(query);
    }
    return titleText.includes(query);
}

function renderRecipes() {
    const filteredRecipes = recipes.filter(recipe => {
        const statusMatches = currentFilter === 'all' || recipe.status === currentFilter;
        const queryMatches = recipeMatchesSearch(recipe, currentSearchQuery);
        return statusMatches && queryMatches;
    });

    if (filteredRecipes.length === 0) {
        recipesContainer.innerHTML = '<p class="loading">No recipes found for your current filter and search.</p>';
        return;
    }

    recipesContainer.innerHTML = filteredRecipes.map((recipe, index) => `
        <div class="recipe-card" style="--i:${index}" onclick="openRecipeModal('${recipe.id}')">
            ${recipe.image_url ? `<img src="${recipe.image_url}" alt="${recipe.title}">` : ''}
            <div class="recipe-card-content">
                <h3>${recipe.title}</h3>
                <span class="recipe-status ${recipe.status}">
                    ${recipe.status === 'want_to_cook' ? 'Want to Cook' : 'Already Cooked'}
                </span>
                ${recipe.rating ? `<div class="recipe-rating">${'⭐'.repeat(recipe.rating)}</div>` : ''}
                ${recipe.notes ? `<p class="recipe-notes">"${recipe.notes}"</p>` : ''}
            </div>
        </div>
    `).join('');
}

function openRecipeModal(recipeId) {
    const recipe = recipes.find(r => r.id === recipeId);
    if (!recipe) return;

    const ingredientsHtml = renderIngredientGroups(recipe.ingredients);
    const instructionsHtml = renderInstructions(recipe.instructions);

    const sourceLink = recipe.url && recipe.url.startsWith('http')
        ? `<p style="margin-top: 20px;"><a href="${recipe.url}" target="_blank">View Original Recipe</a></p>`
        : '';

    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        ${recipe.image_url ? `<img src="${recipe.image_url}" alt="${recipe.title}">` : ''}
        <h2>${recipe.title}</h2>
        ${recipe.total_time ? `<p><strong>Total Time:</strong> ${recipe.total_time} minutes</p>` : ''}
        ${recipe.yields ? `<p><strong>Yields:</strong> ${recipe.yields}</p>` : ''}

        <h3>Ingredients</h3>
        ${ingredientsHtml}

        <h3>Instructions</h3>
        ${instructionsHtml}

        <div class="modal-actions">
            <select id="modal-status" value="${recipe.status}">
                <option value="want_to_cook" ${recipe.status === 'want_to_cook' ? 'selected' : ''}>Want to Cook</option>
                <option value="already_cooked" ${recipe.status === 'already_cooked' ? 'selected' : ''}>Already Cooked</option>
            </select>

            <select id="modal-rating">
                <option value="">No Rating</option>
                <option value="1" ${recipe.rating === 1 ? 'selected' : ''}>⭐</option>
                <option value="2" ${recipe.rating === 2 ? 'selected' : ''}>⭐⭐</option>
                <option value="3" ${recipe.rating === 3 ? 'selected' : ''}>⭐⭐⭐</option>
                <option value="4" ${recipe.rating === 4 ? 'selected' : ''}>⭐⭐⭐⭐</option>
                <option value="5" ${recipe.rating === 5 ? 'selected' : ''}>⭐⭐⭐⭐⭐</option>
            </select>

            <textarea id="modal-notes" placeholder="Add notes...">${recipe.notes || ''}</textarea>

            <button onclick="updateRecipe('${recipe.id}')">Save Changes</button>
            <button class="delete" onclick="deleteRecipe('${recipe.id}')">Delete Recipe</button>
        </div>

        ${sourceLink}
    `;

    recipeModal.classList.add('active');
}

function closeModal() {
    recipeModal.classList.remove('active');
}

async function updateRecipe(recipeId) {
    const status = document.getElementById('modal-status').value;
    const rating = document.getElementById('modal-rating').value;
    const notes = document.getElementById('modal-notes').value;

    try {
        const response = await fetch(`${API_URL}/recipes/${recipeId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                status,
                rating: rating ? parseInt(rating) : null,
                notes,
                date_cooked: status === 'already_cooked' ? new Date().toISOString() : null
            })
        });

        if (response.ok) {
            closeModal();
            loadRecipes();
        } else {
            alert('Failed to update recipe');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function deleteRecipe(recipeId) {
    if (!confirm('Are you sure you want to delete this recipe?')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/recipes/${recipeId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            closeModal();
            loadRecipes();
        } else {
            alert('Failed to delete recipe');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}
