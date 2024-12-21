BASE_URL = 'http://127.0.0.1:8000';


// For getting the disease information 
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
                processDisorders(data.disorder); 
            }
        } catch (error) {
            console.error("Error:", error);
            document.getElementById("resultDiv").innerHTML =
                "<p>Something went wrong. Please try again.</p>";
        }
    });
});







async function processDisorders(disorder) {
    const resultDiv = document.getElementById("resultDiv");

    const paragraph = document.createElement("p");
    paragraph.innerHTML = "<b>Starting Assessments One-by-One</b>";
    resultDiv.appendChild(paragraph);


    for (const [disorderName, details] of Object.entries(disorder)) {
        for (const [subcategory, subcategoryDetails] of Object.entries(details.Subcategories)) {
            const subcategoryParagraph = document.createElement("p");
            subcategoryParagraph.innerHTML = `<b>${subcategory}</b>`;
            resultDiv.appendChild(subcategoryParagraph);

            if (subcategoryDetails.Tests) {
                for (const test of subcategoryDetails.Tests) {
                    const testParagraph = document.createElement("p");
                    testParagraph.innerHTML = `<b>Test: ${test}</b>`;
                    resultDiv.appendChild(testParagraph);
                    
                    console.log('Fetching questions for:', disorderName, subcategory, test);

                    try {
                        const response = await fetch(`${BASE_URL}/get_test_questions/`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ disorder_name: disorderName, sub_category: subcategory, test }),
                        });

                        const data = await response.json();
                        if (response.ok && data.questions) {
                            const questions = data.questions;
                            console.log(`Rendering test: ${test}`);
                            const inference = await renderfunction(subcategory,test, questions);

                            const inferencePara = document.createElement("p");
                            inferencePara.innerHTML = `<b>Inference:</b> ${inference.inference}`;
                            resultDiv.appendChild(inferencePara);
                        } else {
                            console.error(`No questions found for test: ${test}`);
                            const errorPara = document.createElement("p");
                            errorPara.innerHTML = `<b>Error:</b> No questions available for test: ${test}`;
                            resultDiv.appendChild(errorPara);
                        }
                    } catch (error) {
                        console.error('Error while fetching questions:', error);
                        const errorPara = document.createElement("p");
                        errorPara.innerHTML = `<b>Error:</b> Unable to fetch questions for test: ${test}. Please try again later.`;
                        resultDiv.appendChild(errorPara);
                    }
                }
            }
        }
    }
}









async function renderfunction(subcategory,test, list_of_questions) {
    return new Promise((resolve, reject) => {
        if (!Array.isArray(list_of_questions)) {
            console.error("list_of_questions is not an array. Details:", list_of_questions);
            return reject("Invalid question data.");
        }

        const resultDiv = document.getElementById('two');
        resultDiv.innerHTML = ""; // Clear previous test

        const form = document.createElement('form');
        form.id = 'dynamicTestForm';

        for (const obj of list_of_questions) {
            const question_id = obj.question_id;
            const question = obj.question_text;
            const options = obj.options;

            // Create a wrapper for the question
            const questionWrapper = document.createElement('div');
            questionWrapper.className = 'question-item';

            const questionText = document.createElement('p');
            questionText.textContent = `${question_id}. ${question}`;
            questionWrapper.appendChild(questionText);



            // Options value are changing to counters for easy calculation
            let counter = 1;
            options.forEach(({ option_id, text }) => {
                const optionWrapper = document.createElement('div');

                const input = document.createElement('input');
                input.type = 'radio';
                input.name = `${question_id}`;
                input.value = `${counter}`;
                input.id = `question_${question_id}_option_${option_id}`;

                const label = document.createElement('label');
                label.htmlFor = input.id;
                label.textContent = text;

                optionWrapper.appendChild(input);
                optionWrapper.appendChild(label);
                questionWrapper.appendChild(optionWrapper);
                counter++;
            });

            form.appendChild(questionWrapper);
        }


        
        // Add a submit button to the form
        const submitButton = document.createElement('button');
        submitButton.type = 'submit';
        submitButton.textContent = 'Submit Answers';
        form.appendChild(submitButton);

        // Append the form to the resultDiv
        resultDiv.appendChild(form);

        // Handle form submission
        form.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent default form submission

            const formData = new FormData(form);
            const answers = {};

            // key is name attribute of the Form 
            for (const [key, value] of formData.entries()) {
                answers[key] =value; // Collect answers
            }

            const testName = test; // Assuming test contains the name of the test
            const subcat = subcategory;
            console.log('Submitted Answers:', answers);



            try {
                const res = await fetch(`${BASE_URL}/get_inference_from_test/`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                        test_name: testName,
                        subcategory: subcat,
                        answers: answers
                    }),
                });

                if (!res.ok) {
                    const errorText = await res.text();
                    throw new Error(`HTTP error! status: ${res.status}, message: ${errorText}`);
                }
            


                // Inferenvce part of the test 
                const inference = await res.json();
                console.log("Inference received:", inference);
                resolve(inference);
            } catch (error) {
                console.error("Detailed error during submission:", error);
                reject(error);
            }

        });
    });
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



