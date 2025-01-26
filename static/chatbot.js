document.addEventListener("DOMContentLoaded", function () {
    let name = localStorage.getItem("username");
    let age = localStorage.getItem("age");
    let gender = localStorage.getItem("gender");

    // Fetch session data and user name on page load (Sending token to backend to get Name and to maintain context)
  fetch("/start_chatbot_session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name:name,age:age,gender:gender }),
  })
  
    .then((response) => {
      if (!response.ok) throw new Error("Failed to start session");
      return response.json();
    })
    .then((data) => {
      // Show a greeting message using the fetched user name
      const userName = data.name || "User"; // Default to "User" if name is not provided
      appendMessage(`Hello, ${userName}! How can I assist you today?`, "bot");
    })
    .catch((error) => {
      console.error("Error:", error);
      appendMessage("Sorry, something went wrong while starting the session.", "bot");
    });



    // Your code here
    document.getElementById("send_button").addEventListener("click", handleSend);
    
    document.getElementById("input_container").addEventListener("keypress", function (event) {
      if (event.key === "Enter") {
        handleSend();
        event.preventDefault(); // Prevent form submission if inside a form
      }
    });
  
    function handleSend() {
      let inputContainer = document.getElementById("input_container");
  
      // Get user message from input
      let userMessage = inputContainer.value.trim();
  
      if (userMessage === "") return; // Don't send empty messages
  
      // Append user message to chatbot container
      appendMessage(userMessage, "user");
  
      // Clear the input field
      inputContainer.value = "";
  


      // Send the message to the backend
      fetch("/chatbot_response", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userMessage }),
      })
        .then((response) => {
          if (!response.ok) throw new Error("Network response was not ok");
          return response.json();
        })
        .then((data) => {
          // Append the chatbot response to the chatbot container
          appendMessage(data.response, "bot");
        })
        .catch((error) => {
          console.error("Error:", error);
          appendMessage("Sorry, something went wrong. Please try again.", "bot");
        });
    }



  
    // Function to append messages to the chatbot container
    function appendMessage(message, sender) {
      let chatbotContainer = document.getElementById("chatbot_container");
  
      // Create a message element as a DOM node
      let messageElement = document.createElement("div");
      messageElement.className = sender === "user" ? "flex justify-end" : "flex justify-start";
      messageElement.innerHTML = `
        <div class="${sender === "user" ? "bg-indigo-700" : "bg-white text-black"} p-3 rounded-lg shadow-md max-w-xs">
          ${message}
        </div>
      `;
  
      // Append the message element to the chatbot container
      chatbotContainer.appendChild(messageElement);
  
      // Scroll to the latest message
      chatbotContainer.scrollTop = chatbotContainer.scrollHeight;
    }
  });
  