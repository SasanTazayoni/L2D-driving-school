/* jshint esversion: 11 */

document.addEventListener('DOMContentLoaded', () => {
    const positionAlertContainer = () => {
        const navbarHeight = document.querySelector('.navbar').offsetHeight;
        const alertContainer = document.querySelector('[data-alert]');
        alertContainer.style.top = `${navbarHeight + 10}px`;
    };

    // Call the function when the document is ready and if the window is resized
    positionAlertContainer();
    window.addEventListener('resize', positionAlertContainer);

    // Success/info toasts fade out via CSS (paused while hovered or focused).
    // Remove each one only when its fade has actually finished. Errors and
    // warnings have no fade and stay until closed with the x.
    document.querySelectorAll('[data-alert] .alert.auto-dismiss').forEach((alertElement) => {
        alertElement.addEventListener('animationend', (event) => {
            if (event.animationName === 'fadeOut') {
                alertElement.remove();
            }
        });
    });
});
