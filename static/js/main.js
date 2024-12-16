// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Update category counts based on actual data
    async function updateCategoryCounts() {
        try {
            const response = await fetch('/api/categories/counts');
            const counts = await response.json();
            
            Object.entries(counts).forEach(([categoryId, count]) => {
                const countElement = document.querySelector(`[data-category-id="${categoryId}"] .category-count`);
                if (countElement) {
                    countElement.textContent = count;
                }
            });
        } catch (error) {
            console.error('Error updating category counts:', error);
        }
    }

    // Initialize category counts
    updateCategoryCounts();
});