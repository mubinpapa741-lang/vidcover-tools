/**
 * 🎬 VidCover Tools — Dashboard JS
 * Real-time stats, code management, plan actions, auto-refresh
 */

document.addEventListener('DOMContentLoaded', () => {

    // ========================================================================
    // CREATE CODE
    // ========================================================================

    const createForm = document.getElementById('create-code-form');
    const createResult = document.getElementById('create-code-result');

    if (createForm) {
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const code = document.getElementById('new-code').value.trim();
            const planTier = document.getElementById('code-plan-tier').value;

            if (!code || !planTier) {
                showFormResult('Please fill in all fields!', 'error');
                return;
            }

            const result = await apiRequest('/api/codes/create', 'POST', {
                code: code,
                plan_tier: parseInt(planTier)
            });

            if (result.success) {
                showFormResult(result.message, 'success');
                showToast(result.message, 'success');
                document.getElementById('new-code').value = '';
                document.getElementById('code-plan-tier').value = '';
                // Reload after short delay
                setTimeout(() => location.reload(), 1000);
            } else {
                showFormResult(result.error, 'error');
                showToast(result.error, 'error');
            }
        });
    }

    function showFormResult(message, type) {
        if (!createResult) return;
        createResult.textContent = message;
        createResult.className = `form-result ${type}`;
        createResult.style.display = 'block';
        setTimeout(() => { createResult.style.display = 'none'; }, 4000);
    }

    // ========================================================================
    // AUTO-REFRESH STATS (every 30 seconds)
    // ========================================================================

    setInterval(async () => {
        try {
            const stats = await apiRequest('/api/stats');
            if (stats) {
                const el = (id) => document.getElementById(id);
                if (el('stat-active')) el('stat-active').textContent = stats.active_plans;
                if (el('stat-expired')) el('stat-expired').textContent = stats.expired_plans;
                if (el('stat-codes')) el('stat-codes').textContent = stats.available_codes;
                if (el('stat-used')) el('stat-used').textContent = stats.used_codes;
                if (el('last-update')) {
                    const now = new Date().toLocaleTimeString();
                    el('last-update').textContent = `Last: ${now}`;
                }
            }
        } catch (e) {
            console.log('Auto-refresh error:', e);
        }
    }, 30000);

});


// ============================================================================
// GLOBAL FUNCTIONS (called from onclick in HTML)
// ============================================================================

async function deleteCode(codeId) {
    if (!confirmAction('Delete this activation code?')) return;

    const result = await apiRequest(`/api/codes/${codeId}`, 'DELETE');
    if (result.success) {
        showToast('Code deleted!', 'success');
        setTimeout(() => location.reload(), 500);
    } else {
        showToast('Failed to delete code.', 'error');
    }
}

async function deletePlan(planId) {
    if (!confirmAction('Delete this plan? This action cannot be undone.')) return;

    const result = await apiRequest(`/api/plans/${planId}`, 'DELETE');
    if (result.success) {
        showToast('Plan deleted!', 'success');
        setTimeout(() => location.reload(), 500);
    } else {
        showToast('Failed to delete plan.', 'error');
    }
}

async function deactivatePlan(planId) {
    if (!confirmAction('Deactivate this plan?')) return;

    const result = await apiRequest(`/api/plans/${planId}/deactivate`, 'POST');
    if (result.success) {
        showToast('Plan deactivated!', 'success');
        setTimeout(() => location.reload(), 500);
    } else {
        showToast('Failed to deactivate plan.', 'error');
    }
}

async function cleanupExpired() {
    if (!confirmAction('Delete all expired plans?')) return;

    const result = await apiRequest('/api/cleanup', 'POST');
    if (result.success) {
        showToast(result.message, 'success');
        setTimeout(() => location.reload(), 500);
    } else {
        showToast('Cleanup failed.', 'error');
    }
}

function refreshDashboard() {
    location.reload();
}


// ============================================================================
// PROMO LINK MANAGEMENT
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    const promoForm = document.getElementById('promo-link-form');
    const promoResult = document.getElementById('promo-link-result');

    if (promoForm) {
        promoForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const link = document.getElementById('promo-link-input').value.trim();
            if (!link) {
                showPromoResult('Please enter a promo link!', 'error');
                return;
            }

            const result = await apiRequest('/api/promo-link', 'POST', { promo_link: link });

            if (result.success) {
                showPromoResult('✅ Promo link saved successfully!', 'success');
                showToast('Promo link saved!', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showPromoResult(result.error, 'error');
                showToast(result.error, 'error');
            }
        });
    }

    function showPromoResult(message, type) {
        if (!promoResult) return;
        promoResult.textContent = message;
        promoResult.className = `form-result ${type}`;
        promoResult.style.display = 'block';
        setTimeout(() => { promoResult.style.display = 'none'; }, 4000);
    }
});


async function copyPromoLink() {
    const linkEl = document.getElementById('current-promo-link');
    const inputEl = document.getElementById('promo-link-input');
    const link = linkEl ? linkEl.textContent.trim() : (inputEl ? inputEl.value.trim() : '');

    if (!link) {
        showToast('No promo link to copy!', 'error');
        return;
    }

    try {
        await navigator.clipboard.writeText(link);
        showToast('📋 Promo link copied!', 'success');
    } catch (e) {
        // Fallback
        const ta = document.createElement('textarea');
        ta.value = link;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('📋 Promo link copied!', 'success');
    }
}


function copyPromoPageUrl() {
    const promoUrl = window.location.origin + '/promo';
    try {
        navigator.clipboard.writeText(promoUrl);
        showToast('🌐 Promo page URL copied: ' + promoUrl, 'success');
    } catch (e) {
        const ta = document.createElement('textarea');
        ta.value = promoUrl;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('🌐 Promo page URL copied!', 'success');
    }
}


async function deletePromoLink() {
    if (!confirmAction('Remove the promo link?')) return;

    const result = await apiRequest('/api/promo-link', 'DELETE');
    if (result.success) {
        showToast('Promo link removed!', 'success');
        setTimeout(() => location.reload(), 500);
    } else {
        showToast('Failed to remove promo link.', 'error');
    }
}
