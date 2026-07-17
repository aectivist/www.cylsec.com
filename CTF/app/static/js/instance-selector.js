/**
 * Dynamic CTF instance selector for challenge forms
 */

document.addEventListener('DOMContentLoaded', function() {
    const typeSelect = document.getElementById('type');
    const instanceSelect = document.getElementById('instance_name');
    
    if (typeSelect && instanceSelect) {
        // When challenge type changes, update instance options
        typeSelect.addEventListener('change', async function() {
            const challengeType = this.value;
            if (!challengeType) {
                // Reset to default options
                instanceSelect.innerHTML = '<option value="">-- No Instance --</option>';
                return;
            }
            
            try {
                // Fetch available instances for this type
                const response = await fetch(`/admin/api/instances/${challengeType}`);
                const instances = await response.json();
                
                // Clear current options
                instanceSelect.innerHTML = '<option value="">-- No Instance --</option>';
                
                // Add instances to dropdown
                instances.forEach(instance => {
                    const option = document.createElement('option');
                    option.value = instance;
                    option.textContent = instance;
                    instanceSelect.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading instances:', error);
                instanceSelect.innerHTML = '<option value="">-- Error loading instances --</option>';
            }
        });
        
        // Trigger change event on page load to populate instances for current type
        typeSelect.dispatchEvent(new Event('change'));
    }
});
