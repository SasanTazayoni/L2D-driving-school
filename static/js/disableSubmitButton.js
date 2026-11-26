/* jshint esversion: 11 */

// Forms marked with `data-disable-on-submit` disable their submit buttons once
// the browser has accepted the form (built-in validation still runs first).
// This stops a double click sending the form twice, which on login/signup
// shows a CSRF error page because the first request already changed the token.
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form[data-disable-on-submit]');
    const submitButtons = (form) =>
        form.querySelectorAll('button[type="submit"], input[type="submit"]');

    forms.forEach((form) => {
        form.addEventListener('submit', () => {
            submitButtons(form).forEach((button) => {
                button.disabled = true;
            });
        });
    });

    // Coming back with the browser's Back button can restore the page with
    // the buttons still disabled; switch them back on.
    window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
            forms.forEach((form) => {
                submitButtons(form).forEach((button) => {
                    button.disabled = false;
                });
            });
        }
    });
});
