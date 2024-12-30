import {
    initializeApp
} from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-app.js';
import {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    GoogleAuthProvider,
    signInWithPopup
} from 'https://www.gstatic.com/firebasejs/9.22.1/firebase-auth.js';




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
const BASE_URL = 'http://127.0.0.1:8000';






// Register with Email/Password
async function register() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const name  = document.getElementById("name").value;
    const age = document.getElementById("age").value;
    const gender = document.getElementById("gender").value;

    if (!email || !password) {
        alert("Please enter both email and password");
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
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const token = await userCredential.user.getIdToken();
        
        const response = await fetch(`${BASE_URL}/register-user/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token, name, age, gender })
        });

        const responseData = await response.json();
        if (response.ok) {

            // local storage token set to check registration status
            // localStorage.setItem('authToken', token);

            alert("Registration successful!");
        } else {
            alert(`Registration failed: ${responseData.detail || 'Unknown error'}`);
        }
    } catch (error) {
        alert(`Registration error: ${error.message}`);
    }
}







// Login with Email/Password
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
            },
            body: JSON.stringify({ token })
        });

        const data = await response.json();
        if (response.ok) {

            // local storage token set to check login status
            localStorage.setItem('authToken', token);
            alert("Login successful!");

            // On sucess =ful login the page will go back to the home.
            // window.location.href = '/';

            
        } else {
            alert("Error during login: " + data.detail);
        }
    } catch (error) {
        alert("Error during login: " + error.message);
    }
}






// Google Login/Registration
async function googleAuth() {
    const provider = new GoogleAuthProvider();
    try {
        const result = await signInWithPopup(auth, provider);
        const token = await result.user.getIdToken();
        
        const response = await fetch(`${BASE_URL}/verify-token/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token })
        });

        const data = await response.json();
        if (response.ok) {
            alert("Google Authentication successful!");
        } else {
            alert("Error during Google Authentication: " + data.detail);
        }
    } catch (error) {
        alert("Google Authentication error: " + error.message);
    }
}





window.register = register;
window.login = login;
window.googleAuth = googleAuth;
