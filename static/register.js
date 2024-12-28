import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-app.js';

import { 
    getAuth, 
    createUserWithEmailAndPassword, 
    signInWithEmailAndPassword 
} from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-auth.js';

//Base address will be changed once setup done .
const BASE_URL = 'http://127.0.0.1:8000';

// Initialize Firebase
const firebaseConfig = {
    apiKey: "AIzaSyBZG00jAPncsR6BoXquQXI8-fM7qHGHC1c",
    authDomain: "miraat-54aac.firebaseapp.com",
    projectId: "miraat-54aac",
    storageBucket: "miraat-54aac.firebasestorage.app",
    messagingSenderId: "600850679847",
    appId: "1:600850679847:web:4dd0593ae7c247087ce602",
    measurementId: "G-QHL8SL2GBY"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);




async function register() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    
    if (!email || !password) {
        alert("Please enter both email and password");
        return;
    }
    
    if (password.length < 6) {
        alert("Password should be at least 6 characters long.");
        return;
    }    
    
    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const token = await userCredential.user.getIdToken();
        console.log("Generated Token:", token);  // Log token for debugging
        
        const response = await fetch(`${BASE_URL}/register-user/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token })
        });

        const responseData = await response.json();
        console.log("Server Response:", responseData);  // Log full server response

        if (response.ok) {
            alert("Registration successful!");
        } else {
            alert(`Registration failed: ${responseData.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error("Full Error Object:", error);
        alert(`Registration error: ${error.message}`);
    }
}



async function login() {
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const token = await userCredential.user.getIdToken();

        const response = await fetch(`${BASE_URL}/verify-token/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ token })
        });

        const data = await response.json();
        if (response.ok) {
            alert("Login successful!");
        } else {
            alert("Error during login: " + data.detail);
        }
    } catch (error) {
        console.error("Error during login:", error);
        alert("Error during login: " + error.message);
    }
}

window.register = register;
window.login = login;

