document.addEventListener('DOMContentLoaded', () => {
    // --- Existing Selectors ---
    const generateBtn = document.getElementById('generateBtn');
    const promptInput = document.getElementById('promptInput');
    const statusArea = document.getElementById('status-area');
    const imgDisplay = document.getElementById('image-display');
    const statusBar = document.getElementById('server-status-bar');
    const statusText = document.getElementById('status-text');

    // --- Main Page Download Button ---
    const downloadBtn = document.getElementById('mainDownloadBtn');

    // --- Gallery Selectors ---
    const historyScrollbox = document.getElementById('history-scrollbox');
    let imageHistory = []; 

    // --- Modal Selectors (Zoom Only) ---
    const modal = document.getElementById("imageModal");
    const imgFull = document.getElementById("imgFull");
    const closeBtn = document.querySelector(".close");

    // Pan & Zoom State
    let isProcessing = false;
    let failCount = 0;
    let scale = 1, panning = false, pointX = 0, pointY = 0, start = { x: 0, y: 0 };

    function setTransform() {
        imgFull.style.transform = `translate(${pointX}px, ${pointY}px) scale(${scale})`;
    }

    // --- Robust Download Function ---
    async function triggerDownload(url) {
        if (!url || url === "" || url.includes('undefined')) return;
        try {
            const response = await fetch(url);
            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = url.split('/').pop().split('?')[0]; // Extract filename
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(blobUrl);
        } catch (err) {
            console.error("Download failed, falling back to new tab:", err);
            window.open(url, '_blank');
        }
    }

    downloadBtn.onclick = () => triggerDownload(imgDisplay.src);

    function updateGallery(newUrl) {
        const thumb = document.createElement('img');
        const fullUrl = `http://127.0.0.1:8000${newUrl}`;
        thumb.src = fullUrl;
        thumb.className = 'history-thumb active';
        
        document.querySelectorAll('.history-thumb').forEach(t => t.classList.remove('active'));

        thumb.onclick = () => {
            document.querySelectorAll('.history-thumb').forEach(t => t.classList.remove('active'));
            thumb.classList.add('active');
            
            imgDisplay.src = thumb.src;
            imgDisplay.style.display = 'block'; 
            downloadBtn.style.display = 'block'; // Show download for history items
            
            statusArea.className = 'success';
            statusArea.innerText = "Viewing History Image";
            imgDisplay.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        };

        historyScrollbox.prepend(thumb);
    }

    async function checkServerStatus() {
        if (isProcessing) {
            statusBar.className = 'status-busy';
            statusText.innerText = "Processing Flux...";
            return;
        }

        try {
            const controller = new AbortController();
            const id = setTimeout(() => controller.abort(), 2000);
            const response = await fetch('http://127.0.0.1:8000/health', { signal: controller.signal });
            clearTimeout(id);
            
            if (response.ok) {
                failCount = 0;
                statusBar.className = 'status-online';
                statusText.innerText = "Online";
                if (!isProcessing) generateBtn.disabled = false;
            } else { throw new Error(); }
        } catch (error) {
            failCount++;
            if (failCount >= 2) {
                statusBar.className = 'status-offline';
                statusText.innerText = "Offline";
                generateBtn.disabled = true; 
            }
        }
    }

    checkServerStatus();
    setInterval(checkServerStatus, 5000);

    // --- Modal Logic ---
    imgDisplay.addEventListener('click', () => {
        if (imgDisplay.src && imgDisplay.src !== "" && !imgDisplay.src.includes('undefined')) {
            modal.style.display = "block";
            imgFull.src = imgDisplay.src;
            scale = 1; pointX = 0; pointY = 0;
            setTransform();
        }
    });

    modal.onwheel = (e) => {
        e.preventDefault();
        const xs = (e.clientX - pointX) / scale;
        const ys = (e.clientY - pointY) / scale;
        const delta = -e.deltaY;
        (delta > 0) ? (scale *= 1.1) : (scale /= 1.1);
        scale = Math.min(Math.max(0.5, scale), 10);
        pointX = e.clientX - xs * scale;
        pointY = e.clientY - ys * scale;
        setTransform();
    };

    imgFull.onmousedown = (e) => {
        e.preventDefault();
        start = { x: e.clientX - pointX, y: e.clientY - pointY };
        panning = true;
        imgFull.style.cursor = "grabbing";
    };

    window.onmouseup = () => { panning = false; imgFull.style.cursor = "grab"; };

    window.onmousemove = (e) => {
        if (!panning) return;
        e.preventDefault();
        pointX = (e.clientX - start.x);
        pointY = (e.clientY - start.y);
        setTransform();
    };

    closeBtn.onclick = () => modal.style.display = "none";
    window.onclick = (event) => { if (event.target == modal) modal.style.display = "none"; };

    // --- Generation Logic ---
    generateBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) { alert("Please enter a prompt!"); return; }

        isProcessing = true; 
        generateBtn.disabled = true;
        statusArea.className = 'loading';
        statusArea.innerText = "⏳ Request sent successfully. Waiting for Flux...";
        
        statusBar.className = 'status-busy';
        statusText.innerText = "Processing Flux...";

        try {
            const response = await fetch('http://127.0.0.1:8000/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt })
            });

            const data = await response.json();

            if (data.status === 'success') { 
                statusArea.className = 'success';
                statusArea.innerText = "✅ Image Received!";

                const fullImageUrl = `http://127.0.0.1:8000${data.image_url}`;
                imgDisplay.src = fullImageUrl;
                imgDisplay.style.display = 'block';
                downloadBtn.style.display = 'block'; // Show download button

                updateGallery(data.image_url);
            } else {
                statusArea.className = 'error';
                statusArea.innerText = "❌ Failed: " + (data.detail || "Check console");
                imgDisplay.style.display = 'block'; 
            }
        } catch (error) {
            statusArea.className = 'error';
            statusArea.innerText = "❌ Connection Error.";
            imgDisplay.style.display = 'block';
        } finally {
            isProcessing = false;
            await checkServerStatus();
        }
    });
});