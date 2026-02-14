const contactsList = document.getElementById('contacts-list');
const chatOutput = document.getElementById('chat-output');
const chatForm = document.getElementById('chat-form');
const promptInput = document.getElementById('prompt-input');
const submitButton = chatForm.querySelector('button[type="submit"]');


async function fetchContacts() {
    try {
        const response = await fetch('/api/contacts');
        const jsonResponse = await response.json();

        const contactsArray = jsonResponse.data.data;

        contactsList.innerHTML = '';

        if (!contactsArray || contactsArray.length === 0) {
            contactsList.innerHTML = '<li class="text-gray-500 italic">No contacts in database.</li>';
            return;
        }

        contactsArray.forEach(contact => {
            const li = document.createElement('li');
            li.className = "flex justify-between items-center bg-gray-50 p-2 rounded border border-gray-200";
            li.innerHTML = `
                <span class="font-bold text-gray-700">${contact.name}</span>
                <span class="text-blue-600 font-mono">${contact.phone}</span>
            `;
            contactsList.appendChild(li);
        });
    } catch (error) {
        console.error("Error fetching contacts:", error);
        contactsList.innerHTML = '<li class="text-red-500">Connection error.</li>';
    }
}

// Chat UI Helper 
function addMessageToChat(role, text) {
    const msgDiv = document.createElement('div');
    

    let baseClass = "p-3 rounded-lg max-w-[85%] border ";
    
    if (role === 'user') {
        baseClass += "bg-blue-100 text-blue-900 self-end border-blue-200";
    } else {
        if (typeof text === 'object' && text.success === false) {
            baseClass += "bg-red-100 text-red-900 self-start border-red-200";
        } else {
            baseClass += "bg-green-100 text-green-900 self-start border-green-200";
        }
    }
    
    msgDiv.className = baseClass;
    
    if (typeof text === 'object') {
        msgDiv.innerHTML = `
            <pre class="text-xs font-mono whitespace-pre-wrap break-words">${JSON.stringify(text, null, 2)}</pre>
        `;
    } else {
        msgDiv.textContent = text;
    }

    chatOutput.appendChild(msgDiv);
    chatOutput.scrollTop = chatOutput.scrollHeight;
}

// Event Listeners
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const userText = promptInput.value.trim();
    if (!userText) return;

    addMessageToChat('user', userText);
    promptInput.value = ''; 
    
    submitButton.disabled = true;
    submitButton.textContent = 'Thinking...';
    submitButton.classList.add('opacity-50', 'cursor-not-allowed');

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: userText })
        });

        const data = await response.json();

        if (data.status === 'success') {
            addMessageToChat('ai', `Executed: ${data.action}`);
            addMessageToChat('ai', data.message); 
            
            // Refresh contact list
            fetchContacts();
        } else {
            addMessageToChat('ai', data.message);
        }

    } catch (error) {
        console.error("AI Communication Error:", error);
        addMessageToChat('ai', 'Connection to AI server failed.');
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Send';
        submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
    }
});

fetchContacts();