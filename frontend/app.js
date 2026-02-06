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
const INGREDIENT_ALIAS_MAP = [
    ['chicken thighs', 'chicken'],
    ['chicken thigh', 'chicken'],
    ['chicken breasts', 'chicken'],
    ['chicken breast', 'chicken'],
    ['ground chicken', 'chicken'],
    ['pork ribs', 'pork'],
    ['pork rib', 'pork'],
    ['ground pork', 'pork'],
    ['beef ribs', 'beef'],
    ['ground beef', 'beef'],
    ['scallions', 'green onion'],
    ['spring onions', 'green onion'],
    ['green onions', 'green onion'],
    ['garbanzo beans', 'chickpea'],
    ['chick peas', 'chickpea'],
    ['bell peppers', 'bell pepper'],
    ['capsicum', 'bell pepper'],
    ['cilantro', 'coriander'],
    ['romaine lettuce', 'lettuce'],
    ['iceberg lettuce', 'lettuce'],
    ['all purpose flour', 'flour'],
    ['plain flour', 'flour'],
    ['caster sugar', 'sugar'],
    ['powdered sugar', 'sugar'],
    ['confectioners sugar', 'sugar']
];
const INGREDIENT_STOP_WORDS = new Set([
    'a', 'an', 'and', 'or', 'the', 'of', 'to', 'for', 'with', 'optional',
    'fresh', 'dried', 'chopped', 'minced', 'large', 'small', 'medium',
    'cup', 'cups', 'tbsp', 'tsp', 'teaspoon', 'teaspoons', 'tablespoon',
    'tablespoons', 'ounce', 'ounces', 'oz', 'gram', 'grams', 'g', 'kg',
    'lb', 'lbs', 'ml', 'l', 'taste'
]);
const SHOPPING_CATEGORY_ORDER = [
    'Produce',
    'Meat/Seafood',
    'Dairy/Eggs',
    'Grains/Bread',
    'Spices/Seasonings',
    'Sauces/Oils/Condiments',
    'Canned/Pantry',
    'Other'
];
const SHOPPING_CATEGORY_KEYWORDS = {
    'Produce': [
        'onion', 'garlic', 'shallot', 'ginger', 'scallion', 'green onion',
        'tomato', 'lettuce', 'cabbage', 'spinach', 'kale', 'carrot', 'celery',
        'potato', 'mushroom', 'pepper', 'jalapeno', 'chili', 'banana blossom',
        'beansprout', 'bean sprout', 'cilantro', 'parsley', 'basil', 'mint',
        'oregano', 'thyme', 'lemon', 'lime', 'avocado', 'apple', 'banana',
        'perilla'
    ],
    'Meat/Seafood': [
        'chicken', 'beef', 'pork', 'turkey', 'lamb', 'veal', 'duck',
        'sausage', 'bacon', 'ham', 'fish', 'salmon', 'tuna', 'cod', 'shrimp',
        'prawn', 'crab', 'lobster', 'anchovy', 'sardine'
    ],
    'Dairy/Eggs': [
        'milk', 'cream', 'butter', 'cheese', 'parmesan', 'mozzarella',
        'cheddar', 'yogurt', 'yoghurt', 'egg', 'eggs'
    ],
    'Grains/Bread': [
        'rice', 'pasta', 'spaghetti', 'noodle', 'vermicelli', 'flour', 'oat',
        'quinoa', 'barley', 'bread', 'pita', 'tortilla', 'wrap', 'bun'
    ],
    'Spices/Seasonings': [
        'salt', 'pepper', 'paprika', 'cumin', 'coriander', 'turmeric',
        'cayenne', 'chili powder', 'red pepper flakes', 'bay leaf', 'bay leaves',
        'cinnamon', 'nutmeg', 'clove', 'allspice', 'msg', 'seasoning'
    ],
    'Sauces/Oils/Condiments': [
        'oil', 'olive oil', 'sesame oil', 'vinegar', 'soy sauce', 'fish sauce',
        'hot sauce', 'sriracha', 'ketchup', 'mustard', 'mayo', 'mayonnaise',
        'aioli', 'dressing'
    ],
    'Canned/Pantry': [
        'broth', 'stock', 'bouillon', 'tomato paste', 'tomato sauce',
        'coconut milk', 'beans', 'lentils', 'chickpea', 'sugar', 'honey',
        'maple syrup', 'peanut butter', 'jam', 'jelly'
    ]
};

// State
let recipes = [];
let currentFilter = 'all';
let currentSearchQuery = '';
let currentSearchMode = 'name';
let isAuthenticated = false;
let pendingPreviewSourceUrl = '';
let activeRecipeInModal = null;
let isShoppingViewEnabled = false;

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
const previewModal = document.getElementById('preview-modal');
const previewModalClose = document.getElementById('preview-modal-close');
const previewCancelBtn = document.getElementById('preview-cancel-btn');
const previewRecipeForm = document.getElementById('preview-recipe-form');
const previewStatus = document.getElementById('preview-status');
const editRecipeModal = document.getElementById('edit-recipe-modal');
const editRecipeModalClose = document.getElementById('edit-recipe-modal-close');
const editCancelBtn = document.getElementById('edit-cancel-btn');
const editRecipeForm = document.getElementById('edit-recipe-form');
const editStatus = document.getElementById('edit-status');

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
    previewRecipeForm.addEventListener('submit', handleSavePreviewRecipe);
    editRecipeForm.addEventListener('submit', handleSaveEditedRecipe);
    openManualModalBtn.addEventListener('click', openManualModal);
    recipeSearchInput.addEventListener('input', handleSearch);
    searchModeSelect.addEventListener('change', handleSearchModeChange);
    filterBtns.forEach(btn => {
        btn.addEventListener('click', handleFilter);
    });
    recipeModalClose.addEventListener('click', closeModal);
    manualModalClose.addEventListener('click', closeManualModal);
    previewModalClose.addEventListener('click', closePreviewModal);
    previewCancelBtn.addEventListener('click', closePreviewModal);
    editRecipeModalClose.addEventListener('click', closeEditRecipeModal);
    editCancelBtn.addEventListener('click', closeEditRecipeModal);
    window.addEventListener('click', (e) => {
        if (e.target === recipeModal) {
            closeModal();
        }
        if (e.target === manualModal) {
            closeManualModal();
        }
        if (e.target === previewModal) {
            closePreviewModal();
        }
        if (e.target === editRecipeModal) {
            closeEditRecipeModal();
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

function ingredientGroupsToText(ingredients) {
    if (!Array.isArray(ingredients) || ingredients.length === 0) {
        return '';
    }

    if (typeof ingredients[0] === 'string') {
        return ingredients.map(item => String(item)).join('\n');
    }

    const groups = ingredients
        .filter(group => group && typeof group === 'object')
        .map(group => ({
            section: String(group.section || 'Ingredients').trim() || 'Ingredients',
            items: Array.isArray(group.items) ? group.items : []
        }))
        .filter(group => group.items.length > 0);

    if (!groups.length) {
        return '';
    }

    const includeSectionHeaders = (
        groups.length > 1 ||
        (groups[0].section || '').toLowerCase() !== 'ingredients'
    );

    const lines = [];
    for (const group of groups) {
        if (includeSectionHeaders) {
            lines.push(`${group.section}:`);
        }
        for (const item of group.items) {
            lines.push(String(item).trim());
        }
        if (includeSectionHeaders) {
            lines.push('');
        }
    }

    return lines.join('\n').trim();
}

function normalizeIngredientText(text) {
    return String(text || '')
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

function singularizeToken(token) {
    if (token.length <= 3) {
        return token;
    }
    if (token.endsWith('ies') && token.length > 4) {
        return `${token.slice(0, -3)}y`;
    }
    if (token.endsWith('es') && token.length > 4) {
        return token.slice(0, -2);
    }
    if (token.endsWith('s') && !token.endsWith('ss')) {
        return token.slice(0, -1);
    }
    return token;
}

function tokenizeIngredientSearch(rawText) {
    const normalized = normalizeIngredientText(rawText);
    if (!normalized) {
        return new Set();
    }

    let expanded = normalized;
    for (const [alias, canonical] of INGREDIENT_ALIAS_MAP) {
        const aliasPattern = new RegExp(`\\b${alias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
        if (aliasPattern.test(normalized)) {
            expanded += ` ${canonical}`;
        }
    }

    const tokens = new Set();
    for (const token of expanded.split(/\s+/)) {
        if (!token || INGREDIENT_STOP_WORDS.has(token)) {
            continue;
        }
        tokens.add(token);
        const singular = singularizeToken(token);
        if (singular && !INGREDIENT_STOP_WORDS.has(singular)) {
            tokens.add(singular);
        }
    }
    return tokens;
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
    const url = recipeUrlInput.value.trim();

    scrapeStatus.textContent = 'Scraping recipe... hang tight!';
    scrapeStatus.className = 'status-message loading-scrape';

    try {
        const response = await fetch(`${API_URL}/recipes/preview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ url })
        });

        if (response.ok) {
            const recipeData = await response.json();
            openPreviewModal(recipeData, url);
            scrapeStatus.textContent = 'Preview ready. Review and save the recipe.';
            scrapeStatus.classList.add('success');
            setTimeout(() => {
                scrapeStatus.textContent = '';
                scrapeStatus.className = 'status-message';
            }, 4000);
        } else if (response.status === 401) {
            showLogin();
        } else {
            const error = await response.json().catch(() => ({}));
            scrapeStatus.textContent = error.error || 'Failed to preview recipe';
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

function openPreviewModal(recipeData, sourceUrl) {
    pendingPreviewSourceUrl = String(sourceUrl || recipeData.url || '').trim();

    document.getElementById('preview-title').value = recipeData.title ?? '';
    document.getElementById('preview-yields').value = recipeData.yields ?? '';
    document.getElementById('preview-total-time').value = recipeData.total_time ?? '';
    document.getElementById('preview-source-url').value = pendingPreviewSourceUrl;
    document.getElementById('preview-image-url').value = recipeData.image_url ?? '';
    document.getElementById('preview-ingredients').value = ingredientGroupsToText(recipeData.ingredients);
    document.getElementById('preview-instructions').value = recipeData.instructions ?? '';

    previewStatus.textContent = '';
    previewStatus.className = 'status-message';
    previewModal.classList.add('active');
}

function closePreviewModal() {
    previewModal.classList.remove('active');
    pendingPreviewSourceUrl = '';
    previewStatus.textContent = '';
    previewStatus.className = 'status-message';
    previewRecipeForm.reset();
}

function openEditRecipeModal(recipeId) {
    const recipe = recipes.find(r => r.id === recipeId);
    if (!recipe) {
        return;
    }

    document.getElementById('edit-recipe-id').value = recipe.id;
    document.getElementById('edit-title').value = recipe.title ?? '';
    document.getElementById('edit-yields').value = recipe.yields ?? '';
    document.getElementById('edit-total-time').value = recipe.total_time ?? '';
    document.getElementById('edit-source-url').value = recipe.url && recipe.url.startsWith('http')
        ? recipe.url
        : '';
    document.getElementById('edit-image-url').value = recipe.image_url ?? '';
    document.getElementById('edit-ingredients').value = ingredientGroupsToText(recipe.ingredients);
    document.getElementById('edit-instructions').value = recipe.instructions ?? '';

    editStatus.textContent = '';
    editStatus.className = 'status-message';
    closeModal();
    editRecipeModal.classList.add('active');
}

function closeEditRecipeModal() {
    editRecipeModal.classList.remove('active');
    editStatus.textContent = '';
    editStatus.className = 'status-message';
    editRecipeForm.reset();
}

async function handleSavePreviewRecipe(e) {
    e.preventDefault();

    const title = document.getElementById('preview-title').value.trim();
    const ingredientsText = document.getElementById('preview-ingredients').value;
    const instructions = document.getElementById('preview-instructions').value.trim();
    const yields = document.getElementById('preview-yields').value.trim();
    const totalTime = document.getElementById('preview-total-time').value.trim();
    const sourceUrl = document.getElementById('preview-source-url').value.trim() || pendingPreviewSourceUrl;
    const imageUrl = document.getElementById('preview-image-url').value.trim();
    const ingredients = parseManualIngredients(ingredientsText);

    if (!title || !instructions || ingredients.length === 0) {
        previewStatus.textContent = 'Title, ingredients, and instructions are required.';
        previewStatus.className = 'status-message error';
        return;
    }

    previewStatus.textContent = 'Saving recipe...';
    previewStatus.className = 'status-message';

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
            previewStatus.textContent = 'Recipe saved!';
            previewStatus.className = 'status-message success';
            recipeUrlInput.value = '';
            setTimeout(() => {
                closePreviewModal();
            }, 500);
            loadRecipes();
        } else if (response.status === 401) {
            showLogin();
        } else {
            const error = await response.json().catch(() => ({}));
            previewStatus.textContent = error.error || 'Failed to save recipe';
            previewStatus.className = 'status-message error';
        }
    } catch (error) {
        previewStatus.textContent = `Error: ${error.message}`;
        previewStatus.className = 'status-message error';
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
    currentSearchQuery = e.target.value.trim();
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

function flattenIngredientItems(ingredients) {
    if (!Array.isArray(ingredients) || ingredients.length === 0) {
        return [];
    }

    if (typeof ingredients[0] === 'object' && ingredients[0] !== null && 'items' in ingredients[0]) {
        const items = [];
        for (const group of ingredients) {
            const groupItems = Array.isArray(group.items) ? group.items : [];
            for (const item of groupItems) {
                const cleaned = String(item || '').trim();
                if (cleaned) {
                    items.push(cleaned);
                }
            }
        }
        return items;
    }

    return ingredients
        .map(item => String(item || '').trim())
        .filter(Boolean);
}

function includesIngredientWord(text, keyword) {
    const safe = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return new RegExp(`\\b${safe}\\b`).test(text);
}

function categorizeIngredient(item) {
    const normalized = normalizeIngredientText(item);
    if (!normalized) {
        return 'Other';
    }

    // Pantry terms should win for things like chicken broth.
    if (
        includesIngredientWord(normalized, 'broth') ||
        includesIngredientWord(normalized, 'stock') ||
        includesIngredientWord(normalized, 'bouillon')
    ) {
        return 'Canned/Pantry';
    }

    for (const category of SHOPPING_CATEGORY_ORDER) {
        const keywords = SHOPPING_CATEGORY_KEYWORDS[category] || [];
        if (keywords.some(keyword => includesIngredientWord(normalized, keyword))) {
            return category;
        }
    }

    return 'Other';
}

function renderShoppingIngredientGroups(ingredients) {
    const items = flattenIngredientItems(ingredients);
    if (!items.length) {
        return '<p>No ingredients available</p>';
    }

    const grouped = {};
    for (const category of SHOPPING_CATEGORY_ORDER) {
        grouped[category] = [];
    }

    for (const item of items) {
        const category = categorizeIngredient(item);
        grouped[category].push(item);
    }

    const sections = SHOPPING_CATEGORY_ORDER
        .filter(category => grouped[category].length > 0)
        .map(category => `
            <div class="ingredient-group shopping-group">
                <h4>${escapeHtml(category)}</h4>
                <ul>
                    ${grouped[category].map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                </ul>
            </div>
        `)
        .join('');

    return sections || '<p>No ingredients available</p>';
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
    const cleanedQuery = String(query || '').trim();
    if (!cleanedQuery) {
        return true;
    }

    const titleText = (recipe.title || '').toLowerCase();
    const ingredientText = collectRecipeIngredientText(recipe);
    if (currentSearchMode === 'ingredient') {
        const queryTokens = tokenizeIngredientSearch(cleanedQuery);
        if (queryTokens.size === 0) {
            return true;
        }

        const recipeTokens = tokenizeIngredientSearch(ingredientText);
        for (const token of queryTokens) {
            if (!recipeTokens.has(token)) {
                return false;
            }
        }
        return true;
    }
    return titleText.includes(cleanedQuery.toLowerCase());
}

function renderRecipes() {
    const filteredRecipes = recipes.filter(recipe => {
        const statusMatches = currentFilter === 'all' || recipe.status === currentFilter;
        const queryMatches = recipeMatchesSearch(recipe, currentSearchQuery);
        return statusMatches && queryMatches;
    });

    if (filteredRecipes.length === 0) {
        const emptyMessages = [
            'Nothing here yet... time to find something delicious!',
            'No recipes match that. Try a different search?',
            'This shelf is empty. Let\'s fill it up!',
        ];
        const msg = currentSearchQuery || currentFilter !== 'all'
            ? emptyMessages[1]
            : emptyMessages[0];
        recipesContainer.innerHTML = `
            <div class="no-recipes-msg">
                <div class="empty-icon">&#128214;</div>
                <p>${msg}</p>
            </div>`;
        return;
    }

    recipesContainer.innerHTML = filteredRecipes.map((recipe, index) => {
        const hasTime = recipe.total_time;
        const hasYields = recipe.yields;
        const metaHtml = (hasTime || hasYields) ? `
            <div class="recipe-meta">
                ${hasTime ? `<span>&#9201; ${escapeHtml(recipe.total_time)} min</span>` : ''}
                ${hasYields ? `<span>&#127860; ${escapeHtml(recipe.yields)}</span>` : ''}
            </div>` : '';

        return `
        <div class="recipe-card" style="--i:${index}" onclick="openRecipeModal('${recipe.id}')">
            ${recipe.image_url ? `<div class="recipe-card-img-wrap"><img src="${escapeHtml(recipe.image_url)}" alt="${escapeHtml(recipe.title)}"></div>` : ''}
            <div class="recipe-card-content">
                <h3>${escapeHtml(recipe.title)}</h3>
                <span class="recipe-status ${recipe.status}">
                    ${recipe.status === 'want_to_cook' ? 'Want to Cook' : 'Already Cooked'}
                </span>
                ${recipe.rating ? `<div class="recipe-rating">${'&#11088;'.repeat(recipe.rating)}</div>` : ''}
                ${recipe.notes ? `<p class="recipe-notes">"${escapeHtml(recipe.notes)}"</p>` : ''}
                ${metaHtml}
            </div>
        </div>`;
    }).join('');
}

function openRecipeModal(recipeId) {
    const recipe = recipes.find(r => r.id === recipeId);
    if (!recipe) return;

    activeRecipeInModal = recipe;
    isShoppingViewEnabled = false;
    const ingredientsHtml = renderIngredientGroups(recipe.ingredients);
    const instructionsHtml = renderInstructions(recipe.instructions);

    const sourceLink = recipe.url && recipe.url.startsWith('http')
        ? `<div class="modal-source-link"><a href="${escapeHtml(recipe.url)}" target="_blank" rel="noopener">&#8594; View Original Recipe</a></div>`
        : '';

    const metaParts = [];
    if (recipe.total_time) metaParts.push(`<span>&#9201; ${escapeHtml(String(recipe.total_time))} minutes</span>`);
    if (recipe.yields) metaParts.push(`<span>&#127860; ${escapeHtml(recipe.yields)}</span>`);
    const metaHtml = metaParts.length ? `<div class="modal-meta">${metaParts.join('')}</div>` : '';

    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        ${recipe.image_url ? `<img src="${escapeHtml(recipe.image_url)}" alt="${escapeHtml(recipe.title)}">` : ''}
        <h2>${escapeHtml(recipe.title)}</h2>
        ${metaHtml}

        <div class="ingredients-heading-row">
            <h3>Ingredients</h3>
            <button id="shopping-view-toggle" class="modal-inline-btn" onclick="toggleShoppingView()">Shopping View</button>
        </div>
        <div id="modal-ingredients-content">${ingredientsHtml}</div>

        <h3>Instructions</h3>
        ${instructionsHtml}

        <div class="modal-actions">
            <button class="secondary" onclick="openEditRecipeModal('${recipe.id}')">Edit Recipe Details</button>

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

            <textarea id="modal-notes" placeholder="Add notes...">${escapeHtml(recipe.notes || '')}</textarea>

            <button onclick="updateRecipe('${recipe.id}')">Save Changes</button>
            <button class="delete" onclick="deleteRecipe('${recipe.id}')">Delete Recipe</button>
        </div>

        ${sourceLink}
    `;

    recipeModal.classList.add('active');
}

function updateModalIngredientsView() {
    if (!activeRecipeInModal) {
        return;
    }
    const content = document.getElementById('modal-ingredients-content');
    const toggleBtn = document.getElementById('shopping-view-toggle');
    if (!content || !toggleBtn) {
        return;
    }

    if (isShoppingViewEnabled) {
        content.innerHTML = renderShoppingIngredientGroups(activeRecipeInModal.ingredients);
        toggleBtn.textContent = 'Recipe View';
    } else {
        content.innerHTML = renderIngredientGroups(activeRecipeInModal.ingredients);
        toggleBtn.textContent = 'Shopping View';
    }
}

function toggleShoppingView() {
    isShoppingViewEnabled = !isShoppingViewEnabled;
    updateModalIngredientsView();
}

function closeModal() {
    recipeModal.classList.remove('active');
    activeRecipeInModal = null;
    isShoppingViewEnabled = false;
}

async function handleSaveEditedRecipe(e) {
    e.preventDefault();

    const recipeId = document.getElementById('edit-recipe-id').value;
    const title = document.getElementById('edit-title').value.trim();
    const ingredientsText = document.getElementById('edit-ingredients').value;
    const instructions = document.getElementById('edit-instructions').value.trim();
    const yields = document.getElementById('edit-yields').value.trim();
    const totalTime = document.getElementById('edit-total-time').value.trim();
    const imageUrl = document.getElementById('edit-image-url').value.trim();
    const ingredients = parseManualIngredients(ingredientsText);

    if (!recipeId) {
        editStatus.textContent = 'Recipe not found.';
        editStatus.className = 'status-message error';
        return;
    }
    if (!title || !instructions || ingredients.length === 0) {
        editStatus.textContent = 'Title, ingredients, and instructions are required.';
        editStatus.className = 'status-message error';
        return;
    }

    editStatus.textContent = 'Saving updates...';
    editStatus.className = 'status-message';

    try {
        const response = await fetch(`${API_URL}/recipes/${recipeId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                title,
                ingredients,
                instructions,
                yields: yields || null,
                total_time: totalTime || null,
                image_url: imageUrl || null
            })
        });

        if (response.ok) {
            editStatus.textContent = 'Recipe details updated!';
            editStatus.className = 'status-message success';
            await loadRecipes();
            setTimeout(() => {
                closeEditRecipeModal();
            }, 400);
        } else if (response.status === 401) {
            showLogin();
        } else {
            const error = await response.json().catch(() => ({}));
            editStatus.textContent = error.error || 'Failed to update recipe details';
            editStatus.className = 'status-message error';
        }
    } catch (error) {
        editStatus.textContent = `Error: ${error.message}`;
        editStatus.className = 'status-message error';
    }
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
