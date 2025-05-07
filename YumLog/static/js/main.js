// File: js/main.js

// Utility: is user “logged in”?
function isLoggedIn() {
  return !!localStorage.getItem('yumlog_user');
}

document.addEventListener('DOMContentLoaded', () => {
  // NAV TOGGLE (guest vs. auth)
  const guestNav = document.getElementById('nav-guest');
  const authNav  = document.getElementById('nav-auth');
  if (guestNav && authNav) {
    if (isLoggedIn()) {
      guestNav.style.display = 'none';
      authNav.style.display  = 'flex';
    } else {
      guestNav.style.display = 'flex';
      authNav.style.display  = 'none';
    }
  }

  // TAB SWITCHING on restaurant.html
  const tabs    = document.querySelectorAll('.tabs .btn');
  const content = document.querySelector('.tab-content');
  if (tabs.length && content) {
    tabs.forEach(btn => {
      btn.addEventListener('click', () => {
        content.innerHTML = `<p>Loading “${btn.textContent}”…</p>`;
        // TODO: fetch & render real data via your API
      });
    });
  }

  // FAKE LOGIN FORM (login.html)
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', e => {
      e.preventDefault();
      localStorage.setItem('yumlog_user',
        JSON.stringify({ username: e.target.username ? e.target.username.value : e.target.email.value }));
      window.location.href = 'index.html';
    });
  }

  // FAKE SIGNUP FORM (signup.html)
  const signupForm = document.getElementById('signup-form');
  if (signupForm) {
    signupForm.addEventListener('submit', e => {
      e.preventDefault();
      window.location.href = 'login.html';
    });
  }

  // FAKE LOGOUT LINK (must exist in your #nav-auth)
  const logoutLink = document.querySelectorAll('a[href="logout.html"]').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      localStorage.removeItem('yumlog_user');   // clear session
      window.location.href = 'index.html';      // go to guest homepage
    });
  });
});

// Toggle guest vs auth discovery
const guestSection = document.getElementById('guest-discovery');
const authSection  = document.getElementById('auth-discovery');
if (guestSection && authSection) {
  if (isLoggedIn()) {
    guestSection.style.display = 'none';
    authSection.style.display  = 'block';
  } else {
    guestSection.style.display = 'block';
    authSection.style.display  = 'none';
  }
}

// Tab switching (both versions)
document.querySelectorAll('.tabs').forEach(tabContainer => {
  const btns = tabContainer.querySelectorAll('.tab-btn');
  btns.forEach(b => b.addEventListener('click', () => {
    btns.forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    // TODO: swap content like filters vs top rated if you wish
  }));
});

// Filter button toggle
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => btn.classList.toggle('active'));
});

// show/hide list vs map
document.querySelectorAll('[data-action="show-map"]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.getElementById('guest-list').style.display = 'none';
    document.getElementById('auth-list').style.display  = 'none';
    document.getElementById('guest-map').style.display  = isLoggedIn() ? 'none' : 'flex';
    document.getElementById('auth-map').style.display   = isLoggedIn() ? 'flex' : 'none';
  });
});
document.querySelectorAll('[data-action="back-to-list"]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.getElementById('guest-map').style.display  = 'none';
    document.getElementById('auth-map').style.display   = 'none';
    document.getElementById('guest-list').style.display = isLoggedIn() ? 'none' : 'block';
    document.getElementById('auth-list').style.display  = isLoggedIn() ? 'block' : 'none';
  });
});

// COMMUNITY: Heart “like” buttons
document.querySelectorAll('.fav-icon').forEach(icon => {
  // disable guest hearts
  if (!isLoggedIn()) icon.classList.add('disabled');

  icon.addEventListener('click', () => {
    if (!isLoggedIn()) return;         // guests do nothing
    icon.classList.toggle('liked');    // toggle fill
  });
});

// COMMUNITY: Poll options
document.querySelectorAll('.poll-option').forEach(opt => {
  // disable guest poll buttons
  if (!isLoggedIn()) opt.classList.add('disabled');

  opt.addEventListener('click', () => {
    if (!isLoggedIn()) return;         // guests do nothing
    // clear previous selection
    document.querySelectorAll('.poll-option')
      .forEach(o => o.classList.remove('selected'));
    opt.classList.add('selected');
  });
});
