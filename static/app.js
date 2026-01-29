document.addEventListener('DOMContentLoaded', () => {
    // Tab Switching
    const tabs = document.querySelectorAll('.nav-tab');
    const sections = document.querySelectorAll('.section');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));

            tab.classList.add('active');
            const targetId = tab.dataset.target;
            document.getElementById(targetId).classList.add('active');
        });
    });

    // Forms
    setupForm('recipe-url-form', '/api/print/recipe', (formData) => ({
        mode: 'url',
        url: formData.get('url')
    }));

    setupForm('recipe-text-form', '/api/print/recipe', (formData) => ({
        mode: 'text',
        title: formData.get('title'),
        text: formData.get('text')
    }));

    setupForm('todo-form', '/api/print/todo', (formData) => ({
        title: formData.get('title'),
        items: formData.get('items')
    }));

    // Modal Close
    document.querySelector('.close-modal').addEventListener('click', closeModal);
    window.onclick = function (event) {
        if (event.target == document.getElementById('preview-modal')) {
            closeModal();
        }
    }
});

let currentPreviewFormId = null;

function setupForm(formId, endpoint, dataMapper) {
    const form = document.getElementById(formId);
    if (!form) return;

    // Attach dataMapper to form for easy access in preview
    form.dataset.endpoint = endpoint;
    form.dataMapper = dataMapper;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        submitForm(formId, false);
    });
}

async function handlePreview(formId) {
    currentPreviewFormId = formId;
    const form = document.getElementById(formId);
    const btn = form.querySelector('button.btn-secondary'); // The preview button

    // Quick validation
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    setLoading(btn, true, 'Generating...');

    try {
        const formData = new FormData(form);
        const dataMapper = form.dataMapper;
        const data = dataMapper(formData);
        data.preview = true; // Flag for preview

        const res = await fetch(form.dataset.endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await res.json();

        if (res.ok && result.preview) {
            showModal(result.preview);
        } else {
            showStatus('error', result.message || 'Failed to preview.');
        }

    } catch (err) {
        console.error(err);
        showStatus('error', 'Network error during preview.');
    } finally {
        setLoading(btn, false, 'Preview');
    }
}

// Logic to actually print from the modal
document.getElementById('confirm-print').addEventListener('click', () => {
    if (currentPreviewFormId) {
        closeModal();
        submitForm(currentPreviewFormId, false);
    }
});

async function submitForm(formId) {
    const form = document.getElementById(formId);
    const btn = form.querySelector('button[type="submit"]');
    const originalText = btn.innerText;

    setLoading(btn, true, 'Printing...');
    hideStatus();

    try {
        const formData = new FormData(form);
        const dataMapper = form.dataMapper;
        const data = dataMapper(formData);

        const res = await fetch(form.dataset.endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await res.json();

        if (res.ok) {
            showStatus('success', result.message || 'Printed successfully!');
            form.reset();
        } else {
            showStatus('error', result.message || 'Failed to print.');
        }
    } catch (err) {
        showStatus('error', 'Network error. Check connection.');
        console.error(err);
    } finally {
        setLoading(btn, false, originalText);
    }
}

function showModal(content) {
    document.getElementById('preview-content').innerText = content;
    document.getElementById('preview-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('preview-modal').classList.remove('active');
}

function setLoading(btn, isLoading, text) {
    if (isLoading) {
        btn.disabled = true;
        btn.innerText = text;
    } else {
        btn.disabled = false;
        btn.innerText = text;
    }
}

function showStatus(type, msg) {
    const el = document.getElementById('status-message');
    el.className = type === 'success' ? 'status-success' : 'status-error';
    el.innerText = msg;
    el.style.display = 'block';

    setTimeout(() => {
        el.style.display = 'none';
    }, 5000);
}

function hideStatus() {
    document.getElementById('status-message').style.display = 'none';
}
