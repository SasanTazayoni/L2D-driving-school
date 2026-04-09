/* jshint esversion: 11 */

const authBtns = document.querySelectorAll('.auth-button');
const blueBtns = document.querySelectorAll('.blue-button');
const redBtns = document.querySelectorAll('.red-button');

authBtns.forEach(btn => {
    btn.onmousemove = function(e) {
        let x = e.pageX - btn.offsetLeft;
        let y = e.pageY - btn.offsetTop;

        btn.style.setProperty('--x', x + 'px');
        btn.style.setProperty('--y', y + 'px');
    };
});

function createRipple(e) {
    const rect = e.target.getBoundingClientRect();
    let x = e.clientX - rect.left;
    let y = e.clientY - rect.top;
    let ripples = document.createElement('span');
    ripples.style.left = x + 'px';
    ripples.style.top = y + 'px';
    this.appendChild(ripples);

    setTimeout(() => {
        ripples.remove();
    }, 600);
}

blueBtns.forEach(btn => {
    btn.addEventListener('mouseover', createRipple);
});

redBtns.forEach(btn => {
    btn.addEventListener('mouseover', createRipple);
});