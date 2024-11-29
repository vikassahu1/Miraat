BASE_URL = 'http://127.0.0.1:8000';



document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed");

    document.getElementById("submitButton").addEventListener("click", async function (e) {
        e.preventDefault(); // Prevent default form submission behavior
        console.log("Submit button clicked");

        const inputText = document.getElementById("textInput").value;
        console.log("Input text:", inputText);

        try {
            const response = await fetch(`${BASE_URL}/assess_text/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ text: inputText }),
            });

            const data = await response.json();
            console.log("Parsed data:", data);

            const resultDiv = document.getElementById("resultDiv");
            resultDiv.innerHTML = ""; // Clear previous results

            if (data.disorder === "no disorder") {
                resultDiv.innerHTML = "<p>No disorders detected.</p>";
            } else {
                const disorderList = buildDisorderList(data.disorder);
                resultDiv.appendChild(disorderList);
            }
        } catch (error) {
            console.error("Error:", error);
            document.getElementById("resultDiv").innerHTML =
                "<p>Something went wrong. Please try again.</p>";
        }
    });
});



async function processDisorders(disorders) {
    const results = []; 
    for (const disorder of disorders) {
        try {
            // Send a POST request for each disorder
            const response = await fetch(`${BASE_URL}/process_disorder/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ disorder }), // Send the disorder as input
            });

            const data = await response.json();
            console.log(`Response for ${disorder}:`, data);

            // Store the response
            results.push({ disorder, ...data });
        } catch (error) {
            console.error(`Error processing ${disorder}:`, error);
            results.push({ disorder, error: "Failed to process" });
        }
    }

    // Do something with the results
    console.log("All results:", results);
    updateUIWithResults(results);
}


function buildDisorderList(disorder) {
    const ul = document.createElement("ul");

    for (const [disorderName, details] of Object.entries(disorder)) {
        const disorderLi = document.createElement("li");
        disorderLi.innerHTML = `<strong>${disorderName}</strong>`;

        if (details.Subcategories) {
            const subcategoriesUl = document.createElement("ul");

            for (const [subcategory, subcategoryDetails] of Object.entries(details.Subcategories)) {
                const subcategoryLi = document.createElement("li");
                subcategoryLi.innerHTML = `<strong>${subcategory}</strong>`;

                if (subcategoryDetails.Tests) {
                    const testsUl = document.createElement("ul");

                    subcategoryDetails.Tests.forEach((test) => {
                        const testLi = document.createElement("li");
                        testLi.innerText = test;
                        testsUl.appendChild(testLi);
                    });

                    subcategoryLi.appendChild(testsUl);
                }

                subcategoriesUl.appendChild(subcategoryLi);
            }

            disorderLi.appendChild(subcategoriesUl);
        }

        ul.appendChild(disorderLi);
    }

    return ul;
}




// Update the UI with results
function updateUIWithResults(results) {
    const resultDiv = document.getElementById("resultDiv");
    resultDiv.innerHTML = ""; // Clear previous results
    results.forEach(({ disorder, message, error }) => {
        const p = document.createElement("p");
        p.innerText = error
            ? `Failed to process ${disorder}: ${error}`
            : `Result for ${disorder}: ${message}`;
        resultDiv.appendChild(p);
    });
}





