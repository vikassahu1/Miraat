const BASE_URL = 'http://127.0.0.1:8000';



// Register with Email/Password
// Register User
async function register() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const name = document.getElementById("name").value;
    const age = parseInt(document.getElementById("age").value, 10);
    const gender = document.getElementById("gender").value;

    // Validation
    if (!email || !password || !name || !age || !gender) {
        alert("All fields are required.");
        return;
    }

    if (password.length < 6) {
        alert("Password should be at least 6 characters long.");
        return;
    }

    if (age < 1 || age > 120) {
        alert("Age is not valid.");
        return;
    }

    try {
        // Make a POST request to the new /register endpoint
        const response = await fetch(`${BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                hashed_password: password, // Send password in hashed_password field
                name,
                age,
                gender,
            }),
        });

        const responseData = await response.json();
        if (response.ok) {
            alert("Registration successful!");
        } else {
            alert(`Registration failed: ${responseData.detail || 'Unknown error'}`);
        }
    } catch (error) {
        alert(`Registration error: ${error.message}`);
    }
}






// Login User
async function login() {
    const username = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    if (!username || !password) {
        alert("Please enter both username and password.");
        return;
    }

    try {
        // Prepare form data for the /token endpoint
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        // Make a POST request to the new /token endpoint
        const response = await fetch(`${BASE_URL}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
        });

        const data = await response.json();
        if (response.ok) {
            // Save the token to localStorage or use it directly
            localStorage.setItem("authToken", data.access_token);
            localStorage.setItem("username", data.username);
            localStorage.setItem("age",data.age);
            localStorage.setItem("gender", data.gender);
            
            alert("Login successful!");
            

            window.location.href = "/";
        } else {
            alert(`Login failed: ${data.detail || 'Unknown error'}`);
        }
    } catch (error) {
        alert(`Error during login: ${error.message}`);
    }
}







// Bind functions to global window object for accessibility
window.register = register;
window.login = login;
