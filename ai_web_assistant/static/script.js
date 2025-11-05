const form = document.getElementById("chat-form");
const input = document.getElementById("user_input");
const output = document.getElementById("chat-output");

form.addEventListener("submit", function(e) {
    e.preventDefault();
    const userMessage = input.value;
    output.innerHTML += `<p><b>You:</b> ${userMessage}</p>`;
    input.value = "";

    const evtSource = new EventSource("/chat?user_input=" + encodeURIComponent(userMessage));
    
    evtSource.onmessage = function(event) {
        output.innerHTML += `<p><b>AI:</b> ${event.data}</p>`;
        output.scrollTop = output.scrollHeight;
    };
    
    evtSource.onerror = function() {
        evtSource.close();
    };
});
