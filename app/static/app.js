

const options = document.querySelectorAll(".login-option");
document.addEventListener("mousemove", (e) => {
    options.forEach(option => {
        const rect = option.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const distance = Math.sqrt(
            Math.pow(e.clientX - centerX, 2) +
            Math.pow(e.clientY - centerY, 2)
        );

        if (distance < 180) {
            const strength = (180 - distance) / 180;
            const moveX =
                (e.clientX - centerX) * 0.08 * strength;
            const moveY =
                (e.clientY - centerY) * 0.08 * strength;
            option.style.transform =
                `translate(${moveX}px, ${moveY}px) scale(${1 + strength * 0.04})`;

        } else {
            option.style.transform =
                "translate(0, 0) scale(1)";
        }

    });

});
