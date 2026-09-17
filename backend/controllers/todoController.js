const Todo = require('../models/Todo');

exports.getTodos = async (req, res) => {
    try {
        const todos = await Todo.find({ userId: req.user.id });
        res.status(200).json(todos);
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Server error' });
    }
};

exports.createTodo = async (req, res) => {
    try {
        const { title, priority } = req.body;
        const newTodo = new Todo({
            userId: req.user.id,
            title,
            priority
        });

        const savedTodo = await newTodo.save();
        res.status(201).json(savedTodo);
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Server error' });
    }
};

exports.updateTodo = async (req, res) => {
    try {
        const { title, completed, priority } = req.body;
        let todo = await Todo.findById(req.params.id);

        if (!todo) {
            return res.status(404).json({ message: 'Todo not found' });
        }

        if (todo.userId.toString() !== req.user.id) {
            return res.status(401).json({ message: 'Not authorized' });
        }

        if (title !== undefined) todo.title = title;
        if (completed !== undefined) todo.completed = completed;
        if (priority !== undefined) todo.priority = priority;

        await todo.save();
        res.status(200).json(todo);
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Server error' });
    }
};

exports.deleteTodo = async (req, res) => {
    try {
        let todo = await Todo.findById(req.params.id);

        if (!todo) {
            return res.status(404).json({ message: 'Todo not found' });
        }

        if (todo.userId.toString() !== req.user.id) {
            return res.status(401).json({ message: 'Not authorized' });
        }

        await todo.deleteOne();
        res.status(200).json({ message: 'Todo removed' });
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Server error' });
    }
};
