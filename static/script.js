document.addEventListener('DOMContentLoaded', function() {
    // GSAP animations for index page
    if (document.querySelector('.title')) {
        gsap.from(".title", { duration: 1.5, opacity: 0, y: 20, ease: "power2.out" });
        gsap.from(".slogan", { duration: 1.5, y: 100, opacity: 0, delay: 0.5, ease: "power2.out" });
        gsap.from(".crystal-btn", { duration: 1.2, y: 30, opacity: 0, scale: 0.8, ease: "elastic.out(1, 0.5)", stagger: 0.2, delay: 1 });
    }

    // GSAP animations for question, summarize, transcribe, interpret pages
    if (document.querySelector('.info-section')) {
        gsap.from(".title", { duration: 1.5, opacity: 0, y: 20, ease: "power2.out" });
        gsap.from(".slogan", { duration: 1.5, y: 100, opacity: 0, delay: 0.5, ease: "power2.out" });
        gsap.from(".info-section", { duration: 1.2, y: 30, opacity: 0, ease: "power2.out", delay: 0.3 });
        gsap.from("#youtubeLink", { duration: 1.2, y: 30, opacity: 0, ease: "power2.out", delay: 0.4 });
        gsap.from("#question", { duration: 1.2, y: 30, opacity: 0, ease: "power2.out", delay: 0.5 });
        gsap.from(".crystal-btn", { duration: 1.2, y: 30, opacity: 0, scale: 0.8, ease: "elastic.out(1, 0.5)", stagger: 0.2, delay: 0.6 });
    }

    // Initialize theme based on localStorage
    const checkbox = document.getElementById('input');
    if (checkbox) {
        if (localStorage.getItem('mode') === 'light') {
            document.body.classList.remove('dark-mode');
            document.body.classList.add('light-mode');
            checkbox.checked = false;
        } else {
            document.body.classList.add('dark-mode');
            checkbox.checked = true;
        }
    }

    // Add input event listener for youtubeLink
    const youtubeLinkInput = document.getElementById('youtubeLink');
    if (youtubeLinkInput) {
        youtubeLinkInput.addEventListener('input', fetchVideoInfo);
    }
});

function toggleMode() {
    const body = document.body;
    const checkbox = document.getElementById('input');
    if (checkbox.checked) {
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        localStorage.setItem('mode', 'dark');
    } else {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        localStorage.setItem('mode', 'light');
    }
}

async function fetchVideoInfo() {
    const link = document.getElementById('youtubeLink').value.trim();
    const thumbnailImg = document.getElementById('thumbnail-img');
    const titleDiv = document.getElementById('video-title');
    const loader = document.getElementById('url-loading');

    if (thumbnailImg) thumbnailImg.style.display = 'none';
    if (titleDiv) titleDiv.innerText = '';
    if (loader) loader.style.display = 'inline-block';

    if (!link) {
        if (titleDiv) titleDiv.innerText = 'Please enter a YouTube URL';
        if (loader) loader.style.display = 'none';
        return;
    }

    const videoIdMatch = link.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/i);
    const videoId = videoIdMatch ? videoIdMatch[1] : null;

    if (videoId && thumbnailImg) {
        thumbnailImg.src = `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
        thumbnailImg.style.display = 'block';
        thumbnailImg.onerror = () => {
            thumbnailImg.style.display = 'none';
            if (titleDiv) titleDiv.innerText = 'Thumbnail unavailable';
        };
    }

    try {
        const response = await fetch('/get_video_info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: link })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Server error');
        if (titleDiv) titleDiv.innerText = data.title;
    } catch (error) {
        if (titleDiv) titleDiv.innerText = `Error: ${error.message}`;
    } finally {
        if (loader) loader.style.display = 'none';
    }
}

async function processVideo(option) {
    const link = document.getElementById('youtubeLink').value.trim();
    const question = option === 'question' ? document.getElementById('question').value.trim() : '';
    const resultDiv = document.getElementById('result');
    const processingDiv = document.getElementById('processing');
    const progressBar = document.getElementById('progress');
    const processBtn = document.querySelector('.crystal-btn:not(.refresh-btn)');
    const copyBtn = document.getElementById('copy-btn');

    if (resultDiv) resultDiv.innerText = '';
    if (copyBtn) copyBtn.style.display = 'none';

    if (!link) {
        if (resultDiv) resultDiv.innerText = 'Error: Please enter a YouTube URL';
        return;
    }

    if (option === 'question' && !question) {
        if (resultDiv) resultDiv.innerText = 'Error: Please enter a question';
        return;
    }

    if (processingDiv) processingDiv.style.display = 'block';
    if (progressBar) progressBar.style.width = '0%';
    if (processBtn) processBtn.disabled = true;

    let progress = 0;
    let intervalId;

    try {
        const durationResponse = await fetch('/get_video_duration', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: link })
        });
        const durationData = await durationResponse.json();
        const videoDuration = durationData.duration || 600;
        const estimatedTime = (option === 'summarize' ? Math.min(videoDuration * 0.5, 120) : option === 'question' ? Math.min(videoDuration * 0.4, 100) : Math.min(videoDuration * 0.3, 90)) * 1000;

        intervalId = setInterval(() => {
            progress += (100 / (estimatedTime / 100));
            if (progress >= 100) {
                progress = 100;
                clearInterval(intervalId);
            }
            if (progressBar) progressBar.style.width = `${progress}%`;
        }, 100);

        const response = await fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: link, option: option, question: question })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.output || 'Server error');
        if (resultDiv) resultDiv.innerText = result.output;
        if (copyBtn) copyBtn.style.display = 'block';
    } catch (error) {
        if (resultDiv) resultDiv.innerText = `Error: ${error.message}`;
    } finally {
        clearInterval(intervalId);
        if (progressBar) {
            progressBar.style.width = '100%';
            progressBar.style.transition = 'width 0.5s ease-in-out';
        }
        setTimeout(() => {
            if (processingDiv) processingDiv.style.display = 'none';
            if (progressBar) progressBar.style.transition = '';
            if (processBtn) processBtn.disabled = false;
        }, 500);
    }
}

function copyTranscription() {
    const resultDiv = document.getElementById('result');
    const text = resultDiv.innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert('Text copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

function refreshPage() {
    window.location.reload();
}