document.addEventListener('DOMContentLoaded', function () {

    function updateCountdowns() {

        const countdownContainers = document.querySelectorAll(
            '[data-payment-deadline]'
        );

        countdownContainers.forEach(function (container) {

            const deadline = new Date(
                container.dataset.paymentDeadline
            ).getTime();

            const countdown = container.querySelector('.countdown');

            const now = new Date().getTime();

            const difference = deadline - now;

            if (difference <= 0) {

                countdown.textContent =
                    'Payment window has expired.';

                countdown.classList.remove('text-danger');
                countdown.classList.add('text-secondary');

                return;
            }

            const hours = Math.floor(
                difference / (1000 * 60 * 60)
            );

            const minutes = Math.floor(
                (difference % (1000 * 60 * 60))
                / (1000 * 60)
            );

            const seconds = Math.floor(
                (difference % (1000 * 60))
                / 1000
            );

            countdown.textContent =
                'Time remaining: '
                + hours + 'h '
                + minutes + 'm '
                + seconds + 's';
        });
    }

    updateCountdowns();

    setInterval(updateCountdowns, 1000);

});