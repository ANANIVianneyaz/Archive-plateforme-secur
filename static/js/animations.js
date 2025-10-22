// =========================================
// TRUSTARCHIVE - Animations supplémentaires
// Compteurs, parallax et effets modernes
// =========================================

// Animation des compteurs statistiques
function animateCounters() {
    const statNumbers = document.querySelectorAll('.stat-number');
    
    const animateCounter = (element, start, end, duration) => {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                clearInterval(timer);
                current = end;
            }
            const value = Math.floor(current);
            element.textContent = value.toLocaleString() + (end === 99 ? '.9' : '');
        }, 16);
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const finalValue = parseInt(target.getAttribute('data-count'));
                animateCounter(target, 0, finalValue, 2000);
                observer.unobserve(target);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(stat => observer.observe(stat));
}

// Animation au scroll (Reveal on scroll)
function setupScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observer les cartes de fonctionnalités
    document.querySelectorAll('.feature-card').forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${index * 0.1}s`;
        observer.observe(card);
    });

    // Observer les cartes d'items dans le dashboard
    setTimeout(() => {
        document.querySelectorAll('.item-card').forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = `all 0.4s cubic-bezier(0.4, 0, 0.2, 1) ${index * 0.04}s`;
            observer.observe(card);
        });
    }, 100);
}

// Effet parallax sur le hero
function setupParallax() {
    const heroSection = document.querySelector('.hero-section');
    if (!heroSection) return;

    let ticking = false;

    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const scrolled = window.pageYOffset;
                const rate = scrolled * 0.4;
                heroSection.style.transform = `translate3d(0, ${rate}px, 0)`;
                ticking = false;
            });
            ticking = true;
        }
    });
}

// Navbar scroll effect
function setupNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 50) {
            navbar.style.boxShadow = 'var(--shadow-lg)';
            navbar.style.padding = '0.75rem 0';
        } else {
            navbar.style.boxShadow = 'var(--shadow-sm)';
            navbar.style.padding = '1rem 0';
        }
        
        lastScroll = currentScroll;
    });
}

// Initialisation des animations
document.addEventListener('DOMContentLoaded', function() {
    console.log('✨ TrustArchive - Animations chargées');
    
    // Animer les compteurs
    setTimeout(animateCounters, 300);
    
    // Setup scroll animations
    setTimeout(setupScrollAnimations, 200);
    
    // Setup parallax
    setupParallax();
    
    // Setup navbar scroll
    setupNavbarScroll();
});
