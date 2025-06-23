function render_items(data) {
    data = JSON.parse(data)
    data.forEach(e => {
        console.log(e)
        var marker = L.marker(e.coords).addTo(map)
        marker.bindPopup(e.popup)
    })

}

// Global JavaScript file
function initializeCarousels() {
    const galleries = document.querySelectorAll('.image-gallery');

    galleries.forEach((gallery) => {
        const images = gallery.querySelectorAll('img');
        const prevButton = gallery.querySelector('[data-action="prev"]');
        const nextButton = gallery.querySelector('[data-action="next"]');
        let currentIndex = 0;

        function updateCarousel(index) {
            images.forEach((img, i) => {
                img.classList.toggle('opacity-100', i === index);
                img.classList.toggle('opacity-0', i !== index);
            });
        }

        // If there's only one image, ensure it's visible
        if (images.length === 1) {
            images[0].classList.add('opacity-100');
            images[0].classList.remove('opacity-0');
            if (prevButton) prevButton.style.display = 'none';
            if (nextButton) nextButton.style.display = 'none';
            return; // No need to add event listeners for navigation
        }

        // Check if buttons exist before adding event listeners
        if (prevButton && nextButton) {
            prevButton.addEventListener('click', () => {
                currentIndex = (currentIndex - 1 + images.length) % images.length;
                updateCarousel(currentIndex);
            });

            nextButton.addEventListener('click', () => {
                currentIndex = (currentIndex + 1) % images.length;
                updateCarousel(currentIndex);
            });

            updateCarousel(currentIndex); // Initialize carousel
        }
    });
}

// Initialize carousels on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeCarousels();
});

// Reinitialize carousels when "Show More" button is clicked
document.addEventListener('click', (event) => {
    const btnNextPage = document.getElementById('btn_next_page');
    if (btnNextPage && event.target.closest('#btn_next_page')) {
        // Add a slight delay to ensure the new content is added to the DOM
        setTimeout(() => {
            initializeCarousels();
        }, 500); // Adjust delay as needed
    }
});

