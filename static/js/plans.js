/**
 * 🎬 VidCover Tools — Plan Activation JS
 * Handles the plan activation form
 */

document.addEventListener('DOMContentLoaded', () => {

    const form = document.getElementById('activate-form');
    const resultDiv = document.getElementById('activate-result');
    const planInfoDiv = document.getElementById('activated-plan-info');
    const activateBtn = document.getElementById('activate-btn');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const code = document.getElementById('activation-code').value.trim();
        const label = document.getElementById('user-label').value.trim();

        if (!code) {
            showResult('Please enter an activation code!', 'error');
            return;
        }

        // Show loading
        const btnText = activateBtn.querySelector('.btn-text');
        const btnLoading = activateBtn.querySelector('.btn-loading');
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline-flex';
        activateBtn.disabled = true;

        try {
            const result = await apiRequest('/api/activate', 'POST', { code, label });

            if (result.success) {
                showResult(result.message, 'success');

                // Show plan info
                if (result.plan) {
                    document.getElementById('activated-plan-name').textContent =
                        `Plan ${result.plan.tier} — ${result.plan.name}`;
                    document.getElementById('activated-plan-expires').textContent =
                        new Date(result.plan.expires_at).toLocaleDateString('en-US', {
                            year: 'numeric', month: 'long', day: 'numeric'
                        });
                    document.getElementById('activated-plan-days').textContent =
                        `${result.plan.days_remaining} days`;
                    planInfoDiv.style.display = 'block';
                }

                // Hide form
                form.style.display = 'none';

                showToast('Plan activated successfully!', 'success');
            } else {
                showResult(result.error || 'Activation failed!', 'error');
                showToast(result.error || 'Activation failed!', 'error');
            }
        } catch (err) {
            showResult('Network error. Please try again.', 'error');
        }

        // Reset button
        btnText.style.display = 'inline-flex';
        btnLoading.style.display = 'none';
        activateBtn.disabled = false;
    });

    function showResult(message, type) {
        resultDiv.textContent = message;
        resultDiv.className = `activate-result ${type}`;
        resultDiv.style.display = 'block';
    }

});
