document.addEventListener('DOMContentLoaded', () => {
    const taskInput = document.getElementById('taskInput');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const taskList = document.getElementById('taskList');

    const API_URL = '/tasks';

    // Fetch and display tasks
    async function fetchTasks() {
        try {
            const response = await fetch(API_URL);
            if (!response.ok) throw new Error('Failed to fetch tasks');
            const tasks = await response.json();
            renderTasks(tasks);
        } catch (error) {
            console.error('Error fetching tasks:', error);
        }
    }

    // Render tasks to the DOM
    function renderTasks(tasks) {
        taskList.innerHTML = '';
        tasks.forEach(task => {
            const li = document.createElement('li');
            li.textContent = task.title || task.name || 'Untitled Task';
            taskList.appendChild(li);
        });
    }

    // Add a new task
    async function addTask() {
        const title = taskInput.value.trim();
        if (!title) return;

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title })
            });

            if (!response.ok) throw new Error('Failed to add task');
            
            taskInput.value = '';
            fetchTasks(); // Refresh the list
        } catch (error) {
            console.error('Error adding task:', error);
        }
    }

    addTaskBtn.addEventListener('click', addTask);
    taskInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addTask();
    });

    // Initial fetch
    fetchTasks();
});
