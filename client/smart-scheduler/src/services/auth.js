export function setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    let name = cname + "=";
    let ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

// function to get refresh token
export async function refreshToken() {
    try {
        const response = await fetch('http://localhost:8000/api/v1/users/token', {
            method: 'GET',
            credentials: 'include'  // includes the cookies
        });

        if (response.ok) {
            const data = await response.json();
            const newToken = data.access_token;
            localStorage.setItem("token", newToken);

            console.log("Refresh token successful")
        } else {
            console.error('Failed to refresh token:', response.statusText);
        }
    } catch (error) {
        console.error('Error refreshing token:', error);
    }
}

setInterval(refreshToken, 15 * 60 * 1000); // Refresh token every 15 minl

export async function logout() {
    const token = localStorage.getItem("token"); 
    if (!token) {
      console.error("No token found");
      return;
    }
    try {
      const response = await fetch('http://localhost:8000/api/v1/users/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          credentials: "include",
        });

        if (response.status === 204) {
            localStorage.removeItem('token');
            this.$router.push('/');
          console.log('Logout sucessful.')
        } else {
          console.error('Failed to log out:', response.statusText);
        }
    }
    catch {
      console.error('Error logging out:', error);
    }
  }