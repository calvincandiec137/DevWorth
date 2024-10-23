// Function to update user activity
function updateActivity() {
    fetch('/update_activity', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateLeaderboard();
        } else {
            console.error('Failed to update activity');
        }
    })
    .catch(error => {
        console.error('Error updating activity:', error);
    });
}

// Function to update leaderboard
function updateLeaderboard() {
    fetch('/get_leaderboard', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        const leaderboardList = document.querySelector('.list-group');
        if (leaderboardList) {
            leaderboardList.innerHTML = data.leaderboard.map((leader, index) => `
                <li class="list-group-item">
                    <span class="rank">${index + 1}.</span>
                    ${index < 3 ? `<span class="crown ${getCrownClass(index + 1)}">👑</span>` : ''}
                    ${leader.username} - ${leader.total_experience}XP
                </li>
            `).join('');
        }
    })
    .catch(error => {
        console.error('Error updating leaderboard:', error);
    });
}

function getCrownClass(rank) {
    switch(rank) {
        case 1: return 'gold';
        case 2: return 'silver';
        case 3: return 'bronze';
        default: return '';
    }
}

// Update more frequently (every 5 seconds)
let interval = setInterval(updateActivity, 5000);

// Update when the page loads
document.addEventListener('DOMContentLoaded', () => {
    updateActivity();
    updateLeaderboard();
});

// Clear interval when page is unloaded
window.addEventListener('beforeunload', () => {
    clearInterval(interval);
    updateActivity(); // One final update before leaving
});